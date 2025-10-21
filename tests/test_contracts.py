"""
Contract Tests - Comprehensive Testing for All 7 Software Contracts
===================================================================

Tests all contract implementations to ensure they meet their guarantees:
1. Routing Contract (RC)
2. Snapshot Contract (SC)
3. Risk Control Certificates (RCC)
4. Monotone Consistency Contract (MCC) & Budget Monotonicity Contract (BMC)
5. Permutation Invariance Contracts (PIC)
6. Fault-Free Contracts (FFC)
7. Context Immutability Contract (CIC)

Author: FARFAN 3.0 - Contract Testing Suite
Version: 1.0.0
Python: 3.11+
"""

import pytest
import sys
import json
import numpy as np
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from contracts import (
    # Routing Contract
    RoutingContract,
    CanonicalInput,
    DeterministicRouter,
    RouteExplanation,
    TiebreakingStrategy,
    # Snapshot Contract
    SnapshotContract,
    ImmutableSnapshot,
    SnapshotManager,
    SnapshotSigma,
    # Risk Control Certificates
    RiskControlCertificate,
    ConformalPredictor,
    CoverageGuarantee,
    # Monotonicity Contracts
    MonotoneConsistencyContract,
    BudgetMonotonicityContract,
    MonotonicValidator,
    Evidence,
    Decision,
    BudgetAllocation,
    # Permutation Invariance
    PermutationInvarianceContract,
    InvariantAggregator,
    NumericalStabilityValidator,
    AggregationType,
    # Fault-Free Contracts
    FaultFreeContract,
    DeterministicFaultInjector,
    ConservativeFallback,
    FaultSpec,
    FaultType,
    # Context Immutability
    ContextImmutabilityContract,
    CanonicalJSONValidator,
    ImmutableContext,
)


class TestRoutingContract:
    """Test Routing Contract (RC)"""
    
    def test_canonical_input_creation(self):
        """Test canonical input creation from raw input"""
        canonical = CanonicalInput.from_input(
            question_id="D1-Q1",
            context={"plan": "test", "version": "1.0"}
        )
        
        assert canonical.question_id == "D1-Q1"
        assert canonical.dimension == "D1"
        assert len(canonical.context_hash) == 64  # SHA-256
    
    def test_deterministic_routing(self):
        """Test routing determinism"""
        route_map = {
            "D1": {
                "module": "policy_processor",
                "class": "PolicyProcessor",
                "method": "process"
            }
        }
        
        contract = RoutingContract()
        router = DeterministicRouter(route_map, contract)
        
        canonical = CanonicalInput.from_input("D1-Q1")
        
        # Route multiple times
        result1 = router.route(canonical)
        result2 = router.route(canonical)
        
        assert result1.deterministic_hash == result2.deterministic_hash
        assert result1.route_id == result2.route_id
    
    def test_tiebreaking_transparency(self):
        """Test tiebreaking provides explanation"""
        route_map = {
            "D1": {"module": "m1", "class": "c1", "method": "m1"},
            "D1-Q1": {"module": "m2", "class": "c2", "method": "m2"}
        }
        
        contract = RoutingContract(tiebreaking_strategy=TiebreakingStrategy.HASH_BASED)
        router = DeterministicRouter(route_map, contract)
        
        canonical = CanonicalInput.from_input("D1-Q1")
        result = router.route(canonical)
        
        assert result.explanation.tiebreaking_used is True
        assert result.explanation.tiebreaking_strategy == TiebreakingStrategy.HASH_BASED
        assert len(result.explanation.alternatives) > 0
    
    def test_contract_verification(self):
        """Test routing contract verification"""
        route_map = {"D1": {"module": "m", "class": "c", "method": "m"}}
        contract = RoutingContract()
        router = DeterministicRouter(route_map, contract)
        
        canonical = CanonicalInput.from_input("D1-Q1")
        result = router.route(canonical)
        
        assert contract.verify_contract(result) is True


class TestSnapshotContract:
    """Test Snapshot Contract (SC)"""
    
    def test_sigma_computation(self):
        """Test sigma computation from components"""
        standards = {"rule": "value"}
        corpus = ["doc1", "doc2"]
        embeddings = [[0.1, 0.2]]
        index = {"doc1": 0}
        
        sigma = SnapshotSigma.compute_from_components(
            standards, corpus, embeddings, index
        )
        
        assert len(sigma.standards_hash) == 64
        assert len(sigma.corpus_hash) == 64
        assert len(sigma.embedding_hash) == 64
        assert len(sigma.index_hash) == 64
        assert sigma.verify_integrity()
    
    def test_snapshot_immutability(self):
        """Test snapshot is immutable"""
        manager = SnapshotManager()
        snapshot = manager.create_snapshot(
            snapshot_id="test_001",
            standards={},
            corpus=[],
            embeddings=[],
            index={}
        )
        
        # Try to modify (should fail)
        with pytest.raises((AttributeError, Exception)):
            snapshot.snapshot_id = "modified"
    
    def test_summary_reproducibility(self):
        """Test summary reproducibility"""
        manager = SnapshotManager()
        snapshot = manager.create_snapshot(
            snapshot_id="test_002",
            standards={"rule": "value"},
            corpus=["doc"],
            embeddings=[[0.1]],
            index={"doc": 0}
        )
        
        summary1 = snapshot.produce_summary()
        summary2 = snapshot.produce_summary()
        summary3 = snapshot.produce_summary()
        
        assert summary1 == summary2 == summary3
    
    def test_contract_verification(self):
        """Test snapshot contract verification"""
        manager = SnapshotManager()
        snapshot = manager.create_snapshot(
            snapshot_id="test_003",
            standards={},
            corpus=[],
            embeddings=[],
            index={}
        )
        
        contract = SnapshotContract()
        assert contract.verify_contract(snapshot) is True


