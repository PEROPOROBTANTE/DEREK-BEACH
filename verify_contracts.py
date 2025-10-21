#!/usr/bin/env python3
"""
Contract Verification Script
============================

Demonstrates all 7 software contracts in action with comprehensive verification.

Author: FARFAN 3.0 - Contract Enforcement System
Version: 1.0.0
Python: 3.11+
"""

import sys
import numpy as np
from contracts import (
    # All contracts
    RoutingContract, CanonicalInput, DeterministicRouter,
    SnapshotContract, SnapshotManager,
    RiskControlCertificate,
    MonotoneConsistencyContract, BudgetMonotonicityContract,
    Evidence, Decision, BudgetAllocation,
    PermutationInvarianceContract, InvariantAggregator, AggregationType,
    FaultFreeContract, FaultSpec, FaultType,
    ContextImmutabilityContract,
)


def print_section(title):
    """Print formatted section header"""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


def verify_routing_contract():
    """Verify Routing Contract (RC)"""
    print_section("1. ROUTING CONTRACT (RC)")
    
    route_map = {
        "D1": {"module": "policy_processor", "class": "PolicyProcessor", "method": "process"},
        "D1-Q1": {"module": "specialized_processor", "class": "SpecialProcessor", "method": "process_q1"}
    }
    
    contract = RoutingContract()
    router = DeterministicRouter(route_map, contract)
    
    canonical = CanonicalInput.from_input("D1-Q1", context={"version": "1.0"})
    result = router.route(canonical)
    
    print(f"✓ Canonical input created: {canonical.question_id}")
    print(f"✓ Route determined: {result.route_id} → {result.handler_module}")
    print(f"✓ Tiebreaking used: {result.explanation.tiebreaking_used}")
    print(f"✓ Contract verified: {contract.verify_contract(result)}")
    
    return contract.verify_contract(result)


def verify_snapshot_contract():
    """Verify Snapshot Contract (SC)"""
    print_section("2. SNAPSHOT CONTRACT (SC)")
    
    manager = SnapshotManager()
    snapshot = manager.create_snapshot(
        snapshot_id="verification_snapshot",
        standards={"standard_1": "value_1", "standard_2": "value_2"},
        corpus=["document_1", "document_2", "document_3"],
        embeddings=[[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]],
        index={"doc1": 0, "doc2": 1, "doc3": 2}
    )
    
    print(f"✓ Snapshot created: {snapshot.snapshot_id}")
    print(f"✓ Sigma computed:")
    print(f"  - Standards hash: {snapshot.sigma.standards_hash[:16]}...")
    print(f"  - Corpus hash: {snapshot.sigma.corpus_hash[:16]}...")
    print(f"  - Embeddings hash: {snapshot.sigma.embedding_hash[:16]}...")
    print(f"  - Index hash: {snapshot.sigma.index_hash[:16]}...")
    
    # Verify reproducibility
    summary1 = snapshot.produce_summary()
    summary2 = snapshot.produce_summary()
    reproducible = summary1 == summary2
    
    print(f"✓ Summary reproducibility: {reproducible}")
    
    contract = SnapshotContract()
    verified = contract.verify_contract(snapshot)
    print(f"✓ Contract verified: {verified}")
    
    return verified


def verify_risk_control_certificates():
    """Verify Risk Control Certificates (RCC)"""
    print_section("3. RISK CONTROL CERTIFICATES (RCC)")
    
    np.random.seed(42)
    
    certificate = RiskControlCertificate(target_coverage=0.90)
    
    # Calibration
    scores_cal = np.random.randn(200)
    labels_cal = np.ones(200)
    conformal_scores = certificate.calibrate(scores_cal, labels_cal)
    
    print(f"✓ Calibrated on {len(scores_cal)} samples")
    print(f"✓ Threshold: {conformal_scores.threshold:.4f}")
    print(f"✓ Target coverage: {certificate.target_coverage:.2f}")
    
    # Verification
    scores_test = np.random.randn(100)
    labels_test = np.ones(100)
    guarantee = certificate.verify_coverage(conformal_scores, scores_test, labels_test)
    
    print(f"✓ Actual coverage: {guarantee.actual_coverage:.2f}")
    
    verified = certificate.verify_contract(guarantee)
    print(f"✓ Contract verified: {verified}")
    
    return verified


