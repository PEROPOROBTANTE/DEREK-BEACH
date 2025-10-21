# Software Contracts Module

This module implements 7 explicit software contracts that guarantee determinism, auditability, security, and statistical validity for the DEREK-BEACH system.

## Quick Start

```python
from contracts import (
    RoutingContract,
    SnapshotContract,
    RiskControlCertificate,
    MonotoneConsistencyContract,
    BudgetMonotonicityContract,
    PermutationInvarianceContract,
    FaultFreeContract,
    ContextImmutabilityContract
)
```

## Contract Overview

| Contract | Purpose | Based On |
|----------|---------|----------|
| **RC** - Routing Contract | Deterministic routing with canonical inputs | Abernethy et al. (2022) |
| **SC** - Snapshot Contract | Immutable snapshots with σ hash | Snapshot theory |
| **RCC** - Risk Control Certificates | Distribution-free coverage guarantees | Angelopoulos et al. (2024) |
| **MCC/BMC** - Monotonicity Contracts | Consistency & budget monotonicity | Monotonicity theory |
| **PIC** - Permutation Invariance | Set/multiset aggregation invariance | Invariance theory |
| **FFC** - Fault-Free Contracts | Deterministic fault injection | Fault tolerance |
| **CIC** - Context Immutability | Canonical JSON with immutability | Bernardy et al. (2021) |

## Verification

### Run Unit Tests
```bash
cd /home/runner/work/DEREK-BEACH/DEREK-BEACH
python3 -m pytest tests/test_contracts.py -v
```

**Expected Output:**
```
============================== 30 passed in 0.59s ==============================
```

### Run Integration Verification
```bash
python3 verify_contracts.py
```

**Expected Output:**
```
✓ PASS   Routing Contract (RC)
✓ PASS   Snapshot Contract (SC)
✓ PASS   Risk Control Certificates (RCC)
✓ PASS   Monotonicity Contracts (MCC & BMC)
✓ PASS   Permutation Invariance (PIC)
✓ PASS   Fault-Free Contracts (FFC)
✓ PASS   Context Immutability (CIC)

Total: 7/7 contracts verified (100%)
🎉 ALL CONTRACTS VERIFIED SUCCESSFULLY! 🎉
```

## Example Usage

### 1. Routing Contract
```python
from contracts import RoutingContract, DeterministicRouter, CanonicalInput

route_map = {
    "D1": {"module": "processor", "class": "Processor", "method": "process"}
}

contract = RoutingContract()
router = DeterministicRouter(route_map, contract)

canonical = CanonicalInput.from_input("D1-Q1")
result = router.route(canonical)

assert contract.verify_contract(result)
```

### 2. Snapshot Contract
```python
from contracts import SnapshotManager

manager = SnapshotManager()
snapshot = manager.create_snapshot(
    snapshot_id="snap_001",
    standards={}, corpus=[], embeddings=[], index={}
)

assert snapshot.verify_sigma()
```

### 3. Risk Control Certificates
```python
import numpy as np
from contracts import RiskControlCertificate

certificate = RiskControlCertificate(target_coverage=0.95)
scores = np.random.randn(100)
labels = np.ones(100)

conformal_scores = certificate.calibrate(scores, labels)
```

### 4. Monotonicity Contracts
```python
from contracts import (
    MonotoneConsistencyContract,
    BudgetMonotonicityContract,
    Evidence, Decision, BudgetAllocation
)

# Monotone Consistency
mcc = MonotoneConsistencyContract()
ev = Evidence(source="expert", strength=0.5, supporting=Decision.ACCEPT)
state = mcc.add_evidence("decision_1", ev)

# Budget Monotonicity
bmc = BudgetMonotonicityContract()
alloc = BudgetAllocation(budget=100, achieved_value=50, allocation_id="a1")
bmc.record_allocation(alloc)
```

### 5. Permutation Invariance
```python
import numpy as np
from contracts import PermutationInvarianceContract, InvariantAggregator, AggregationType

contract = PermutationInvarianceContract()
inputs = np.array([1.0, 2.0, 3.0])

# Verify invariance
mean_fn = lambda x: np.mean(x)
assert contract.verify_invariance(mean_fn, inputs)

# Use invariant aggregator
aggregator = InvariantAggregator(AggregationType.MEAN)
result = aggregator.aggregate(inputs)
```

### 6. Fault-Free Contracts
```python
from contracts import FaultFreeContract, FaultSpec, FaultType

contract = FaultFreeContract(seed=42)
contract.fallback_provider.register_fallback(
    "component",
    lambda: {"status": "fallback"}
)

fault_spec = FaultSpec(
    fault_type=FaultType.COMPUTATION_ERROR,
    probability=0.3,
    severity=0.5,
    target_component="component"
)

result = contract.injector.inject_fault(
    fault_spec,
    lambda: {"status": "success"},
    "component"
)
```

### 7. Context Immutability
```python
from contracts import ContextImmutabilityContract

contract = ContextImmutabilityContract()
data = {"plan": "test", "dimension": "D1"}
context = contract.create_context("ctx_001", data)

assert contract.verify_contract("ctx_001")
```

## Module Structure

```
contracts/
├── __init__.py                          # Module exports
├── routing_contract.py                  # RC implementation
├── snapshot_contract.py                 # SC implementation
├── risk_control_contract.py             # RCC implementation
├── monotonicity_contracts.py            # MCC/BMC implementation
├── permutation_invariance_contract.py   # PIC implementation
├── fault_free_contract.py               # FFC implementation
├── context_immutability_contract.py     # CIC implementation
└── README.md                            # This file
```

## Dependencies

- Python 3.11+
- numpy (for RCC and PIC)
- scipy (optional, for RCC coverage bounds)
- pytest (for testing)

## Documentation

For complete documentation, see:
- [`../CONTRACTS.md`](../CONTRACTS.md) - Detailed contract documentation
- [`../tests/test_contracts.py`](../tests/test_contracts.py) - Test examples
- [`../verify_contracts.py`](../verify_contracts.py) - Integration verification

## Testing

All contracts include:
- Unit tests (30 tests total)
- Integration tests (verify_contracts.py)
- Example code in each module's `__main__` block

Run individual contract tests:
```bash
python3 contracts/routing_contract.py
python3 contracts/snapshot_contract.py
python3 contracts/risk_control_contract.py
# ... etc
```

## Contract Guarantees

Each contract provides explicit guarantees:

1. **RC**: Same canonical input → same route (deterministic)
2. **SC**: Same snapshot → same summary (reproducible)
3. **RCC**: Coverage ≥ target with high probability (statistical)
4. **MCC**: More evidence → monotonic confidence (consistency)
5. **BMC**: More budget → non-decreasing value (monotonicity)
6. **PIC**: f(x) = f(π(x)) for any permutation π (invariance)
7. **FFC**: Same seed → same faults (deterministic)
8. **CIC**: Frozen context → no modifications (immutability)

## Integration

Contracts integrate with existing DEREK-BEACH components:

- `question_router.py` → Use `RoutingContract`
- `deterministic_utils.py` → Use `FaultFreeContract` with deterministic seeds
- `event_driven_choreographer.py` → Use `SnapshotContract` and `ContextImmutabilityContract`
- Analysis modules → Use `RiskControlCertificate` and `MonotonicityContracts`

## Version

- **Version**: 1.0.0
- **Date**: 2025-10-21
- **Status**: Production Ready

## Authors

- FARFAN 3.0 Integration Team
- Contract Enforcement System Developers

## License

Same as DEREK-BEACH system