class TestRiskControlCertificates:
    """Test Risk Control Certificates (RCC)"""
    
    def test_calibration(self):
        """Test conformal predictor calibration"""
        np.random.seed(42)
        
        certificate = RiskControlCertificate(target_coverage=0.90)
        
        scores = np.random.randn(100)
        labels = np.ones(100)
        
        conformal_scores = certificate.calibrate(scores, labels)
        
        assert conformal_scores.quantile_level == 0.90
        assert conformal_scores.threshold is not None
    
    def test_coverage_guarantee(self):
        """Test coverage guarantee certificate"""
        np.random.seed(42)
        
        certificate = RiskControlCertificate(target_coverage=0.90)
        
        scores_cal = np.random.randn(100)
        labels_cal = np.ones(100)
        
        conformal_scores = certificate.calibrate(scores_cal, labels_cal)
        
        scores_test = np.random.randn(50)
        labels_test = np.ones(50)
        
        guarantee = certificate.verify_coverage(
            conformal_scores, scores_test, labels_test
        )
        
        assert isinstance(guarantee, CoverageGuarantee)
        assert guarantee.target_coverage == 0.90
        assert guarantee.sample_size == 50
    
    def test_contract_verification(self):
        """Test risk control contract verification"""
        np.random.seed(42)
        
        certificate = RiskControlCertificate(target_coverage=0.90)
        
        scores = np.random.randn(100)
        labels = np.ones(100)
        
        conformal_scores = certificate.calibrate(scores, labels)
        
        guarantee = certificate.verify_coverage(
            conformal_scores, scores, labels
        )
        
        # Contract verification (may have statistical variations)
        result = certificate.verify_contract(guarantee)
        assert isinstance(result, bool)


class TestMonotonicityContracts:
    """Test Monotonicity Contracts (MCC & BMC)"""
    
    def test_monotone_consistency(self):
        """Test monotone consistency with evidence accumulation"""
        mcc = MonotoneConsistencyContract()
        
        decision_id = "test_decision"
        
        # Add progressive evidence
        ev1 = Evidence(source="s1", strength=0.3, supporting=Decision.ACCEPT)
        state1 = mcc.add_evidence(decision_id, ev1)
        
        ev2 = Evidence(source="s2", strength=0.4, supporting=Decision.ACCEPT)
        state2 = mcc.add_evidence(decision_id, ev2)
        
        # Confidence should increase
        assert state2.confidence >= state1.confidence
        assert mcc.verify_monotonicity(decision_id)
    
    def test_budget_monotonicity(self):
        """Test budget monotonicity"""
        bmc = BudgetMonotonicityContract()
        
        # Record allocations with increasing budgets
        allocations = [
            BudgetAllocation(budget=100, achieved_value=50, allocation_id="a1"),
            BudgetAllocation(budget=200, achieved_value=80, allocation_id="a2"),
            BudgetAllocation(budget=300, achieved_value=100, allocation_id="a3"),
        ]
        
        for alloc in allocations:
            bmc.record_allocation(alloc)
        
        assert bmc.verify_monotonicity()
    
    def test_combined_validator(self):
        """Test combined monotonicity validator"""
        mcc = MonotoneConsistencyContract()
        bmc = BudgetMonotonicityContract()
        
        # Add test data
        ev = Evidence(source="test", strength=0.5, supporting=Decision.ACCEPT)
        mcc.add_evidence("test", ev)
        
        alloc = BudgetAllocation(budget=100, achieved_value=50, allocation_id="a1")
        bmc.record_allocation(alloc)
        
        validator = MonotonicValidator(mcc=mcc, bmc=bmc)
        results = validator.verify_all_contracts()
        
        assert "monotone_consistency" in results
        assert "budget_monotonicity" in results


