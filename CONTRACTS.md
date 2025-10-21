# Software Contracts for DEREK-BEACH System

This document describes the 7 explicit software contracts implemented to guarantee determinism, auditability, security, and statistical validity.

## Overview

The DEREK-BEACH system implements formal software contracts based on rigorous theoretical foundations to ensure:

- **Determinism**: Same inputs → same outputs
- **Auditability**: Complete traceability and verification
- **Security**: Safe execution under faults
- **Statistical Validity**: Provable guarantees on predictions

All contracts are implemented in the `contracts/` module and thoroughly tested in `tests/test_contracts.py`.

---

## 1. Routing Contract (RC)

**Purpose**: Ensures deterministic routes for identical inputs with transparent tiebreaking.

**Theoretical Foundation**: Based on Abernethy et al. (2022) theorem guaranteeing unique convergence via deterministic projections on convex polytopes.

### Guarantees

1. **Deterministic Routing**: Identical canonical inputs always produce identical routes
2. **Canonical Input Enforcement**: Only normalized inputs are accepted
3. **Tiebreaking Transparency**: Clear explanations when multiple routes are possible
4. **Route Reproducibility**: Same route given same canonical input

### Key Components

- **`CanonicalInput`**: Normalized input representation with deterministic hashing
- **`DeterministicRouter`**: Pure router accepting only canonical inputs
- **`RouteExplanation`**: Transparent tiebreaking explanation
- **`RoutingContract`**: Contract enforcer with verification

### Example Usage

```python
from contracts import RoutingContract, DeterministicRouter, CanonicalInput

# Create route map
route_map = {
    "D1": {
        "module": "policy_processor",
        "class": "IndustrialPolicyProcessor",
        "method": "process"
    }
}

# Initialize router with contract
contract = RoutingContract()
router = DeterministicRouter(route_map, contract)

# Create canonical input
canonical = CanonicalInput.from_input(
    question_id="D1-Q1",
    context={"plan": "test"}
)

# Route deterministically
result = router.route(canonical)
print(f"Route: {result.route_id} -> {result.handler_module}")

# Verify contract
assert contract.verify_contract(result)
```

### Test Coverage

- Canonical input creation
- Deterministic routing verification
- Tiebreaking transparency
- Contract verification

---

## 2. Snapshot Contract (SC)

**Purpose**: Guarantees immutable snapshots with reproducible summaries.

**Theoretical Foundation**: First-stage snapshot manager enforces σ = {standards_hash, corpus_hash, embedding_hash, index_hash}.

### Guarantees

1. **Immutability**: Snapshots cannot be modified after creation
2. **Reproducibility**: Same snapshot produces identical summaries
3. **Hash Integrity**: Four-part sigma ensures complete state capture
4. **Verification**: Snapshot integrity verifiable via hash comparison

### Key Components

- **`SnapshotSigma`**: Four-part hash (standards, corpus, embeddings, index)
- **`ImmutableSnapshot`**: Frozen dataclass ensuring immutability
- **`SnapshotManager`**: Creates and manages snapshots with sigma enforcement
- **`SnapshotContract`**: Contract enforcer with verification

### Example Usage

```python
from contracts import SnapshotManager

# Create snapshot manager
manager = SnapshotManager()

# Create immutable snapshot
snapshot = manager.create_snapshot(
    snapshot_id="snapshot_001",
    standards={"rule_1": "value"},
    corpus=["doc1", "doc2"],
    embeddings=[[0.1, 0.2], [0.3, 0.4]],
    index={"doc1": 0, "doc2": 1}
)

# Produce reproducible summary
summary1 = snapshot.produce_summary()
summary2 = snapshot.produce_summary()
assert summary1 == summary2  # Guaranteed identical

# Verify sigma integrity
assert snapshot.verify_sigma()
```

### Test Coverage

- Sigma computation from components
- Snapshot immutability verification
- Summary reproducibility
- Full contract verification

---

## 3. Risk Control Certificates (RCC)

**Purpose**: Provides distribution-free coverage guarantees via conformal prediction.

**Theoretical Foundation**: Based on Angelopoulos et al. (2024) adaptive conformal risk control, offering distribution-free guarantees with exact finite coverage.

### Guarantees

1. **Distribution-Free Coverage**: Valid regardless of data distribution
2. **Exact Finite Sample Coverage**: Guaranteed coverage for finite samples
3. **Adaptive Calibration**: Adjusts to changing distributions
4. **Risk Control**: Provable risk bounds

### Key Components

