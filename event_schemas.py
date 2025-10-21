"""
Event Schemas for Orchestrator-Choreographer Communication
===========================================================

Defines the contract between Orchestrator (centralized control) and Choreographer 
(decentralized execution) using strongly-typed event schemas.

This module implements the Interaction Protocol that:
1. Clearly defines boundary between Orchestrator and Choreographer responsibilities
2. Specifies triggering events for initiating choreographed sub-processes
3. Specifies outcome events for reporting completion/failure
4. Mandates context propagation (correlation_id, question_ids)
5. Enables state synchronization between patterns
6. Supports error handling across the boundary

Schema Registry inspired by AsyncAPI specification for event-driven architectures.

Author: FARFAN 3.0 - Orchestrator-Choreographer Partnership
Version: 1.0.0
Python: 3.10+
"""

import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of events in the system"""
    # Orchestrator -> Choreographer (Triggering Events)
    SUB_PROCESS_INITIATED = "sub_process.initiated"
    ANALYSIS_REQUESTED = "analysis.requested"
    
    # Choreographer -> Orchestrator (Outcome Events)
    SUB_PROCESS_COMPLETED = "sub_process.completed"
    SUB_PROCESS_FAILED = "sub_process.failed"
    ANALYSIS_COMPLETED = "analysis.completed"
    ANALYSIS_FAILED = "analysis.failed"
    
    # State synchronization events
    STATE_CHANGED = "state.changed"
    CHECKPOINT_REACHED = "checkpoint.reached"


class SubProcessType(Enum):
    """Types of choreographed sub-processes"""
    QUESTION_ANALYSIS = "question_analysis"
    POLICY_EVALUATION = "policy_evaluation"
    EVIDENCE_AGGREGATION = "evidence_aggregation"
    VALIDATION_CHECK = "validation_check"
    DEPENDENCY_RESOLUTION = "dependency_resolution"


@dataclass(frozen=True)
class EventMetadata:
    """
    Standard metadata for all events
    
    Ensures every event can be traced and correlated across the boundary
    """
    event_id: str  # Unique event identifier (UUID)
    event_type: EventType
    timestamp: str  # ISO 8601 timestamp
    source: str  # Originating component (e.g., "orchestrator", "choreographer")
    version: str = "1.0.0"  # Schema version for forward compatibility
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "source": self.source,
            "version": self.version
        }


@dataclass(frozen=True)
class ContextPropagation:
    """
    Context information propagated across Orchestrator-Choreographer boundary
    
    MANDATORY FIELDS per Interaction Protocol:
    - correlation_id: Links related events across the boundary
    - question_ids: Question identifiers being processed
    - workflow_id: Parent workflow identifier
    """
    correlation_id: str  # Unique identifier linking request-response pairs
    workflow_id: str  # Parent workflow ID
    question_ids: List[str]  # Question IDs being analyzed in this sub-process
    
    # Optional context enrichment
    dimension: Optional[str] = None
    policy_area: Optional[str] = None
    sub_process_id: Optional[str] = None
    parent_step_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "correlation_id": self.correlation_id,
            "workflow_id": self.workflow_id,
            "question_ids": self.question_ids,
            "dimension": self.dimension,
            "policy_area": self.policy_area,
            "sub_process_id": self.sub_process_id,
            "parent_step_id": self.parent_step_id
        }


# ============================================================================
# TRIGGERING EVENTS (Orchestrator -> Choreographer)
# ============================================================================

@dataclass(frozen=True)
class SubProcessInitiatedEvent:
    """
    Event emitted by Orchestrator to initiate a choreographed sub-process
    
    TRIGGER CONDITIONS:
    - Orchestrator delegates a portion of workflow to Choreographer
    - Multiple adapters must be coordinated without centralized control
    - Dependency resolution needed within a question analysis
    
    REQUIRED PAYLOAD per Interaction Protocol:
    - metadata: Standard event metadata
    - context: Context propagation with correlation_id
    - sub_process_type: Type of sub-process to execute
    - input_data: Data references and parameters
    """
    metadata: EventMetadata
    context: ContextPropagation
    sub_process_type: SubProcessType
    input_data: Dict[str, Any]  # Contains plan_text, question_specs, etc.
    
    # Optional configuration
    timeout_seconds: Optional[int] = None
    retry_policy: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "metadata": self.metadata.to_dict(),
            "context": self.context.to_dict(),
            "sub_process_type": self.sub_process_type.value,
            "input_data": self.input_data,
            "timeout_seconds": self.timeout_seconds,
            "retry_policy": self.retry_policy
        }


@dataclass(frozen=True)
class AnalysisRequestedEvent:
    """
    Event emitted by Orchestrator to request analysis of specific questions
    
    More specific variant of SubProcessInitiatedEvent for question analysis
    """
    metadata: EventMetadata
    context: ContextPropagation
    question_ids: List[str]
    plan_text: str
    execution_config: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "metadata": self.metadata.to_dict(),
            "context": self.context.to_dict(),
            "question_ids": self.question_ids,
            "plan_text": self.plan_text,
            "execution_config": self.execution_config
        }


# ============================================================================
# OUTCOME EVENTS (Choreographer -> Orchestrator)
# ============================================================================

@dataclass(frozen=True)
class SubProcessResult:
    """
    Result payload from choreographed sub-process
    
    Contains all outputs needed by Orchestrator to continue workflow
    """
    status: str  # "completed", "partial", "failed"
    output_data: Dict[str, Any]  # Results keyed by question_id or adapter.method
    execution_time: float
    steps_executed: int
    steps_successful: int
    steps_failed: int
    
    # Evidence and confidence
    evidence_collected: List[Dict[str, Any]] = field(default_factory=list)
    overall_confidence: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "status": self.status,
            "output_data": self.output_data,
            "execution_time": self.execution_time,
            "steps_executed": self.steps_executed,
            "steps_successful": self.steps_successful,
            "steps_failed": self.steps_failed,
            "evidence_collected": self.evidence_collected,
            "overall_confidence": self.overall_confidence
        }


@dataclass(frozen=True)
class SubProcessCompletedEvent:
    """
    Event emitted by Choreographer upon successful completion
    
    REQUIRED PAYLOAD per Interaction Protocol:
    - metadata: Standard event metadata
    - context: Context propagation (same correlation_id as triggering event)
    - result: Complete results from sub-process
    
    ORCHESTRATOR ACTIONS on receipt:
    - Transition from WaitingForSubAnalysis to next state
    - Extract results and merge into workflow state
    - Continue with dependent steps
    """
    metadata: EventMetadata
    context: ContextPropagation
    result: SubProcessResult
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "metadata": self.metadata.to_dict(),
            "context": self.context.to_dict(),
            "result": self.result.to_dict()
        }


@dataclass(frozen=True)
class SubProcessFailedEvent:
    """
    Event emitted by Choreographer upon failure
    
    REQUIRED PAYLOAD per Interaction Protocol:
    - metadata: Standard event metadata
    - context: Context propagation (same correlation_id as triggering event)
    - error_details: Detailed error information
    
    ORCHESTRATOR ACTIONS on receipt:
    - Invoke ResilienceManager for error handling
    - Decide on retry, fallback, or fail-fast
    - Update workflow state with failure information
    """
    metadata: EventMetadata
    context: ContextPropagation
    error_code: str
    error_message: str
    error_details: Dict[str, Any]
    
    # Partial results if available
    partial_result: Optional[SubProcessResult] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "metadata": self.metadata.to_dict(),
            "context": self.context.to_dict(),
            "error_code": self.error_code,
            "error_message": self.error_message,
            "error_details": self.error_details,
            "partial_result": self.partial_result.to_dict() if self.partial_result else None
        }


# ============================================================================
# EVENT SCHEMA REGISTRY
# ============================================================================

class EventSchemaRegistry:
    """
    Shared contract registry for event schemas
    
    Both Orchestrator and Choreographer MUST adhere to schemas defined here.
    
    Inspired by AsyncAPI specification for event-driven architectures.
    Ensures forward compatibility through versioning.
    """
    
    def __init__(self):
        """Initialize registry with all event schemas"""
        self._schemas: Dict[EventType, Dict[str, Any]] = {}
        self._register_schemas()
        
        logger.info(f"EventSchemaRegistry initialized with {len(self._schemas)} schemas")
    
    def _register_schemas(self) -> None:
        """Register all event schemas"""
        
        # Triggering Events
        self._schemas[EventType.SUB_PROCESS_INITIATED] = {
            "name": "SubProcessInitiatedEvent",
            "version": "1.0.0",
            "direction": "orchestrator_to_choreographer",
            "required_fields": [
                "metadata",
                "context",
                "sub_process_type",
                "input_data"
            ],
            "description": "Initiates a choreographed sub-process",
            "example_payload": {
                "metadata": {
                    "event_id": "evt_123",
                    "event_type": "sub_process.initiated",
                    "timestamp": "2024-01-01T12:00:00Z",
                    "source": "orchestrator",
                    "version": "1.0.0"
                },
                "context": {
                    "correlation_id": "corr_abc123",
                    "workflow_id": "wf_456",
                    "question_ids": ["P1-D1-Q1", "P1-D1-Q2"]
                },
                "sub_process_type": "question_analysis",
                "input_data": {
                    "plan_text": "...",
                    "question_specs": [...]
                }
            }
        }
        
        self._schemas[EventType.ANALYSIS_REQUESTED] = {
            "name": "AnalysisRequestedEvent",
            "version": "1.0.0",
            "direction": "orchestrator_to_choreographer",
            "required_fields": [
                "metadata",
                "context",
                "question_ids",
                "plan_text"
            ],
            "description": "Requests analysis of specific questions"
        }
        
        # Outcome Events
        self._schemas[EventType.SUB_PROCESS_COMPLETED] = {
            "name": "SubProcessCompletedEvent",
            "version": "1.0.0",
            "direction": "choreographer_to_orchestrator",
            "required_fields": [
                "metadata",
                "context",
                "result"
            ],
            "description": "Reports successful completion of sub-process",
            "example_payload": {
                "metadata": {
                    "event_id": "evt_124",
                    "event_type": "sub_process.completed",
                    "timestamp": "2024-01-01T12:05:00Z",
                    "source": "choreographer",
                    "version": "1.0.0"
                },
                "context": {
                    "correlation_id": "corr_abc123",  # Same as triggering event
                    "workflow_id": "wf_456",
                    "question_ids": ["P1-D1-Q1", "P1-D1-Q2"]
                },
                "result": {
                    "status": "completed",
                    "output_data": {...},
                    "execution_time": 45.2,
                    "steps_executed": 5,
                    "steps_successful": 5,
                    "steps_failed": 0
                }
            }
        }
        
        self._schemas[EventType.SUB_PROCESS_FAILED] = {
            "name": "SubProcessFailedEvent",
            "version": "1.0.0",
            "direction": "choreographer_to_orchestrator",
            "required_fields": [
                "metadata",
                "context",
                "error_code",
                "error_message"
            ],
            "description": "Reports failure of sub-process"
        }
    
    def get_schema(self, event_type: EventType) -> Optional[Dict[str, Any]]:
        """
        Get schema for an event type
        
        Args:
            event_type: Type of event
            
        Returns:
            Schema definition or None if not found
        """
        return self._schemas.get(event_type)
    
    def validate_event(
        self,
        event_type: EventType,
        event_data: Dict[str, Any]
    ) -> tuple[bool, List[str]]:
        """
        Validate event data against schema
        
        Args:
            event_type: Type of event
            event_data: Event data dictionary
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        schema = self.get_schema(event_type)
        if not schema:
            return False, [f"No schema found for event type: {event_type}"]
        
        errors = []
        required_fields = schema.get("required_fields", [])
        
        # Check required fields
        for field in required_fields:
            if field not in event_data:
                errors.append(f"Missing required field: {field}")
        
        # Check metadata structure
        if "metadata" in event_data:
            metadata = event_data["metadata"]
            required_metadata = ["event_id", "event_type", "timestamp", "source"]
            for field in required_metadata:
                if field not in metadata:
                    errors.append(f"Missing required metadata field: {field}")
        
        # Check context structure (if required)
        if "context" in required_fields and "context" in event_data:
            context = event_data["context"]
            required_context = ["correlation_id", "workflow_id", "question_ids"]
            for field in required_context:
                if field not in context:
                    errors.append(f"Missing required context field: {field}")
        
        return len(errors) == 0, errors
    
    def list_schemas(self) -> List[str]:
        """List all registered event types"""
        return [et.value for et in self._schemas.keys()]
    
    def get_schema_version(self, event_type: EventType) -> Optional[str]:
        """Get version of a schema"""
        schema = self.get_schema(event_type)
        return schema.get("version") if schema else None


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_event_metadata(
    event_type: EventType,
    source: str
) -> EventMetadata:
    """
    Create standard event metadata
    
    Args:
        event_type: Type of event
        source: Source component
        
    Returns:
        EventMetadata instance
    """
    return EventMetadata(
        event_id=f"evt_{uuid.uuid4().hex[:12]}",
        event_type=event_type,
        timestamp=datetime.now().isoformat(),
        source=source,
        version="1.0.0"
    )


