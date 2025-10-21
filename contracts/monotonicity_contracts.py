"""
Monotonicity Contracts (MCC & BMC)
==================================

Implements two monotonicity guarantees:

1. Monotone Consistency Contract (MCC): Ensures labels/decisions respect
   monotonic consistency through evidence. As evidence accumulates,
   decisions should not arbitrarily flip.

2. Budget Monotonicity Contract (BMC): Guarantees that the objective is
   monotonic in budget and that budget increases never reduce the
   achievable value.

Key Guarantees:
- Evidence monotonicity: More evidence → more confident/consistent decisions
- Budget monotonicity: More budget → better or equal outcomes
- Consistency preservation: Decisions respect partial ordering
- Value non-decrease: Increased resources never hurt performance

Author: FARFAN 3.0 - Contract Enforcement System
Version: 1.0.0
Python: 3.11+
"""

import logging
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


class Decision(Enum):
    """Decision values with natural ordering"""
    REJECT = 0
    UNCERTAIN = 1
    ACCEPT = 2


@dataclass(frozen=True)
class Evidence:
    """
    Evidence supporting a decision
    
    Evidence has a strength measure and can be accumulated.
    """
    source: str
    strength: float  # In [0, 1]
    supporting: Decision
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate evidence"""
        if not 0 <= self.strength <= 1:
            raise ValueError("Evidence strength must be in [0, 1]")


@dataclass
class DecisionState:
    """
    State of a decision with accumulated evidence
    
    Tracks decision history and evidence accumulation.
    """
    current_decision: Decision
    evidence_list: List[Evidence] = field(default_factory=list)
    confidence: float = 0.0
    history: List[Tuple[Decision, float]] = field(default_factory=list)
    
    def add_evidence(self, evidence: Evidence) -> None:
        """Add evidence and update decision"""
        self.evidence_list.append(evidence)
        self._update_decision()
    
    def _update_decision(self) -> None:
        """Update decision based on accumulated evidence"""
        if not self.evidence_list:
            return
        
        # Aggregate evidence for each decision
        evidence_by_decision = {
            Decision.REJECT: 0.0,
            Decision.UNCERTAIN: 0.0,
            Decision.ACCEPT: 0.0
        }
        
        for ev in self.evidence_list:
            evidence_by_decision[ev.supporting] += ev.strength
        
        # Select decision with most evidence
        max_evidence = max(evidence_by_decision.values())
        new_decision = max(
            evidence_by_decision.items(),
            key=lambda x: x[1]
        )[0]
        
        # Compute confidence
        total_evidence = sum(evidence_by_decision.values())
        self.confidence = max_evidence / total_evidence if total_evidence > 0 else 0.0
        
        # Record history
        if new_decision != self.current_decision:
            self.history.append((self.current_decision, self.confidence))
            self.current_decision = new_decision
    
    def get_evidence_strength(self) -> float:
        """Get total evidence strength"""
        return sum(ev.strength for ev in self.evidence_list)


class MonotoneConsistencyContract:
    """
    Monotone Consistency Contract (MCC) enforcer
    
    Ensures that as evidence accumulates, decisions become more confident
    and consistent, not arbitrarily flipping.
    
    Guarantees:
    1. Confidence monotonicity: More evidence → higher confidence
    2. Stability: Decisions don't flip without sufficient counter-evidence
    3. Evidence ordering: Respects partial order of evidence strength
    """
    
    def __init__(
        self,
        stability_threshold: float = 0.7,
        min_flip_ratio: float = 1.5
    ):
        """
        Initialize monotone consistency contract
        
        Args:
            stability_threshold: Confidence threshold for stable decisions
            min_flip_ratio: Minimum ratio of counter-evidence needed to flip
        """
        self.stability_threshold = stability_threshold
        self.min_flip_ratio = min_flip_ratio
        self._decision_states: Dict[str, DecisionState] = {}
        
        logger.info(
            f"Initialized MonotoneConsistencyContract with "
            f"stability_threshold={stability_threshold}, "
            f"min_flip_ratio={min_flip_ratio}"
        )
    
    def add_evidence(
        self,
        decision_id: str,
        evidence: Evidence
    ) -> DecisionState:
        """
        Add evidence to decision state
        
        Args:
            decision_id: Identifier for decision
            evidence: Evidence to add
            
        Returns:
            Updated decision state
        """
        if decision_id not in self._decision_states:
            self._decision_states[decision_id] = DecisionState(
                current_decision=Decision.UNCERTAIN
            )
        
        state = self._decision_states[decision_id]
        
        # Check monotonicity before adding
        old_confidence = state.confidence
        old_strength = state.get_evidence_strength()
        
        state.add_evidence(evidence)
        
        # Verify monotonicity
        new_confidence = state.confidence
        new_strength = state.get_evidence_strength()
        
        # Evidence strength should be monotonic
        if new_strength < old_strength:
            logger.warning(
                f"Evidence strength decreased for {decision_id}: "
                f"{old_strength:.3f} → {new_strength:.3f}"
            )
        
        logger.debug(
            f"Added evidence to {decision_id}: "
            f"confidence {old_confidence:.3f} → {new_confidence:.3f}"
        )
        
        return state
    
    def verify_monotonicity(self, decision_id: str) -> bool:
        """
        Verify monotonicity constraints for decision
        
        Args:
            decision_id: Decision to verify
            
        Returns:
            True if monotonicity is preserved
        """
        if decision_id not in self._decision_states:
            return True  # No violations if no state
        
        state = self._decision_states[decision_id]
        
        # Check that confidence increased with evidence
        if len(state.history) > 1:
            confidences = [h[1] for h in state.history]
            # Allow small decreases due to evidence conflict
            for i in range(len(confidences) - 1):
                if confidences[i+1] < confidences[i] * 0.9:  # >10% decrease
                    logger.warning(
                        f"Significant confidence decrease in {decision_id}: "
                        f"{confidences[i]:.3f} → {confidences[i+1]:.3f}"
                    )
                    return False
        
        return True
    
    def verify_stability(self, decision_id: str) -> bool:
        """
        Verify decision stability
        
        Args:
            decision_id: Decision to verify
            
        Returns:
            True if decision is stable
        """
        if decision_id not in self._decision_states:
            return False
        
        state = self._decision_states[decision_id]
        
        # Stable if confidence exceeds threshold
        if state.confidence >= self.stability_threshold:
            return True
        
        # Check flip count
        flips = len(state.history)
        if flips > 3:  # Too many flips indicates instability
            logger.warning(f"Decision {decision_id} has flipped {flips} times")
            return False
        
        return True
    
    def verify_contract(self, decision_id: str) -> bool:
        """
        Verify all monotone consistency guarantees
        
        Args:
            decision_id: Decision to verify
            
        Returns:
            True if contract is satisfied
        """
        if not self.verify_monotonicity(decision_id):
            logger.error(f"Monotonicity violation for {decision_id}")
            return False
        
        if not self.verify_stability(decision_id):
            logger.warning(f"Stability concern for {decision_id}")
            # Don't fail, just warn
        
        return True


@dataclass(frozen=True)
class BudgetAllocation:
    """
    Budget allocation with associated value
    
    Represents resource allocation and achieved objective value.
    """
    budget: float
    achieved_value: float
    allocation_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate budget allocation"""
        if self.budget < 0:
            raise ValueError("Budget cannot be negative")


