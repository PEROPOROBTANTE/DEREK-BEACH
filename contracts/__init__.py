"""
Software Contracts for DEREK-BEACH System
=========================================

This module implements explicit software contracts that guarantee:
- Determinism
- Auditability  
- Security
- Statistical validity

Contracts:
1. Routing Contract (RC) - Deterministic routing with canonical inputs
2. Snapshot Contract (SC) - Immutable snapshots with reproducible summaries
3. Risk Control Certificates (RCC) - Conformal prediction guarantees
4. Monotone Consistency (MCC) & Budget Monotonicity (BMC) - Consistency guarantees
5. Permutation Invariance (PIC) - Set/multiset aggregation invariance
6. Fault-Free Contracts (FFC) - Deterministic fault injection
7. Context Immutability (CIC) - Canonical JSON source acceptance

Based on theoretical foundations from:
- Abernethy et al. (2022) - Deterministic projections on convex polytopes
- Angelopoulos et al. (2024) - Conformal prediction theory
- Bernardy et al. (2021) - Substructural linear types

Author: FARFAN 3.0 - Contract Enforcement System
Version: 1.0.0
Python: 3.11+
"""

from .routing_contract import (
    RoutingContract,
    CanonicalInput,
    DeterministicRouter,
    RouteExplanation,
)
from .snapshot_contract import (
    SnapshotContract,
    ImmutableSnapshot,
    SnapshotManager,
    SnapshotSigma,
)
from .risk_control_contract import (
    RiskControlCertificate,
    ConformalPredictor,
    CoverageGuarantee,
)
from .monotonicity_contracts import (
    MonotoneConsistencyContract,
    BudgetMonotonicityContract,
    MonotonicValidator,
)
from .permutation_invariance_contract import (
    PermutationInvarianceContract,
    InvariantAggregator,
    NumericalStabilityValidator,
)
from .fault_free_contract import (
    FaultFreeContract,
    DeterministicFaultInjector,
    ConservativeFallback,
)
from .context_immutability_contract import (
    ContextImmutabilityContract,
    CanonicalJSONValidator,
    ImmutableContext,
)

__all__ = [
    # Routing Contract (RC)
    "RoutingContract",
    "CanonicalInput",
    "DeterministicRouter",
    "RouteExplanation",
    # Snapshot Contract (SC)
    "SnapshotContract",
    "ImmutableSnapshot",
    "SnapshotManager",
    "SnapshotSigma",
    # Risk Control Certificates (RCC)
    "RiskControlCertificate",
    "ConformalPredictor",
    "CoverageGuarantee",
    # Monotonicity Contracts (MCC/BMC)
    "MonotoneConsistencyContract",
    "BudgetMonotonicityContract",
    "MonotonicValidator",
    # Permutation Invariance (PIC)
    "PermutationInvarianceContract",
    "InvariantAggregator",
    "NumericalStabilityValidator",
    # Fault-Free Contracts (FFC)
    "FaultFreeContract",
    "DeterministicFaultInjector",
    "ConservativeFallback",
    # Context Immutability (CIC)
    "ContextImmutabilityContract",
    "CanonicalJSONValidator",
    "ImmutableContext",
]

__version__ = "1.0.0"
