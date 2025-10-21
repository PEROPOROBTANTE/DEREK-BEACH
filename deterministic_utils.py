"""
Deterministic Utilities - Reproducible Execution Support
=========================================================

Provides utilities for deterministic execution including seed generation,
hash-based identifiers, and reproducible random number generation.

Key Features:
- Deterministic seed generation from workflow/step identifiers
- Hash-based unique identifiers
- Reproducible random number generators
- Timestamp utilities for deterministic logging

Author: FARFAN 3.0 - Industrial Orchestrator
Version: 1.0.0
Python: 3.10+
"""

import hashlib
import random
import logging
from typing import Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DeterministicContext:
    """Immutable context for deterministic operations"""
    workflow_id: str
    step_id: str
    version: str
    seed: int
    
    @property
    def random_generator(self):
        """Get a random.Random instance seeded with this context"""
        return random.Random(self.seed)


def create_deterministic_seed(
    workflow_id: str,
    step_id: str,
    version: str = "1.0.0",
    additional_data: Optional[List[str]] = None
) -> int:
    """
    Create a deterministic seed from workflow and step identifiers
    
    This ensures that given the same workflow_id, step_id, and version,
    the same seed is always generated, enabling reproducible execution.
    
    Args:
        workflow_id: Unique workflow instance identifier
        step_id: Unique step identifier within workflow
        version: Version of the workflow/component (for schema versioning)
        additional_data: Optional list of additional strings to include in seed
        
    Returns:
        Integer seed for random number generation
        
    Example:
        >>> seed = create_deterministic_seed("wf_123", "step_1", "2.0.0")
        >>> rng = random.Random(seed)
        >>> value = rng.random()  # Reproducible random value
    """
    # Combine all inputs into a single string
    components = [workflow_id, step_id, version]
    
    if additional_data:
        components.extend(additional_data)
    
    seed_string = "|".join(components)
    
    # Create SHA-256 hash
    hash_obj = hashlib.sha256(seed_string.encode('utf-8'))
    hash_hex = hash_obj.hexdigest()
    
    # Convert first 8 bytes of hash to integer seed
    # This gives us a large but manageable seed value
    seed = int(hash_hex[:16], 16)
    
    logger.debug(
        f"Created deterministic seed: {seed} from "
        f"workflow={workflow_id}, step={step_id}, version={version}"
    )
    
    return seed


def create_advanced_seed(
    workflow_id: str,
    step_id: str,
    question_id: str,
    version: str = "1.0.0",
    attempt: int = 0
) -> int:
    """
    Create advanced deterministic seed with retry support
    
    This version includes question_id and attempt number, allowing
    different seeds for retry attempts while maintaining determinism.
    
    Args:
        workflow_id: Unique workflow instance identifier
        step_id: Unique step identifier
        question_id: Question being processed
        version: Version for schema compatibility
        attempt: Retry attempt number (0 for first attempt)
        
    Returns:
        Integer seed for random number generation
    """
    return create_deterministic_seed(
        workflow_id=workflow_id,
        step_id=step_id,
        version=version,
        additional_data=[question_id, str(attempt)]
    )


def create_deterministic_context(
    workflow_id: str,
    step_id: str,
    version: str = "1.0.0"
) -> DeterministicContext:
    """
    Create a DeterministicContext with embedded seed and random generator
    
    Args:
        workflow_id: Unique workflow instance identifier
        step_id: Unique step identifier
        version: Version for schema compatibility
        
    Returns:
        DeterministicContext with seed and random generator
    """
    seed = create_deterministic_seed(workflow_id, step_id, version)
    
    return DeterministicContext(
        workflow_id=workflow_id,
        step_id=step_id,
        version=version,
        seed=seed
    )


def hash_content(content: str, algorithm: str = "sha256") -> str:
    """
    Create a hash of content for deterministic identification
    
    Args:
        content: String content to hash
        algorithm: Hash algorithm (sha256, sha1, md5)
        
    Returns:
        Hexadecimal hash string
    """
    if algorithm == "sha256":
        hash_obj = hashlib.sha256(content.encode('utf-8'))
    elif algorithm == "sha1":
        hash_obj = hashlib.sha1(content.encode('utf-8'))
    elif algorithm == "md5":
        hash_obj = hashlib.md5(content.encode('utf-8'))
    else:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")
    
    return hash_obj.hexdigest()