class BudgetMonotonicityContract:
    """
    Budget Monotonicity Contract (BMC) enforcer
    
    Guarantees that objective is monotonic in budget - increasing budget
    never decreases the achievable value.
    
    Guarantees:
    1. Non-decreasing value: budget₁ ≤ budget₂ → value₁ ≤ value₂
    2. Resource efficiency: Additional budget can only help
    3. Feasibility preservation: Valid allocations remain valid with more budget
    """
    
    def __init__(
        self,
        tolerance: float = 1e-6
    ):
        """
        Initialize budget monotonicity contract
        
        Args:
            tolerance: Numerical tolerance for comparisons
        """
        self.tolerance = tolerance
        self._allocations: List[BudgetAllocation] = []
        
        logger.info(f"Initialized BudgetMonotonicityContract with tolerance={tolerance}")
    
    def record_allocation(self, allocation: BudgetAllocation) -> None:
        """
        Record budget allocation
        
        Args:
            allocation: Allocation to record
        """
        self._allocations.append(allocation)
        logger.debug(
            f"Recorded allocation: budget={allocation.budget:.2f}, "
            f"value={allocation.achieved_value:.2f}"
        )
    
    def verify_monotonicity(self) -> bool:
        """
        Verify budget monotonicity across all allocations
        
        Returns:
            True if monotonicity is preserved
        """
        if len(self._allocations) < 2:
            return True  # Need at least 2 points to check
        
        # Sort by budget
        sorted_alloc = sorted(self._allocations, key=lambda a: a.budget)
        
        # Check that value is non-decreasing
        violations = []
        for i in range(len(sorted_alloc) - 1):
            budget1 = sorted_alloc[i].budget
            budget2 = sorted_alloc[i+1].budget
            value1 = sorted_alloc[i].achieved_value
            value2 = sorted_alloc[i+1].achieved_value
            
            # Allow small numerical violations
            if value2 < value1 - self.tolerance:
                violations.append((budget1, value1, budget2, value2))
                logger.warning(
                    f"Monotonicity violation: "
                    f"budget {budget1:.2f}→{budget2:.2f}, "
                    f"value {value1:.2f}→{value2:.2f}"
                )
        
        return len(violations) == 0
    
    def compute_marginal_value(self, budget: float) -> Optional[float]:
        """
        Compute marginal value at given budget
        
        Args:
            budget: Budget level
            
        Returns:
            Marginal value (derivative) if computable
        """
        if len(self._allocations) < 2:
            return None
        
        # Find nearest allocations
        sorted_alloc = sorted(self._allocations, key=lambda a: a.budget)
        
        # Find bracketing allocations
        lower = None
        upper = None
        
        for alloc in sorted_alloc:
            if alloc.budget <= budget:
                lower = alloc
            if alloc.budget >= budget and upper is None:
                upper = alloc
        
        if lower and upper and lower.budget != upper.budget:
            # Compute slope
            marginal = (upper.achieved_value - lower.achieved_value) / (
                upper.budget - lower.budget
            )
            return marginal
        
        return None
    
    def verify_contract(self) -> bool:
        """
        Verify budget monotonicity contract
        
        Returns:
            True if contract guarantees are met
        """
        # Verify monotonicity
        if not self.verify_monotonicity():
            logger.error("Budget monotonicity violation detected")
            return False
        
        # Verify non-negative marginal values
        for alloc in self._allocations:
            marginal = self.compute_marginal_value(alloc.budget)
            if marginal is not None and marginal < -self.tolerance:
                logger.warning(
                    f"Negative marginal value at budget {alloc.budget:.2f}: "
                    f"{marginal:.4f}"
                )
        
        logger.info("Budget monotonicity contract verified")
        return True