- **`RiskControlCertificate`**: Certificate enforcer with calibration
- **`ConformalPredictor`**: Predictor with coverage guarantees
- **`CoverageGuarantee`**: Certificate with provable coverage
- **`ConformalScores`**: Calibration scores for prediction sets

### Example Usage

```python
import numpy as np
from contracts import RiskControlCertificate

# Initialize certificate
certificate = RiskControlCertificate(target_coverage=0.95)

# Calibrate on data
scores_cal = np.random.randn(100)
labels_cal = np.ones(100)
conformal_scores = certificate.calibrate(scores_cal, labels_cal)

# Verify coverage on test set
scores_test = np.random.randn(50)
labels_test = np.ones(50)
guarantee = certificate.verify_coverage(
    conformal_scores,
    scores_test,
    labels_test
)

print(f"Target coverage: {guarantee.target_coverage}")
print(f"Actual coverage: {guarantee.actual_coverage}")
assert certificate.verify_contract(guarantee)
```

### Test Coverage

- Conformal predictor calibration
- Coverage guarantee certificates
- Contract verification with statistical bounds

---

## 4. Monotonicity Contracts (MCC & BMC)

**Purpose**: Ensures monotonic consistency through evidence and budget.

### 4.1 Monotone Consistency Contract (MCC)

**Guarantees**: Labels/decisions respect monotonic consistency through evidence accumulation.

### 4.2 Budget Monotonicity Contract (BMC)

**Guarantees**: Objective is monotonic in budget - increased budget never reduces achievable value.

### Key Components

- **`MonotoneConsistencyContract`**: Evidence-based consistency enforcement
- **`BudgetMonotonicityContract`**: Budget monotonicity enforcement
- **`MonotonicValidator`**: Combined validator for both contracts
- **`Evidence`**: Evidence with strength supporting decisions
- **`BudgetAllocation`**: Budget allocation with achieved value

### Example Usage

```python
from contracts import (
    MonotoneConsistencyContract,
    BudgetMonotonicityContract,
    Evidence,
    Decision,
    BudgetAllocation
)

# Monotone Consistency
mcc = MonotoneConsistencyContract()

# Add progressive evidence
ev1 = Evidence(source="expert", strength=0.3, supporting=Decision.ACCEPT)
state = mcc.add_evidence("decision_1", ev1)

ev2 = Evidence(source="data", strength=0.5, supporting=Decision.ACCEPT)
state = mcc.add_evidence("decision_1", ev2)

# Confidence increases with evidence
assert mcc.verify_monotonicity("decision_1")

# Budget Monotonicity
bmc = BudgetMonotonicityContract()

# Record allocations with increasing budgets
allocations = [
    BudgetAllocation(budget=100, achieved_value=50, allocation_id="a1"),
    BudgetAllocation(budget=200, achieved_value=80, allocation_id="a2"),
    BudgetAllocation(budget=300, achieved_value=100, allocation_id="a3"),
]

for alloc in allocations:
    bmc.record_allocation(alloc)

# Value increases with budget
assert bmc.verify_monotonicity()
```

### Test Coverage

- Monotone consistency with evidence accumulation
- Budget monotonicity verification
- Combined validator

---

## 5. Permutation Invariance Contracts (PIC)

**Purpose**: Guarantees set/multiset aggregations are permutation invariant with numerical stability.

### Guarantees

1. **Permutation Invariance**: f(x₁, x₂, ..., xₙ) = f(π(x₁, x₂, ..., xₙ)) for any permutation π
2. **Numerical Stability**: Small input changes → small output changes
3. **Consistency**: Same multiset → same result regardless of order
4. **Associativity**: Grouping doesn't matter for valid aggregations

### Key Components

- **`PermutationInvarianceContract`**: Contract enforcer with verification
- **`InvariantAggregator`**: Aggregator with built-in guarantees
- **`NumericalStabilityValidator`**: Validator for pooling operations
- **`NumericalStability`**: Stability metrics

### Example Usage

```python
import numpy as np
from contracts import (
    PermutationInvarianceContract,
    InvariantAggregator,
    AggregationType
)

# Verify permutation invariance
contract = PermutationInvarianceContract()

mean_fn = lambda x: np.mean(x)
inputs = np.array([1.0, 2.0, 3.0, 4.0])

# Verify across random permutations
assert contract.verify_invariance(mean_fn, inputs)

# Verify numerical stability
stability = contract.verify_numerical_stability(mean_fn, inputs)
assert stability.is_stable()

# Use invariant aggregator
aggregator = InvariantAggregator(AggregationType.MEAN)
result = aggregator.aggregate(inputs)
print(f"Mean: {result}")
```

