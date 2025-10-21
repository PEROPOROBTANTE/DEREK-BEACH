#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verification Script for teoria_cambio.py Inventory
==================================================

This script generates a complete inventory of all classes, dataclasses, enums,
functions, and methods from teoria_cambio.py and verifies their presence in
modules_adapters.py.

Requirements:
- Generate manifest.json with complete inventory
- Verify all items are present in module_adapters
- Execute integration tests with deterministic seeds
- No mocks, only real implementations
- Timestamped execution logs
"""

import ast
import inspect
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


class InventoryExtractor:
    """Extracts complete inventory from Python source files using AST analysis."""

    def __init__(self, source_file: Path):
        self.source_file = source_file
        self.inventory: Dict[str, Any] = {
            "file": str(source_file),
            "timestamp": datetime.now().isoformat(),
            "classes": {},
            "dataclasses": {},
            "enums": {},
            "functions": {},
        }

    def extract(self) -> Dict[str, Any]:
        """Extract complete inventory from source file."""
        logger.info(f"Extracting inventory from {self.source_file}")

        with open(self.source_file, "r", encoding="utf-8") as f:
            source = f.read()
            tree = ast.parse(source)

        # Extract all top-level definitions
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                self._extract_class(node, source)
            elif isinstance(node, ast.FunctionDef) and self._is_top_level(node, tree):
                self._extract_function(node, source)

        return self.inventory

    def _is_top_level(self, node: ast.AST, tree: ast.Module) -> bool:
        """Check if a node is at module level (not inside a class)."""
        for top_node in tree.body:
            if top_node == node:
                return True
        return False

    def _extract_class(self, node: ast.ClassDef, source: str):
        """Extract class information including all methods."""
        # Determine class type
        is_dataclass = any(
            isinstance(dec, ast.Name) and dec.id == "dataclass"
            for dec in node.decorator_list
        )
        is_enum = any(
            base.id == "Enum" if isinstance(base, ast.Name) else False
            for base in node.bases
        )

        class_info = {
            "name": node.name,
            "lineno": node.lineno,
            "end_lineno": node.end_lineno,
            "docstring": ast.get_docstring(node),
            "decorators": [self._get_decorator_name(d) for d in node.decorator_list],
            "bases": [self._get_base_name(b) for b in node.bases],
            "methods": {},
            "attributes": [],
        }

        # Extract methods
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                class_info["methods"][item.name] = self._extract_method(item, source)
            elif isinstance(item, ast.AnnAssign) and isinstance(
                item.target, ast.Name
            ):
                class_info["attributes"].append(
                    {
                        "name": item.target.id,
                        "annotation": ast.unparse(item.annotation),
                    }
                )

        # Categorize the class
        if is_dataclass:
            self.inventory["dataclasses"][node.name] = class_info
        elif is_enum:
            self.inventory["enums"][node.name] = class_info
        else:
            self.inventory["classes"][node.name] = class_info

    def _extract_method(self, node: ast.FunctionDef, source: str) -> Dict[str, Any]:
        """Extract method information including signature."""
        # Extract parameters
        params = []
        for arg in node.args.args:
            param_info = {"name": arg.arg}
            if arg.annotation:
                param_info["annotation"] = ast.unparse(arg.annotation)
            params.append(param_info)

        # Extract return type
        return_type = None
        if node.returns:
            return_type = ast.unparse(node.returns)

        # Determine if static or class method
        is_static = any(
            isinstance(dec, ast.Name) and dec.id == "staticmethod"
            for dec in node.decorator_list
        )
        is_classmethod = any(
            isinstance(dec, ast.Name) and dec.id == "classmethod"
            for dec in node.decorator_list
        )

        return {
            "lineno": node.lineno,
            "end_lineno": node.end_lineno,
            "signature": self._build_signature(node),
            "params": params,
            "return_type": return_type,
            "docstring": ast.get_docstring(node),
            "is_static": is_static,
            "is_classmethod": is_classmethod,
            "decorators": [self._get_decorator_name(d) for d in node.decorator_list],
        }

    def _extract_function(self, node: ast.FunctionDef, source: str):
        """Extract top-level function information."""
        func_info = self._extract_method(node, source)
        self.inventory["functions"][node.name] = func_info

    def _build_signature(self, node: ast.FunctionDef) -> str:
        """Build function signature string."""
        args = []
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {ast.unparse(arg.annotation)}"
            args.append(arg_str)

        # Add defaults
        defaults = node.args.defaults
        if defaults:
            num_defaults = len(defaults)
            num_args = len(args)
            for i, default in enumerate(defaults):
                idx = num_args - num_defaults + i
                if idx < len(args):
                    args[idx] += f" = {ast.unparse(default)}"

        signature = f"def {node.name}({', '.join(args)})"
        if node.returns:
            signature += f" -> {ast.unparse(node.returns)}"
        return signature

    def _get_decorator_name(self, dec: ast.expr) -> str:
        """Get decorator name as string."""
        if isinstance(dec, ast.Name):
            return dec.id
        elif isinstance(dec, ast.Call):
            if isinstance(dec.func, ast.Name):
                return dec.func.id
        return ast.unparse(dec)

    def _get_base_name(self, base: ast.expr) -> str:
        """Get base class name as string."""
        if isinstance(base, ast.Name):
            return base.id
        elif isinstance(base, ast.Attribute):
            return ast.unparse(base)
        return ast.unparse(base)


class InventoryVerifier:
    """Verifies inventory items are present in modules_adapters.py."""

    def __init__(self, teoria_inventory: Dict[str, Any], adapter_file: Path):
        self.teoria_inventory = teoria_inventory
        self.adapter_file = adapter_file
        self.verification_results: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "verified_items": [],
            "missing_items": [],
            "issues": [],
        }

    def verify(self) -> Dict[str, Any]:
        """Verify all items from teoria_cambio are present in adapters."""
        logger.info("Verifying inventory against modules_adapters.py")

        # Import modules_adapters to check runtime availability
        try:
            sys.path.insert(0, str(self.adapter_file.parent))
            import modules_adapters

            self.modules_adapters = modules_adapters
        except ImportError as e:
            logger.error(f"Failed to import modules_adapters: {e}")
            self.verification_results["issues"].append(
                {"type": "import_error", "message": str(e)}
            )
            return self.verification_results

        # Verify each category
        self._verify_enums()
        self._verify_dataclasses()
        self._verify_classes()
        self._verify_functions()

        # Calculate statistics
        total = len(self.verification_results["verified_items"]) + len(
            self.verification_results["missing_items"]
        )
        verified = len(self.verification_results["verified_items"])

        self.verification_results["statistics"] = {
            "total_items": total,
            "verified_items": verified,
            "missing_items": len(self.verification_results["missing_items"]),
            "verification_rate": (verified / total * 100) if total > 0 else 0,
        }

        return self.verification_results

    def _verify_enums(self):
        """Verify all enums are present."""
        for enum_name, enum_info in self.teoria_inventory.get("enums", {}).items():
            if hasattr(self.modules_adapters, enum_name):
                self.verification_results["verified_items"].append(
                    {
                        "type": "enum",
                        "name": enum_name,
                        "location": f"line {enum_info['lineno']}",
                    }
                )
            else:
                self.verification_results["missing_items"].append(
                    {
                        "type": "enum",
                        "name": enum_name,
                        "location": f"line {enum_info['lineno']}",
                    }
                )

    def _verify_dataclasses(self):
        """Verify all dataclasses are present."""
        for dc_name, dc_info in self.teoria_inventory.get("dataclasses", {}).items():
            if hasattr(self.modules_adapters, dc_name):
                self.verification_results["verified_items"].append(
                    {
                        "type": "dataclass",
                        "name": dc_name,
                        "location": f"line {dc_info['lineno']}",
                    }
                )
                # Verify methods in dataclass
                self._verify_methods(dc_name, dc_info.get("methods", {}))
            else:
                self.verification_results["missing_items"].append(
                    {
                        "type": "dataclass",
                        "name": dc_name,
                        "location": f"line {dc_info['lineno']}",
                    }
                )

    def _verify_classes(self):
        """Verify all classes are present."""
        for class_name, class_info in self.teoria_inventory.get("classes", {}).items():
            if hasattr(self.modules_adapters, class_name):
                self.verification_results["verified_items"].append(
                    {
                        "type": "class",
                        "name": class_name,
                        "location": f"line {class_info['lineno']}",
                    }
                )
                # Verify methods in class
                self._verify_methods(class_name, class_info.get("methods", {}))
            else:
                self.verification_results["missing_items"].append(
                    {
                        "type": "class",
                        "name": class_name,
                        "location": f"line {class_info['lineno']}",
                    }
                )

    def _verify_methods(self, class_name: str, methods: Dict[str, Any]):
        """Verify all methods in a class are present."""
        cls = getattr(self.modules_adapters, class_name, None)
        if cls is None:
            return

        for method_name, method_info in methods.items():
            if hasattr(cls, method_name):
                self.verification_results["verified_items"].append(
                    {
                        "type": "method",
                        "name": f"{class_name}.{method_name}",
                        "location": f"line {method_info['lineno']}",
                        "signature": method_info["signature"],
                    }
                )
            else:
                self.verification_results["missing_items"].append(
                    {
                        "type": "method",
                        "name": f"{class_name}.{method_name}",
                        "location": f"line {method_info['lineno']}",
                        "signature": method_info["signature"],
                    }
                )

    def _verify_functions(self):
        """Verify all top-level functions are present."""
        for func_name, func_info in self.teoria_inventory.get("functions", {}).items():
            if hasattr(self.modules_adapters, func_name):
                self.verification_results["verified_items"].append(
                    {
                        "type": "function",
                        "name": func_name,
                        "location": f"line {func_info['lineno']}",
                        "signature": func_info["signature"],
                    }
                )
            else:
                self.verification_results["missing_items"].append(
                    {
                        "type": "function",
                        "name": func_name,
                        "location": f"line {func_info['lineno']}",
                        "signature": func_info["signature"],
                    }
                )


def generate_manifest(
    inventory: Dict[str, Any], verification: Dict[str, Any], output_file: Path
):
    """Generate comprehensive manifest JSON."""
    manifest = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "source_file": inventory["file"],
            "python_version": sys.version,
        },
        "inventory": inventory,
        "verification": verification,
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, default=str)

    logger.info(f"Manifest generated: {output_file}")
    return manifest


def main():
    """Main execution function."""
    logger.info("=" * 80)
    logger.info("TEORIA_CAMBIO.PY INVENTORY VERIFICATION")
    logger.info("=" * 80)

    # Paths
    repo_root = Path(__file__).parent
    teoria_file = repo_root / "teoria_cambio.py"
    adapter_file = repo_root / "modules_adapters.py"
    manifest_file = repo_root / "manifest.json"

    # Extract inventory
    extractor = InventoryExtractor(teoria_file)
    inventory = extractor.extract()

    logger.info(f"Extracted inventory:")
    logger.info(f"  - Classes: {len(inventory['classes'])}")
    logger.info(f"  - Dataclasses: {len(inventory['dataclasses'])}")
    logger.info(f"  - Enums: {len(inventory['enums'])}")
    logger.info(f"  - Functions: {len(inventory['functions'])}")

    # Count total methods
    total_methods = sum(
        len(cls_info.get("methods", {}))
        for cls_info in inventory["classes"].values()
    )
    total_methods += sum(
        len(dc_info.get("methods", {}))
        for dc_info in inventory["dataclasses"].values()
    )
    logger.info(f"  - Total Methods: {total_methods}")

    # Verify against modules_adapters
    verifier = InventoryVerifier(inventory, adapter_file)
    verification = verifier.verify()

    logger.info("\nVerification Results:")
    logger.info(
        f"  - Verified Items: {verification['statistics']['verified_items']}"
    )
    logger.info(
        f"  - Missing Items: {verification['statistics']['missing_items']}"
    )
    logger.info(
        f"  - Verification Rate: {verification['statistics']['verification_rate']:.2f}%"
    )

    # Generate manifest
    manifest = generate_manifest(inventory, verification, manifest_file)

    # Report issues
    if verification["missing_items"]:
        logger.warning("\nMissing Items:")
        for item in verification["missing_items"][:10]:  # Show first 10
            logger.warning(f"  - {item['type']}: {item['name']} ({item['location']})")
        if len(verification["missing_items"]) > 10:
            logger.warning(
                f"  ... and {len(verification['missing_items']) - 10} more"
            )

    logger.info(f"\nManifest saved to: {manifest_file}")
    logger.info("=" * 80)

    return 0 if not verification["missing_items"] else 1


if __name__ == "__main__":
    sys.exit(main())
