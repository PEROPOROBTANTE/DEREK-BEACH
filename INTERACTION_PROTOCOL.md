# Interaction Protocol: Orchestrator-Choreographer Partnership

## Overview

This document defines the **Interaction Protocol** between the **Orchestrator** (centralized control pattern) and the **Choreographer** (decentralized execution pattern) in the FARFAN 3.0 system.

The protocol establishes clear boundaries, event-driven communication, context propagation, state synchronization, and error handling across the pattern boundary.

## 1. Boundary Definition

### Orchestrator Responsibilities

The Orchestrator manages high-level workflow control and decision-making:

- **Workflow State Management**: Maintains workflow state through `StateStore`
- **Validation Rule Enforcement**: Applies validation rules via `ValidationEngine`
- **Resilience Strategy Selection**: Determines retry, fallback, or fail-fast strategies
- **Final Result Aggregation**: Combines results from multiple sub-processes
- **Metadata-Driven Execution**: Interprets `cuestionario.json` to drive workflow

### Choreographer Responsibilities

The Choreographer handles decentralized adapter execution with dependency management:

- **Adapter Execution**: Invokes 9 specialized adapters (413 methods total)
- **Dependency Resolution**: Executes adapters in correct DAG-based order (5 waves)
- **Parallel Coordination**: Runs independent adapters concurrently within waves
- **Evidence Aggregation**: Collects and synthesizes evidence from all adapters
- **Sub-Process Error Handling**: Manages failures within adapter execution chains

### Clear Separation of Concerns

```
┌─────────────────────────────────────────────────────────────────┐
│                        ORCHESTRATOR                              │
│  (Centralized Control - What to do and when)                    │
├─────────────────────────────────────────────────────────────────┤
│  • Workflow state management                                    │
│  • Decision-making & validation                                 │
│  • Resilience strategy selection                                │
│  • Result aggregation                                           │
└────────────────────┬────────────────────────────────────────────┘
                     │
           EVENT-BASED COMMUNICATION
           (SubProcessInitiated/Completed/Failed)
                     │
┌────────────────────┴────────────────────────────────────────────┐
│                       CHOREOGRAPHER                              │
│  (Decentralized Execution - How to execute)                     │
├─────────────────────────────────────────────────────────────────┤
│  • Adapter execution                                            │
│  • Dependency resolution (DAG)                                  │
│  • Parallel coordination                                        │
│  • Evidence aggregation                                         │
└─────────────────────────────────────────────────────────────────┘
```

## 2. Triggering Events (Orchestrator → Choreographer)

### SubProcessInitiatedEvent

Emitted by Orchestrator to initiate a choreographed sub-process.

**Event Structure:**

```python
{
  "metadata": {
    "event_id": "evt_abc123",           # Unique event identifier
    "event_type": "sub_process.initiated",
    "timestamp": "2024-01-01T12:00:00Z",
    "source": "orchestrator",
    "version": "1.0.0"
  },
  "context": {
    "correlation_id": "corr_xyz789",    # MANDATORY: Links request-response
    "workflow_id": "wf_456",             # MANDATORY: Parent workflow
    "question_ids": ["P1-D1-Q1", "P1-D1-Q2"],  # MANDATORY: Questions to process
    "dimension": "D1",                   # Optional: Dimension filter
    "policy_area": "P1",                 # Optional: Policy area filter
    "sub_process_id": "sub_001",         # Optional: Sub-process identifier
    "parent_step_id": "step_001"         # Optional: Parent step reference
  },
  "sub_process_type": "question_analysis",  # Type of sub-process
  "input_data": {
    "plan_text": "...",                 # Plan document text
    "question_specs": [...],            # Question specifications
    "execution_config": {...}           # Execution configuration
  },
  "timeout_seconds": 300,               # Optional: Timeout
  "retry_policy": {...}                 # Optional: Retry configuration
}
```

**Required Payload Fields:**

- `metadata`: Standard event metadata
- `context.correlation_id`: **Unique identifier linking request-response pairs**
- `context.workflow_id`: Parent workflow identifier
- `context.question_ids`: Questions being processed
- `sub_process_type`: Type of sub-process (e.g., `question_analysis`)
- `input_data`: Data references and parameters

**Trigger Conditions:**

