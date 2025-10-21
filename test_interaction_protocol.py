"""
Integration Test for Orchestrator-Choreographer Interaction Protocol
=====================================================================

Tests the complete interaction flow including:
1. Event schema validation
2. Event bus communication
3. Context propagation
4. State synchronization
5. Error handling across boundary

Author: FARFAN 3.0 - Orchestrator-Choreographer Partnership
Version: 1.0.0
Python: 3.10+
"""

import asyncio
from pathlib import Path

from event_schemas import (
    EventType,
    SubProcessType,
    SubProcessResult,
    SubProcessInitiatedEvent,
    SubProcessCompletedEvent,
    SubProcessFailedEvent,
    create_event_metadata,
    create_context_propagation,
    get_event_schema_registry
)
from event_bus import EventBus, SyncEventBus
from orchestrator_choreographer_integration import (
    OrchestratorChoreographerBridge,
    SubProcessRequest
)
from state_store import StateStore
from resilience_manager import ResilienceManager
from metadata_service import get_metadata_service


def test_event_schema_validation():
    """Test 1: Event schema validation"""
    print("\n" + "=" * 80)
    print("TEST 1: Event Schema Validation")
    print("=" * 80)
    
    registry = get_event_schema_registry()
    
    # Valid event
    valid_event = {
        "metadata": {
            "event_id": "evt_test_123",
            "event_type": "sub_process.initiated",
            "timestamp": "2024-01-01T12:00:00Z",
            "source": "orchestrator"
        },
        "context": {
            "correlation_id": "corr_test_abc",
            "workflow_id": "wf_test_456",
            "question_ids": ["P1-D1-Q1"]
        },
        "sub_process_type": "question_analysis",
        "input_data": {"plan_text": "..."}
    }
    
    is_valid, errors = registry.validate_event(
        EventType.SUB_PROCESS_INITIATED,
        valid_event
    )
    
    assert is_valid, f"Valid event failed validation: {errors}"
    print("✓ Valid event passed validation")
    
    # Invalid event (missing correlation_id)
    invalid_event = {
        "metadata": {
            "event_id": "evt_test_124",
            "event_type": "sub_process.initiated",
            "timestamp": "2024-01-01T12:00:00Z",
            "source": "orchestrator"
        },
        "context": {
            "workflow_id": "wf_test_456",
            "question_ids": ["P1-D1-Q1"]
        },
        "sub_process_type": "question_analysis",
        "input_data": {"plan_text": "..."}
    }
    
    is_valid, errors = registry.validate_event(
        EventType.SUB_PROCESS_INITIATED,
        invalid_event
    )
    
    assert not is_valid, "Invalid event passed validation"
    assert "correlation_id" in str(errors), "Should detect missing correlation_id"
    print(f"✓ Invalid event detected: {errors}")
    
    print("✓ TEST 1 PASSED")


async def test_event_bus_communication():
    """Test 2: Event bus communication"""
    print("\n" + "=" * 80)
    print("TEST 2: Event Bus Communication")
    print("=" * 80)
    
    event_bus = EventBus(enable_persistence=False)
    
    # Track received events
    received_events = []
    
    async def handle_initiated(event_data):
        received_events.append("initiated")
        print(f"  → Handler received SubProcessInitiatedEvent")
    
    async def handle_completed(event_data):
        received_events.append("completed")
        print(f"  → Handler received SubProcessCompletedEvent")
    
    # Subscribe handlers
    event_bus.subscribe(EventType.SUB_PROCESS_INITIATED, handle_initiated)
    event_bus.subscribe(EventType.SUB_PROCESS_COMPLETED, handle_completed)
    
    # Publish initiated event
    metadata = create_event_metadata(EventType.SUB_PROCESS_INITIATED, "orchestrator")
    context = create_context_propagation(
        workflow_id="wf_test_123",
        question_ids=["P1-D1-Q1"]
    )
    
    event = SubProcessInitiatedEvent(
        metadata=metadata,
        context=context,
        sub_process_type=SubProcessType.QUESTION_ANALYSIS,
        input_data={"plan_text": "Test plan"}
    )
    
    success = await event_bus.publish(
        EventType.SUB_PROCESS_INITIATED,
        event.to_dict()
    )
    
    assert success, "Failed to publish initiated event"
    await asyncio.sleep(0.1)  # Allow handlers to execute
    
    # Publish completed event
    completion_metadata = create_event_metadata(EventType.SUB_PROCESS_COMPLETED, "choreographer")
    result = SubProcessResult(
        status="completed",
        output_data={"P1-D1-Q1": {"score": 2.5}},
        execution_time=10.0,
        steps_executed=3,
        steps_successful=3,
        steps_failed=0
    )
    
    completion_event = SubProcessCompletedEvent(
        metadata=completion_metadata,
        context=context,
        result=result
    )
    
    success = await event_bus.publish(
        EventType.SUB_PROCESS_COMPLETED,
        completion_event.to_dict()
    )
    
    assert success, "Failed to publish completed event"
    await asyncio.sleep(0.1)  # Allow handlers to execute
    
    # Verify events received
    assert received_events == ["initiated", "completed"], \
        f"Expected ['initiated', 'completed'], got {received_events}"
    
    print("✓ Events published and received successfully")
    
    # Check correlation chain
    chain = event_bus.get_correlation_chain(context.correlation_id)
    assert chain is not None, "Correlation chain not tracked"
    assert len(chain["events"]) == 2, "Should have 2 events in chain"
    
    print(f"✓ Correlation chain tracked: {len(chain['events'])} events")
    print("✓ TEST 2 PASSED")


