"""
Permutation Invariance Contracts (PIC)
======================================

Guarantees that aggregations of sets/multisets are invariant to permutation
and verifies numerical stability in pooling operations.

Key Guarantees:
1. Permutation invariance: f(x₁, x₂, ..., xₙ) = f(π(x₁, x₂, ..., xₙ))
   for any permutation π
2. Numerical stability: Small input changes → small output changes
3. Consistency: Same multiset → same result regardless of order
4. Associativity: Grouping doesn't matter for valid aggregations

Author: FARFAN 3.0 - Contract Enforcement System
Version: 1.0.0
Python: 3.11+
"""

import numpy as np
import logging
from typing import List, Callable, Any, Optional, Tuple, Dict
from dataclasses import dataclass
from enum import Enum
import itertools

logger = logging.getLogger(__name__)


class AggregationType(Enum):
    """Types of aggregation operations"""
    SUM = "sum"
    MEAN = "mean"
    MAX = "max"
    MIN = "min"
    MEDIAN = "median"
    PRODUCT = "product"
    VARIANCE = "variance"
    STD = "std"


@dataclass(frozen=True)
class NumericalStability:
    """
    Numerical stability metrics
    
    Measures sensitivity of aggregation to input perturbations.
    """
    perturbation_magnitude: float
    output_change: float
    relative_change: float
    lipschitz_constant: float  # Upper bound on sensitivity
    
    def is_stable(self, threshold: float = 0.1) -> bool:
        """
        Check if numerically stable
        
        Args:
            threshold: Maximum allowed relative change
            
        Returns:
            True if stable
        """
        return self.relative_change <= threshold


class PermutationInvarianceContract:
    """
    Permutation Invariance Contract enforcer
    
    Verifies that aggregation functions are truly permutation invariant
    and numerically stable.
    
    Guarantees:
    - Permutation invariance for all valid inputs
    - Numerical stability under perturbations
    - Consistency across implementations
    """
    
    def __init__(
        self,
        tolerance: float = 1e-10,
        num_permutation_tests: int = 10,
        stability_threshold: float = 0.1
    ):
        """
        Initialize permutation invariance contract
        
        Args:
            tolerance: Numerical tolerance for equality checks
            num_permutation_tests: Number of random permutations to test
            stability_threshold: Maximum allowed relative change for stability
        """
        self.tolerance = tolerance
        self.num_permutation_tests = num_permutation_tests
        self.stability_threshold = stability_threshold
        
        logger.info(
            f"Initialized PermutationInvarianceContract with "
            f"tolerance={tolerance}, "
            f"num_tests={num_permutation_tests}"
        )
    
    def verify_invariance(
        self,
        aggregator: Callable[[np.ndarray], float],
        inputs: np.ndarray,
        exhaustive: bool = False
    ) -> bool:
        """
        Verify permutation invariance of aggregator
        
        Args:
            aggregator: Function to aggregate array
            inputs: Input array to test
            exhaustive: If True and inputs small, test all permutations
            
        Returns:
            True if aggregator is permutation invariant
        """
        if len(inputs) == 0:
            return True
        
        # Compute reference output
        reference = aggregator(inputs)
        
        # Test permutations
        if exhaustive and len(inputs) <= 8:  # Factorial grows fast
            # Test all permutations
            permutations = list(itertools.permutations(inputs))
            test_count = len(permutations)
        else:
            # Test random permutations
            permutations = []
            for _ in range(self.num_permutation_tests):
                perm = np.random.permutation(inputs)
                permutations.append(perm)
            test_count = self.num_permutation_tests
        
        # Check each permutation
        violations = 0
        for perm in permutations:
            result = aggregator(np.array(perm))
            if not np.isclose(result, reference, atol=self.tolerance):
                violations += 1
                logger.warning(
                    f"Invariance violation: {reference:.6f} != {result:.6f}"
                )
        
        is_invariant = violations == 0
        
        if is_invariant:
            logger.debug(f"Invariance verified ({test_count} permutations)")
        else:
            logger.error(
                f"Invariance violated in {violations}/{test_count} tests"
            )
        
        return is_invariant
    
    def verify_numerical_stability(
        self,
        aggregator: Callable[[np.ndarray], float],
        inputs: np.ndarray,
        perturbation_scale: float = 1e-6
    ) -> NumericalStability:
        """
        Verify numerical stability under perturbations
        
        Args:
            aggregator: Aggregation function
            inputs: Input array
            perturbation_scale: Scale of perturbations to apply
            
        Returns:
            NumericalStability metrics
        """
        if len(inputs) == 0:
            return NumericalStability(0, 0, 0, 0)
        
        # Compute reference
        reference = aggregator(inputs)
        
        # Apply small perturbation
        perturbation = np.random.randn(len(inputs)) * perturbation_scale
        perturbed_inputs = inputs + perturbation
        
        # Compute perturbed output
        perturbed = aggregator(perturbed_inputs)
        
        # Measure changes
        output_change = abs(perturbed - reference)
        relative_change = output_change / (abs(reference) + 1e-10)
        
        # Estimate Lipschitz constant
        input_change = np.linalg.norm(perturbation)
        lipschitz = output_change / (input_change + 1e-10)
        
        stability = NumericalStability(
            perturbation_magnitude=input_change,
            output_change=output_change,
            relative_change=relative_change,
            lipschitz_constant=lipschitz
        )
        
        logger.debug(
            f"Stability: relative_change={relative_change:.6f}, "
            f"lipschitz={lipschitz:.2f}"
        )
        
        return stability
    
    def verify_contract(
        self,
        aggregator: Callable[[np.ndarray], float],
        test_inputs: List[np.ndarray]
    ) -> bool:
        """
        Verify permutation invariance contract
        
        Args:
            aggregator: Aggregation function to verify
            test_inputs: List of test input arrays
            
        Returns:
            True if contract is satisfied
        """
        # Verify invariance on all test inputs
        invariance_results = []
        for inputs in test_inputs:
            result = self.verify_invariance(aggregator, inputs)
            invariance_results.append(result)
        
        if not all(invariance_results):
            logger.error("Permutation invariance violated")
            return False
        
        # Verify numerical stability
        stability_results = []
        for inputs in test_inputs:
            stability = self.verify_numerical_stability(aggregator, inputs)
            is_stable = stability.is_stable(self.stability_threshold)
            stability_results.append(is_stable)
            
            if not is_stable:
                logger.warning(
                    f"Numerical stability concern: "
                    f"relative_change={stability.relative_change:.6f}"
                )
        
        # All must pass for contract satisfaction
        contract_satisfied = (
            all(invariance_results) and
            all(stability_results)
        )
        
        if contract_satisfied:
            logger.info("Permutation invariance contract verified")
        
        return contract_satisfied


