# Industrial-Grade Orchestrator Documentation

## Overview

This document describes the industrial-grade orchestrator system implemented for managing complex policy analysis workflows. The orchestrator ensures deterministic execution, enforces data immutability, and dynamically drives component interactions based on external metadata defined in `cuestionario.json`.

## Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                  IndustrialOrchestrator                      │
│  (Centralized Control & Workflow Coordination)               │
└───────┬─────────────────────────────────────────────────────┘
        │
        ├─► MetadataService
        │   • Loads cuestionario.json
        │   • Enriches QuestionContext
        │   • Version tracking
        │
        ├─► StateStore
        │   • Immutable WorkflowState
        │   • Atomic updates (optimistic locking)
        │   • State history & audit trail
        │   • Disk persistence
        │
        ├─► ValidationEngine
        │   • Multi-type validation rules
        │   • Detailed violation reporting
        │   • Performance tracking
        │
        ├─► ResilienceManager
        │   • Circuit breaker integration
        │   • Retry strategies (exponential backoff)
        │   • Failure classification
        │   • Compensation actions (Saga pattern)
        │
        ├─► ModuleController
        │   • Standardized invocation interface
        │   • QuestionContext injection
        │   • Result normalization
        │   • Integration with validation & resilience
        │
        └─► DeterministicUtils
            • Seed generation for reproducibility
            • Hash-based identifiers
            • Deterministic random generators
```

## Component Details

### 1. MetadataService (`metadata_service.py`)

**Purpose**: Centralized management of `cuestionario.json` metadata.

**Key Features**:
- Thread-safe singleton pattern
- Lazy loading and caching
- Strongly-typed `QuestionContext` dataclass
- Version tracking for deterministic execution
- Rich query interface (by dimension, policy area, dependencies)

**Usage**:
```python
from metadata_service import get_metadata_service

service = get_metadata_service()
service.load()

# Get question context
context = service.get_question_context("P1-D1-Q1")

# Query by dimension
contexts = service.get_contexts_by_dimension("D1")

# Get critical questions
critical = service.get_critical_questions()
```

**Data Structures**:
- `QuestionContext`: Immutable context with validation rules, dependencies, scoring config
- `ValidationRule`: Type-safe validation rule definitions
- `ErrorStrategy`: Enum for error handling strategies (RETRY, FALLBACK, FAIL_FAST, etc.)

### 2. StateStore (`state_store.py`)

**Purpose**: Immutable workflow state management with persistence.

**Key Features**:
- Immutable `WorkflowState` using frozen dataclasses
- Atomic updates with optimistic locking (version-based)
- Complete state history for audit trail
- Thread-safe operations
- JSON persistence to disk for recovery

**Usage**:
```python
from state_store import StateStore

store = StateStore(storage_dir=Path("./workflow_states"))

# Create workflow
state = store.create_workflow(
    workflow_id="wf_123",
    metadata={"plan_name": "Plan ABC"}
)

# Update state atomically
state = store.update_state(
    "wf_123",
    {"status": WorkflowStatus.RUNNING},
    expected_version=1  # Optimistic locking
)

# Mark step completed
result = StepResult(...)
state = store.mark_step_completed("wf_123", "step_1", result)

# Get state history
history = store.get_history("wf_123")
```

**Data Structures**:
- `WorkflowState`: Immutable workflow snapshot with version tracking
- `StepResult`: Immutable step execution result
- `WorkflowStatus`: CREATED, RUNNING, COMPLETED, FAILED, PAUSED, CANCELLED
- `StepStatus`: PENDING, RUNNING, COMPLETED, FAILED, SKIPPED, RETRYING

### 3. ValidationEngine (`validation_engine.py`)

**Purpose**: Centralized validation of module outputs against rules.

**Key Features**:
- Multiple validation types: type check, schema, regex, range, required fields
- Detailed violation reporting with severity levels (error/warning)
- Immutable `ValidationResult` and `ValidationViolation` dataclasses
- Performance tracking and statistics
- Extensible rule system

**Usage**:
```python
from validation_engine import ValidationEngine