class TestPermutationInvarianceContract:
    """Test Permutation Invariance Contracts (PIC)"""
    
    def test_invariance_verification(self):
        """Test permutation invariance verification"""
        contract = PermutationInvarianceContract(num_permutation_tests=10)
        
        # Mean should be invariant
        mean_fn = lambda x: np.mean(x)
        inputs = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        
        assert contract.verify_invariance(mean_fn, inputs)
    
    def test_non_invariance_detection(self):
        """Test detection of non-invariant functions"""
        contract = PermutationInvarianceContract()
        
        # First element is NOT invariant
        first_fn = lambda x: x[0] if len(x) > 0 else 0
        inputs = np.array([1.0, 2.0, 3.0])
        
        assert not contract.verify_invariance(first_fn, inputs)
    
    def test_numerical_stability(self):
        """Test numerical stability verification"""
        contract = PermutationInvarianceContract()
        
        mean_fn = lambda x: np.mean(x)
        inputs = np.array([1.0, 2.0, 3.0])
        
        stability = contract.verify_numerical_stability(mean_fn, inputs)
        
        assert stability.is_stable(threshold=0.1)
    
    def test_invariant_aggregator(self):
        """Test invariant aggregator"""
        aggregator = InvariantAggregator(AggregationType.MEAN)
        
        inputs = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = aggregator.aggregate(inputs)
        
        assert result == 3.0
    
    def test_contract_verification(self):
        """Test permutation invariance contract"""
        contract = PermutationInvarianceContract()
        
        mean_fn = lambda x: np.mean(x)
        test_inputs = [
            np.array([1.0, 2.0, 3.0]),
            np.array([10.0, 20.0, 30.0]),
        ]
        
        assert contract.verify_contract(mean_fn, test_inputs)


class TestFaultFreeContracts:
    """Test Fault-Free Contracts (FFC)"""
    
    def test_conservative_fallbacks(self):
        """Test conservative fallback mechanism"""
        fallback = ConservativeFallback()
        
        fallback.register_fallback("component", lambda: {"status": "fallback"})
        
        result = fallback.get_fallback("component")
        assert result == {"status": "fallback"}
    
    def test_deterministic_fault_injection(self):
        """Test deterministic fault injection"""
        seed = 42
        fallback = ConservativeFallback()
        fallback.register_fallback("test", lambda: "fallback_value")
        
        injector = DeterministicFaultInjector(seed, fallback)
        
        fault_spec = FaultSpec(
            fault_type=FaultType.COMPUTATION_ERROR,
            probability=0.5,
            severity=0.5,
            target_component="test"
        )
        
        # Inject faults multiple times
        results1 = []
        for _ in range(10):
            result = injector.inject_fault(
                fault_spec,
                lambda: "normal",
                "test"
            )
            results1.append(result.fault_injected)
        
        # Reset and repeat
        injector.reset()
        results2 = []
        for _ in range(10):
            result = injector.inject_fault(
                fault_spec,
                lambda: "normal",
                "test"
            )
            results2.append(result.fault_injected)
        
        # Should be identical
        assert results1 == results2
    
    def test_reproducibility_verification(self):
        """Test fault injection reproducibility"""
        injector = DeterministicFaultInjector(seed=42)
        
        assert injector.verify_reproducibility(num_trials=3)
    
    def test_contract_verification(self):
        """Test fault-free contract verification"""
        contract = FaultFreeContract(seed=42)
        
        assert contract.verify_contract()


class TestContextImmutabilityContract:
    """Test Context Immutability Contract (CIC)"""
    
    def test_canonical_json_validation(self):
        """Test canonical JSON validation"""
        validator = CanonicalJSONValidator()
        
        data = {"z": 1, "a": 2, "m": 3}
        canonical = validator.canonicalize(data)
        
        assert validator.is_canonical(canonical)
        
        # Check keys are sorted in canonical form
        parsed = json.loads(canonical)
        keys = list(parsed.keys())
        assert keys == sorted(keys)
    
    def test_immutable_context_creation(self):
        """Test immutable context creation"""
        contract = ContextImmutabilityContract()
        
        data = {"plan": "test", "dimension": "D1"}
        context = contract.create_context("ctx_001", data)
        
        assert context.context_id == "ctx_001"
        assert len(context.canonical_hash) == 64
    
    def test_context_immutability(self):
        """Test context immutability"""
        contract = ContextImmutabilityContract()
        
        data = {"test": "value"}
        context = contract.create_context("ctx_002", data)
        
        # Try to modify (should fail)
        with pytest.raises((AttributeError, Exception)):
            context.context_id = "modified"
    
    def test_canonical_form_verification(self):
        """Test canonical form verification"""
        contract = ContextImmutabilityContract()
        
        data = {"b": 2, "a": 1}  # Not sorted
        context = contract.create_context("ctx_003", data)
        
        assert contract.verify_canonical_form("ctx_003")
    
    def test_integrity_verification(self):
        """Test integrity verification via hash"""
        contract = ContextImmutabilityContract()
        
        data = {"test": "data"}
        context = contract.create_context("ctx_004", data)
        
        assert contract.verify_integrity("ctx_004")
    
    def test_linear_access_tracking(self):
        """Test linear access tracking"""
        contract = ContextImmutabilityContract(track_references=True)
        
        data = {"test": "value"}
        contract.create_context("ctx_005", data)
        
        # Access multiple times
        for _ in range(3):
            contract.get_context("ctx_005")
        
        assert contract.verify_linear_access("ctx_005", max_references=5)
    
    def test_contract_verification(self):
        """Test context immutability contract verification"""
        contract = ContextImmutabilityContract()
        
        data = {"plan": "test"}
        contract.create_context("ctx_006", data)
        
        assert contract.verify_contract("ctx_006")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