1. Orchestrator decides to delegate work requiring multiple adapters
2. Dependency resolution needed within question analysis
3. Parallel execution opportunities identified

### AnalysisRequestedEvent

More specific variant for question analysis sub-processes.

```python
{
  "metadata": {...},
  "context": {...},
  "question_ids": ["P1-D1-Q1", "P1-D1-Q2"],
  "plan_text": "Full plan document text...",
  "execution_config": {
    "max_workers": 4,
    "enable_circuit_breaker": true
  }
}
```

## 3. Outcome Events (Choreographer → Orchestrator)

### SubProcessCompletedEvent

Emitted by Choreographer upon successful completion.

**Event Structure:**

```python
{
  "metadata": {
    "event_id": "evt_def456",
    "event_type": "sub_process.completed",
    "timestamp": "2024-01-01T12:05:00Z",
    "source": "choreographer",
    "version": "1.0.0"
  },
  "context": {
    "correlation_id": "corr_xyz789",    # SAME as triggering event
    "workflow_id": "wf_456",
    "question_ids": ["P1-D1-Q1", "P1-D1-Q2"]
  },
  "result": {
    "status": "completed",              # "completed", "partial"
    "output_data": {
      "P1-D1-Q1": {
        "score": 2.5,
        "confidence": 0.85,
        "evidence": [...]
      },
      "P1-D1-Q2": {...}
    },
    "execution_time": 45.2,
    "steps_executed": 5,
    "steps_successful": 5,
    "steps_failed": 0,
    "evidence_collected": [...],
    "overall_confidence": 0.87
  }
}
```

**Required Payload Fields:**

- `metadata`: Standard event metadata
- `context.correlation_id`: **Same correlation_id as triggering event**
- `context.workflow_id`: Same workflow_id
- `context.question_ids`: Same question_ids
- `result`: Complete results from sub-process

**Orchestrator Actions on Receipt:**

1. Validate `correlation_id` matches pending request
2. Transition from `WAITING_FOR_SUB_ANALYSIS` to next state
3. Extract results and merge into workflow state
4. Continue with dependent steps
5. Update metrics

### SubProcessFailedEvent

Emitted by Choreographer upon failure.

**Event Structure:**

```python
{
  "metadata": {
    "event_id": "evt_ghi789",
    "event_type": "sub_process.failed",
    "timestamp": "2024-01-01T12:03:00Z",
    "source": "choreographer",
    "version": "1.0.0"
  },
  "context": {
    "correlation_id": "corr_xyz789",    # SAME as triggering event
    "workflow_id": "wf_456",
    "question_ids": ["P1-D1-Q1", "P1-D1-Q2"]
  },
  "error_code": "CHOREOGRAPHER_EXECUTION_ERROR",
  "error_message": "Adapter execution failed: teoria_cambio.calculate_bayesian_confidence",
  "error_details": {
    "exception_type": "ValueError",
    "steps_completed": 3,
    "steps_failed": 2,
    "total_steps": 5
  },
  "partial_result": {              # Optional: Partial results if available
    "status": "failed",
    "output_data": {
      "P1-D1-Q1": {...}           # Results from completed steps
    },
    "steps_successful": 3
  }
}
```

**Required Payload Fields:**

- `metadata`: Standard event metadata
- `context.correlation_id`: Same as triggering event
- `error_code`: Error classification code
- `error_message`: Human-readable error description
- `error_details`: Detailed error information

**Orchestrator Actions on Receipt:**

1. Validate `correlation_id` matches pending request
2. Invoke `ResilienceManager.handle_choreographer_failure()`
3. Apply resilience strategy (retry, fallback, fail-fast, compensate)
4. Update workflow state based on strategy
5. Handle partial results if available
6. Update metrics

## 4. Context Propagation

### Mandatory Fields

All events **MUST** include these context fields:

- `correlation_id`: **Unique identifier linking request-response pairs**
- `workflow_id`: Parent workflow identifier
- `question_ids`: List of question identifiers being processed

### Optional Enrichment Fields

- `dimension`: Dimension filter (D1-D6)
- `policy_area`: Policy area filter (P1-P10)
- `sub_process_id`: Sub-process identifier for nested choreography
- `parent_step_id`: Reference to parent step in workflow

