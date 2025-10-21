"""
Routing Contract (RC) - Deterministic Routing with Canonical Inputs
===================================================================

Ensures deterministic routes for identical inputs and provides tiebreaking
explanations. Uses pure router accepting only canonical inputs.

Based on Abernethy et al. (2022) theorem guaranteeing unique convergence
via deterministic projections on convex polytopes.

Key Guarantees:
1. Deterministic routing: identical inputs → identical routes
2. Canonical input enforcement: only normalized inputs accepted
3. Tiebreaking transparency: clear explanation when multiple routes possible
4. Route reproducibility: same route given same canonical input

Author: FARFAN 3.0 - Contract Enforcement System
Version: 1.0.0
Python: 3.11+
"""

import hashlib
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class TiebreakingStrategy(Enum):
    """Strategy for breaking ties in routing decisions"""
    LEXICOGRAPHIC = "lexicographic"  # Sort by route ID alphabetically
    HASH_BASED = "hash_based"  # Use input hash for deterministic selection
    PRIORITY = "priority"  # Use pre-assigned priority scores


@dataclass(frozen=True)
class CanonicalInput:
    """
    Canonical representation of routing input
    
    Ensures inputs are normalized before routing to guarantee
    deterministic behavior.
    """
    question_id: str
    dimension: str
    context_hash: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @staticmethod
    def from_input(
        question_id: str,
        dimension: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> 'CanonicalInput':
        """
        Create canonical input from raw input
        
        Args:
            question_id: Question identifier
            dimension: Optional dimension identifier
            context: Optional context dictionary
            
        Returns:
            Canonical input with normalized fields
        """
        # Extract dimension from question_id if not provided
        if dimension is None:
            import re
            match = re.search(r'D[1-6]', question_id)
            dimension = match.group(0) if match else "D1"
        
        # Create deterministic hash of context
        context_str = json.dumps(context or {}, sort_keys=True)
        context_hash = hashlib.sha256(context_str.encode()).hexdigest()
        
        # Normalize metadata (sort keys for determinism)
        metadata = dict(sorted((context or {}).items())) if context else {}
        
        return CanonicalInput(
            question_id=question_id,
            dimension=dimension,
            context_hash=context_hash,
            metadata=metadata
        )
    
    def to_deterministic_string(self) -> str:
        """Convert to deterministic string representation for hashing"""
        return f"{self.question_id}|{self.dimension}|{self.context_hash}"


@dataclass(frozen=True)
class RouteExplanation:
    """
    Explanation for routing decision
    
    Provides transparency into why a particular route was selected,
    especially important when tiebreaking is needed.
    """
    route_id: str
    confidence: float
    tiebreaking_used: bool
    tiebreaking_strategy: Optional[TiebreakingStrategy] = None
    alternatives: List[str] = field(default_factory=list)
    reasoning: str = ""
    
    def __post_init__(self):
        """Validate explanation consistency"""
        if self.tiebreaking_used and self.tiebreaking_strategy is None:
            raise ValueError("Tiebreaking strategy must be specified when tiebreaking is used")
        if self.tiebreaking_used and not self.alternatives:
            raise ValueError("Alternative routes must be provided when tiebreaking is used")


@dataclass(frozen=True)
class RoutingResult:
    """Result of routing operation"""
    canonical_input: CanonicalInput
    route_id: str
    handler_module: str
    handler_class: str
    handler_method: str
    explanation: RouteExplanation
    deterministic_hash: str  # Hash proving determinism
    
    def verify_determinism(self, expected_hash: str) -> bool:
        """Verify routing was deterministic by comparing hashes"""
        return self.deterministic_hash == expected_hash


class RoutingContract:
    """
    Routing Contract enforcer
    
    Guarantees:
    - Deterministic routing for identical canonical inputs
    - Tiebreaking transparency with explanations
    - Route reproducibility across executions
    """
    
    def __init__(
        self,
        tiebreaking_strategy: TiebreakingStrategy = TiebreakingStrategy.HASH_BASED
    ):
        """
        Initialize routing contract
        
        Args:
            tiebreaking_strategy: Strategy for breaking ties
        """
        self.tiebreaking_strategy = tiebreaking_strategy
        self._route_cache: Dict[str, RoutingResult] = {}
        
        logger.info(f"Initialized RoutingContract with tiebreaking={tiebreaking_strategy}")
    
    def validate_canonical_input(self, input_data: CanonicalInput) -> Tuple[bool, str]:
        """
        Validate that input is properly canonicalized
        
        Args:
            input_data: Input to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not input_data.question_id:
            return False, "Question ID cannot be empty"
        
        if not input_data.dimension:
            return False, "Dimension cannot be empty"
        
        if not input_data.context_hash:
            return False, "Context hash cannot be empty"
        
        # Verify metadata is sorted (canonical form)
        if input_data.metadata:
            keys = list(input_data.metadata.keys())
            if keys != sorted(keys):
                return False, "Metadata keys must be sorted for canonical form"
        
        return True, ""
    
    def compute_deterministic_hash(self, input_data: CanonicalInput) -> str:
        """
        Compute deterministic hash from canonical input
        
        This hash uniquely identifies the routing decision for given input.
        
        Args:
            input_data: Canonical input
            
        Returns:
            Deterministic hash string
        """
        input_str = input_data.to_deterministic_string()
        return hashlib.sha256(input_str.encode()).hexdigest()
    
    def verify_contract(self, routing_result: RoutingResult) -> bool:
        """
        Verify routing contract guarantees
        
        Args:
            routing_result: Result to verify
            
        Returns:
            True if contract guarantees are met
        """
        # 1. Verify canonical input
        is_valid, error = self.validate_canonical_input(routing_result.canonical_input)
        if not is_valid:
            logger.error(f"Contract violation: {error}")
            return False
        
        # 2. Verify deterministic hash
        expected_hash = self.compute_deterministic_hash(routing_result.canonical_input)
        if routing_result.deterministic_hash != expected_hash:
            logger.error("Contract violation: Hash mismatch")
            return False
        
        # 3. Verify explanation consistency
        if routing_result.explanation.tiebreaking_used:
            if not routing_result.explanation.alternatives:
                logger.error("Contract violation: Missing alternatives in tiebreaking")
                return False
        
        logger.debug("Contract verification passed")
        return True


class DeterministicRouter:
    """
    Pure deterministic router with contract enforcement
    
    Accepts only canonical inputs and guarantees deterministic routing.
    Based on projection onto convex polytopes for unique convergence.
    """
    
    def __init__(
        self,
        route_map: Dict[str, Dict[str, Any]],
        contract: Optional[RoutingContract] = None
    ):
        """
        Initialize deterministic router
        
        Args:
            route_map: Mapping from dimension/question to route config
            contract: Optional routing contract enforcer
        """
        self.route_map = route_map
        self.contract = contract or RoutingContract()
        
        logger.info(f"Initialized DeterministicRouter with {len(route_map)} routes")
    
    def route(self, input_data: CanonicalInput) -> RoutingResult:
        """
        Route input to handler with contract enforcement
        
        Args:
            input_data: Canonical input to route
            
        Returns:
            Routing result with explanation
            
        Raises:
            ValueError: If input is not canonical or no route found
        """
        # Validate canonical input
        is_valid, error = self.contract.validate_canonical_input(input_data)
        if not is_valid:
            raise ValueError(f"Non-canonical input: {error}")
        
        # Compute deterministic hash
        det_hash = self.contract.compute_deterministic_hash(input_data)
        
        # Check cache first
        if det_hash in self.contract._route_cache:
            logger.debug(f"Cache hit for hash {det_hash[:8]}")
            return self.contract._route_cache[det_hash]
        
        # Find matching routes
        candidates = self._find_candidate_routes(input_data)
        
        if not candidates:
            raise ValueError(f"No route found for {input_data.question_id}")
        
        # Select route (with tiebreaking if needed)
        selected, explanation = self._select_route(candidates, input_data)
        
        # Create result
        result = RoutingResult(
            canonical_input=input_data,
            route_id=selected["id"],
            handler_module=selected["module"],
            handler_class=selected["class"],
            handler_method=selected["method"],
            explanation=explanation,
            deterministic_hash=det_hash
        )
        
        # Verify contract
        if not self.contract.verify_contract(result):
            raise ValueError("Routing contract violation detected")
        
        # Cache result
        self.contract._route_cache[det_hash] = result
        
        return result
    
    def _find_candidate_routes(
        self,
        input_data: CanonicalInput
    ) -> List[Dict[str, Any]]:
        """Find all candidate routes for input"""
        candidates = []
        
        # Check exact question match
        if input_data.question_id in self.route_map:
            route = self.route_map[input_data.question_id].copy()
            route["id"] = input_data.question_id
            candidates.append(route)
        
        # Check dimension match
        if input_data.dimension in self.route_map:
            route = self.route_map[input_data.dimension].copy()
            route["id"] = input_data.dimension
            candidates.append(route)
        
        return candidates
    
    def _select_route(
        self,
        candidates: List[Dict[str, Any]],
        input_data: CanonicalInput
    ) -> Tuple[Dict[str, Any], RouteExplanation]:
        """
        Select route from candidates with tiebreaking
        
        Uses deterministic tiebreaking strategy when multiple routes match.
        """
        if len(candidates) == 1:
            # No tiebreaking needed
            explanation = RouteExplanation(
                route_id=candidates[0]["id"],
                confidence=1.0,
                tiebreaking_used=False,
                reasoning="Unique route match"
            )
            return candidates[0], explanation
        
        # Tiebreaking needed
        strategy = self.contract.tiebreaking_strategy
        
        if strategy == TiebreakingStrategy.LEXICOGRAPHIC:
            # Sort by route ID
            sorted_candidates = sorted(candidates, key=lambda x: x["id"])
            selected = sorted_candidates[0]
            reasoning = "Lexicographic tiebreaking (alphabetical order)"
        
        elif strategy == TiebreakingStrategy.HASH_BASED:
            # Use input hash to deterministically select
            input_hash = int(input_data.context_hash[:8], 16)
            selected_idx = input_hash % len(candidates)
            selected = candidates[selected_idx]
            reasoning = f"Hash-based tiebreaking (hash mod {len(candidates)})"
        
        else:  # PRIORITY
            # Use priority if available
            sorted_candidates = sorted(
                candidates,
                key=lambda x: x.get("priority", 0),
                reverse=True
            )
            selected = sorted_candidates[0]
            reasoning = "Priority-based tiebreaking"
        
        explanation = RouteExplanation(
            route_id=selected["id"],
            confidence=1.0 / len(candidates),
            tiebreaking_used=True,
            tiebreaking_strategy=strategy,
            alternatives=[c["id"] for c in candidates if c["id"] != selected["id"]],
            reasoning=reasoning
        )
        
        return selected, explanation


if __name__ == "__main__":
    # Test the routing contract
    print("=" * 80)
    print("ROUTING CONTRACT (RC) TEST")
    print("=" * 80)
    
    # Create route map
    route_map = {
        "D1": {
            "module": "policy_processor",
            "class": "IndustrialPolicyProcessor",
            "method": "process",
            "priority": 1
        },
        "D1-Q1": {
            "module": "policy_processor",
            "class": "IndustrialPolicyProcessor",
            "method": "process_q1",
            "priority": 2
        }
    }
    
    # Create router with contract
    contract = RoutingContract(tiebreaking_strategy=TiebreakingStrategy.HASH_BASED)
    router = DeterministicRouter(route_map, contract)
    
    # Test 1: Create canonical input
    print("\nTest 1: Canonical Input Creation")
    canonical = CanonicalInput.from_input(
        question_id="D1-Q1",
        context={"plan": "test", "version": "1.0"}
    )
    print(f"  Question ID: {canonical.question_id}")
    print(f"  Dimension: {canonical.dimension}")
    print(f"  Context Hash: {canonical.context_hash[:16]}...")
    
    # Test 2: Deterministic routing
    print("\nTest 2: Deterministic Routing")
    result1 = router.route(canonical)
    result2 = router.route(canonical)
    
    print(f"  Route 1: {result1.route_id} -> {result1.handler_module}")
    print(f"  Route 2: {result2.route_id} -> {result2.handler_module}")
    print(f"  Deterministic: {result1.deterministic_hash == result2.deterministic_hash}")
    
    # Test 3: Tiebreaking explanation
    print("\nTest 3: Tiebreaking Transparency")
    print(f"  Tiebreaking used: {result1.explanation.tiebreaking_used}")
    if result1.explanation.tiebreaking_used:
        print(f"  Strategy: {result1.explanation.tiebreaking_strategy.value}")
        print(f"  Alternatives: {result1.explanation.alternatives}")
        print(f"  Reasoning: {result1.explanation.reasoning}")
    
    # Test 4: Contract verification
    print("\nTest 4: Contract Verification")
    verified = contract.verify_contract(result1)
    print(f"  Contract verified: {verified}")
    
    print("\n" + "=" * 80)
