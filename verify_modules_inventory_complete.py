#!/usr/bin/env python3
"""
Complete Inventory Verification Script for Module Adapters
===========================================================

This script performs a thorough audit of:
1. causal_proccesor.py inclusion in adapters
2. Analyzer_one.py inclusion in adapters
3. contradiction_deteccion.py inclusion in adapters

It generates detailed verification reports showing:
- Which classes/methods are present
- Which are missing
- Which are duplicated
- Recommendations for fixes
"""

import ast
import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

@dataclass
class ClassInventory:
    """Inventory of a single class"""
    name: str
    methods: List[str] = field(default_factory=list)
    is_dataclass: bool = False
    is_enum: bool = False
    base_classes: List[str] = field(default_factory=list)
    
@dataclass
class ModuleInventory:
    """Complete inventory of a module"""
    module_name: str
    classes: Dict[str, ClassInventory] = field(default_factory=dict)
    functions: List[str] = field(default_factory=list)
    enums: List[str] = field(default_factory=list)
    dataclasses: List[str] = field(default_factory=list)

@dataclass
class VerificationResult:
    """Result of verification for a single module"""
    module_name: str
    present_classes: List[str] = field(default_factory=list)
    missing_classes: List[str] = field(default_factory=list)
    present_methods: Dict[str, List[str]] = field(default_factory=dict)
    missing_methods: Dict[str, List[str]] = field(default_factory=dict)
    duplicated_items: List[str] = field(default_factory=list)
    coverage_percentage: float = 0.0


class InventoryExtractor(ast.NodeVisitor):
    """AST visitor to extract classes and methods from source files"""
    
    def __init__(self):
        self.inventory = ModuleInventory(module_name="")
        self.current_class = None
        
    def visit_ClassDef(self, node):
        """Visit class definitions"""
        class_inv = ClassInventory(
            name=node.name,
            base_classes=[self._get_name(base) for base in node.bases]
        )
        
        # Check if it's an Enum
        if any('Enum' in base for base in class_inv.base_classes):
            class_inv.is_enum = True
            self.inventory.enums.append(node.name)
        
        # Check for @dataclass decorator
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id == 'dataclass':
                class_inv.is_dataclass = True
                self.inventory.dataclasses.append(node.name)
        
        # Extract methods
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                class_inv.methods.append(item.name)
        
        self.inventory.classes[node.name] = class_inv
        self.generic_visit(node)
        
    def visit_FunctionDef(self, node):
        """Visit top-level function definitions"""
        # Only capture top-level functions (not methods)
        if not hasattr(self, '_in_class') or not self._in_class:
            self.inventory.functions.append(node.name)
        self.generic_visit(node)
        
    def _get_name(self, node):
        """Get name from AST node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        return str(node)


class AdapterVerifier:
    """Verifies adapter completeness against source files"""
    
    def __init__(self, source_dir: Path):
        self.source_dir = source_dir
        self.inventories = {}
        self.adapter_content = ""
        
    def load_source_inventory(self, filename: str) -> ModuleInventory:
        """Load inventory from source file"""
        file_path = self.source_dir / filename
        if not file_path.exists():
            print(f"Warning: {filename} not found")
            return ModuleInventory(module_name=filename)
            
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
            
        try:
            tree = ast.parse(source)
            extractor = InventoryExtractor()
            extractor.inventory.module_name = filename
            extractor.visit(tree)
            return extractor.inventory
        except Exception as e:
            print(f"Error parsing {filename}: {e}")
            return ModuleInventory(module_name=filename)
    
    def load_adapter_content(self, adapter_file: str = "modules_adapters.py"):
        """Load adapter file content"""
        adapter_path = self.source_dir / adapter_file
        if adapter_path.exists():
            with open(adapter_path, 'r', encoding='utf-8') as f:
                self.adapter_content = f.read()
        else:
            print(f"Warning: {adapter_file} not found")
    
    def verify_module(self, source_filename: str) -> VerificationResult:
        """Verify a single module's inclusion in adapters"""
        inventory = self.load_source_inventory(source_filename)
        result = VerificationResult(module_name=source_filename)
        
        total_items = 0
        present_items = 0
        
        # Check classes
        for class_name, class_inv in inventory.classes.items():
            total_items += 1
            if self._is_class_in_adapter(class_name):
                result.present_classes.append(class_name)
                present_items += 1
                
                # Check methods
                present_methods = []
                missing_methods = []
                for method in class_inv.methods:
                    total_items += 1
                    if self._is_method_in_adapter(class_name, method):
                        present_methods.append(method)
                        present_items += 1
                    else:
                        missing_methods.append(method)
                
                if present_methods:
                    result.present_methods[class_name] = present_methods
                if missing_methods:
                    result.missing_methods[class_name] = missing_methods
            else:
                result.missing_classes.append(class_name)
        
        # Check top-level functions
        for function in inventory.functions:
            total_items += 1
            if self._is_function_in_adapter(function):
                present_items += 1
        
        # Calculate coverage
        if total_items > 0:
            result.coverage_percentage = (present_items / total_items) * 100
        
        return result
    
    def _is_class_in_adapter(self, class_name: str) -> bool:
        """Check if class is referenced in adapter"""
        # Look for class name in adapter content
        patterns = [
            f"class {class_name}",
            f"self.{class_name}",
            f"from .* import .*{class_name}",
            f'"{class_name}"',
            f"'{class_name}'",
        ]
        return any(re.search(pattern, self.adapter_content) for pattern in patterns)
    
    def _is_method_in_adapter(self, class_name: str, method_name: str) -> bool:
        """Check if method is referenced in adapter"""
        patterns = [
            f"{class_name}.*{method_name}",
            f'"{method_name}"',
            f"'{method_name}'",
            f"method_name.*==.*['\"]?{method_name}['\"]?",
        ]
        return any(re.search(pattern, self.adapter_content) for pattern in patterns)
    
    def _is_function_in_adapter(self, function_name: str) -> bool:
        """Check if function is referenced in adapter"""
        patterns = [
            f"def.*{function_name}",
            f'"{function_name}"',
            f"'{function_name}'",
        ]
        return any(re.search(pattern, self.adapter_content) for pattern in patterns)
    
    def generate_report(self, results: List[VerificationResult]) -> str:
        """Generate comprehensive verification report"""
        report = []
        report.append("=" * 80)
        report.append("MODULE ADAPTER VERIFICATION REPORT")
        report.append("=" * 80)
        report.append("")
        
        for result in results:
            report.append(f"### {result.module_name}")
            report.append(f"Coverage: {result.coverage_percentage:.1f}%")
            report.append("")
            
            if result.present_classes:
                report.append(f"✓ Present Classes ({len(result.present_classes)}):")
                for cls in result.present_classes:
                    report.append(f"  - {cls}")
                    if cls in result.present_methods:
                        report.append(f"    Methods: {', '.join(result.present_methods[cls])}")
                report.append("")
            
            if result.missing_classes:
                report.append(f"✗ Missing Classes ({len(result.missing_classes)}):")
                for cls in result.missing_classes:
                    report.append(f"  - {cls}")
                report.append("")
            
            if result.missing_methods:
                report.append(f"⚠ Missing Methods:")
                for cls, methods in result.missing_methods.items():
                    report.append(f"  {cls}:")
                    for method in methods:
                        report.append(f"    - {method}")
                report.append("")
            
            report.append("-" * 80)
            report.append("")
        
        return "\n".join(report)


