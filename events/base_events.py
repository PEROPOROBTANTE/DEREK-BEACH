"""
Base Event Classes for Event-Driven Choreography
=================================================

Defines immutable base event structure with versioning, correlation,
and schema validation support.

Author: FARFAN Integration Team
Version: 1.0.0
Python: 3.11+
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict


class EventType(Enum):
    """Event types in the choreography"""
    
    # Workflow events
    ANALYSIS_REQUESTED = "analysis.requested"
    ENRICHED_ANALYSIS_STEP = "analysis.enriched"
    CHUNKING_COMPLETE = "chunking.complete"
    CAUSAL_EXTRACTION_COMPLETE = "causal.extraction.complete"
    FINANCIAL_AUDIT_COMPLETE = "financial.audit.complete"
    MICRO_SCORE_COMPLETE = "scoring.micro.complete"
    MESO_SCORE_COMPLETE = "scoring.meso.complete"
    MACRO_SCORE_COMPLETE = "scoring.macro.complete"
    FINAL_REPORT_READY = "report.final.ready"
    
    # Error events
    VALIDATION_FAILED = "validation.failed"
    PROCESSING_FAILED = "processing.failed"
    PRECONDITION_FAILED = "precondition.failed"
    
    # Component-specific events
    SEGMENTATION_COMPLETE = "segmentation.complete"
    PREPROCESSING_COMPLETE = "preprocessing.complete"
    EMBEDDING_COMPLETE = "embedding.complete"
    SEMANTIC_ANALYSIS_COMPLETE = "semantic.analysis.complete"
    MUNICIPAL_ANALYSIS_COMPLETE = "municipal.analysis.complete"
    THEORY_CHANGE_COMPLETE = "theory.change.complete"
    DEREK_BEACH_COMPLETE = "derek.beach.complete"
    CONTRADICTION_DETECTION_COMPLETE = "contradiction.detection.complete"


class EventStatus(Enum):
    """Event processing status"""
    
    CREATED = "created"
    PUBLISHED = "published"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    VALIDATED = "validated"
    REJECTED = "rejected"


@dataclass(frozen=True)
class BaseEvent:
    """
    Immutable base event for all choreography events
    
    All events in the system inherit from this base class to ensure:
    - Immutability via frozen=True
    - Unique event identification via event_id
    - Correlation for traceability via correlation_id
    - Schema versioning via schema_version
    - Temporal ordering via timestamp
    
    Attributes:
        event_id: Unique identifier for this event instance
        event_type: Type of event (from EventType enum)
        schema_version: Version of the event schema (e.g., "1.0.0")
        correlation_id: ID linking related events in a workflow
        question_id: Optional question ID this event relates to
        timestamp: When the event was created (ISO 8601 format)
        status: Current status of the event
        metadata: Additional event metadata
    """
    
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = field(default=EventType.ANALYSIS_REQUESTED)
    schema_version: str = "1.0.0"
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    question_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: EventStatus = EventStatus.CREATED
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert event to dictionary for serialization
        
        Returns:
            Dictionary representation of the event
        """
        result = asdict(self)
        result['event_type'] = self.event_type.value
        result['status'] = self.status.value
        return result
    
    def with_status(self, status: EventStatus) -> 'BaseEvent':
        """
        Create a new event with updated status
        
        Since events are immutable, this creates a new instance
        
        Args:
            status: New status for the event
            
        Returns:
            New BaseEvent instance with updated status
        """
        data = asdict(self)
        data['status'] = status
        data['event_type'] = self.event_type  # Keep enum, not value
        return BaseEvent(**data)
    
    def validate_schema(self) -> bool:
        """
        Validate event conforms to schema requirements
        
        Returns:
            True if valid, False otherwise
        """
        # Basic validation
        if not self.event_id or not self.correlation_id:
            return False
        
        if not self.schema_version:
            return False
        
        if not isinstance(self.event_type, EventType):
            return False
        
        if not isinstance(self.status, EventStatus):
            return False
        
        return True
    
    def __repr__(self) -> str:
        """String representation for logging"""
        return (
            f"{self.__class__.__name__}("
            f"event_id={self.event_id[:8]}..., "
            f"type={self.event_type.value}, "
            f"correlation_id={self.correlation_id[:8]}..., "
            f"question_id={self.question_id}, "
            f"status={self.status.value}"
            f")"
        )