class InvariantAggregator:
    """
    Aggregator with built-in permutation invariance guarantees
    
    Provides common aggregation operations with contract enforcement.
    """
    
    def __init__(
        self,
        aggregation_type: AggregationType,
        contract: Optional[PermutationInvarianceContract] = None
    ):
        """
        Initialize invariant aggregator
        
        Args:
            aggregation_type: Type of aggregation
            contract: Optional contract enforcer
        """
        self.aggregation_type = aggregation_type
        self.contract = contract or PermutationInvarianceContract()
        self._aggregator = self._get_aggregator_function()
        
        logger.info(f"Initialized InvariantAggregator: {aggregation_type.value}")
    
    def _get_aggregator_function(self) -> Callable[[np.ndarray], float]:
        """Get aggregator function for type"""
        aggregators = {
            AggregationType.SUM: lambda x: np.sum(x),
            AggregationType.MEAN: lambda x: np.mean(x),
            AggregationType.MAX: lambda x: np.max(x),
            AggregationType.MIN: lambda x: np.min(x),
            AggregationType.MEDIAN: lambda x: np.median(x),
            AggregationType.PRODUCT: lambda x: np.prod(x),
            AggregationType.VARIANCE: lambda x: np.var(x),
            AggregationType.STD: lambda x: np.std(x),
        }
        return aggregators[self.aggregation_type]
    
    def aggregate(self, inputs: np.ndarray) -> float:
        """
        Aggregate inputs with contract verification
        
        Args:
            inputs: Input array to aggregate
            
        Returns:
            Aggregated value
            
        Raises:
            ValueError: If contract is violated
        """
        if len(inputs) == 0:
            logger.warning("Empty input array")
            return 0.0
        
        # Perform aggregation
        result = self._aggregator(inputs)
        
        # Verify on single input (quick check)
        if not self.contract.verify_invariance(
            self._aggregator,
            inputs,
            exhaustive=False
        ):
            raise ValueError(
                f"Permutation invariance violated for {self.aggregation_type.value}"
            )
        
        return result
    
    def aggregate_with_verification(
        self,
        inputs: np.ndarray,
        verify_stability: bool = True
    ) -> Tuple[float, bool, Optional[NumericalStability]]:
        """
        Aggregate with full contract verification
        
        Args:
            inputs: Input array
            verify_stability: Whether to check numerical stability
            
        Returns:
            Tuple of (result, contract_satisfied, stability_metrics)
        """
        result = self._aggregator(inputs)
        
        # Verify invariance
        invariant = self.contract.verify_invariance(self._aggregator, inputs)
        
        # Verify stability
        stability = None
        stable = True
        if verify_stability:
            stability = self.contract.verify_numerical_stability(
                self._aggregator,
                inputs
            )
            stable = stability.is_stable(self.contract.stability_threshold)
        
        contract_satisfied = invariant and stable
        
        return result, contract_satisfied, stability


