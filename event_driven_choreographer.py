"""
Event-Driven Choreographer for Policy Analysis
===============================================

Implements event-driven choreography pattern where components
react independently to events without central orchestration.

Features:
- Components subscribe to events they can process
- Validation happens distributively in components
- Events carry QuestionContext for validation
- Full traceability via correlation IDs
- Deterministic processing with seeding

Author: FARFAN Integration Team
Version: 1.0.0
Python: 3.11+
"""

import logging
import random
import time
import uuid
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from event_bus import EventBus, get_event_bus
from events import (
    BaseEvent,
    EventType,
    EventStatus,
    AnalysisRequestedEvent,
    ChunkingCompleteEvent,
    ValidationFailedEvent,
    ProcessingFailedEvent,
    QuestionContext,
)
from metadata_service import MetadataService
from traceability_service import TraceabilityService

logger = logging.getLogger(__name__)


@dataclass
class ChoreographyConfig:
    """
    Configuration for event-driven choreography
    
    Attributes:
        enable_traceability: Enable traceability tracking
        deterministic_seed: Seed for deterministic behavior (None = non-deterministic)
        validation_mode: Validation mode (strict, lenient, disabled)
        max_retry_count: Maximum retries for failed processing
    """
    
    enable_traceability: bool = True
    deterministic_seed: Optional[int] = 42
    validation_mode: str = "strict"
    max_retry_count: int = 3


class EventDrivenChoreographer:
    """
    Event-driven choreographer implementing decentralized coordination
    
    Components subscribe to events and publish new events autonomously.
    The choreographer initializes components and coordinates startup/shutdown.
    """
    
    def __init__(
        self,
        metadata_service: MetadataService,
        event_bus: Optional[EventBus] = None,
        config: Optional[ChoreographyConfig] = None,
    ):
        """
        Initialize event-driven choreographer
        
        Args:
            metadata_service: MetadataService for question context
            event_bus: EventBus instance (uses global if not provided)
            config: Choreography configuration
        """
        self.metadata_service = metadata_service
        self.event_bus = event_bus or get_event_bus()
        self.config = config or ChoreographyConfig()
        
        # Traceability
        self.traceability_service: Optional[TraceabilityService] = None
        if self.config.enable_traceability:
            self.traceability_service = TraceabilityService(metadata_service)
            self._subscribe_traceability()
        
        # Set deterministic seed if configured
        if self.config.deterministic_seed is not None:
            random.seed(self.config.deterministic_seed)
            logger.info(f"Set deterministic seed: {self.config.deterministic_seed}")
        
        # Component registry
        self.components: Dict[str, Any] = {}
        
        logger.info("EventDrivenChoreographer initialized")
    
    def _subscribe_traceability(self) -> None:
        """Subscribe traceability service to all events"""
        if not self.traceability_service:
            return
        
        def record_event(event: BaseEvent) -> None:
            self.traceability_service.record_event(event)
        
        # Subscribe to all event types
        all_event_types = [event_type for event_type in EventType]
        
        self.event_bus.subscribe(
            subscriber_id="traceability_service",
            event_types=all_event_types,
            callback=record_event,
        )
        
        logger.info("Traceability service subscribed to all events")
    
    def register_component(
        self,
        component_name: str,
        component: Any,
        subscribed_events: List[EventType],
        published_events: List[EventType],
    ) -> None:
        """
        Register a component in the choreography
        
        Args:
            component_name: Name of the component
            component: Component instance
            subscribed_events: Events this component subscribes to
            published_events: Events this component can publish
        """
        self.components[component_name] = component
        
        # Register with traceability
        if self.traceability_service:
            module_path = component.__class__.__module__
            class_name = component.__class__.__name__
            
            self.traceability_service.register_component(
                component_name=component_name,
                module_path=module_path,
                class_name=class_name,
                subscribed_events=subscribed_events,
                published_events=published_events,
            )
        
        logger.info(
            f"Registered component {component_name} "
            f"(subscribes to {len(subscribed_events)} events)"
        )
    
    def start_analysis(
        self,
        document_reference: str,
        target_question_ids: List[str],
        plan_name: str,
        plan_text: str,
    ) -> str:
        """
        Start policy analysis by publishing AnalysisRequestedEvent
        
        Args:
            document_reference: Reference to document
            target_question_ids: Questions to analyze
            plan_name: Name of plan
            plan_text: Full plan text
            
        Returns:
            Correlation ID for tracking
        """
        correlation_id = str(uuid.uuid4())
        
        logger.info(
            f"Starting analysis for {len(target_question_ids)} questions "
            f"(correlation_id={correlation_id})"
        )
        
        # Publish initial event for each question
        for question_id in target_question_ids:
            event = AnalysisRequestedEvent(
                correlation_id=correlation_id,
                question_id=question_id,
                document_reference=document_reference,
                target_question_ids=target_question_ids,
                plan_name=plan_name,
                plan_text=plan_text,
            )
            
            self.event_bus.publish(event)
        
        return correlation_id
    
    def get_analysis_status(self, correlation_id: str) -> Dict[str, Any]:
        """
        Get status of analysis by correlation ID
        
        Args:
            correlation_id: Correlation ID to check
            
        Returns:
            Status information
        """
        if not self.traceability_service:
            return {"error": "Traceability not enabled"}
        
        trace = self.traceability_service.get_correlation_trace(correlation_id)
        
        if not trace:
            return {"status": "not_found"}
        
        return {
            "question_id": trace.question_id,
            "status": trace.status,
            "events": len(trace.events),
            "components": list(trace.components),
            "start_time": trace.start_time,
            "end_time": trace.end_time,
        }
    
    def get_traceability_report(self) -> str:
        """
        Get traceability report
        
        Returns:
            Formatted report string
        """
        if not self.traceability_service:
            return "Traceability not enabled"
        
        return self.traceability_service.generate_report()
    
    def shutdown(self) -> None:
        """Shutdown choreographer and cleanup"""
        logger.info("Shutting down EventDrivenChoreographer")
        
        # Unsubscribe traceability
        if self.traceability_service:
            self.event_bus.unsubscribe("traceability_service")