def test_context_propagation():
    """Test 3: Context propagation across boundary"""
    print("\n" + "=" * 80)
    print("TEST 3: Context Propagation")
    print("=" * 80)
    
    # Create context with specific correlation_id
    context = create_context_propagation(
        workflow_id="wf_test_789",
        question_ids=["P1-D1-Q1", "P1-D1-Q2"],
        dimension="D1",
        policy_area="P1"
    )
    
    original_correlation_id = context.correlation_id
    
    # Simulate event flow
    initiated_event = SubProcessInitiatedEvent(
        metadata=create_event_metadata(EventType.SUB_PROCESS_INITIATED, "orchestrator"),
        context=context,
        sub_process_type=SubProcessType.QUESTION_ANALYSIS,
        input_data={"plan_text": "Test"}
    )
    
    # Verify context in initiated event
    assert initiated_event.context.correlation_id == original_correlation_id
    assert initiated_event.context.workflow_id == "wf_test_789"
    assert set(initiated_event.context.question_ids) == {"P1-D1-Q1", "P1-D1-Q2"}
    
    print(f"✓ Context preserved in initiated event: correlation_id={original_correlation_id}")
    
    # Simulate completion with SAME context
    completed_event = SubProcessCompletedEvent(
        metadata=create_event_metadata(EventType.SUB_PROCESS_COMPLETED, "choreographer"),
        context=context,  # SAME context
        result=SubProcessResult(
            status="completed",
            output_data={},
            execution_time=5.0,
            steps_executed=2,
            steps_successful=2,
            steps_failed=0
        )
    )
    
    # Verify context preserved
    assert completed_event.context.correlation_id == original_correlation_id
    assert completed_event.context.workflow_id == "wf_test_789"
    
    print(f"✓ Context preserved in completed event: correlation_id={original_correlation_id}")
    print("✓ TEST 3 PASSED")


def test_bridge_integration():
    """Test 4: Bridge integration (initiate and complete)"""
    print("\n" + "=" * 80)
    print("TEST 4: Bridge Integration")
    print("=" * 80)
    
    # Initialize components
    state_store = StateStore(storage_dir=Path("/tmp/test_states_bridge"))
    resilience_manager = ResilienceManager()
    event_bus = SyncEventBus()
    
    bridge = OrchestratorChoreographerBridge(
        state_store=state_store,
        resilience_manager=resilience_manager,
        event_bus=event_bus
    )
    
    # Load metadata
    metadata_service = get_metadata_service()
    metadata_service.load()
    context = metadata_service.get_question_context("P1-D1-Q1")
    
    # Create request
    request = SubProcessRequest(
        workflow_id="wf_test_bridge_123",
        question_ids=["P1-D1-Q1"],
        sub_process_type=SubProcessType.QUESTION_ANALYSIS,
        input_data={"plan_text": "Test plan"},
        context=context,
        timeout_seconds=300
    )
    
    # Initiate sub-process
    correlation_id = bridge.initiate_sub_process(request)
    print(f"✓ Sub-process initiated: correlation_id={correlation_id}")
    
    # Verify pending
    assert bridge.is_request_pending(correlation_id), "Request should be pending"
    assert len(bridge.get_pending_requests()) == 1
    print(f"✓ Request tracked as pending")
    
    # Simulate completion
    completion_metadata = create_event_metadata(
        EventType.SUB_PROCESS_COMPLETED,
        "choreographer"
    )
    
    result = SubProcessResult(
        status="completed",
        output_data={"P1-D1-Q1": {"score": 2.5}},
        execution_time=15.0,
        steps_executed=3,
        steps_successful=3,
        steps_failed=0
    )
    
    completion_context = create_context_propagation(
        workflow_id="wf_test_bridge_123",
        question_ids=["P1-D1-Q1"],
        correlation_id=correlation_id
    )
    
    completion_event = SubProcessCompletedEvent(
        metadata=completion_metadata,
        context=completion_context,
        result=result
    )
    
    # Handle completion
    response = bridge.handle_completion(completion_event)
    
    assert response.success, "Response should indicate success"
    assert response.correlation_id == correlation_id
    assert response.steps_successful == 3
    
    print(f"✓ Completion handled: {response.steps_successful}/{response.steps_executed} steps")
    
    # Verify no longer pending
    assert not bridge.is_request_pending(correlation_id), "Request should no longer be pending"
    assert len(bridge.get_pending_requests()) == 0
    
    print("✓ Request removed from pending")
    print("✓ TEST 4 PASSED")