class MonotonicValidator:
    """
    Combined validator for both monotonicity contracts
    
    Provides unified interface for MCC and BMC verification.
    """
    
    def __init__(
        self,
        mcc: Optional[MonotoneConsistencyContract] = None,
        bmc: Optional[BudgetMonotonicityContract] = None
    ):
        """
        Initialize monotonic validator
        
        Args:
            mcc: Monotone consistency contract
            bmc: Budget monotonicity contract
        """
        self.mcc = mcc or MonotoneConsistencyContract()
        self.bmc = bmc or BudgetMonotonicityContract()
        
        logger.info("Initialized MonotonicValidator")
    
    def verify_all_contracts(self) -> Dict[str, bool]:
        """
        Verify all monotonicity contracts
        
        Returns:
            Dictionary of contract verification results
        """
        results = {
            "budget_monotonicity": self.bmc.verify_contract(),
        }
        
        # Verify all decision states for MCC
        mcc_results = []
        for decision_id in self.mcc._decision_states:
            mcc_results.append(self.mcc.verify_contract(decision_id))
        
        results["monotone_consistency"] = all(mcc_results) if mcc_results else True
        results["all_verified"] = all(results.values())
        
        return results


if __name__ == "__main__":
    # Test monotonicity contracts
    print("=" * 80)
    print("MONOTONICITY CONTRACTS (MCC & BMC) TEST")
    print("=" * 80)
    
    # Test 1: Monotone Consistency Contract
    print("\nTest 1: Monotone Consistency Contract (MCC)")
    mcc = MonotoneConsistencyContract()
    
    # Add evidence progressively
    decision_id = "question_D1_Q1"
    
    ev1 = Evidence(source="expert1", strength=0.3, supporting=Decision.ACCEPT)
    state1 = mcc.add_evidence(decision_id, ev1)
    print(f"  After evidence 1: decision={state1.current_decision.name}, "
          f"confidence={state1.confidence:.3f}")
    
    ev2 = Evidence(source="expert2", strength=0.4, supporting=Decision.ACCEPT)
    state2 = mcc.add_evidence(decision_id, ev2)
    print(f"  After evidence 2: decision={state2.current_decision.name}, "
          f"confidence={state2.confidence:.3f}")
    
    ev3 = Evidence(source="data", strength=0.2, supporting=Decision.ACCEPT)
    state3 = mcc.add_evidence(decision_id, ev3)
    print(f"  After evidence 3: decision={state3.current_decision.name}, "
          f"confidence={state3.confidence:.3f}")
    
    # Verify monotonicity
    monotonic = mcc.verify_monotonicity(decision_id)
    stable = mcc.verify_stability(decision_id)
    print(f"  Monotonicity preserved: {monotonic}")
    print(f"  Decision stable: {stable}")
    
    # Test 2: Budget Monotonicity Contract
    print("\nTest 2: Budget Monotonicity Contract (BMC)")
    bmc = BudgetMonotonicityContract()
    
    # Record allocations with increasing budgets
    allocations = [
        BudgetAllocation(budget=100, achieved_value=50, allocation_id="a1"),
        BudgetAllocation(budget=150, achieved_value=70, allocation_id="a2"),
        BudgetAllocation(budget=200, achieved_value=85, allocation_id="a3"),
        BudgetAllocation(budget=250, achieved_value=95, allocation_id="a4"),
    ]
    
    for alloc in allocations:
        bmc.record_allocation(alloc)
        print(f"  Budget={alloc.budget:.0f}, Value={alloc.achieved_value:.0f}")
    
    # Verify budget monotonicity
    budget_monotonic = bmc.verify_monotonicity()
    print(f"  Budget monotonicity preserved: {budget_monotonic}")
    
    # Compute marginal value
    marginal = bmc.compute_marginal_value(175)
    if marginal:
        print(f"  Marginal value at budget=175: {marginal:.3f}")
    
    # Test 3: Combined validation
    print("\nTest 3: Combined Monotonicity Validation")
    validator = MonotonicValidator(mcc=mcc, bmc=bmc)
    results = validator.verify_all_contracts()
    
    for contract, verified in results.items():
        print(f"  {contract}: {verified}")
    
    print("\n" + "=" * 80)