def verify_monotonicity_contracts():
    """Verify Monotonicity Contracts (MCC & BMC)"""
    print_section("4. MONOTONICITY CONTRACTS (MCC & BMC)")
    
    # Monotone Consistency Contract
    print("\n4.1 Monotone Consistency Contract (MCC)")
    mcc = MonotoneConsistencyContract()
    
    decision_id = "policy_decision_001"
    evidences = [
        Evidence(source="expert_1", strength=0.3, supporting=Decision.ACCEPT),
        Evidence(source="expert_2", strength=0.4, supporting=Decision.ACCEPT),
        Evidence(source="data_analysis", strength=0.2, supporting=Decision.ACCEPT),
    ]
    
    for i, ev in enumerate(evidences, 1):
        state = mcc.add_evidence(decision_id, ev)
        print(f"  Evidence {i}: confidence = {state.confidence:.3f}, decision = {state.current_decision.name}")
    
    mcc_verified = mcc.verify_contract(decision_id)
    print(f"✓ MCC verified: {mcc_verified}")
    
    # Budget Monotonicity Contract
    print("\n4.2 Budget Monotonicity Contract (BMC)")
    bmc = BudgetMonotonicityContract()
    
    allocations = [
        BudgetAllocation(budget=100, achieved_value=45, allocation_id="a1"),
        BudgetAllocation(budget=150, achieved_value=65, allocation_id="a2"),
        BudgetAllocation(budget=200, achieved_value=82, allocation_id="a3"),
        BudgetAllocation(budget=250, achieved_value=93, allocation_id="a4"),
    ]
    
    for alloc in allocations:
        bmc.record_allocation(alloc)
        print(f"  Budget {alloc.budget:.0f} → Value {alloc.achieved_value:.0f}")
    
    bmc_verified = bmc.verify_contract()
    print(f"✓ BMC verified: {bmc_verified}")
    
    return mcc_verified and bmc_verified


def verify_permutation_invariance_contract():
    """Verify Permutation Invariance Contracts (PIC)"""
    print_section("5. PERMUTATION INVARIANCE CONTRACTS (PIC)")
    
    contract = PermutationInvarianceContract(num_permutation_tests=20)
    
    # Test standard aggregations
    inputs = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    
    results = []
    for agg_type in [AggregationType.MEAN, AggregationType.SUM, AggregationType.MAX]:
        aggregator = InvariantAggregator(agg_type, contract)
        value = aggregator.aggregate(inputs)
        
        # Verify invariance
        mean_fn = lambda x: np.mean(x) if agg_type == AggregationType.MEAN else (
            np.sum(x) if agg_type == AggregationType.SUM else np.max(x)
        )
        invariant = contract.verify_invariance(mean_fn, inputs)
        
        print(f"✓ {agg_type.value}: value={value:.2f}, invariant={invariant}")
        results.append(invariant)
    
    # Test numerical stability
    stability = contract.verify_numerical_stability(lambda x: np.mean(x), inputs)
    print(f"✓ Numerical stability: relative_change={stability.relative_change:.2e}")
    
    return all(results) and stability.is_stable()


def verify_fault_free_contracts():
    """Verify Fault-Free Contracts (FFC)"""
    print_section("6. FAULT-FREE CONTRACTS (FFC)")
    
    contract = FaultFreeContract(seed=42)
    
    # Register fallbacks
    contract.fallback_provider.register_fallback(
        "analyzer",
        lambda: {"status": "fallback", "confidence": 0.0}
    )
    
    print("✓ Fallback registered for 'analyzer'")
    
    # Test deterministic fault injection
    fault_spec = FaultSpec(
        fault_type=FaultType.COMPUTATION_ERROR,
        probability=0.4,
        severity=0.5,
        target_component="analyzer"
    )
    
    def normal_operation():
        return {"status": "success", "confidence": 0.95}
    
    # Inject faults multiple times
    results = []
    for i in range(5):
        result = contract.injector.inject_fault(fault_spec, normal_operation, "analyzer")
        results.append(result.fault_injected)
    
    print(f"✓ Fault pattern (5 trials): {results}")
    
    # Verify reproducibility
    contract.injector.reset()
    results2 = []
    for i in range(5):
        result = contract.injector.inject_fault(fault_spec, normal_operation, "analyzer")
        results2.append(result.fault_injected)
    
    reproducible = results == results2
    print(f"✓ Reproducibility: {reproducible}")
    
    verified = contract.verify_contract()
    print(f"✓ Contract verified: {verified}")
    
    return verified and reproducible