class EventDrivenComponent:
    """
    Base class for event-driven components
    
    Components extend this class and implement:
    - on_event() to handle incoming events
    - validate_input() to validate event data
    - process() to execute component logic
    - emit_events() to publish result events
    """
    
    def __init__(
        self,
        component_name: str,
        event_bus: EventBus,
        metadata_service: MetadataService,
    ):
        """
        Initialize component
        
        Args:
            component_name: Name of this component
            event_bus: EventBus for pub/sub
            metadata_service: MetadataService for context
        """
        self.component_name = component_name
        self.event_bus = event_bus
        self.metadata_service = metadata_service
        self.logger = logging.getLogger(f"{__name__}.{component_name}")
    
    def on_event(self, event: BaseEvent) -> None:
        """
        Handle incoming event
        
        Args:
            event: Event to process
        """
        self.logger.debug(
            f"Received {event.event_type.value} (event_id={event.event_id[:8]}...)"
        )
        
        try:
            # Get question context if available
            question_context = None
            if event.question_id:
                question_context = self.metadata_service.get_question_context(
                    event.question_id
                )
            
            # Validate input
            validation_errors = self.validate_input(event, question_context)
            
            if validation_errors:
                self.logger.warning(
                    f"Validation failed for {event.event_type.value}: "
                    f"{validation_errors}"
                )
                self._emit_validation_failed(event, validation_errors, question_context)
                return
            
            # Process event
            result = self.process(event, question_context)
            
            # Emit result events
            self.emit_events(event, result, question_context)
            
        except Exception as e:
            self.logger.error(
                f"Error processing {event.event_type.value}: {e}",
                exc_info=True
            )
            self._emit_processing_failed(event, e)
    
    def validate_input(
        self,
        event: BaseEvent,
        question_context: Optional[QuestionContext]
    ) -> List[str]:
        """
        Validate input event data
        
        Args:
            event: Event to validate
            question_context: Question context with validation rules
            
        Returns:
            List of validation errors (empty if valid)
        """
        # Override in subclass to implement validation
        return []
    
    def process(
        self,
        event: BaseEvent,
        question_context: Optional[QuestionContext]
    ) -> Any:
        """
        Process event and return result
        
        Args:
            event: Event to process
            question_context: Question context
            
        Returns:
            Processing result
        """
        # Override in subclass to implement processing
        raise NotImplementedError(
            f"{self.component_name}.process() not implemented"
        )
    
    def emit_events(
        self,
        original_event: BaseEvent,
        result: Any,
        question_context: Optional[QuestionContext]
    ) -> None:
        """
        Emit result events
        
        Args:
            original_event: Original event that triggered processing
            result: Processing result
            question_context: Question context
        """
        # Override in subclass to emit appropriate events
        pass
    
    def _emit_validation_failed(
        self,
        event: BaseEvent,
        validation_errors: List[str],
        question_context: Optional[QuestionContext]
    ) -> None:
        """Emit validation failed event"""
        failed_event = ValidationFailedEvent(
            correlation_id=event.correlation_id,
            question_id=event.question_id,
            component_name=self.component_name,
            validation_errors=validation_errors,
            failed_rules=[],  # TODO: Extract rule names
            input_data_summary={
                "event_type": event.event_type.value,
                "event_id": event.event_id,
            },
            remediation_hint="Check input data against validation rules",
        )
        
        self.event_bus.publish(failed_event)
    
    def _emit_processing_failed(
        self,
        event: BaseEvent,
        error: Exception
    ) -> None:
        """Emit processing failed event"""
        failed_event = ProcessingFailedEvent(
            correlation_id=event.correlation_id,
            question_id=event.question_id,
            component_name=self.component_name,
            error_type=type(error).__name__,
            error_message=str(error),
            stack_trace=None,  # Could add traceback here
            retry_count=0,
            can_retry=True,
        )
        
        self.event_bus.publish(failed_event)