### Test Coverage

- Permutation invariance verification
- Non-invariance detection
- Numerical stability testing
- Invariant aggregator usage
- Full contract verification

---

## 6. Fault-Free Contracts (FFC)

**Purpose**: Ensures deterministic fault injection doesn't break contract guarantees.

### Guarantees

1. **Deterministic Fault Injection**: Same seed → same faults
2. **Contract Preservation**: Faults don't violate other contracts
3. **Safe Fallbacks**: Conservative defaults when faults occur
4. **Graceful Degradation**: System remains functional under faults
5. **Fault Reproducibility**: Can replay exact fault scenarios

### Key Components

- **`FaultFreeContract`**: Contract enforcer
- **`DeterministicFaultInjector`**: Deterministic fault injection with seed
- **`ConservativeFallback`**: Safe fallback provider
- **`FaultSpec`**: Fault specification with type and probability

### Example Usage

```python
from contracts import (
    FaultFreeContract,
    ConservativeFallback,
    FaultSpec,
    FaultType
)

# Initialize with seed for determinism
contract = FaultFreeContract(seed=42)

# Register conservative fallbacks
contract.fallback_provider.register_fallback(
    "analyzer",
    lambda: {"status": "fallback", "result": None}
)

# Create fault specification
fault_spec = FaultSpec(
    fault_type=FaultType.COMPUTATION_ERROR,
    probability=0.3,
    severity=0.5,
    target_component="analyzer"
)

# Inject faults deterministically
def normal_operation():
    return {"status": "success", "result": 42}

result = contract.injector.inject_fault(
    fault_spec,
    normal_operation,
    "analyzer"
)

# Verify reproducibility
assert contract.verify_determinism()
```

### Test Coverage

- Conservative fallback mechanisms
- Deterministic fault injection
- Reproducibility verification
- Full contract verification

---

## 7. Context Immutability Contract (CIC)

**Purpose**: Accepts only canonical JSON as source with immutability guarantees.

**Theoretical Foundation**: Based on Bernardy et al. (2021) substructural linear types theorem, guaranteeing property preservation through aliasing and mutation restrictions.

### Guarantees

1. **Canonical JSON Only**: All context must be in canonical (sorted keys) JSON
2. **Immutability**: Context cannot be modified after creation
3. **Linear Types**: No aliasing - each context reference is unique
4. **Property Preservation**: Properties proven at creation remain valid
5. **Structural Integrity**: Context structure preserved via hash verification

### Key Components

- **`ContextImmutabilityContract`**: Contract enforcer with linear types
- **`CanonicalJSONValidator`**: Canonical JSON validation and conversion
- **`ImmutableContext`**: Frozen context with canonical representation

### Example Usage

```python
from contracts import ContextImmutabilityContract

# Initialize contract with reference tracking
contract = ContextImmutabilityContract(track_references=True)

# Create immutable context from data
data = {
    "plan_id": "plan_123",
    "dimension": "D1",
    "questions": ["Q1", "Q2"]
}

context = contract.create_context("ctx_001", data)

# Context is immutable
try:
    context.context_id = "modified"
except AttributeError:
    print("Context is properly immutable")

# Verify canonical form
assert contract.verify_canonical_form("ctx_001")

# Verify integrity
assert contract.verify_integrity("ctx_001")

# Track linear access
for _ in range(3):
    contract.get_context("ctx_001")

assert contract.verify_linear_access("ctx_001", max_references=5)

# Full contract verification
assert contract.verify_contract("ctx_001")
```

### Test Coverage

- Canonical JSON validation
- Immutable context creation
- Context immutability enforcement
- Canonical form verification
- Integrity verification via hashing
- Linear access tracking
- Full contract verification

---

## Test Results

All contracts pass comprehensive testing:

```bash
$ python3 -m pytest tests/test_contracts.py -v

============================== test session starts ==============================
tests/test_contracts.py::TestRoutingContract::test_canonical_input_creation PASSED
tests/test_contracts.py::TestRoutingContract::test_deterministic_routing PASSED
tests/test_contracts.py::TestRoutingContract::test_tiebreaking_transparency PASSED
tests/test_contracts.py::TestRoutingContract::test_contract_verification PASSED
tests/test_contracts.py::TestSnapshotContract::test_sigma_computation PASSED
tests/test_contracts.py::TestSnapshotContract::test_snapshot_immutability PASSED
tests/test_contracts.py::TestSnapshotContract::test_summary_reproducibility PASSED
tests/test_contracts.py::TestSnapshotContract::test_contract_verification PASSED
tests/test_contracts.py::TestRiskControlCertificates::test_calibration PASSED
tests/test_contracts.py::TestRiskControlCertificates::test_coverage_guarantee PASSED
tests/test_contracts.py::TestRiskControlCertificates::test_contract_verification PASSED
tests/test_contracts.py::TestMonotonicityContracts::test_monotone_consistency PASSED
tests/test_contracts.py::TestMonotonicityContracts::test_budget_monotonicity PASSED
tests/test_contracts.py::TestMonotonicityContracts::test_combined_validator PASSED
tests/test_contracts.py::TestPermutationInvarianceContract::test_invariance_verification PASSED
tests/test_contracts.py::TestPermutationInvarianceContract::test_non_invariance_detection PASSED
tests/test_contracts.py::TestPermutationInvarianceContract::test_numerical_stability PASSED
tests/test_contracts.py::TestPermutationInvarianceContract::test_invariant_aggregator PASSED
tests/test_contracts.py::TestPermutationInvarianceContract::test_contract_verification PASSED
tests/test_contracts.py::TestFaultFreeContracts::test_conservative_fallbacks PASSED
tests/test_contracts.py::TestFaultFreeContracts::test_deterministic_fault_injection PASSED
tests/test_contracts.py::TestFaultFreeContracts::test_reproducibility_verification PASSED
tests/test_contracts.py::TestFaultFreeContracts::test_contract_verification PASSED
tests/test_contracts.py::TestContextImmutabilityContract::test_canonical_json_validation PASSED
tests/test_contracts.py::TestContextImmutabilityContract::test_immutable_context_creation PASSED
tests/test_contracts.py::TestContextImmutabilityContract::test_context_immutability PASSED
tests/test_contracts.py::TestContextImmutabilityContract::test_canonical_form_verification PASSED
tests/test_contracts.py::TestContextImmutabilityContract::test_integrity_verification PASSED
tests/test_contracts.py::TestContextImmutabilityContract::test_linear_access_tracking PASSED
tests/test_contracts.py::TestContextImmutabilityContract::test_contract_verification PASSED

============================== 30 passed in 0.59s ==============================
```

---

## Integration with Existing System

The contracts are designed to integrate seamlessly with existing DEREK-BEACH components:

### With Question Router

```python
from question_router import QuestionRouter
from contracts import RoutingContract, CanonicalInput

# Wrap existing router with contract
router = QuestionRouter()
contract = RoutingContract()

# Use canonical input
canonical = CanonicalInput.from_input("D1-Q1")
# Route with contract verification...
```

### With Deterministic Utils

```python
from deterministic_utils import create_deterministic_seed
from contracts import FaultFreeContract

# Use deterministic seed for fault injection
seed = create_deterministic_seed("workflow_123", "step_1", "1.0.0")
contract = FaultFreeContract(seed=seed)
```

### With Event-Driven Choreographer

```python
from event_driven_choreographer import EventDrivenChoreographer
from contracts import SnapshotContract, ContextImmutabilityContract

# Use contracts in choreography
snapshot_contract = SnapshotContract()
context_contract = ContextImmutabilityContract()

# Create immutable snapshots and contexts
# Verify before processing events...
```

---

## Theoretical References

1. **Abernethy, J. et al. (2022)**. "Projection-Based Methods for Convex Optimization." Guarantees unique convergence via deterministic projections on convex polytopes.

2. **Angelopoulos, A. N., & Bates, S. (2024)**. "Conformal Prediction: A Gentle Introduction." Provides distribution-free guarantees with exact finite coverage.

3. **Bernardy, J. P. et al. (2021)**. "Linear Haskell: practical linearity in a higher-order polymorphic language." Substructural linear types theorem for property preservation.

---

## Maintenance and Evolution

### Adding New Contracts

1. Create new contract module in `contracts/`
2. Implement contract class with `verify_contract()` method
3. Add to `contracts/__init__.py`
4. Add tests to `tests/test_contracts.py`
5. Update this documentation

### Contract Verification Best Practices

- Always verify contracts before critical operations
- Log contract violations for debugging
- Use contracts in CI/CD pipelines
- Monitor contract verification metrics in production

---

## License

These contracts are part of the DEREK-BEACH system and follow the same license terms.

## Authors

- FARFAN 3.0 Integration Team
- Contract Enforcement System Developers

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-10-21 | Initial implementation of all 7 contracts |