def verify_context_immutability_contract():
    """Verify Context Immutability Contract (CIC)"""
    print_section("7. CONTEXT IMMUTABILITY CONTRACT (CIC)")
    
    contract = ContextImmutabilityContract(track_references=True)
    
    # Create immutable context
    data = {
        "plan_id": "municipal_plan_2024",
        "dimension": "D1",
        "questions": ["Q1", "Q2", "Q3"],
        "metadata": {
            "created_by": "system",
            "version": "1.0"
        }
    }
    
    context = contract.create_context("verification_context", data)
    
    print(f"✓ Context created: {context.context_id}")
    print(f"✓ Canonical hash: {context.canonical_hash[:16]}...")
    
    # Verify immutability
    immutable = contract.verify_immutability(context.context_id)
    print(f"✓ Immutability: {immutable}")
    
    # Verify canonical form
    canonical = contract.verify_canonical_form(context.context_id)
    print(f"✓ Canonical form: {canonical}")
    
    # Verify integrity
    integrity = contract.verify_integrity(context.context_id)
    print(f"✓ Integrity: {integrity}")
    
    # Track references
    for i in range(3):
        contract.get_context(context.context_id)
    
    linear = contract.verify_linear_access(context.context_id, max_references=5)
    print(f"✓ Linear access: {linear}")
    
    verified = contract.verify_contract(context.context_id)
    print(f"✓ Contract verified: {verified}")
    
    return verified


def main():
    """Main verification function"""
    print("\n" + "█" * 80)
    print("█" + " " * 78 + "█")
    print("█" + "  CONTRACT VERIFICATION - DEREK-BEACH SYSTEM".center(78) + "█")
    print("█" + " " * 78 + "█")
    print("█" * 80)
    
    results = {
        "Routing Contract (RC)": False,
        "Snapshot Contract (SC)": False,
        "Risk Control Certificates (RCC)": False,
        "Monotonicity Contracts (MCC & BMC)": False,
        "Permutation Invariance (PIC)": False,
        "Fault-Free Contracts (FFC)": False,
        "Context Immutability (CIC)": False,
    }
    
    try:
        results["Routing Contract (RC)"] = verify_routing_contract()
    except Exception as e:
        print(f"✗ Error: {e}")
    
    try:
        results["Snapshot Contract (SC)"] = verify_snapshot_contract()
    except Exception as e:
        print(f"✗ Error: {e}")
    
    try:
        results["Risk Control Certificates (RCC)"] = verify_risk_control_certificates()
    except Exception as e:
        print(f"✗ Error: {e}")
    
    try:
        results["Monotonicity Contracts (MCC & BMC)"] = verify_monotonicity_contracts()
    except Exception as e:
        print(f"✗ Error: {e}")
    
    try:
        results["Permutation Invariance (PIC)"] = verify_permutation_invariance_contract()
    except Exception as e:
        print(f"✗ Error: {e}")
    
    try:
        results["Fault-Free Contracts (FFC)"] = verify_fault_free_contracts()
    except Exception as e:
        print(f"✗ Error: {e}")
    
    try:
        results["Context Immutability (CIC)"] = verify_context_immutability_contract()
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Summary
    print_section("VERIFICATION SUMMARY")
    
    for contract_name, verified in results.items():
        status = "✓ PASS" if verified else "✗ FAIL"
        print(f"{status:8} {contract_name}")
    
    passed = sum(results.values())
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} contracts verified ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 ALL CONTRACTS VERIFIED SUCCESSFULLY! 🎉")
        return 0
    else:
        print(f"\n⚠️  {total - passed} contract(s) failed verification")
        return 1


if __name__ == "__main__":
    sys.exit(main())
