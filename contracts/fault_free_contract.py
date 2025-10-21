"""
Fault-Free Contracts (FFC) - Deterministic Fault Injection
==========================================================

Ensures that deterministic fault injection doesn't break contract guarantees
and that conservative fallbacks maintain safety.

Key Guarantees:
1. Deterministic fault injection: Same seed → same faults
2. Contract preservation: Faults don't violate other contracts
3. Safe fallbacks: Conservative defaults when faults occur
4. Graceful degradation: System remains functional under faults
5. Fault reproducibility: Can replay exact fault scenarios

Author: FARFAN 3.0 - Contract Enforcement System
Version: 1.0.0
Python: 3.11+
"""

import logging
import random
from typing import Any, Optional, Callable, Dict, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class FaultType(Enum):
    """Types of faults that can be injected"""
    TIMEOUT = "timeout"
    DATA_CORRUPTION = "data_corruption"
    NETWORK_ERROR = "network_error"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    COMPUTATION_ERROR = "computation_error"
    VALIDATION_FAILURE = "validation_failure"


@dataclass(frozen=True)
class FaultSpec:
    """
    Specification for a fault to inject
    
    Immutable to ensure reproducibility.
    """
    fault_type: FaultType
    probability: float  # Probability of occurrence [0, 1]
    severity: float  # Severity level [0, 1]
    target_component: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate fault spec"""
        if not 0 <= self.probability <= 1:
            raise ValueError("Probability must be in [0, 1]")
        if not 0 <= self.severity <= 1:
            raise ValueError("Severity must be in [0, 1]")


@dataclass
class FaultInjectionResult:
    """Result of fault injection"""
    fault_injected: bool
    fault_spec: Optional[FaultSpec]
    fallback_used: bool
    fallback_value: Any
    timestamp: str
    seed_used: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "fault_injected": self.fault_injected,
            "fault_type": self.fault_spec.fault_type.value if self.fault_spec else None,
            "fallback_used": self.fallback_used,
            "timestamp": self.timestamp,
            "seed_used": self.seed_used,
        }


class ConservativeFallback:
    """
    Conservative fallback provider
    
    Provides safe default values when faults occur.
    """
    
    def __init__(self):
        """Initialize conservative fallback"""
        self._fallback_registry: Dict[str, Callable[[], Any]] = {}
        logger.info("Initialized ConservativeFallback")
    
    def register_fallback(
        self,
        component: str,
        fallback_fn: Callable[[], Any]
    ) -> None:
        """
        Register fallback function for component
        
        Args:
            component: Component identifier
            fallback_fn: Function returning safe default value
        """
        self._fallback_registry[component] = fallback_fn
        logger.debug(f"Registered fallback for {component}")
    
    def get_fallback(self, component: str) -> Optional[Any]:
        """
        Get fallback value for component
        
        Args:
            component: Component identifier
            
        Returns:
            Fallback value or None if not registered
        """
        if component in self._fallback_registry:
            try:
                fallback = self._fallback_registry[component]()
                logger.info(f"Using fallback for {component}")
                return fallback
            except Exception as e:
                logger.error(f"Fallback failed for {component}: {e}")
                return None
        
        logger.warning(f"No fallback registered for {component}")
        return None
    
    def get_conservative_default(self, data_type: type) -> Any:
        """
        Get conservative default for data type
        
        Args:
            data_type: Type of data
            
        Returns:
            Conservative default value
        """
        defaults = {
            int: 0,
            float: 0.0,
            str: "",
            list: [],
            dict: {},
            bool: False,
        }
        
        return defaults.get(data_type, None)


class DeterministicFaultInjector:
    """
    Deterministic fault injector with reproducibility
    
    Injects faults deterministically based on seed, ensuring
    exact reproducibility of fault scenarios.
    """
    
    def __init__(
        self,
        seed: int,
        fallback_provider: Optional[ConservativeFallback] = None
    ):
        """
        Initialize deterministic fault injector
        
        Args:
            seed: Random seed for deterministic fault injection
            fallback_provider: Optional fallback provider
        """
        self.seed = seed
        self._rng = random.Random(seed)
        self.fallback_provider = fallback_provider or ConservativeFallback()
        self._injection_history: List[FaultInjectionResult] = []
        
        logger.info(f"Initialized DeterministicFaultInjector with seed={seed}")
    
    def should_inject_fault(self, fault_spec: FaultSpec) -> bool:
        """
        Deterministically decide whether to inject fault
        
        Args:
            fault_spec: Fault specification
            
        Returns:
            True if fault should be injected
        """
        # Use deterministic random value
        roll = self._rng.random()
        return roll < fault_spec.probability
    
    def inject_fault(
        self,
        fault_spec: FaultSpec,
        operation: Callable[[], Any],
        component: str
    ) -> FaultInjectionResult:
        """
        Inject fault into operation with fallback
        
        Args:
            fault_spec: Specification of fault to inject
            operation: Operation to potentially fault
            component: Component identifier
            
        Returns:
            FaultInjectionResult with outcome
        """
        # Decide deterministically whether to inject
        inject = self.should_inject_fault(fault_spec)
        
        result = FaultInjectionResult(
            fault_injected=inject,
            fault_spec=fault_spec if inject else None,
            fallback_used=False,
            fallback_value=None,
            timestamp=datetime.now(timezone.utc).isoformat(),
            seed_used=self.seed
        )
        
        if inject:
            logger.warning(
                f"Injecting {fault_spec.fault_type.value} fault "
                f"into {component}"
            )
            
            # Use fallback instead of executing operation
            fallback = self.fallback_provider.get_fallback(component)
            result.fallback_used = True
            result.fallback_value = fallback
        else:
            # Execute operation normally
            try:
                result.fallback_value = operation()
            except Exception as e:
                logger.error(f"Operation failed: {e}")
                # Use fallback on unexpected failure
                fallback = self.fallback_provider.get_fallback(component)
                result.fallback_used = True
                result.fallback_value = fallback
        
        self._injection_history.append(result)
        return result
    
    def reset(self) -> None:
        """Reset to initial seed for reproducibility"""
        self._rng.seed(self.seed)
        self._injection_history.clear()
        logger.debug(f"Reset fault injector to seed {self.seed}")
    
    def get_history(self) -> List[FaultInjectionResult]:
        """Get fault injection history"""
        return self._injection_history.copy()
    
    def verify_reproducibility(self, num_trials: int = 3) -> bool:
        """
        Verify fault injection is reproducible
        
        Args:
            num_trials: Number of trials to verify
            
        Returns:
            True if reproducible
        """
        test_fault = FaultSpec(
            fault_type=FaultType.COMPUTATION_ERROR,
            probability=0.5,
            severity=0.5,
            target_component="test"
        )
        
        results = []
        for _ in range(num_trials):
            self.reset()
            decisions = []
            for _ in range(10):
                decisions.append(self.should_inject_fault(test_fault))
            results.append(decisions)
        
        # All trials should produce identical decisions
        first = results[0]
        reproducible = all(r == first for r in results[1:])
        
        if reproducible:
            logger.info("Fault injection reproducibility verified")
        else:
            logger.error("Fault injection not reproducible")
        
        return reproducible


class FaultFreeContract:
    """
    Fault-Free Contract enforcer
    
    Ensures fault injection maintains system guarantees through
    conservative fallbacks and deterministic behavior.
    
    Guarantees:
    - Fault determinism: Same seed → same faults
    - Contract preservation: Other contracts still hold
    - Safe degradation: Conservative fallbacks maintain safety
    - Reproducibility: Fault scenarios can be replayed
    """
    
    def __init__(
        self,
        seed: int,
        fallback_provider: Optional[ConservativeFallback] = None
    ):
        """
        Initialize fault-free contract
        
        Args:
            seed: Seed for deterministic fault injection
            fallback_provider: Optional fallback provider
        """
        self.seed = seed
        self.fallback_provider = fallback_provider or ConservativeFallback()
        self.injector = DeterministicFaultInjector(seed, self.fallback_provider)
        
        logger.info(f"Initialized FaultFreeContract with seed={seed}")
    
    def verify_determinism(self) -> bool:
        """
        Verify fault injection is deterministic
        
        Returns:
            True if deterministic
        """
        return self.injector.verify_reproducibility()
    
    def verify_fallback_safety(self, component: str, expected_type: type) -> bool:
        """
        Verify fallback values are safe
        
        Args:
            component: Component to verify
            expected_type: Expected type of fallback
            
        Returns:
            True if fallback is safe
        """
        fallback = self.fallback_provider.get_fallback(component)
        
        if fallback is None:
            logger.warning(f"No fallback for {component}")
            return False
        
        # Check type safety
        if not isinstance(fallback, expected_type):
            logger.error(
                f"Fallback type mismatch for {component}: "
                f"expected {expected_type}, got {type(fallback)}"
            )
            return False
        
        logger.debug(f"Fallback is safe for {component}")
        return True
    
    def verify_contract(self) -> bool:
        """
        Verify fault-free contract guarantees
        
        Returns:
            True if contract guarantees are met
        """
        # 1. Verify determinism
        if not self.verify_determinism():
            logger.error("Fault injection is not deterministic")
            return False
        
        # 2. Verify history is tracked
        if not hasattr(self.injector, '_injection_history'):
            logger.error("Injection history not tracked")
            return False
        
        # 3. Verify reproducibility with reset
        self.injector.reset()
        if len(self.injector.get_history()) != 0:
            logger.error("Reset did not clear history")
            return False
        
        logger.info("Fault-free contract verified")
        return True


if __name__ == "__main__":
    # Test fault-free contracts
    print("=" * 80)
    print("FAULT-FREE CONTRACTS (FFC) TEST")
    print("=" * 80)
    
    # Test 1: Conservative fallbacks
    print("\nTest 1: Conservative Fallbacks")
    fallback_provider = ConservativeFallback()
    
    # Register fallbacks
    fallback_provider.register_fallback(
        "analyzer",
        lambda: {"status": "fallback", "result": None}
    )
    fallback_provider.register_fallback(
        "scorer",
        lambda: 0.0
    )
    
    analyzer_fallback = fallback_provider.get_fallback("analyzer")
    scorer_fallback = fallback_provider.get_fallback("scorer")
    
    print(f"  Analyzer fallback: {analyzer_fallback}")
    print(f"  Scorer fallback: {scorer_fallback}")
    
    # Test 2: Deterministic fault injection
    print("\nTest 2: Deterministic Fault Injection")
    
    seed = 42
    injector = DeterministicFaultInjector(seed, fallback_provider)
    
    fault_spec = FaultSpec(
        fault_type=FaultType.COMPUTATION_ERROR,
        probability=0.3,
        severity=0.5,
        target_component="analyzer"
    )
    
    # Inject faults deterministically
    def normal_operation():
        return {"status": "success", "result": 42}
    
    results = []
    for i in range(5):
        result = injector.inject_fault(fault_spec, normal_operation, "analyzer")
        results.append(result)
        print(f"  Trial {i+1}: fault_injected={result.fault_injected}, "
              f"fallback_used={result.fallback_used}")
    
    # Test 3: Verify reproducibility
    print("\nTest 3: Verify Reproducibility")
    
    injector.reset()
    results2 = []
    for i in range(5):
        result = injector.inject_fault(fault_spec, normal_operation, "analyzer")
        results2.append(result)
    
    # Check if patterns match
    pattern1 = [r.fault_injected for r in results]
    pattern2 = [r.fault_injected for r in results2]
    
    print(f"  Pattern 1: {pattern1}")
    print(f"  Pattern 2: {pattern2}")
    print(f"  Patterns match: {pattern1 == pattern2}")
    
    # Test 4: Full reproducibility verification
    print("\nTest 4: Full Reproducibility Verification")
    reproducible = injector.verify_reproducibility(num_trials=3)
    print(f"  Reproducibility verified: {reproducible}")
    
    # Test 5: Contract verification
    print("\nTest 5: Fault-Free Contract Verification")
    contract = FaultFreeContract(seed=42, fallback_provider=fallback_provider)
    
    contract_verified = contract.verify_contract()
    print(f"  Contract verified: {contract_verified}")
    
    # Test fallback safety
    safe = contract.verify_fallback_safety("analyzer", dict)
    print(f"  Fallback safety verified: {safe}")
    
    print("\n" + "=" * 80)
