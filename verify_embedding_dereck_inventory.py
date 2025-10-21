#!/usr/bin/env python3
"""
Verification Script for embedding_policy.py and dereck_beach.py Integration
===========================================================================

This script verifies that modules_adapters.py contains ALL required classes and methods
from embedding_policy.py and dereck_beach.py according to the problem statement specification.

Success Criteria: Script passes only after achieving >= 97% aggregation
"""

import ast
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


def extract_inventory_from_file(filepath: str) -> Dict[str, List[str]]:
    """Extract classes and their methods from a Python file"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    tree = ast.parse(content)
    classes = {}
    functions = []
    
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            methods = []
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    methods.append(item.name)
            classes[node.name] = methods
        elif isinstance(node, ast.FunctionDef):
            functions.append(node.name)
    
    return {"classes": classes, "functions": functions}


def check_adapter_has_methods(adapter_file: str, source_inventory: Dict) -> Tuple[int, int, List[str]]:
    """
    Check if adapter file contains references to all classes and methods from source
    
    Returns: (found_count, total_count, missing_items)
    """
    with open(adapter_file, 'r') as f:
        adapter_content = f.read()
    
    total_items = 0
    found_items = 0
    missing_items = []
    
    # Check classes and their methods
    for class_name, methods in source_inventory["classes"].items():
        total_items += 1  # Count the class itself
        
        # Check if class is mentioned in adapter
        if class_name in adapter_content:
            found_items += 1
        else:
            missing_items.append(f"Class: {class_name}")
        
        # Check methods
        for method in methods:
            total_items += 1
            # Look for method name in adapter (as string or in documentation)
            if f'"{method}"' in adapter_content or f"'{method}'" in adapter_content or f"def {method}" in adapter_content:
                found_items += 1
            else:
                missing_items.append(f"  Method: {class_name}.{method}")
    
    # Check top-level functions
    for func in source_inventory["functions"]:
        total_items += 1
        if f'"{func}"' in adapter_content or f"'{func}'" in adapter_content or f"def {func}" in adapter_content:
            found_items += 1
        else:
            missing_items.append(f"Function: {func}")
    
    return found_items, total_items, missing_items


def generate_matching_report():
    """Generate comprehensive matching report contrasting inventories"""
    print("=" * 100)
    print("EMBEDDING_POLICY.PY AND DERECK_BEACH.PY INVENTORY VERIFICATION REPORT")
    print("=" * 100)
    print()
    
    # Extract inventories
    embedding_inventory = extract_inventory_from_file("embedding_policy.py")
    dereck_inventory = extract_inventory_from_file("dereck_beach.py")
    
    # Print source inventories
    print("SOURCE INVENTORY - embedding_policy.py")
    print("-" * 100)
    print(f"Total Classes: {len(embedding_inventory['classes'])}")
    print(f"Total Top-Level Functions: {len(embedding_inventory['functions'])}")
    
    total_embedding_methods = sum(len(methods) for methods in embedding_inventory['classes'].values())
    print(f"Total Methods: {total_embedding_methods}")
    print()
    
    print("Classes:")
    for cls_name, methods in sorted(embedding_inventory['classes'].items()):
        print(f"  {cls_name} ({len(methods)} methods)")
        for method in methods:
            print(f"    - {method}")
    
    print("\nTop-Level Functions:")
    for func in embedding_inventory['functions']:
        print(f"  - {func}")
    
    print()
    print("=" * 100)
    print("SOURCE INVENTORY - dereck_beach.py")
    print("-" * 100)
    print(f"Total Classes: {len(dereck_inventory['classes'])}")
    print(f"Total Top-Level Functions: {len(dereck_inventory['functions'])}")
    
    total_dereck_methods = sum(len(methods) for methods in dereck_inventory['classes'].values())
    print(f"Total Methods: {total_dereck_methods}")
    print()
    
    print("Classes:")
    for cls_name, methods in sorted(dereck_inventory['classes'].items()):
        print(f"  {cls_name} ({len(methods)} methods)")
        for method in methods:
            print(f"    - {method}")
    
    print("\nTop-Level Functions:")
    for func in dereck_inventory['functions']:
        print(f"  - {func}")
    
    print()
    print("=" * 100)
    print("AGGREGATION VERIFICATION - modules_adapters.py")
    print("=" * 100)
    
    # Check embedding_policy aggregation
    embed_found, embed_total, embed_missing = check_adapter_has_methods(
        "modules_adapters.py", embedding_inventory
    )
    embed_percentage = (embed_found / embed_total * 100) if embed_total > 0 else 0
    
    print(f"\nembedding_policy.py Aggregation:")
    print(f"  Found: {embed_found}/{embed_total} items ({embed_percentage:.2f}%)")
    if embed_missing:
        print(f"  Missing {len(embed_missing)} items:")
        for item in embed_missing[:10]:  # Show first 10
            print(f"    - {item}")
        if len(embed_missing) > 10:
            print(f"    ... and {len(embed_missing) - 10} more")
    
    # Check dereck_beach aggregation
    dereck_found, dereck_total, dereck_missing = check_adapter_has_methods(
        "modules_adapters.py", dereck_inventory
    )
    dereck_percentage = (dereck_found / dereck_total * 100) if dereck_total > 0 else 0
    
    print(f"\ndereck_beach.py Aggregation:")
    print(f"  Found: {dereck_found}/{dereck_total} items ({dereck_percentage:.2f}%)")
    if dereck_missing:
        print(f"  Missing {len(dereck_missing)} items:")
        for item in dereck_missing[:10]:  # Show first 10
            print(f"    - {item}")
        if len(dereck_missing) > 10:
            print(f"    ... and {len(dereck_missing) - 10} more")
    
    # Calculate overall aggregation
    total_found = embed_found + dereck_found
    total_items = embed_total + dereck_total
    overall_percentage = (total_found / total_items * 100) if total_items > 0 else 0
    
    print()
    print("=" * 100)
    print("OVERALL AGGREGATION RESULT")
    print("=" * 100)
    print(f"Total Items Found: {total_found}/{total_items}")
    print(f"Overall Aggregation: {overall_percentage:.2f}%")
    print(f"Required Threshold: 97.00%")
    print()
    
    # Pass/Fail determination
    if overall_percentage >= 97.0:
        print("✅ VERIFICATION PASSED - Aggregation >= 97%")
        print("=" * 100)
        return 0
    else:
        print(f"❌ VERIFICATION FAILED - Aggregation {overall_percentage:.2f}% < 97%")
        print(f"   Need to add {total_items - total_found} more items")
        print("=" * 100)
        return 1


def main():
    """Main entry point"""
    try:
        exit_code = generate_matching_report()
        sys.exit(exit_code)
    except FileNotFoundError as e:
        print(f"ERROR: Required file not found: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Verification failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
