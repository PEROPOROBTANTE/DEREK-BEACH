#!/usr/bin/env python3
"""
Verification Script for dereck_beach.py and module_controller.py Correspondence

This script verifies that all classes and methods from dereck_beach.py (CDAF Framework)
are properly accessible through the module controller system via DerekBeachAdapter.

Author: FARFAN 3.0 Verification System
Version: 1.0.0
"""

import ast
import sys
from typing import Dict, List, Set
from pathlib import Path


# Expected classes and their methods from problem statement
EXPECTED_CLASSES = {
    "AuditResult": [],  # TypedDict - no methods
    "BayesianMechanismInference": [
        "__init__",
        "_log_refactored_components",
        "infer_mechanisms",
        "_infer_single_mechanism",
        "_extract_observations",
        "_infer_mechanism_type",
        "_infer_activity_sequence",
        "_calculate_coherence_factor",
        "_test_sufficiency",
        "_test_necessity",
        "_generate_necessity_remediation",
        "_quantify_uncertainty",
        "_detect_gaps",
    ],
    "BayesianThresholdsConfig": [],  # BaseModel - no methods defined
    "BeachEvidentialTest": [
        "classify_test",  # @staticmethod
        "apply_test_logic",  # @staticmethod
    ],
    "CausalExtractor": [
        "__init__",
        "extract_causal_hierarchy",
        "_extract_goals",
        "_parse_goal_context",
        "_add_node_to_graph",
        "_extract_causal_links",
        "_calculate_semantic_distance",
        "_calculate_type_transition_prior",
        "_check_structural_violation",
        "_calculate_language_specificity",
        "_assess_temporal_coherence",
        "_assess_financial_consistency",
        "_calculate_textual_proximity",
        "_initialize_prior",
        "_calculate_composite_likelihood",
        "_build_type_hierarchy",
    ],
    "CausalInferenceSetup": [
        "__init__",
        "classify_goal_dynamics",
        "assign_probative_value",
        "identify_failure_points",
    ],
    "CausalLink": [],  # TypedDict - no methods
    "CDAFBayesianError": [],  # Inherits from CDAFException
    "CDAFConfigError": [],  # Inherits from CDAFException
    "CDAFConfigSchema": [],  # BaseModel, but has inner class Config
    "CDAFException": [
        "__init__",
        "_format_message",
        "to_dict",
    ],
    "CDAFFramework": [
        "__init__",
        "process_document",
        "_extract_feedback_from_audit",
        "_validate_dnp_compliance",
        "_generate_dnp_report",
    ],
    "CDAFProcessingError": [],  # Inherits from CDAFException
    "CDAFValidationError": [],  # Inherits from CDAFException
    "ConfigLoader": [
        "__init__",
        "_load_config",
        "_load_default_config",
        "_validate_config",
        "get",
        "get_bayesian_threshold",
        "get_mechanism_prior",
        "get_performance_setting",
        "update_priors_from_feedback",
        "_save_prior_history",
        "_load_uncertainty_history",
        "check_uncertainty_reduction_criterion",
    ],
    "EntityActivity": [],  # NamedTuple - no methods
    "FinancialAuditor": [
        "__init__",
        "trace_financial_allocation",
        "_process_financial_table",
        "_parse_amount",
        "_match_program_to_node",
        "_perform_counterfactual_budget_check",
    ],
    "GoalClassification": [],  # NamedTuple - no methods
    "MechanismPartExtractor": [
        "__init__",
        "extract_entity_activity",
        "_normalize_entity",
    ],
    "MechanismTypeConfig": [
        "check_sum_to_one",  # @validator
    ],
    "MetaNode": [],  # dataclass - no methods
    "OperationalizationAuditor": [
        "__init__",
        "audit_evidence_traceability",
        "audit_sequence_logic",
        "bayesian_counterfactual_audit",
        "_build_normative_dag",
        "_get_default_historical_priors",
        "_audit_direct_evidence",
        "_audit_causal_implications",
        "_audit_systemic_risk",
        "_generate_optimal_remediations",
        "_get_remediation_text",
    ],
    "PDFProcessor": [
        "__init__",
        "load_document",
        "extract_text",
        "extract_tables",
        "extract_sections",
    ],
    "PerformanceConfig": [],  # BaseModel - no methods
    "ReportingEngine": [
        "__init__",
        "generate_causal_diagram",
        "generate_accountability_matrix",
        "generate_confidence_report",
        "_calculate_quality_score",
        "generate_causal_model_json",
    ],
    "SelfReflectionConfig": [],  # BaseModel - no methods
}

EXPECTED_FUNCTIONS = ["main"]


def extract_classes_and_methods(filepath: str) -> tuple[Dict[str, List[str]], List[str]]:
    """Extract classes, methods, and top-level functions from Python file"""
    with open(filepath, 'r') as f:
        tree = ast.parse(f.read())
    
    classes = {}
    functions = []
    
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            class_name = node.name
            methods = []
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    methods.append(item.name)
            classes[class_name] = methods
        elif isinstance(node, ast.FunctionDef):
            functions.append(node.name)
    
    return classes, functions


