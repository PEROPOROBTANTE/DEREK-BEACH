"""
Event Schemas for FARFAN 3.0 Event-Driven Choreography
=======================================================

This module defines immutable event schemas with strict versioning
for the event-driven policy analysis choreography.

All events follow these principles:
- Immutability: Events cannot be modified after creation
- Versioning: Each event has a schema version
- Correlation: All events carry correlation IDs for traceability
- Context: Events include QuestionContext for validation

Author: FARFAN Integration Team
Version: 1.0.0
Python: 3.11+
"""

from .base_events import (
    BaseEvent,
    EventType,
    EventStatus,
)
from .workflow_events import (
    AnalysisRequestedEvent,
    EnrichedAnalysisStepEvent,
    ChunkingCompleteEvent,
    CausalExtractionCompleteEvent,
    FinancialAuditCompleteEvent,
    MicroScoreCompleteEvent,
    MesoScoreCompleteEvent,
    MacroScoreCompleteEvent,
    FinalReportReadyEvent,
)
from .error_events import (
    ValidationFailedEvent,
    ProcessingFailedEvent,
    PreconditionFailedEvent,
)
from .question_context import (
    QuestionContext,
    ValidationRule,
    ScoringModality,
)

__all__ = [
    # Base
    "BaseEvent",
    "EventType",
    "EventStatus",
    # Workflow events
    "AnalysisRequestedEvent",
    "EnrichedAnalysisStepEvent",
    "ChunkingCompleteEvent",
    "CausalExtractionCompleteEvent",
    "FinancialAuditCompleteEvent",
    "MicroScoreCompleteEvent",
    "MesoScoreCompleteEvent",
    "MacroScoreCompleteEvent",
    "FinalReportReadyEvent",
    # Error events
    "ValidationFailedEvent",
    "ProcessingFailedEvent",
    "PreconditionFailedEvent",
    # Context
    "QuestionContext",
    "ValidationRule",
    "ScoringModality",
]

__version__ = "1.0.0"