def test_error_handling():
    """Test 5: Error handling across boundary"""
    print("\n" + "=" * 80)
    print("TEST 5: Error Handling Across Boundary")
    print("=" * 80)
    
    # Initialize components
    state_store = StateStore(storage_dir=Path("/tmp/test_states_error"))
    resilience_manager = ResilienceManager()
    event_bus = SyncEventBus()
    
    bridge = OrchestratorChoreographerBridge(
        state_store=state_store,
        resilience_manager=resilience_manager,
        event_bus=event_bus
    )
    
    # Load metadata
    metadata_service = get_metadata_service()
    metadata_service.load()
    context = metadata_service.get_question_context("P1-D1-Q1")
    
    # Create request
    request = SubProcessRequest(
        workflow_id="wf_test_error_123",
        question_ids=["P1-D1-Q1", "P1-D1-Q2"],
        sub_process_type=SubProcessType.QUESTION_ANALYSIS,
        input_data={"plan_text": "Test plan"},
        context=context,
        timeout_seconds=300
    )
    
    # Initiate sub-process
    correlation_id = bridge.initiate_sub_process(request)
    print(f"✓ Sub-process initiated: correlation_id={correlation_id}")
    
    # Simulate failure with partial results
    failure_metadata = create_event_metadata(
        EventType.SUB_PROCESS_FAILED,
        "choreographer"
    )
    
    partial_result = SubProcessResult(
        status="failed",
        output_data={"P1-D1-Q1": {"score": 2.5}},  # One question completed
        execution_time=8.0,
        steps_executed=3,
        steps_successful=1,
        steps_failed=2
    )
    
    failure_context = create_context_propagation(
        workflow_id="wf_test_error_123",
        question_ids=["P1-D1-Q1", "P1-D1-Q2"],
        correlation_id=correlation_id
    )
    
    failure_event = SubProcessFailedEvent(
        metadata=failure_metadata,
        context=failure_context,
        error_code="CHOREOGRAPHER_EXECUTION_ERROR",
        error_message="Adapter execution failed",
        error_details={
            "exception_type": "ValueError",
            "steps_completed": 1,
            "steps_failed": 2
        },
        partial_result=partial_result
    )
    
    # Handle failure
    response = bridge.handle_failure(failure_event)
    
    assert not response.success, "Response should indicate failure"
    assert response.correlation_id == correlation_id
    assert response.error_message == "Adapter execution failed"
    
    print(f"✓ Failure handled: error={response.error_message[:50]}")
    
    # Verify partial results available
    if response.results:
        print(f"✓ Partial results recovered: {len(response.results)} questions")
    
    # Verify ResilienceManager was invoked
    metrics = resilience_manager.get_metrics()
    assert metrics["by_failure_type"]["choreographer_error"] > 0, \
        "ResilienceManager should have tracked choreographer error"
    
    print("✓ ResilienceManager tracked error")
    print("✓ TEST 5 PASSED")


def run_all_tests():
    """Run all integration tests"""
    print("\n" + "=" * 80)
    print("ORCHESTRATOR-CHOREOGRAPHER INTERACTION PROTOCOL TESTS")
    print("=" * 80)
    
    # Test 1: Schema validation
    test_event_schema_validation()
    
    # Test 2: Event bus communication (async)
    asyncio.run(test_event_bus_communication())
    
    # Test 3: Context propagation
    test_context_propagation()
    
    # Test 4: Bridge integration
    test_bridge_integration()
    
    # Test 5: Error handling
    test_error_handling()
    
    print("\n" + "=" * 80)
    print("✓ ALL TESTS PASSED!")
    print("=" * 80)
    print("\nInteraction Protocol Implementation Verified:")
    print("  ✓ Event schema validation")
    print("  ✓ Event-based communication")
    print("  ✓ Context propagation (correlation_id)")
    print("  ✓ State synchronization")
    print("  ✓ Error handling across boundary")
    print("=" * 80)


if __name__ == "__main__":
    run_all_tests()