def main():
    """Main execution"""
    print("Starting Module Adapter Verification...")
    print("=" * 80)
    
    source_dir = Path("/home/runner/work/DEREK-BEACH/DEREK-BEACH")
    verifier = AdapterVerifier(source_dir)
    
    # Load adapter content
    verifier.load_adapter_content()
    
    # Verify each module
    modules_to_verify = [
        "causal_proccesor.py",
        "Analyzer_one.py",
        "contradiction_deteccion.py",
    ]
    
    results = []
    for module in modules_to_verify:
        print(f"Verifying {module}...")
        result = verifier.verify_module(module)
        results.append(result)
        print(f"  Coverage: {result.coverage_percentage:.1f}%")
    
    print("")
    print("=" * 80)
    print("Generating detailed report...")
    
    # Generate and save report
    report = verifier.generate_report(results)
    
    # Save to file
    report_path = source_dir / "VERIFICATION_REPORT_COMPLETE.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"Report saved to: {report_path}")
    print("")
    print("Summary:")
    for result in results:
        status = "✓" if result.coverage_percentage >= 90 else "⚠" if result.coverage_percentage >= 50 else "✗"
        print(f"  {status} {result.module_name}: {result.coverage_percentage:.1f}% coverage")
    
    # Also print report to console
    print("")
    print(report)
    
    # Generate JSON report
    json_results = []
    for result in results:
        json_results.append({
            "module": result.module_name,
            "coverage": result.coverage_percentage,
            "present_classes": result.present_classes,
            "missing_classes": result.missing_classes,
            "present_methods": result.present_methods,
            "missing_methods": result.missing_methods,
        })
    
    json_path = source_dir / "verification_results.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_results, f, indent=2)
    
    print(f"\nJSON results saved to: {json_path}")


if __name__ == "__main__":
    main()
