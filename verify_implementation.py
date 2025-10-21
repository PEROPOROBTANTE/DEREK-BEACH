#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Implementation Verification Script
==================================

Verifies that semantic_chunking_policy.py and financiero_viabilidad_tablas.py
have all required classes, methods, enums, dataclasses, and functions as specified.

This script performs static analysis (no model loading) to verify completeness.
"""

import ast
import json
import sys
from pathlib import Path
from typing import Dict, List, Set


class ImplementationVerifier:
    """Verifies implementation completeness"""
    
    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.content = filepath.read_text(encoding='utf-8')
        self.tree = ast.parse(self.content)
        
    def get_classes(self) -> Set[str]:
        """Get all class names"""
        return {
            node.name for node in ast.walk(self.tree)
            if isinstance(node, ast.ClassDef)
        }
    
    def get_methods(self, class_name: str) -> Set[str]:
        """Get all methods for a class (including async)"""
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                return {
                    item.name for item in node.body
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                }
        return set()
    
    def get_functions(self) -> Set[str]:
        """Get all top-level functions"""
        functions = set()
        for node in self.tree.body:
            if isinstance(node, ast.FunctionDef):
                functions.add(node.name)
            elif isinstance(node, ast.AsyncFunctionDef):
                functions.add(node.name)
        return functions
    
    def is_enum(self, class_name: str) -> bool:
        """Check if class is an enum"""
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                return any(
                    'Enum' in (base.id if isinstance(base, ast.Name) else str(base))
                    for base in node.bases
                )
        return False
    
    def is_dataclass(self, class_name: str) -> bool:
        """Check if class is a dataclass"""
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                return any(
                    (isinstance(dec, ast.Name) and dec.id == 'dataclass') or
                    (isinstance(dec, ast.Call) and 
                     isinstance(dec.func, ast.Name) and 
                     dec.func.id == 'dataclass')
                    for dec in node.decorator_list
                )
        return False
    
    def is_exception(self, class_name: str) -> bool:
        """Check if class is an exception"""
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                return any(
                    'Exception' in (base.id if isinstance(base, ast.Name) else str(base))
                    for base in node.bases
                )
        return False


def verify_semantic_chunking():
    """Verify semantic_chunking_policy.py"""
    print("\n" + "=" * 80)
    print("VERIFYING semantic_chunking_policy.py")
    print("=" * 80)
    
    filepath = Path("semantic_chunking_policy.py")
    if not filepath.exists():
        print(f"❌ File not found: {filepath}")
        return False
    
    verifier = ImplementationVerifier(filepath)
    all_passed = True
    
    # Required classes
    required_classes = {
        'BayesianEvidenceIntegrator': [
            '__init__', 'integrate_evidence', '_similarity_to_probability',
            '_compute_reliability_weights', '_null_evidence', 'causal_strength'
        ],
        'SemanticProcessor': [
            '__init__', '_lazy_load', 'chunk_text', '_detect_pdm_structure',
            '_detect_table', '_detect_numerical_data', '_embed_batch', 'embed_single'
        ],
        'PolicyDocumentAnalyzer': [
            '__init__', '_init_dimension_embeddings', 'analyze', '_extract_key_excerpts'
        ]
    }
    
    # Required enums
    required_enums = ['CausalDimension', 'PDMSection']
    
    # Required dataclasses
    required_dataclasses = ['SemanticConfig']
    
    # Required functions
    required_functions = ['main']
    
    # Verify classes and methods
    print("\n📦 Classes and Methods:")
    for class_name, methods in required_classes.items():
        if class_name in verifier.get_classes():
            actual_methods = verifier.get_methods(class_name)
            missing = set(methods) - actual_methods
            if missing:
                print(f"  ❌ {class_name}: Missing methods {missing}")
                all_passed = False
            else:
                print(f"  ✅ {class_name}: All {len(methods)} methods present")
        else:
            print(f"  ❌ {class_name}: Class not found")
            all_passed = False
    
    # Verify enums
    print("\n🔢 Enums:")
    for enum_name in required_enums:
        if enum_name in verifier.get_classes() and verifier.is_enum(enum_name):
            print(f"  ✅ {enum_name}")
        else:
            print(f"  ❌ {enum_name}: Not found or not an enum")
            all_passed = False
    
    # Verify dataclasses
    print("\n📋 Dataclasses:")
    for dc_name in required_dataclasses:
        if dc_name in verifier.get_classes() and verifier.is_dataclass(dc_name):
            print(f"  ✅ {dc_name}")
        else:
            print(f"  ❌ {dc_name}: Not found or not a dataclass")
            all_passed = False
    
    # Verify functions
    print("\n⚙️  Functions:")
    functions = verifier.get_functions()
    for func_name in required_functions:
        if func_name in functions:
            print(f"  ✅ {func_name}")
        else:
            print(f"  ❌ {func_name}: Not found")
            all_passed = False
    
    return all_passed


def verify_financiero_viabilidad():
    """Verify financiero_viabilidad_tablas.py"""
    print("\n" + "=" * 80)
    print("VERIFYING financiero_viabilidad_tablas.py")
    print("=" * 80)
    
    filepath = Path("financiero_viabilidad_tablas.py")
    if not filepath.exists():
        print(f"❌ File not found: {filepath}")
        return False
    
    verifier = ImplementationVerifier(filepath)
    all_passed = True
    
    # Required classes
    required_classes = {
        'ColombianMunicipalContext': [],  # No methods expected
        'PDETMunicipalPlanAnalyzer': [
            '__init__', '_get_spanish_stopwords', 'extract_tables',
            '_clean_dataframe', '_is_likely_header', '_deduplicate_tables',
            '_reconstruct_fragmented_tables', '_classify_tables',
            'analyze_financial_feasibility', '_extract_financial_amounts',
            '_identify_funding_source', '_extract_from_budget_table',
            '_analyze_funding_sources', '_assess_financial_sustainability',
            '_bayesian_risk_inference', '_interpret_risk', '_indicator_to_dict',
            'identify_responsible_entities', '_extract_entities_ner',
            '_extract_entities_syntax', '_classify_entity_type',
            '_extract_from_responsibility_tables', '_consolidate_entities',
            '_score_entity_specificity', 'construct_causal_dag',
            '_identify_causal_nodes', '_find_semantic_mentions',
            '_find_outcome_mentions', '_find_mediator_mentions',
            '_extract_budget_for_pillar', '_identify_causal_edges',
            '_match_text_to_node', '_refine_edge_probabilities', '_break_cycles',
            'estimate_causal_effects', '_estimate_effect_bayesian',
            '_get_prior_effect', '_identify_confounders',
            'generate_counterfactuals', '_simulate_intervention',
            '_generate_scenario_narrative', 'sensitivity_analysis',
            '_compute_e_value', '_compute_robustness_value', '_interpret_sensitivity',
            'calculate_quality_score', '_score_financial_component',
            '_score_indicators', '_score_responsibility_clarity',
            '_score_temporal_consistency', '_score_pdet_alignment',
            '_score_causal_coherence', '_estimate_score_confidence',
            'export_causal_network', 'generate_executive_report',
            '_interpret_overall_quality', '_generate_recommendations',
            'analyze_municipal_plan', '_extract_full_text',
            '_entity_to_dict', '_effect_to_dict', '_scenario_to_dict',
            '_quality_to_dict'
        ]
    }
    
    # Required dataclasses
    required_dataclasses = [
        'CausalNode', 'CausalEdge', 'CausalDAG', 'CausalEffect',
        'CounterfactualScenario', 'ExtractedTable', 'FinancialIndicator',
        'QualityScore', 'ResponsibleEntity'
    ]
    
    # Required exceptions
    required_exceptions = ['PDETAnalysisException']
    
    # Required functions
    required_functions = ['validate_pdf_path', 'setup_logging', 'main_example']
    
    # Verify classes and methods
    print("\n📦 Classes and Methods:")
    total_methods = 0
    for class_name, methods in required_classes.items():
        if class_name in verifier.get_classes():
            if methods:  # Check methods only if expected
                actual_methods = verifier.get_methods(class_name)
                missing = set(methods) - actual_methods
                if missing:
                    print(f"  ❌ {class_name}: Missing methods {missing}")
                    all_passed = False
                else:
                    print(f"  ✅ {class_name}: All {len(methods)} methods present")
                    total_methods += len(methods)
            else:
                print(f"  ✅ {class_name}")
        else:
            print(f"  ❌ {class_name}: Class not found")
            all_passed = False
    
    print(f"\n  📊 Total methods verified: {total_methods}")
    
    # Verify dataclasses
    print("\n📋 Dataclasses:")
    for dc_name in required_dataclasses:
        if dc_name in verifier.get_classes() and verifier.is_dataclass(dc_name):
            print(f"  ✅ {dc_name}")
        else:
            print(f"  ❌ {dc_name}: Not found or not a dataclass")
            all_passed = False
    
    # Verify exceptions
    print("\n⚠️  Exceptions:")
    for exc_name in required_exceptions:
        if exc_name in verifier.get_classes() and verifier.is_exception(exc_name):
            print(f"  ✅ {exc_name}")
        else:
            print(f"  ❌ {exc_name}: Not found or not an exception")
            all_passed = False
    
    # Verify functions
    print("\n⚙️  Functions:")
    functions = verifier.get_functions()
    for func_name in required_functions:
        if func_name in functions:
            print(f"  ✅ {func_name}")
        else:
            print(f"  ❌ {func_name}: Not found")
            all_passed = False
    
    return all_passed


def verify_manifests():
    """Verify manifest files"""
    print("\n" + "=" * 80)
    print("VERIFYING Manifest Files")
    print("=" * 80)
    
    all_passed = True
    
    # Check semantic_chunking manifest
    semantic_manifest = Path("semantic_chunking_policy.manifest.json")
    if semantic_manifest.exists():
        try:
            with open(semantic_manifest) as f:
                data = json.load(f)
            print(f"\n✅ semantic_chunking_policy.manifest.json")
            print(f"   Classes: {len(data.get('classes', {}))}")
            print(f"   Enums: {len(data.get('enums', {}))}")
            print(f"   Dataclasses: {len(data.get('dataclasses', {}))}")
            print(f"   Functions: {len(data.get('functions', {}))}")
        except Exception as e:
            print(f"\n❌ semantic_chunking_policy.manifest.json: {e}")
            all_passed = False
    else:
        print(f"\n❌ semantic_chunking_policy.manifest.json: Not found")
        all_passed = False
    
    # Check financiero manifest
    financiero_manifest = Path("financiero_viabilidad_tablas.manifest.json")
    if financiero_manifest.exists():
        try:
            with open(financiero_manifest) as f:
                data = json.load(f)
            print(f"\n✅ financiero_viabilidad_tablas.manifest.json")
            print(f"   Classes: {len(data.get('classes', {}))}")
            print(f"   Dataclasses: {len(data.get('dataclasses', {}))}")
            print(f"   Exceptions: {len(data.get('exceptions', {}))}")
            print(f"   Functions: {len(data.get('functions', {}))}")
        except Exception as e:
            print(f"\n❌ financiero_viabilidad_tablas.manifest.json: {e}")
            all_passed = False
    else:
        print(f"\n❌ financiero_viabilidad_tablas.manifest.json: Not found")
        all_passed = False
    
    return all_passed


def verify_adapters():
    """Verify adapter files"""
    print("\n" + "=" * 80)
    print("VERIFYING Adapter Files")
    print("=" * 80)
    
    all_passed = True
    
    adapters = [
        "semantic_chunking_adapter.py",
        "financiero_viabilidad_adapter.py"
    ]
    
    for adapter_file in adapters:
        filepath = Path(adapter_file)
        if filepath.exists():
            print(f"\n✅ {adapter_file}")
            # Check for required functions
            content = filepath.read_text()
            if "create_adapter" in content:
                print(f"   ✅ create_adapter() function present")
            else:
                print(f"   ❌ create_adapter() function missing")
                all_passed = False
        else:
            print(f"\n❌ {adapter_file}: Not found")
            all_passed = False
    
    return all_passed


def main():
    """Main verification"""
    print("\n" + "=" * 80)
    print("IMPLEMENTATION VERIFICATION")
    print("=" * 80)
    print("\nVerifying complete implementation of:")
    print("  - semantic_chunking_policy.py")
    print("  - financiero_viabilidad_tablas.py")
    print("  - Integration adapters")
    print("  - Manifest files")
    print("  - Documentation")
    
    results = []
    
    # Verify implementations
    results.append(("semantic_chunking_policy.py", verify_semantic_chunking()))
    results.append(("financiero_viabilidad_tablas.py", verify_financiero_viabilidad()))
    results.append(("Manifest files", verify_manifests()))
    results.append(("Adapter files", verify_adapters()))
    
    # Check documentation
    print("\n" + "=" * 80)
    print("VERIFYING Documentation")
    print("=" * 80)
    
    docs = [
        "SEMANTIC_CHUNKING_README.md",
        "defects_report.md",
    ]
    
    docs_passed = True
    for doc in docs:
        filepath = Path(doc)
        if filepath.exists():
            size = filepath.stat().st_size
            print(f"\n✅ {doc} ({size:,} bytes)")
        else:
            print(f"\n❌ {doc}: Not found")
            docs_passed = False
    
    results.append(("Documentation", docs_passed))
    
    # Final summary
    print("\n" + "=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"\n{status}: {name}")
    
    all_passed = all(passed for _, passed in results)
    
    if all_passed:
        print("\n" + "=" * 80)
        print("🎉 ALL VERIFICATION CHECKS PASSED")
        print("=" * 80)
        print("\nImplementation is COMPLETE and VERIFIED!")
        return 0
    else:
        print("\n" + "=" * 80)
        print("❌ SOME VERIFICATION CHECKS FAILED")
        print("=" * 80)
        print("\nPlease review the failures above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