engine = ValidationEngine()

# Validate output
result = engine.validate(output, question_context)

if result.is_valid:
    print(f"Validation passed: {len(result.passed_rules)} rules")
else:
    print(f"Validation failed: {result.error_count} errors")
    for violation in result.violations:
        print(f"  - {violation.field_name}: {violation.message}")

# Get statistics
stats = engine.get_stats()
```

**Validation Types**:
- `TYPE_CHECK`: Validate field types
- `SCHEMA_VALIDATION`: JSON schema validation
- `REGEX_MATCH`: Pattern matching in text fields
- `RANGE_CHECK`: Numeric range validation
- `REQUIRED_FIELDS`: Presence validation
- `CUSTOM_LOGIC`: Extensible custom validation

### 4. ResilienceManager (`resilience_manager.py`)

**Purpose**: Fault tolerance with retry, circuit breaker, and compensation.

**Key Features**:
- Integration with existing `CircuitBreaker`
- Multiple retry strategies: fixed, exponential, jittered exponential
- Failure classification: technical, validation, business logic, resource
- Differentiated handling based on failure type
- Compensation actions for transactional behavior (Saga pattern)
- Comprehensive failure tracking and metrics

**Usage**:
```python
from resilience_manager import ResilienceManager, RetryConfig, RetryStrategy

manager = ResilienceManager()

# Execute with resilience
result = manager.execute_with_resilience(
    operation=lambda: some_operation(),
    context=question_context,
    step_id="step_1",
    retry_config=RetryConfig(
        strategy=RetryStrategy.EXPONENTIAL,
        max_attempts=3,
        base_delay=1.0
    )
)

# Get metrics
metrics = manager.get_metrics()
print(f"Total retries: {metrics['total_retries']}")
print(f"Retry success rate: {metrics['retry_success_rate']:.1%}")
```

**Retry Strategies**:
- `NONE`: No retries
- `FIXED`: Fixed delay between retries
- `EXPONENTIAL`: Exponential backoff (delay = base * 2^(attempt-1))
- `JITTERED_EXPONENTIAL`: Exponential with random jitter to avoid thundering herd

### 5. ModuleController (`module_controller.py`)

**Purpose**: Standardized interface for component invocation.

**Key Features**:
- QuestionContext injection into module calls
- Result normalization from `ModuleResult` to orchestrator format
- Integration with `ValidationEngine` and `ResilienceManager`
- Performance tracking per module/method
- Adapter availability checking

**Usage**:
```python
from module_controller import ModuleController

controller = ModuleController(
    module_registry=registry,
    enable_validation=True,
    enable_resilience=True
)

# Invoke module with context
result = controller.invoke(
    module_name="policy_processor",
    method_name="extract_baseline_data",
    context=question_context,
    kwargs={"document_text": text}
)

# Check result
if result.is_success and result.is_validated:
    print(f"Output: {result.output}")
else:
    print(f"Errors: {result.errors}")
```

### 6. DeterministicUtils (`deterministic_utils.py`)

**Purpose**: Support for deterministic, reproducible execution.

**Key Features**:
- Deterministic seed generation from workflow/step identifiers
- Hash-based unique identifiers
- Reproducible random number generation
- Verification utilities for determinism testing

**Usage**:
```python
from deterministic_utils import (
    create_deterministic_seed,
    create_deterministic_id,
    DeterministicRandom
)

# Create deterministic seed
seed = create_deterministic_seed(
    workflow_id="wf_123",
    step_id="step_1",
    version="2.0.0"
)

# Use deterministic random generator
rng = DeterministicRandom(seed)
value = rng.random()  # Reproducible!

