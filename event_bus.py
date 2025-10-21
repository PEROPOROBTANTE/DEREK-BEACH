"""
Event Bus - Asynchronous Communication between Orchestrator and Choreographer
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Callable, Awaitable, Set
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import json
from pathlib import Path

from event_schemas import (
    EventType,
    EventMetadata,
    ContextPropagation,
    SubProcessInitiatedEvent,
    SubProcessCompletedEvent,
    SubProcessFailedEvent,
    get_event_schema_registry
)

logger = logging.getLogger(__name__)


@dataclass
class EventRecord:
    """Record of an event for audit trail"""
    event_type: EventType
    event_data: Dict[str, Any]
    timestamp: str
    correlation_id: Optional[str] = None
    workflow_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "event_type": self.event_type.value,
            "event_data": self.event_data,
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id,
            "workflow_id": self.workflow_id
        }


EventHandler = Callable[[Dict[str, Any]], Awaitable[None]]


class EventBus:
    """
    Event bus for asynchronous event-driven communication
    
    Enables Orchestrator and Choreographer to communicate through events
    without direct coupling. Events are validated against schemas and
    routed to registered handlers.
    
    ORCHESTRATOR USAGE:
    - Publish SubProcessInitiatedEvent to trigger choreography
    - Subscribe to SubProcessCompletedEvent/SubProcessFailedEvent for outcomes
    
    CHOREOGRAPHER USAGE:
    - Subscribe to SubProcessInitiatedEvent to receive work
    - Publish SubProcessCompletedEvent/SubProcessFailedEvent to report outcomes
    """
    
    def __init__(
        self,
        enable_persistence: bool = True,
        persistence_dir: Optional[Path] = None
    ):
        """
        Initialize event bus
        
        Args:
            enable_persistence: Whether to persist events to disk
            persistence_dir: Directory for event persistence
        """
        self._handlers: Dict[EventType, List[EventHandler]] = defaultdict(list)
        self._event_history: List[EventRecord] = []
        self._pending_correlations: Dict[str, Dict[str, Any]] = {}
        self._dead_letter_queue: List[Dict[str, Any]] = []
        
        self.enable_persistence = enable_persistence
        self.persistence_dir = persistence_dir or Path("./events")
        if self.enable_persistence:
            self.persistence_dir.mkdir(exist_ok=True, parents=True)
        
        self._schema_registry = get_event_schema_registry()
        
        # Metrics
        self._metrics = {
            "total_published": 0,
            "total_delivered": 0,
            "total_failed": 0,
            "by_event_type": defaultdict(int),
            "by_correlation": defaultdict(int)
        }
        
        logger.info("EventBus initialized")
    
    def subscribe(
        self,
        event_type: EventType,
        handler: EventHandler
    ) -> None:
        """
        Subscribe to an event type
        
        Args:
            event_type: Type of event to subscribe to
            handler: Async function to handle events
        """
        self._handlers[event_type].append(handler)
        logger.info(f"Handler subscribed to {event_type.value}")
    
    def unsubscribe(
        self,
        event_type: EventType,
        handler: EventHandler
    ) -> None:
        """
        Unsubscribe from an event type
        
        Args:
            event_type: Type of event to unsubscribe from
            handler: Handler to remove
        """
        if event_type in self._handlers and handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
            logger.info(f"Handler unsubscribed from {event_type.value}")
    
    async def publish(
        self,
        event_type: EventType,
        event_data: Dict[str, Any],
        validate: bool = True
    ) -> bool:
        """
        Publish an event to the bus
        
        Args:
            event_type: Type of event
            event_data: Event payload
            validate: Whether to validate against schema
            
        Returns:
            True if event was published successfully
        """
        # Validate event if requested
        if validate:
            is_valid, errors = self._schema_registry.validate_event(
                event_type,
                event_data
            )
            if not is_valid:
                logger.error(
                    f"Event validation failed for {event_type.value}: {errors}"
                )
                self._dead_letter_queue.append({
                    "event_type": event_type.value,
                    "event_data": event_data,
                    "errors": errors,
                    "timestamp": datetime.now().isoformat()
                })
                self._metrics["total_failed"] += 1
                return False
        
        # Extract correlation info
        correlation_id = None
        workflow_id = None
        if "context" in event_data:
            context = event_data["context"]
            correlation_id = context.get("correlation_id")
            workflow_id = context.get("workflow_id")
        
        # Record event
        record = EventRecord(
            event_type=event_type,
            event_data=event_data,
            timestamp=datetime.now().isoformat(),
            correlation_id=correlation_id,
            workflow_id=workflow_id
        )
        self._event_history.append(record)
        
        # Persist if enabled
        if self.enable_persistence:
            self._persist_event(record)
        
        # Update metrics
        self._metrics["total_published"] += 1
        self._metrics["by_event_type"][event_type.value] += 1
        if correlation_id:
            self._metrics["by_correlation"][correlation_id] += 1
        
        # Track correlation for matching
        if correlation_id:
            if correlation_id not in self._pending_correlations:
                self._pending_correlations[correlation_id] = {
                    "initiated_at": datetime.now().isoformat(),
                    "events": []
                }
            self._pending_correlations[correlation_id]["events"].append({
                "event_type": event_type.value,
                "timestamp": record.timestamp
            })
        
        # Dispatch to handlers
        await self._dispatch(event_type, event_data)
        
        logger.info(
            f"Published event: {event_type.value} "
            f"(correlation_id={correlation_id})"
        )
        
        return True
    
    async def _dispatch(
        self,
        event_type: EventType,
        event_data: Dict[str, Any]
    ) -> None:
        """
        Dispatch event to registered handlers
        
        Args:
            event_type: Type of event
            event_data: Event payload
        """
        handlers = self._handlers.get(event_type, [])
        
        if not handlers:
            logger.warning(f"No handlers registered for {event_type.value}")
            return
        
        # Execute all handlers concurrently
        tasks = [handler(event_data) for handler in handlers]
        
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check for handler failures
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(
                        f"Handler {i} failed for {event_type.value}: {result}",
                        exc_info=result
                    )
                    self._metrics["total_failed"] += 1
                else:
                    self._metrics["total_delivered"] += 1
                    
        except Exception as e:
            logger.error(f"Error dispatching event: {e}", exc_info=True)
            self._metrics["total_failed"] += 1
    
    def _persist_event(self, record: EventRecord) -> None:
        """
        Persist event to disk for audit trail
        
        Args:
            record: Event record to persist
        """
        try:
            # Organize by workflow_id if available
            if record.workflow_id:
                workflow_dir = self.persistence_dir / record.workflow_id
                workflow_dir.mkdir(exist_ok=True)
                file_path = workflow_dir / f"{record.timestamp}_{record.event_type.value}.json"
            else:
                file_path = self.persistence_dir / f"{record.timestamp}_{record.event_type.value}.json"
            
            with open(file_path, 'w') as f:
                json.dump(record.to_dict(), f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to persist event: {e}", exc_info=True)
    
    def get_correlation_chain(
        self,
        correlation_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get all events in a correlation chain
        
        Useful for tracing request-response pairs across Orchestrator-Choreographer boundary
        
        Args:
            correlation_id: Correlation identifier
            
        Returns:
            Dictionary with correlation chain info or None
        """
        return self._pending_correlations.get(correlation_id)
    
    def get_event_history(
        self,
        event_type: Optional[EventType] = None,
        correlation_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        limit: int = 100
    ) -> List[EventRecord]:
        """
        Get event history with optional filtering
        
        Args:
            event_type: Filter by event type
            correlation_id: Filter by correlation ID
            workflow_id: Filter by workflow ID
            limit: Maximum number of records
            
        Returns:
            List of event records
        """
        history = self._event_history
        
        if event_type:
            history = [r for r in history if r.event_type == event_type]
        
        if correlation_id:
            history = [r for r in history if r.correlation_id == correlation_id]
        
        if workflow_id:
            history = [r for r in history if r.workflow_id == workflow_id]
        
        return history[-limit:]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get event bus metrics"""
        metrics = self._metrics.copy()
        metrics["pending_correlations"] = len(self._pending_correlations)
        metrics["dead_letter_queue_size"] = len(self._dead_letter_queue)
        metrics["total_handlers"] = sum(len(h) for h in self._handlers.values())
        metrics["handler_counts"] = {
            et.value: len(handlers)
            for et, handlers in self._handlers.items()
        }
        return metrics
    
    def get_dead_letter_queue(self) -> List[Dict[str, Any]]:
        """Get events that failed validation or delivery"""
        return self._dead_letter_queue.copy()
    
    def clear_history(self) -> None:
        """Clear event history (for testing)"""
        self._event_history.clear()
        self._pending_correlations.clear()
        logger.info("Event history cleared")


# Singleton instance
_event_bus = None

def get_event_bus(
    enable_persistence: bool = True,
    persistence_dir: Optional[Path] = None
) -> EventBus:
    """Get singleton event bus instance"""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus(
            enable_persistence=enable_persistence,
            persistence_dir=persistence_dir
        )
    return _event_bus


# ============================================================================
# SYNCHRONOUS WRAPPER for non-async contexts
# ============================================================================

class SyncEventBus:
    """
    Synchronous wrapper for EventBus
    
    Provides blocking publish/subscribe interface for use in non-async code
    """
    
    def __init__(self, event_bus: Optional[EventBus] = None):
        """
        Initialize sync wrapper
        
        Args:
            event_bus: EventBus instance (creates new if None)
        """
        self._event_bus = event_bus or get_event_bus()
        self._loop = asyncio.new_event_loop()
    
    def publish(
        self,
        event_type: EventType,
        event_data: Dict[str, Any],
        validate: bool = True
    ) -> bool:
        """
        Publish event synchronously
        
        Args:
            event_type: Type of event
            event_data: Event payload
            validate: Whether to validate against schema
            
        Returns:
            True if published successfully
        """
        return self._loop.run_until_complete(
            self._event_bus.publish(event_type, event_data, validate)
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get event bus metrics"""
        return self._event_bus.get_metrics()
    
    def get_event_history(self, **kwargs) -> List[EventRecord]:
        """Get event history"""
        return self._event_bus.get_event_history(**kwargs)
    
    def get_correlation_chain(self, correlation_id: str) -> Optional[Dict[str, Any]]:
        """Get correlation chain"""
        return self._event_bus.get_correlation_chain(correlation_id)