def create_context_propagation(
    workflow_id: str,
    question_ids: List[str],
    correlation_id: Optional[str] = None,
    **kwargs
) -> ContextPropagation:
    """
    Create context propagation object
    
    Args:
        workflow_id: Workflow identifier
        question_ids: Question identifiers
        correlation_id: Optional correlation ID (generated if not provided)
        **kwargs: Additional context fields
        
    Returns:
        ContextPropagation instance
    """
    return ContextPropagation(
        correlation_id=correlation_id or f"corr_{uuid.uuid4().hex[:12]}",
        workflow_id=workflow_id,
        question_ids=question_ids,
        dimension=kwargs.get("dimension"),
        policy_area=kwargs.get("policy_area"),
        sub_process_id=kwargs.get("sub_process_id"),
        parent_step_id=kwargs.get("parent_step_id")
    )


# Initialize global registry
_registry = None

def get_event_schema_registry() -> EventSchemaRegistry:
    """Get singleton event schema registry"""
    global _registry
    if _registry is None:
        _registry = EventSchemaRegistry()
    return _registry


if __name__ == "__main__":
    # Test the schema registry
    print("=" * 80)
    print("EVENT SCHEMA REGISTRY TEST")
    print("=" * 80)
    
    registry = get_event_schema_registry()
    
    print(f"\nRegistered schemas: {len(registry.list_schemas())}")
    for schema_name in registry.list_schemas():
        print(f"  - {schema_name}")
    
    # Test schema validation
    print("\n" + "-" * 80)
    print("Testing SubProcessInitiatedEvent schema validation")
    print("-" * 80)
    
    # Valid event
    valid_event = {
        "metadata": {
            "event_id": "evt_123",
            "event_type": "sub_process.initiated",
            "timestamp": "2024-01-01T12:00:00Z",
            "source": "orchestrator"
        },
        "context": {
            "correlation_id": "corr_abc",
            "workflow_id": "wf_456",
            "question_ids": ["P1-D1-Q1"]
        },
        "sub_process_type": "question_analysis",
        "input_data": {"plan_text": "..."}
    }
    
    is_valid, errors = registry.validate_event(
        EventType.SUB_PROCESS_INITIATED,
        valid_event
    )
    print(f"Valid event: {is_valid}")
    if errors:
        print(f"Errors: {errors}")
    
    # Invalid event (missing correlation_id)
    invalid_event = {
        "metadata": {
            "event_id": "evt_123",
            "event_type": "sub_process.initiated",
            "timestamp": "2024-01-01T12:00:00Z",
            "source": "orchestrator"
        },
        "context": {
            "workflow_id": "wf_456",
            "question_ids": ["P1-D1-Q1"]
        },
        "sub_process_type": "question_analysis",
        "input_data": {"plan_text": "..."}
    }
    
    is_valid, errors = registry.validate_event(
        EventType.SUB_PROCESS_INITIATED,
        invalid_event
    )
    print(f"\nInvalid event: {is_valid}")
    print(f"Errors: {errors}")
    
    # Test event creation
    print("\n" + "-" * 80)
    print("Testing event creation")
    print("-" * 80)
    
    metadata = create_event_metadata(
        EventType.SUB_PROCESS_INITIATED,
        "orchestrator"
    )
    print(f"Created metadata: {metadata.to_dict()}")
    
    context = create_context_propagation(
        workflow_id="wf_789",
        question_ids=["P1-D1-Q1", "P1-D1-Q2"],
        dimension="D1",
        policy_area="P1"
    )
    print(f"Created context: {context.to_dict()}")
    
    event = SubProcessInitiatedEvent(
        metadata=metadata,
        context=context,
        sub_process_type=SubProcessType.QUESTION_ANALYSIS,
        input_data={"plan_text": "Sample plan text"}
    )
    print(f"Created event: {event.to_dict()}")
    
    print("\n" + "=" * 80)