# Create deterministic ID
workflow_id = create_deterministic_id("workflow", "plan_abc", "2024-01-01")
```

### 7. IndustrialOrchestrator (`industrial_orchestrator.py`)

**Purpose**: Central orchestration engine integrating all components.

**Key Features**:
- Metadata-driven workflow from `cuestionario.json`
- Deterministic execution with seed-based reproducibility
- Immutable state management with atomic updates
- Comprehensive validation at each step
- Resilience with retry/circuit breaker
- Dependency checking and resolution
- Structured logging with workflow context
- Complete audit trail

**Usage**:
```python
from industrial_orchestrator import IndustrialOrchestrator, WorkflowConfig

# Initialize orchestrator
config = WorkflowConfig(
    enable_validation=True,
    enable_resilience=True,
    enable_deterministic_mode=True,
    fail_fast=False
)

orchestrator = IndustrialOrchestrator(
    module_registry=registry,
    config=config
)

# Execute workflow
result = orchestrator.execute_workflow(
    question_ids=["P1-D1-Q1", "P1-D1-Q2", "P1-D1-Q3"],
    document_text=document_text,
    workflow_name="Plan ABC Analysis",
    metadata={"plan_id": "abc123"}
)

# Check result
print(f"Success: {result.success}")
print(f"Success rate: {result.success_rate:.1%}")
print(f"Completed: {len(result.completed_steps)}")
print(f"Failed: {len(result.failed_steps)}")
print(f"Execution time: {result.execution_time:.2f}s")

# Get workflow status
state = orchestrator.get_workflow_status(result.workflow_id)
print(f"Status: {state.status.value}")
```

## Workflow Execution Flow

```
1. INITIATION
   ├─► Create WorkflowState with unique ID
   ├─► Load metadata from cuestionario.json
   └─► Initialize deterministic seed

2. FOR EACH QUESTION:
   ├─► Load QuestionContext from MetadataService
   │
   ├─► Check Dependencies
   │   └─► If not met: Skip step
   │
   ├─► Mark Step Running
   │   └─► Update StateStore atomically
   │
   ├─► Invoke Component (with resilience)
   │   ├─► Check circuit breaker
   │   ├─► Inject QuestionContext
   │   ├─► Execute with retry on failure
   │   └─► Return normalized result
   │
   ├─► Validate Output
   │   ├─► Apply validation rules
   │   ├─► Generate ValidationResult
   │   └─► Log violations if any
   │
   ├─► Decision Point
   │   ├─► PASS: Mark step completed
   │   ├─► FAIL (validation): Retry or fail
   │   ├─► FAIL (technical): Retry with backoff
   │   └─► FAIL (exhausted): Mark step failed
   │
   └─► Update State
       └─► Atomic state update with new version

3. COMPLETION
   ├─► Aggregate results
   ├─► Mark workflow completed/failed
   ├─► Generate WorkflowResult
   └─► Return to caller
```

## Determinism Guarantees

The orchestrator ensures deterministic execution through:

1. **Deterministic Identifiers**: Workflow and step IDs generated from hash of inputs
2. **Version Tracking**: All components and schemas are versioned
3. **Seed-Based Random**: All randomness derived from deterministic seeds
4. **Immutable State**: No in-place modifications, only new state versions
5. **Ordered Execution**: Dependencies ensure consistent execution order
6. **Fixed Metadata**: cuestionario.json version locked per workflow

**Example**:
```python
# Same inputs always produce same outputs
result1 = orchestrator.execute_workflow(
    question_ids=["P1-D1-Q1"],
    document_text="Sample document",
    workflow_name="Test"
)

result2 = orchestrator.execute_workflow(
    question_ids=["P1-D1-Q1"],
    document_text="Sample document",
    workflow_name="Test"
)