### Context Flow

```
1. Orchestrator creates ContextPropagation with correlation_id
   ↓
2. ContextPropagation included in SubProcessInitiatedEvent
   ↓
3. Choreographer receives event and extracts context
   ↓
4. Choreographer executes sub-process
   ↓
5. Choreographer includes SAME context in outcome event
   ↓
6. Orchestrator matches outcome to original request via correlation_id
```

### Example Context Propagation

```python
from event_schemas import create_context_propagation

# Orchestrator creates context
context = create_context_propagation(
    workflow_id="wf_abc123",
    question_ids=["P1-D1-Q1", "P1-D1-Q2", "P1-D1-Q3"],
    dimension="D1",
    policy_area="P1",
    parent_step_id="step_policy_analysis"
)

# Context flows through events
# correlation_id: "corr_xyz789" (auto-generated)

# Choreographer receives and processes
# ...

# Choreographer returns SAME context in outcome event
# correlation_id: "corr_xyz789" (preserved)
```

## 5. State Synchronization

### Orchestrator State Transitions

The Orchestrator uses a new state `WAITING_FOR_SUB_ANALYSIS` to track delegated work:

```python
class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"
    WAITING_FOR_SUB_ANALYSIS = "waiting_for_sub_analysis"  # NEW
```

### State Transition Flow

```
1. Orchestrator decides to delegate work
   Status: RUNNING → WAITING_FOR_SUB_ANALYSIS
   
2. Orchestrator emits SubProcessInitiatedEvent
   Status: WAITING_FOR_SUB_ANALYSIS (stable)
   
3. Choreographer executes sub-process
   (Orchestrator state unchanged)
   
4a. SubProcessCompletedEvent received
    Status: WAITING_FOR_SUB_ANALYSIS → COMPLETED
    
4b. SubProcessFailedEvent received
    Status: WAITING_FOR_SUB_ANALYSIS → FAILED/RETRYING/COMPLETED (based on strategy)
```

### State Management Code Example

```python
# Orchestrator initiates sub-process
bridge.initiate_sub_process(request)
# → Updates state to WAITING_FOR_SUB_ANALYSIS

# Choreographer completes
bridge.handle_completion(completion_event)
# → Updates state to COMPLETED

# Choreographer fails
bridge.handle_failure(failure_event)
# → Invokes ResilienceManager
# → Updates state based on recovery strategy
```

## 6. Error Handling Across Boundary

### ResilienceManager Integration

The `ResilienceManager` handles errors originating from choreographed sub-processes:

```python
def handle_choreographer_failure(
    failed_event: SubProcessFailedEvent,
    context: QuestionContext,
    retry_config: Optional[RetryConfig] = None
) -> Dict[str, Any]:
    """
    Handle failure reported by choreographed sub-process
    
    Returns recommended action:
    - retry: Retry with exponential backoff
    - fallback: Use partial results or degraded output
    - compensate: Execute compensation actions
    - skip: Skip this sub-process
    - fail: Fail immediately
    """
```

### Error Handling Strategies

| Strategy | Trigger | Action |
|----------|---------|--------|
| **RETRY** | Transient errors (network, timeout) | Retry with exponential backoff (up to 3 attempts) |
| **FALLBACK** | Non-critical errors with partial results | Use partial results or degraded output |
| **COMPENSATE** | Errors requiring rollback | Execute compensation actions (Saga pattern) |
| **SKIP** | Optional steps | Skip sub-process and continue workflow |
| **FAIL_FAST** | Critical errors | Fail workflow immediately |

### Error Handling Flow

```
1. Choreographer encounters error during execution
   ↓
2. Choreographer emits SubProcessFailedEvent with error details
   ↓
3. Orchestrator receives event via bridge
   ↓
4. Orchestrator invokes ResilienceManager.handle_choreographer_failure()
   ↓
5. ResilienceManager analyzes error code and context
   ↓
6. ResilienceManager returns recommended action
   ↓
7. Orchestrator applies action:
   - RETRY: Re-emit SubProcessInitiatedEvent (with backoff)
   - FALLBACK: Use partial_result from failed event
   - COMPENSATE: Execute compensation logic
   - SKIP: Mark step as skipped, continue workflow
   - FAIL: Mark workflow as failed
   ↓
8. Orchestrator updates workflow state accordingly
```