if __name__ == "__main__":
    # Test the event bus
    import asyncio
    from event_schemas import (
        create_event_metadata,
        create_context_propagation,
        SubProcessType,
        SubProcessResult
    )
    
    print("=" * 80)
    print("EVENT BUS TEST")
    print("=" * 80)
    
    async def test_event_bus():
        # Create event bus
        bus = EventBus(enable_persistence=False)
        
        # Track received events
        received_events = []
        
        # Define handlers
        async def handle_initiated(event_data: Dict[str, Any]):
            print(f"\n[CHOREOGRAPHER] Received SubProcessInitiatedEvent")
            print(f"  Correlation ID: {event_data['context']['correlation_id']}")
            print(f"  Question IDs: {event_data['context']['question_ids']}")
            received_events.append("initiated")
        
        async def handle_completed(event_data: Dict[str, Any]):
            print(f"\n[ORCHESTRATOR] Received SubProcessCompletedEvent")
            print(f"  Correlation ID: {event_data['context']['correlation_id']}")
            print(f"  Status: {event_data['result']['status']}")
            received_events.append("completed")
        
        # Subscribe to events
        bus.subscribe(EventType.SUB_PROCESS_INITIATED, handle_initiated)
        bus.subscribe(EventType.SUB_PROCESS_COMPLETED, handle_completed)
        
        print("\nHandlers subscribed")
        
        # Test 1: Publish SubProcessInitiatedEvent
        print("\n" + "-" * 80)
        print("Test 1: Orchestrator initiates sub-process")
        print("-" * 80)
        
        metadata = create_event_metadata(
            EventType.SUB_PROCESS_INITIATED,
            "orchestrator"
        )
        context = create_context_propagation(
            workflow_id="wf_test_123",
            question_ids=["P1-D1-Q1", "P1-D1-Q2"]
        )
        
        event = SubProcessInitiatedEvent(
            metadata=metadata,
            context=context,
            sub_process_type=SubProcessType.QUESTION_ANALYSIS,
            input_data={"plan_text": "Sample plan"}
        )
        
        success = await bus.publish(
            EventType.SUB_PROCESS_INITIATED,
            event.to_dict()
        )
        print(f"Event published: {success}")
        
        # Wait for async handling
        await asyncio.sleep(0.1)
        
        # Test 2: Choreographer responds with completion
        print("\n" + "-" * 80)
        print("Test 2: Choreographer reports completion")
        print("-" * 80)
        
        completion_metadata = create_event_metadata(
            EventType.SUB_PROCESS_COMPLETED,
            "choreographer"
        )
        
        result = SubProcessResult(
            status="completed",
            output_data={"P1-D1-Q1": {"score": 2.5}},
            execution_time=45.2,
            steps_executed=5,
            steps_successful=5,
            steps_failed=0
        )
        
        completion_event = SubProcessCompletedEvent(
            metadata=completion_metadata,
            context=context,  # Same context with correlation_id
            result=result
        )
        
        success = await bus.publish(
            EventType.SUB_PROCESS_COMPLETED,
            completion_event.to_dict()
        )
        print(f"Event published: {success}")
        
        # Wait for async handling
        await asyncio.sleep(0.1)
        
        # Show metrics
        print("\n" + "-" * 80)
        print("Event Bus Metrics")
        print("-" * 80)
        
        metrics = bus.get_metrics()
        print(f"Total published: {metrics['total_published']}")
        print(f"Total delivered: {metrics['total_delivered']}")
        print(f"Total failed: {metrics['total_failed']}")
        print(f"By event type: {dict(metrics['by_event_type'])}")
        
        # Show correlation chain
        print("\n" + "-" * 80)
        print("Correlation Chain")
        print("-" * 80)
        
        chain = bus.get_correlation_chain(context.correlation_id)
        if chain:
            print(f"Correlation ID: {context.correlation_id}")
            print(f"Initiated at: {chain['initiated_at']}")
            print(f"Events in chain:")
            for evt in chain['events']:
                print(f"  - {evt['event_type']} @ {evt['timestamp']}")
        
        print(f"\nReceived events: {received_events}")
        print("Expected: ['initiated', 'completed']")
        assert received_events == ['initiated', 'completed'], "Event handling failed!"
        
        print("\n" + "=" * 80)
        print("✓ All tests passed!")
        print("=" * 80)
    
    # Run async test
    asyncio.run(test_event_bus())
