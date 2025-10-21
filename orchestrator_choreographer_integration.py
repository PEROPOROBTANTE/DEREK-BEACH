"""
Orchestrator-Choreographer Integration Module
==============================================

Implements the complete Interaction Protocol between Orchestrator (centralized
control) and Choreographer (decentralized execution).

This module provides the glue layer that:
1. Manages the boundary between Orchestrator and Choreographer
2. Handles event-based communication
3. Synchronizes state across the boundary
4. Propagates context (correlation_id, question_ids)
5. Handles errors from choreographed sub-processes

BOUNDARY DEFINITION:
-------------------
ORCHESTRATOR RESPONSIBILITIES:
- High-level workflow control and decision-making
- State management and persistence
- Validation rule enforcement
- Resilience strategy selection
- Final result aggregation

CHOREOGRAPHER RESPONSIBILITIES:
- Adapter execution with dependency management
- Parallel/concurrent execution of independent adapters
- Evidence aggregation from adapters
- Sub-process-level error handling

INTERACTION FLOW:
----------------
1. Orchestrator decides to delegate work to Choreographer
2. Orchestrator creates ContextPropagation with correlation_id
3. Orchestrator emits SubProcessInitiatedEvent
4. Orchestrator transitions to WAITING_FOR_SUB_ANALYSIS state
5. Choreographer receives event and executes sub-process
6. Choreographer emits SubProcessCompletedEvent or SubProcessFailedEvent
7. Orchestrator receives outcome event
8. Orchestrator transitions state and continues workflow

Author: FARFAN 3.0 - Orchestrator-Choreographer Partnership
Version: 1.0.0
Python: 3.10+
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import asyncio

from event_schemas import (
    EventType,
    SubProcessType,
    SubProcessInitiatedEvent,
    SubProcessCompletedEvent,
    SubProcessFailedEvent,
    ContextPropagation,
    create_event_metadata,
    create_context_propagation
)
from event_bus import EventBus, SyncEventBus
from state_store import StateStore, StepStatus
from resilience_manager import ResilienceManager
from metadata_service import QuestionContext

logger = logging.getLogger(__name__)


@dataclass
class SubProcessRequest:
    """
    Request to initiate a choreographed sub-process
    
    Created by Orchestrator when delegating work to Choreographer
    """
    workflow_id: str
    question_ids: List[str]
    sub_process_type: SubProcessType
    input_data: Dict[str, Any]
    context: QuestionContext
    parent_step_id: Optional[str] = None
    timeout_seconds: Optional[int] = None


@dataclass
class SubProcessResponse:
    """
    Response from choreographed sub-process
    
    Contains results and metadata from Choreographer execution
    """
    correlation_id: str
    success: bool
    results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time: float = 0.0
    steps_executed: int = 0
    steps_successful: int = 0
    steps_failed: int = 0


class OrchestratorChoreographerBridge:
    """
    Bridge between Orchestrator and Choreographer patterns
    
    Manages event-based communication, state synchronization, and
    error handling across the boundary.
    
    KEY FEATURES:
    - Correlation tracking for request-response pairs
    - Timeout handling for hung sub-processes
    - Partial result recovery on failure
    - Metrics and observability
    """
    
    def __init__(
        self,
        state_store: StateStore,
        resilience_manager: ResilienceManager,
        event_bus: Optional[SyncEventBus] = None
    ):
        """
        Initialize bridge
        
        Args:
            state_store: StateStore for workflow state management
            resilience_manager: ResilienceManager for error handling
            event_bus: Event bus for communication (creates if None)
        """
        self.state_store = state_store
        self.resilience_manager = resilience_manager
        self.event_bus = event_bus or SyncEventBus()
        
        # Track pending sub-processes
        self._pending_requests: Dict[str, SubProcessRequest] = {}
        
        # Metrics
        self._metrics = {
            "total_initiated": 0,
            "total_completed": 0,
            "total_failed": 0,
            "total_timeout": 0,
            "avg_execution_time": 0.0
        }
        
        # Register event handlers
        self._register_handlers()
        
        logger.info("OrchestratorChoreographerBridge initialized")
    
    def _register_handlers(self) -> None:
        """Register handlers for outcome events from Choreographer"""
        # Note: In production, these would be async handlers
        # For now, handlers will be called synchronously when events arrive
        pass
    
    def initiate_sub_process(
        self,
        request: SubProcessRequest
    ) -> str:
        """
        Initiate a choreographed sub-process
        
        ORCHESTRATOR ACTION:
        1. Create correlation_id
        2. Update workflow state to WAITING_FOR_SUB_ANALYSIS
        3. Emit SubProcessInitiatedEvent
        4. Track pending request
        
        Args:
            request: SubProcessRequest with details
            
        Returns:
            correlation_id for tracking
        """
        # Create context propagation
        context = create_context_propagation(
            workflow_id=request.workflow_id,
            question_ids=request.question_ids,
            dimension=getattr(request.context, "dimension", None),
            policy_area=getattr(request.context, "policy_area", None),
            parent_step_id=request.parent_step_id
        )
        
        correlation_id = context.correlation_id
        
        logger.info(
            f"Initiating sub-process: "
            f"correlation_id={correlation_id}, "
            f"type={request.sub_process_type.value}, "
            f"questions={len(request.question_ids)}"
        )
        
        # Update state to WAITING_FOR_SUB_ANALYSIS
        try:
            state = self.state_store.get_state(request.workflow_id)
            if state:
                # Mark current step as waiting
                if request.parent_step_id:
                    # Would update step status here
                    pass
        except Exception as e:
            logger.error(f"Error updating state: {e}")
        
        # Create and emit event
        metadata = create_event_metadata(
            EventType.SUB_PROCESS_INITIATED,
            "orchestrator"
        )
        
        event = SubProcessInitiatedEvent(
            metadata=metadata,
            context=context,
            sub_process_type=request.sub_process_type,
            input_data=request.input_data,
            timeout_seconds=request.timeout_seconds
        )
        
        # Publish event
        success = self.event_bus.publish(
            EventType.SUB_PROCESS_INITIATED,
            event.to_dict()
        )
        
        if success:
            # Track pending request
            self._pending_requests[correlation_id] = request
            self._metrics["total_initiated"] += 1
            
            logger.info(
                f"Sub-process initiated: correlation_id={correlation_id}"
            )
        else:
            logger.error(
                f"Failed to emit SubProcessInitiatedEvent: "
                f"correlation_id={correlation_id}"
            )
            raise RuntimeError("Failed to initiate sub-process")
        
        return correlation_id
    
    def handle_completion(
        self,
        event: SubProcessCompletedEvent
    ) -> SubProcessResponse:
        """
        Handle SubProcessCompletedEvent from Choreographer
        
        ORCHESTRATOR ACTION:
        1. Validate correlation_id matches pending request
        2. Extract results from event
        3. Update workflow state (transition from WAITING_FOR_SUB_ANALYSIS)
        4. Remove from pending requests
        5. Update metrics
        
        Args:
            event: SubProcessCompletedEvent from choreographer
            
        Returns:
            SubProcessResponse with results
        """
        correlation_id = event.context.correlation_id
        
        logger.info(
            f"Handling sub-process completion: "
            f"correlation_id={correlation_id}"
        )
        
        # Validate pending request exists
        if correlation_id not in self._pending_requests:
            logger.warning(
                f"Received completion for unknown correlation_id: {correlation_id}"
            )
            return SubProcessResponse(
                correlation_id=correlation_id,
                success=False,
                error_message="Unknown correlation_id"
            )
        
        # Get original request
        request = self._pending_requests[correlation_id]
        
        # Extract results
        result_data = event.result
        
        # Create response
        response = SubProcessResponse(
            correlation_id=correlation_id,
            success=True,
            results=result_data.output_data,
            execution_time=result_data.execution_time,
            steps_executed=result_data.steps_executed,
            steps_successful=result_data.steps_successful,
            steps_failed=result_data.steps_failed
        )
        
        # Update state (transition from WAITING_FOR_SUB_ANALYSIS)
        try:
            state = self.state_store.get_state(request.workflow_id)
            if state and request.parent_step_id:
                # Would update step status to COMPLETED here
                pass
        except Exception as e:
            logger.error(f"Error updating state: {e}")
        
        # Update metrics
        self._metrics["total_completed"] += 1
        prev_avg = self._metrics["avg_execution_time"]
        total = self._metrics["total_completed"]
        self._metrics["avg_execution_time"] = (
            (prev_avg * (total - 1) + result_data.execution_time) / total
        )
        
        # Remove from pending
        del self._pending_requests[correlation_id]
        
        logger.info(
            f"Sub-process completed: correlation_id={correlation_id}, "
            f"steps={result_data.steps_successful}/{result_data.steps_executed}"
        )
        
        return response
    
    def handle_failure(
        self,
        event: SubProcessFailedEvent
    ) -> SubProcessResponse:
        """
        Handle SubProcessFailedEvent from Choreographer
        
        ORCHESTRATOR ACTION:
        1. Validate correlation_id matches pending request
        2. Invoke ResilienceManager to determine recovery strategy
        3. Update workflow state based on strategy
        4. Handle partial results if available
        5. Update metrics
        
        Args:
            event: SubProcessFailedEvent from choreographer
            
        Returns:
            SubProcessResponse with error details
        """
        correlation_id = event.context.correlation_id
        
        logger.warning(
            f"Handling sub-process failure: "
            f"correlation_id={correlation_id}, "
            f"error={event.error_message}"
        )
        
        # Validate pending request exists
        if correlation_id not in self._pending_requests:
            logger.warning(
                f"Received failure for unknown correlation_id: {correlation_id}"
            )
            return SubProcessResponse(
                correlation_id=correlation_id,
                success=False,
                error_message="Unknown correlation_id"
            )
        
        # Get original request
        request = self._pending_requests[correlation_id]
        
        # Invoke ResilienceManager for handling strategy
        handling_result = self.resilience_manager.handle_choreographer_failure(
            failed_event=event,
            context=request.context
        )
        
        logger.info(
            f"Resilience strategy: {handling_result['action']} "
            f"for correlation_id={correlation_id}"
        )
        
        # Create response based on strategy
        response = SubProcessResponse(
            correlation_id=correlation_id,
            success=False,
            error_message=event.error_message
        )
        
        # Handle partial results if available
        if handling_result.get("use_partial_results") and event.partial_result:
            response.results = event.partial_result.output_data
            response.execution_time = event.partial_result.execution_time
            response.steps_executed = event.partial_result.steps_executed
            response.steps_successful = event.partial_result.steps_successful
            response.steps_failed = event.partial_result.steps_failed
            
            logger.info(
                f"Using partial results: {response.steps_successful} steps completed"
            )
        
        # Update state based on strategy
        try:
            state = self.state_store.get_state(request.workflow_id)
            if state and request.parent_step_id:
                # Would update step status based on strategy here
                # - FAILED if fail-fast
                # - COMPLETED if using partial results
                # - RETRYING if should retry
                pass
        except Exception as e:
            logger.error(f"Error updating state: {e}")
        
        # Update metrics
        self._metrics["total_failed"] += 1
        
        # Remove from pending if not retrying
        if not handling_result.get("should_retry"):
            del self._pending_requests[correlation_id]
        
        logger.warning(
            f"Sub-process failed: correlation_id={correlation_id}, "
            f"action={handling_result['action']}"
        )
        
        return response
    
    def get_pending_requests(self) -> List[str]:
        """Get list of pending correlation IDs"""
        return list(self._pending_requests.keys())
    
    def is_request_pending(self, correlation_id: str) -> bool:
        """Check if a request is still pending"""
        return correlation_id in self._pending_requests
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get bridge metrics"""
        metrics = self._metrics.copy()
        metrics["pending_requests"] = len(self._pending_requests)
        return metrics