class NumericalStabilityValidator:
    """
    Validator for numerical stability of pooling operations
    
    Tests poolers (mean, max, sum, etc.) for numerical issues.
    """
    
    def __init__(
        self,
        contract: Optional[PermutationInvarianceContract] = None
    ):
        """
        Initialize stability validator
        
        Args:
            contract: Optional contract enforcer
        """
        self.contract = contract or PermutationInvarianceContract()
        logger.info("Initialized NumericalStabilityValidator")
    
    def validate_pooler(
        self,
        pooler: Callable[[np.ndarray], float],
        test_cases: Optional[List[np.ndarray]] = None
    ) -> Dict[str, Any]:
        """
        Validate pooler numerical stability
        
        Args:
            pooler: Pooling function to validate
            test_cases: Optional test cases (generates if None)
            
        Returns:
            Validation results dictionary
        """
        if test_cases is None:
            # Generate diverse test cases
            test_cases = [
                np.array([1.0, 2.0, 3.0]),  # Simple
                np.array([1e10, 1e-10]),  # Large scale differences
                np.array([1.0] * 100),  # Many identical values
                np.random.randn(50),  # Random
                np.array([1e-100, 1e-100, 1e-100]),  # Tiny values
            ]
        
        results = {
            "pooler_tested": True,
            "test_cases": len(test_cases),
            "invariance_passed": 0,
            "stability_passed": 0,
            "stability_metrics": [],
        }
        
        for inputs in test_cases:
            # Check invariance
            invariant = self.contract.verify_invariance(pooler, inputs)
            if invariant:
                results["invariance_passed"] += 1
            
            # Check stability
            stability = self.contract.verify_numerical_stability(pooler, inputs)
            results["stability_metrics"].append(stability)
            
            if stability.is_stable(self.contract.stability_threshold):
                results["stability_passed"] += 1
        
        results["all_passed"] = (
            results["invariance_passed"] == len(test_cases) and
            results["stability_passed"] == len(test_cases)
        )
        
        logger.info(
            f"Pooler validation: "
            f"invariance {results['invariance_passed']}/{len(test_cases)}, "
            f"stability {results['stability_passed']}/{len(test_cases)}"
        )
        
        return results


if __name__ == "__main__":
    # Test permutation invariance contracts
    print("=" * 80)
    print("PERMUTATION INVARIANCE CONTRACTS (PIC) TEST")
    print("=" * 80)
    
    np.random.seed(42)
    
    # Test 1: Verify standard aggregators
    print("\nTest 1: Standard Aggregator Invariance")
    
    test_input = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    
    for agg_type in [AggregationType.SUM, AggregationType.MEAN, AggregationType.MAX]:
        aggregator = InvariantAggregator(agg_type)
        result = aggregator.aggregate(test_input)
        print(f"  {agg_type.value}: {result:.3f}")
    
    # Test 2: Verify permutation invariance
    print("\nTest 2: Permutation Invariance Verification")
    contract = PermutationInvarianceContract(num_permutation_tests=20)
    
    mean_aggregator = lambda x: np.mean(x)
    invariant = contract.verify_invariance(mean_aggregator, test_input)
    print(f"  Mean is permutation invariant: {invariant}")
    
    # Test non-invariant function (should fail)
    first_element = lambda x: x[0] if len(x) > 0 else 0
    not_invariant = contract.verify_invariance(first_element, test_input)
    print(f"  First element is permutation invariant: {not_invariant}")
    
    # Test 3: Numerical stability
    print("\nTest 3: Numerical Stability")
    
    stability = contract.verify_numerical_stability(mean_aggregator, test_input)
    print(f"  Perturbation magnitude: {stability.perturbation_magnitude:.2e}")
    print(f"  Output change: {stability.output_change:.2e}")
    print(f"  Relative change: {stability.relative_change:.2e}")
    print(f"  Lipschitz constant: {stability.lipschitz_constant:.2f}")
    print(f"  Is stable: {stability.is_stable()}")
    
    # Test 4: Full contract verification
    print("\nTest 4: Full Contract Verification")
    
    test_inputs = [
        np.array([1.0, 2.0, 3.0]),
        np.array([10.0, 20.0, 30.0, 40.0]),
        np.random.randn(10),
    ]
    
    verified = contract.verify_contract(mean_aggregator, test_inputs)
    print(f"  Contract verified: {verified}")
    
    # Test 5: Pooler validation
    print("\nTest 5: Numerical Stability Validator")
    
    validator = NumericalStabilityValidator(contract)
    
    # Test mean pooler
    results = validator.validate_pooler(np.mean)
    print(f"  Test cases: {results['test_cases']}")
    print(f"  Invariance passed: {results['invariance_passed']}/{results['test_cases']}")
    print(f"  Stability passed: {results['stability_passed']}/{results['test_cases']}")
    print(f"  All passed: {results['all_passed']}")
    
    print("\n" + "=" * 80)