### Partial Result Recovery

If a choreographed sub-process fails after completing some steps, the `partial_result` field allows recovery:

```python
# Choreographer fails after completing 3 of 5 steps
failed_event = SubProcessFailedEvent(
    ...,
    partial_result=SubProcessResult(
        status="failed",
        output_data={
            "P1-D1-Q1": {"score": 2.5},  # Completed
            "P1-D1-Q2": {"score": 1.8},  # Completed
            "P1-D1-Q3": {"score": 2.0}   # Completed
            # P1-D1-Q4 and P1-D1-Q5 not completed
        },
        steps_successful=3,
        steps_failed=2
    )
)

# Orchestrator can use partial results if strategy allows
if strategy == ErrorStrategy.FALLBACK:
    results = failed_event.partial_result.output_data
    # Continue with partial results
```

## 7. Shared Contract Registry

### EventSchemaRegistry

Both Orchestrator and Choreographer **MUST** adhere to event schemas defined in `EventSchemaRegistry`:

```python
from event_schemas import get_event_schema_registry

registry = get_event_schema_registry()

# Validate event before publishing
is_valid, errors = registry.validate_event(
    EventType.SUB_PROCESS_INITIATED,
    event_data
)

if not is_valid:
    logger.error(f"Event validation failed: {errors}")
    # Event will not be published
```

### Schema Versioning

All events include a `version` field for forward compatibility:

```python
"metadata": {
    "event_id": "evt_abc123",
    "event_type": "sub_process.initiated",
    "version": "1.0.0"  # Schema version
}
```

Version evolution:
- `1.0.0`: Initial protocol implementation
- `1.1.0`: Backward-compatible additions (new optional fields)
- `2.0.0`: Breaking changes (requires consumer updates)

### Registered Schemas

```python
# List all registered schemas
schemas = registry.list_schemas()
# ['sub_process.initiated', 'sub_process.completed', 'sub_process.failed', ...]

# Get schema details
schema = registry.get_schema(EventType.SUB_PROCESS_INITIATED)
# {
#   "name": "SubProcessInitiatedEvent",
#   "version": "1.0.0",
#   "direction": "orchestrator_to_choreographer",
#   "required_fields": ["metadata", "context", "sub_process_type", "input_data"],
#   "description": "Initiates a choreographed sub-process"
# }
```

## 8. Complete Integration Example

### Orchestrator Side

```python
from orchestrator_choreographer_integration import (
    OrchestratorChoreographerBridge,
    SubProcessRequest
)
from event_schemas import SubProcessType

# Initialize bridge
bridge = OrchestratorChoreographerBridge(
    state_store=state_store,
    resilience_manager=resilience_manager,
    event_bus=event_bus
)

# Create request
request = SubProcessRequest(
    workflow_id="wf_plan_abc_2024",
    question_ids=["P1-D1-Q1", "P1-D1-Q2", "P1-D1-Q3"],
    sub_process_type=SubProcessType.QUESTION_ANALYSIS,
    input_data={
        "plan_text": plan_text,
        "question_specs": question_specs
    },
    context=question_context,
    timeout_seconds=300
)

# Initiate sub-process
correlation_id = bridge.initiate_sub_process(request)
# → State transitions to WAITING_FOR_SUB_ANALYSIS
# → SubProcessInitiatedEvent emitted

# Wait for outcome event (in real system, handled asynchronously)
# ...

# Handle completion
response = bridge.handle_completion(completion_event)
if response.success:
    results = response.results
    # Continue workflow with results
    
# Or handle failure
response = bridge.handle_failure(failure_event)
# → ResilienceManager determines strategy
# → State updated based on strategy
```

### Choreographer Side

```python
from choreographer import ExecutionChoreographer
from event_schemas import create_context_propagation

# Initialize choreographer with event bus
choreographer = ExecutionChoreographer(
    max_workers=4,
    event_bus=event_bus
)

# Execute question chain with context propagation
context = create_context_propagation(
    workflow_id="wf_plan_abc_2024",
    question_ids=["P1-D1-Q1"],
    correlation_id="corr_xyz789"  # From SubProcessInitiatedEvent
)

results = choreographer.execute_question_chain(
    question_spec=question_spec,
    plan_text=plan_text,
    module_adapter_registry=registry,
    circuit_breaker=circuit_breaker,
    context_propagation=context
)
# → If context provided, emits SubProcessCompletedEvent on success
# → Or emits SubProcessFailedEvent on failure
```