def create_deterministic_id(prefix: str, *components: Any) -> str:
    """
    Create a deterministic identifier from components
    
    Args:
        prefix: Prefix for the ID (e.g., "workflow", "step")
        *components: Variable number of components to include in ID
        
    Returns:
        Deterministic identifier string
        
    Example:
        >>> id1 = create_deterministic_id("wf", "plan_123", "2024-01-01")
        >>> id2 = create_deterministic_id("wf", "plan_123", "2024-01-01")
        >>> id1 == id2  # True - deterministic
    """
    # Convert all components to strings
    component_strings = [str(c) for c in components]
    
    # Join with separator
    combined = "|".join(component_strings)
    
    # Create short hash
    hash_hex = hash_content(combined, "sha256")[:12]
    
    # Combine prefix with hash
    return f"{prefix}_{hash_hex}"


class DeterministicRandom:
    """
    Wrapper around random.Random for clearer deterministic usage
    
    This class makes it explicit that random operations are deterministic
    and provides additional utilities.
    """
    
    def __init__(self, seed: int):
        """
        Initialize with a seed
        
        Args:
            seed: Integer seed for reproducibility
        """
        self.seed = seed
        self._rng = random.Random(seed)
        self._call_count = 0
        
        logger.debug(f"Initialized DeterministicRandom with seed: {seed}")
    
    def random(self) -> float:
        """Generate random float in [0.0, 1.0)"""
        self._call_count += 1
        return self._rng.random()
    
    def randint(self, a: int, b: int) -> int:
        """Generate random integer in [a, b]"""
        self._call_count += 1
        return self._rng.randint(a, b)
    
    def choice(self, seq: List[Any]) -> Any:
        """Choose random element from sequence"""
        self._call_count += 1
        return self._rng.choice(seq)
    
    def shuffle(self, seq: List[Any]) -> None:
        """Shuffle sequence in place"""
        self._call_count += 1
        self._rng.shuffle(seq)
    
    def sample(self, population: List[Any], k: int) -> List[Any]:
        """Sample k items from population without replacement"""
        self._call_count += 1
        return self._rng.sample(population, k)
    
    def uniform(self, a: float, b: float) -> float:
        """Generate random float in [a, b]"""
        self._call_count += 1
        return self._rng.uniform(a, b)
    
    def gauss(self, mu: float, sigma: float) -> float:
        """Generate random number from Gaussian distribution"""
        self._call_count += 1
        return self._rng.gauss(mu, sigma)
    
    def get_state(self) -> tuple:
        """Get internal state (for debugging/verification)"""
        return self._rng.getstate()
    
    def get_call_count(self) -> int:
        """Get number of random calls made"""
        return self._call_count
    
    def reset(self) -> None:
        """Reset to original seed"""
        self._rng.seed(self.seed)
        self._call_count = 0
        logger.debug(f"Reset DeterministicRandom to seed: {self.seed}")


def verify_determinism(
    operation: callable,
    seed: int,
    num_trials: int = 3
) -> bool:
    """
    Verify that an operation produces deterministic results
    
    Args:
        operation: Callable that takes a DeterministicRandom instance
        seed: Seed to use for all trials
        num_trials: Number of trials to run (default 3)
        
    Returns:
        True if all trials produce identical results, False otherwise
        
    Example:
        >>> def my_operation(rng):
        ...     return [rng.random() for _ in range(10)]
        >>> 
        >>> is_deterministic = verify_determinism(my_operation, seed=42)
        >>> print(is_deterministic)  # Should be True
    """
    results = []
    
    for trial in range(num_trials):
        rng = DeterministicRandom(seed)
        result = operation(rng)
        results.append(result)
        
        logger.debug(f"Trial {trial + 1}: {result}")
    
    # Check if all results are identical
    first_result = results[0]
    is_deterministic = all(r == first_result for r in results[1:])
    
    if is_deterministic:
        logger.info(f"✓ Operation is deterministic (seed={seed}, trials={num_trials})")
    else:
        logger.warning(f"✗ Operation is NOT deterministic (seed={seed}, trials={num_trials})")
    
    return is_deterministic


