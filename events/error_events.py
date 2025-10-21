"""
Error Events for Event-Driven Choreography
===========================================

Defines error and failure events for distributed error handling.

Author: FARFAN Integration Team
Version: 1.0.0
Python: 3.11+
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from .base_events import BaseEvent, EventType, EventStatus


@dataclass(frozen=True)
class ValidationFailedEvent(BaseEvent):
    """
    Validation failed for input data
    
    Emitted when a component validates incoming data against
    QuestionContext rules and finds violations.
    
    Attributes:
        component_name: Name of component that detected failure
        validation_errors: List of validation error messages
        failed_rules: List of rules that failed
        input_data_summary: Summary of input data (no sensitive data)
        remediation_hint: Suggestion for fixing the issue
    """
    
    event_type: EventType = EventType.VALIDATION_FAILED
    status: EventStatus = EventStatus.FAILED
    component_name: str = ""
    validation_errors: List[str] = field(default_factory=list)
    failed_rules: List[str] = field(default_factory=list)
    input_data_summary: Dict[str, Any] = field(default_factory=dict)
    remediation_hint: str = ""


@dataclass(frozen=True)
class ProcessingFailedEvent(BaseEvent):
    """
    Processing failed during component execution
    
    Emitted when a component encounters an error during processing
    that prevents it from completing its task.
    
    Attributes:
        component_name: Name of component that failed
        error_type: Type of error (exception class name)
        error_message: Detailed error message
        stack_trace: Stack trace (if available)
        retry_count: Number of retries attempted
        can_retry: Whether this failure is retryable
    """
    
    event_type: EventType = EventType.PROCESSING_FAILED
    status: EventStatus = EventStatus.FAILED
    component_name: str = ""
    error_type: str = ""
    error_message: str = ""
    stack_trace: Optional[str] = None
    retry_count: int = 0
    can_retry: bool = True


@dataclass(frozen=True)
class PreconditionFailedEvent(BaseEvent):
    """
    Preconditions not met for component execution
    
    Emitted when a component checks preconditions (e.g., for scoring)
    and finds that required inputs are missing or invalid.
    
    Attributes:
        component_name: Name of component checking preconditions
        unmet_preconditions: List of unmet precondition names
        required_inputs: Inputs that were required but missing
        available_inputs: Inputs that were available
        should_skip_downstream: Whether to skip downstream processing
    """
    
    event_type: EventType = EventType.PRECONDITION_FAILED
    status: EventStatus = EventStatus.FAILED
    component_name: str = ""
    unmet_preconditions: List[str] = field(default_factory=list)
    required_inputs: List[str] = field(default_factory=list)
    available_inputs: List[str] = field(default_factory=list)
    should_skip_downstream: bool = True


class AdapterContractError(Exception):
    """
    Exception raised when adapter contract is violated
    
    Used internally by components when detecting contract violations.
    Components should emit appropriate error events when catching this.
    """
    
    def __init__(
        self,
        message: str,
        component_name: str = "",
        contract_type: str = "",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.component_name = component_name
        self.contract_type = contract_type
        self.details = details or {}