assert result1.workflow_id == result2.workflow_id
assert result1.step_results == result2.step_results
```

## Immutability Patterns

All data structures favor immutability:

1. **Frozen Dataclasses**: Core data types use `@dataclass(frozen=True)`
2. **Copy-on-Update**: State updates create new instances
3. **Version Tracking**: Each state change increments version number
4. **History Preservation**: All previous states retained for audit
5. **Atomic Updates**: Optimistic locking prevents race conditions

## Error Handling Strategies

Different strategies for different error types:

| Strategy | When to Use | Behavior |
|----------|-------------|----------|
| RETRY | Transient technical failures | Retry with exponential backoff |
| FALLBACK | Non-critical failures | Return degraded result |
| FAIL_FAST | Critical failures | Stop immediately |
| SKIP | Optional steps | Skip and continue |
| COMPENSATE | Transactional workflows | Execute compensation actions |

## Observability

### Structured Logging

All log entries include workflow context:

```python
logger.info(
    "Processing step",
    extra={"workflow_id": workflow_id}
)
```

### Metrics

Available metrics:
- Workflow execution time
- Step success/failure rates
- Validation pass rates
- Retry counts and success rates
- Circuit breaker status
- Module performance (avg time per call)

```python
stats = orchestrator.get_statistics()
print(f"Total workflows: {stats['total_workflows']}")
print(f"Validation pass rate: {stats['validation_engine']['pass_rate']:.1%}")
```

### State History

Complete audit trail of state changes:

```python
history = state_store.get_history(workflow_id)
for state in history:
    print(f"v{state.version}: {state.status.value} @ {state.updated_at}")
```

## Configuration

### WorkflowConfig Options

```python
config = WorkflowConfig(
    enable_validation=True,       # Enable output validation
    enable_resilience=True,        # Enable retry/circuit breaker
    fail_fast=False,               # Stop on first error
    parallel_execution=False,      # Future: parallel steps
    max_retries=3,                 # Max retry attempts
    timeout_seconds=3600,          # Workflow timeout (1 hour)
    storage_dir=Path("./states"),  # State persistence directory
    enable_deterministic_mode=True,# Deterministic execution
    seed_base=None                 # Optional seed override
)
```

## Best Practices

1. **Always Use QuestionContext**: Inject context for metadata-driven behavior
2. **Enable Validation**: Catch issues early with validation rules
3. **Use Deterministic Mode**: Ensures reproducible results for testing
4. **Monitor State History**: Use for debugging and audit compliance
5. **Set Appropriate Timeouts**: Prevent hanging workflows
6. **Check Dependencies**: Ensure proper execution order
7. **Handle Failures Gracefully**: Use appropriate error strategies
8. **Track Metrics**: Monitor system health and performance

## Testing

### Unit Tests

Test individual components:

```bash
python3 metadata_service.py       # Test metadata loading
python3 validation_engine.py      # Test validation
python3 state_store.py           # Test state management
python3 resilience_manager.py    # Test retry logic
python3 deterministic_utils.py   # Test determinism
```

### Integration Tests

Test complete workflow:

```python
# Test determinism
result1 = orchestrator.execute_workflow(...)
result2 = orchestrator.execute_workflow(...)
assert result1.workflow_id == result2.workflow_id

# Test resilience
# (Inject failures to test retry behavior)

# Test validation
# (Provide invalid outputs to test validation)
```

## Future Enhancements

1. **Parallel Execution**: Execute independent steps in parallel
2. **Streaming Results**: Stream step results as they complete
3. **Distributed Orchestration**: Support for distributed workflows
4. **Advanced Compensation**: More sophisticated Saga pattern implementation
5. **OpenTelemetry Integration**: Distributed tracing support
6. **GraphQL API**: Query interface for workflow status
7. **Web Dashboard**: Real-time workflow monitoring UI

## References

- Circuit Breaker Pattern: Martin Fowler's pattern catalog
- Saga Pattern: Microservices transaction management
- Optimistic Locking: Concurrent state management
- Immutable Infrastructure: Infrastructure as Code principles
- OpenTelemetry: Observability standard

## License

Part of FARFAN 3.0 - Industrial Policy Analysis System