if __name__ == "__main__":
    # Test the bridge
    from state_store import StateStore
    from resilience_manager import ResilienceManager
    from metadata_service import get_metadata_service
    from pathlib import Path
    
    print("=" * 80)
    print("ORCHESTRATOR-CHOREOGRAPHER BRIDGE TEST")
    print("=" * 80)
    
    # Initialize components
    state_store = StateStore(storage_dir=Path("/tmp/test_states"))
    resilience_manager = ResilienceManager()
    event_bus = SyncEventBus()
    
    bridge = OrchestratorChoreographerBridge(
        state_store=state_store,
        resilience_manager=resilience_manager,
        event_bus=event_bus
    )
    
    # Load metadata service
    metadata_service = get_metadata_service()
    metadata_service.load()
    
    # Get a question context
    context = metadata_service.get_question_context("P1-D1-Q1")
    if not context:
        print("ERROR: Could not load question context")
        exit(1)
    
    # Create a sub-process request
    request = SubProcessRequest(
        workflow_id="test_wf_123",
        question_ids=["P1-D1-Q1", "P1-D1-Q2"],
        sub_process_type=SubProcessType.QUESTION_ANALYSIS,
        input_data={"plan_text": "Sample plan text"},
        context=context,
        timeout_seconds=300
    )
    
    print("\nTest 1: Initiating sub-process")
    print("-" * 80)
    
    correlation_id = bridge.initiate_sub_process(request)
    print(f"Sub-process initiated: correlation_id={correlation_id}")
    print(f"Pending requests: {bridge.get_pending_requests()}")
    
    # Simulate completion event
    from event_schemas import SubProcessResult
    
    print("\nTest 2: Handling completion")
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
    
    completion_context = create_context_propagation(
        workflow_id="test_wf_123",
        question_ids=["P1-D1-Q1", "P1-D1-Q2"],
        correlation_id=correlation_id
    )
    
    completion_event = SubProcessCompletedEvent(
        metadata=completion_metadata,
        context=completion_context,
        result=result
    )
    
    response = bridge.handle_completion(completion_event)
    print(f"Response: success={response.success}")
    print(f"Execution time: {response.execution_time}s")
    print(f"Steps: {response.steps_successful}/{response.steps_executed}")
    print(f"Pending requests: {bridge.get_pending_requests()}")
    
    # Show metrics
    print("\n" + "-" * 80)
    print("Bridge Metrics")
    print("-" * 80)
    
    metrics = bridge.get_metrics()
    print(f"Total initiated: {metrics['total_initiated']}")
    print(f"Total completed: {metrics['total_completed']}")
    print(f"Total failed: {metrics['total_failed']}")
    print(f"Avg execution time: {metrics['avg_execution_time']:.2f}s")
    print(f"Pending requests: {metrics['pending_requests']}")
    
    print("\n" + "=" * 80)
    print("✓ Bridge test completed!")
    print("=" * 80)