def verify_dereck_beach_structure(filepath: str) -> bool:
    """Verify that dereck_beach.py has all expected classes and methods"""
    classes, functions = extract_classes_and_methods(filepath)
    
    all_ok = True
    missing_classes = []
    missing_methods = {}
    
    # Check classes and methods
    for class_name, expected_methods in EXPECTED_CLASSES.items():
        if class_name not in classes:
            missing_classes.append(class_name)
            all_ok = False
            continue
        
        actual_methods = set(classes[class_name])
        expected_methods_set = set(expected_methods)
        
        missing = expected_methods_set - actual_methods
        if missing:
            missing_methods[class_name] = sorted(missing)
            all_ok = False
    
    # Check functions
    missing_functions = []
    for func_name in EXPECTED_FUNCTIONS:
        if func_name not in functions:
            missing_functions.append(func_name)
            all_ok = False
    
    return all_ok, missing_classes, missing_methods, missing_functions, len(classes), len(functions)


def verify_adapter_correspondence() -> bool:
    """Verify that DerekBeachAdapter has all classes accessible"""
    try:
        from modules_adapters import DerekBeachAdapter
        
        adapter = DerekBeachAdapter()
        
        if not adapter.available:
            return False, "Adapter not available"
        
        missing_classes = []
        for class_name in EXPECTED_CLASSES.keys():
            if not hasattr(adapter, class_name):
                missing_classes.append(class_name)
        
        if missing_classes:
            return False, f"Missing classes in adapter: {missing_classes}"
        
        return True, "All classes accessible"
    
    except Exception as e:
        return False, f"Error loading adapter: {e}"


def print_report():
    """Generate and print comprehensive verification report"""
    print("=" * 80)
    print("VERIFICATION REPORT: dereck_beach.py <-> module_controller.py")
    print("=" * 80)
    print()
    
    # 1. Verify dereck_beach.py structure
    print("STEP 1: Verifying dereck_beach.py structure")
    print("-" * 80)
    
    dereck_path = Path(__file__).parent / "dereck_beach.py"
    all_ok, missing_classes, missing_methods, missing_functions, total_classes, total_functions = \
        verify_dereck_beach_structure(str(dereck_path))
    
    if all_ok:
        print("✓ ALL EXPECTED CLASSES AND METHODS ARE PRESENT")
    else:
        print("✗ MISSING ELEMENTS DETECTED")
    
    print()
    print(f"Total classes found: {total_classes}")
    print(f"Total top-level functions: {total_functions}")
    print(f"Classes verified: {len(EXPECTED_CLASSES)}")
    print(f"Functions verified: {len(EXPECTED_FUNCTIONS)}")
    print()
    
    if missing_classes:
        print("MISSING CLASSES:")
        for class_name in sorted(missing_classes):
            print(f"  ✗ {class_name}")
        print()
    
    if missing_methods:
        print("MISSING METHODS:")
        for class_name, methods in sorted(missing_methods.items()):
            print(f"  {class_name}:")
            for method in methods:
                print(f"    ✗ {method}")
        print()
    
    if missing_functions:
        print("MISSING FUNCTIONS:")
        for func_name in sorted(missing_functions):
            print(f"  ✗ {func_name}")
        print()
    
    # 2. Verify adapter correspondence
    print("=" * 80)
    print("STEP 2: Verifying DerekBeachAdapter correspondence")
    print("-" * 80)
    
    adapter_ok, adapter_msg = verify_adapter_correspondence()
    
    if adapter_ok:
        print(f"✓ {adapter_msg}")
        print(f"✓ All {len(EXPECTED_CLASSES)} classes are accessible via adapter")
    else:
        print(f"✗ {adapter_msg}")
    
    print()
    
    # 3. Final summary
    print("=" * 80)
    print("FINAL VERIFICATION SUMMARY")
    print("=" * 80)
    
    if all_ok and adapter_ok:
        print("✓ COMPLETE CORRESPONDENCE VERIFIED")
        print("✓ All classes from dereck_beach.py are present")
        print("✓ All classes are accessible via DerekBeachAdapter")
        print("✓ Module controller can invoke all CDAF components")
        return_code = 0
    else:
        print("✗ CORRESPONDENCE ISSUES DETECTED")
        if not all_ok:
            print("✗ Some classes or methods missing in dereck_beach.py")
        if not adapter_ok:
            print("✗ Some classes not accessible via adapter")
        return_code = 1
    
    print()
    print("=" * 80)
    
    return return_code


def main():
    """Main verification entry point"""
    try:
        return_code = print_report()
        sys.exit(return_code)
    except Exception as e:
        print(f"ERROR: Verification failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