if __name__ == "__main__":
    import json
    
    print("=" * 80)
    print("DETERMINISTIC UTILITIES TEST")
    print("=" * 80)
    
    # Test 1: Seed generation
    print("\n" + "-" * 80)
    print("Test 1: Deterministic Seed Generation")
    print("-" * 80)
    
    workflow_id = "test_workflow_001"
    step_id = "step_1"
    version = "2.0.0"
    
    # Generate seed multiple times - should be identical
    seed1 = create_deterministic_seed(workflow_id, step_id, version)
    seed2 = create_deterministic_seed(workflow_id, step_id, version)
    seed3 = create_deterministic_seed(workflow_id, step_id, version)
    
    print(f"Seed 1: {seed1}")
    print(f"Seed 2: {seed2}")
    print(f"Seed 3: {seed3}")
    print(f"All equal: {seed1 == seed2 == seed3}")
    
    # Different step should give different seed
    seed_different = create_deterministic_seed(workflow_id, "step_2", version)
    print(f"\nDifferent step seed: {seed_different}")
    print(f"Different from step_1: {seed_different != seed1}")
    
    # Test 2: Deterministic random generation
    print("\n" + "-" * 80)
    print("Test 2: Deterministic Random Generation")
    print("-" * 80)
    
    rng1 = DeterministicRandom(seed1)
    values1 = [rng1.random() for _ in range(5)]
    print(f"Trial 1 values: {values1}")
    
    rng2 = DeterministicRandom(seed1)
    values2 = [rng2.random() for _ in range(5)]
    print(f"Trial 2 values: {values2}")
    
    print(f"Values identical: {values1 == values2}")
    
    # Test 3: Advanced seed with retry
    print("\n" + "-" * 80)
    print("Test 3: Advanced Seed with Retry Support")
    print("-" * 80)
    
    question_id = "P1-D1-Q1"
    
    seed_attempt_0 = create_advanced_seed(workflow_id, step_id, question_id, version, attempt=0)
    seed_attempt_1 = create_advanced_seed(workflow_id, step_id, question_id, version, attempt=1)
    seed_attempt_2 = create_advanced_seed(workflow_id, step_id, question_id, version, attempt=2)
    
    print(f"Attempt 0 seed: {seed_attempt_0}")
    print(f"Attempt 1 seed: {seed_attempt_1}")
    print(f"Attempt 2 seed: {seed_attempt_2}")
    print(f"All different: {len({seed_attempt_0, seed_attempt_1, seed_attempt_2}) == 3}")
    
    # Test 4: Deterministic context
    print("\n" + "-" * 80)
    print("Test 4: Deterministic Context")
    print("-" * 80)
    
    context = create_deterministic_context(workflow_id, step_id, version)
    print(f"Workflow ID: {context.workflow_id}")
    print(f"Step ID: {context.step_id}")
    print(f"Version: {context.version}")
    print(f"Seed: {context.seed}")
    
    rng = context.random_generator
    print(f"Random value from context: {rng.random():.6f}")
    
    # Test 5: Hash-based IDs
    print("\n" + "-" * 80)
    print("Test 5: Deterministic ID Generation")
    print("-" * 80)
    
    id1 = create_deterministic_id("workflow", "plan_abc", "2024-01-01")
    id2 = create_deterministic_id("workflow", "plan_abc", "2024-01-01")
    id3 = create_deterministic_id("workflow", "plan_xyz", "2024-01-01")
    
    print(f"ID 1: {id1}")
    print(f"ID 2: {id2}")
    print(f"ID 3: {id3}")
    print(f"ID1 == ID2: {id1 == id2}")
    print(f"ID1 != ID3: {id1 != id3}")
    
    # Test 6: Verify determinism
    print("\n" + "-" * 80)
    print("Test 6: Determinism Verification")
    print("-" * 80)
    
    def test_operation(rng: DeterministicRandom) -> List[float]:
        """Test operation that should be deterministic"""
        result = []
        for _ in range(10):
            result.append(rng.random())
        return result
    
    is_deterministic = verify_determinism(test_operation, seed=12345, num_trials=5)
    print(f"\nOperation is deterministic: {is_deterministic}")
    
    print("\n" + "=" * 80)