## 9. Observability and Monitoring

### Metrics

**Event Bus Metrics:**
```python
metrics = event_bus.get_metrics()
# {
#   "total_published": 150,
#   "total_delivered": 148,
#   "total_failed": 2,
#   "by_event_type": {
#     "sub_process.initiated": 50,
#     "sub_process.completed": 45,
#     "sub_process.failed": 5
#   }
# }
```

**Bridge Metrics:**
```python
metrics = bridge.get_metrics()
# {
#   "total_initiated": 50,
#   "total_completed": 45,
#   "total_failed": 5,
#   "avg_execution_time": 42.5,
#   "pending_requests": 0
# }
```

### Correlation Tracking

```python
# Get all events in a correlation chain
chain = event_bus.get_correlation_chain("corr_xyz789")
# {
#   "initiated_at": "2024-01-01T12:00:00Z",
#   "events": [
#     {"event_type": "sub_process.initiated", "timestamp": "2024-01-01T12:00:00Z"},
#     {"event_type": "sub_process.completed", "timestamp": "2024-01-01T12:05:00Z"}
#   ]
# }
```

### Event Persistence

All events are persisted to disk for audit trail:

```
./events/
  ├── wf_plan_abc_2024/
  │   ├── 2024-01-01T12:00:00_sub_process.initiated.json
  │   ├── 2024-01-01T12:05:00_sub_process.completed.json
  │   └── ...
  └── wf_plan_xyz_2024/
      └── ...
```

## 10. Best Practices

### For Orchestrator Developers

1. **Always provide correlation_id**: Ensures request-response tracking
2. **Set appropriate timeouts**: Prevent hanging on choreographer failures
3. **Handle partial results**: Extract value from failed sub-processes
4. **Monitor pending requests**: Track long-running sub-processes
5. **Use appropriate error strategies**: Match strategy to criticality

### For Choreographer Developers

1. **Always emit outcome events**: Even on failure, report status
2. **Include partial results**: Help orchestrator recover from failures
3. **Preserve context**: Pass correlation_id unchanged in outcome events
4. **Aggregate evidence**: Collect evidence from all adapters
5. **Handle adapter failures gracefully**: Continue execution when possible

### For Integration

1. **Validate events against schemas**: Catch contract violations early
2. **Monitor event bus metrics**: Detect communication issues
3. **Review correlation chains**: Trace request-response flows
4. **Test error scenarios**: Ensure resilience strategies work
5. **Version schemas carefully**: Maintain backward compatibility

## 11. Testing

### Unit Tests

Test individual components:

```bash
python3 event_schemas.py            # Test schema registry
python3 event_bus.py                # Test event bus
python3 orchestrator_choreographer_integration.py  # Test bridge
```

### Integration Tests

Test complete request-response flow:

```python
# Test successful sub-process
correlation_id = bridge.initiate_sub_process(request)
# → Choreographer executes
# → Choreographer emits completion
response = bridge.handle_completion(completion_event)
assert response.success == True

# Test failed sub-process with retry
correlation_id = bridge.initiate_sub_process(request)
# → Choreographer fails
response = bridge.handle_failure(failure_event)
# → ResilienceManager recommends retry
# → Orchestrator re-emits SubProcessInitiatedEvent
```

## 12. Summary

The Interaction Protocol establishes a robust, event-driven partnership between Orchestrator and Choreographer:

✅ **Boundary Definition**: Clear separation of responsibilities  
✅ **Triggering Events**: Structured events for initiating sub-processes  
✅ **Outcome Events**: Success and failure reporting with results  
✅ **Context Propagation**: Correlation tracking across boundary  
✅ **State Synchronization**: WAITING_FOR_SUB_ANALYSIS state tracking  
✅ **Error Handling**: Resilience strategies for choreographer failures  
✅ **Shared Contract Registry**: Schema validation and versioning  

This protocol enables loose coupling while maintaining strong contracts, supporting scalable and maintainable orchestration of complex policy analysis workflows.
