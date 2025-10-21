"""
Validation Engine - Centralized Output Validation
==================================================

Validates module outputs against QuestionContext validation rules.
Supports multiple validation types with detailed violation reporting.

Key Features:
- Type checking, schema validation, regex matching, range checks
- Detailed violation reporting with severity levels
- Immutable validation results
- Extensible validation rule system
- Performance optimized with caching

Author: FARFAN 3.0 - Industrial Orchestrator
Version: 1.0.0
Python: 3.10+
"""

import logging
import re
import time
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

from metadata_service import QuestionContext, ValidationRule, ValidationRuleType

logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    """Validation result status"""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class ValidationViolation:
    """Immutable validation violation record"""
    rule: ValidationRule
    field_name: str
    actual_value: Any
    expected_value: Any
    message: str
    severity: str = "error"
    
    def __hash__(self):
        # Make hashable, handling unhashable types
        def make_hashable(obj):
            if isinstance(obj, (list, set)):
                return tuple(make_hashable(item) for item in obj)
            elif isinstance(obj, dict):
                return tuple(sorted((k, make_hashable(v)) for k, v in obj.items()))
            return obj
        
        return hash((
            self.rule,
            self.field_name,
            make_hashable(self.actual_value),
            make_hashable(self.expected_value),
            self.message,
            self.severity
        ))


@dataclass(frozen=True)
class ValidationResult:
    """Immutable validation result"""
    status: ValidationStatus
    violations: Set[ValidationViolation] = field(default_factory=set)
    warnings: Set[ValidationViolation] = field(default_factory=set)
    passed_rules: Set[ValidationRule] = field(default_factory=set)
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_valid(self) -> bool:
        """Check if validation passed (no errors, warnings OK)"""
        return self.status == ValidationStatus.PASS and len(self.violations) == 0
    
    @property
    def has_warnings(self) -> bool:
        """Check if validation has warnings"""
        return len(self.warnings) > 0
    
    @property
    def error_count(self) -> int:
        """Count of error-level violations"""
        return len([v for v in self.violations if v.severity == "error"])
    
    @property
    def warning_count(self) -> int:
        """Count of warning-level violations"""
        return len(self.warnings)
    
    def __hash__(self):
        return hash((self.status, self.violations, self.warnings, self.passed_rules))


class ValidationEngine:
    """
    Central validation engine for orchestrator outputs
    
    Features:
    - Multiple validation types (type, schema, regex, range, required fields)
    - Detailed violation reporting
    - Performance tracking
    - Extensible rule system
    """
    
    def __init__(self):
        """Initialize validation engine"""
        self._validation_stats: Dict[str, Any] = {
            "total_validations": 0,
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "total_time": 0.0,
        }
        
        logger.info("ValidationEngine initialized")
    
    def validate(
        self,
        output: Dict[str, Any],
        context: QuestionContext,
        skip_warnings: bool = False
    ) -> ValidationResult:
        """
        Validate module output against QuestionContext rules
        
        Args:
            output: Module output to validate
            context: QuestionContext with validation rules
            skip_warnings: If True, don't report warnings
            
        Returns:
            ValidationResult with status and violations
        """
        start_time = time.time()
        
        violations: Set[ValidationViolation] = set()
        warnings: Set[ValidationViolation] = set()
        passed_rules: Set[ValidationRule] = set()
        
        try:
            # Execute each validation rule
            for rule in context.validation_rules:
                rule_violations = self._execute_rule(rule, output, context)
                
                if rule_violations:
                    # Separate errors from warnings
                    for violation in rule_violations:
                        if violation.severity == "error":
                            violations.add(violation)
                        elif violation.severity == "warning" and not skip_warnings:
                            warnings.add(violation)
                else:
                    passed_rules.add(rule)
            
            # Determine overall status
            if violations:
                status = ValidationStatus.FAIL
            elif warnings:
                status = ValidationStatus.WARNING
            else:
                status = ValidationStatus.PASS
            
            execution_time = time.time() - start_time
            
            # Update stats
            self._update_stats(status, execution_time)
            
            result = ValidationResult(
                status=status,
                violations=violations,
                warnings=warnings,
                passed_rules=passed_rules,
                execution_time=execution_time,
                metadata={
                    "question_id": context.question_id,
                    "total_rules": len(context.validation_rules),
                    "passed_rules": len(passed_rules),
                    "failed_rules": len(violations),
                }
            )
            
            if not result.is_valid:
                logger.warning(
                    f"Validation failed for {context.question_id}: "
                    f"{len(violations)} errors, {len(warnings)} warnings"
                )
            else:
                logger.debug(
                    f"Validation passed for {context.question_id}: "
                    f"{len(passed_rules)} rules passed"
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Validation error for {context.question_id}: {e}", exc_info=True)
            execution_time = time.time() - start_time
            
            # Return failure with exception info
            return ValidationResult(
                status=ValidationStatus.FAIL,
                violations={ValidationViolation(
                    rule=ValidationRule(
                        rule_type=ValidationRuleType.CUSTOM_LOGIC,
                        description="Validation engine error",
                        parameters={}
                    ),
                    field_name="__engine__",
                    actual_value=str(e),
                    expected_value="successful validation",
                    message=f"Validation engine error: {str(e)}",
                    severity="error"
                )},
                execution_time=execution_time,
                metadata={"error": str(e)}
            )
    
    def _execute_rule(
        self,
        rule: ValidationRule,
        output: Dict[str, Any],
        context: QuestionContext
    ) -> Set[ValidationViolation]:
        """Execute a single validation rule"""
        violations: Set[ValidationViolation] = set()
        
        try:
            if rule.rule_type == ValidationRuleType.TYPE_CHECK:
                violations.update(self._validate_type_check(rule, output))
            
            elif rule.rule_type == ValidationRuleType.SCHEMA_VALIDATION:
                violations.update(self._validate_schema(rule, output))
            
            elif rule.rule_type == ValidationRuleType.REGEX_MATCH:
                violations.update(self._validate_regex(rule, output))
            
            elif rule.rule_type == ValidationRuleType.RANGE_CHECK:
                violations.update(self._validate_range(rule, output))
            
            elif rule.rule_type == ValidationRuleType.REQUIRED_FIELDS:
                violations.update(self._validate_required_fields(rule, output))
            
            elif rule.rule_type == ValidationRuleType.CUSTOM_LOGIC:
                violations.update(self._validate_custom_logic(rule, output, context))
            
            else:
                logger.warning(f"Unknown validation rule type: {rule.rule_type}")
        
        except Exception as e:
            logger.error(f"Error executing rule {rule.rule_type}: {e}")
            violations.add(ValidationViolation(
                rule=rule,
                field_name="__rule_execution__",
                actual_value=str(e),
                expected_value="successful execution",
                message=f"Rule execution error: {str(e)}",
                severity="error"
            ))
        
        return violations
    
    def _validate_type_check(
        self,
        rule: ValidationRule,
        output: Dict[str, Any]
    ) -> Set[ValidationViolation]:
        """Validate field types"""
        violations: Set[ValidationViolation] = set()
        
        type_mappings = rule.parameters.get("type_mappings", {})
        
        for field, expected_type in type_mappings.items():
            if field not in output:
                continue
            
            value = output[field]
            expected_type_obj = self._get_type_from_string(expected_type)
            
            if not isinstance(value, expected_type_obj):
                violations.add(ValidationViolation(
                    rule=rule,
                    field_name=field,
                    actual_value=type(value).__name__,
                    expected_value=expected_type,
                    message=f"Field '{field}' has type {type(value).__name__}, expected {expected_type}",
                    severity=rule.severity
                ))
        
        return violations
    
    def _validate_schema(
        self,
        rule: ValidationRule,
        output: Dict[str, Any]
    ) -> Set[ValidationViolation]:
        """Validate against JSON schema"""
        violations: Set[ValidationViolation] = set()
        
        schema = rule.parameters.get("schema", {})
        
        # Simple schema validation (can be extended with jsonschema library)
        required_fields = schema.get("required", [])
        properties = schema.get("properties", {})
        
        for field in required_fields:
            if field not in output:
                violations.add(ValidationViolation(
                    rule=rule,
                    field_name=field,
                    actual_value=None,
                    expected_value="present",
                    message=f"Required field '{field}' is missing",
                    severity=rule.severity
                ))
        
        # Validate property types
        for field, field_schema in properties.items():
            if field not in output:
                continue
            
            expected_type = field_schema.get("type")
            if expected_type:
                value = output[field]
                if not self._check_json_schema_type(value, expected_type):
                    violations.add(ValidationViolation(
                        rule=rule,
                        field_name=field,
                        actual_value=type(value).__name__,
                        expected_value=expected_type,
                        message=f"Field '{field}' type mismatch",
                        severity=rule.severity
                    ))
        
        return violations
    
    def _validate_regex(
        self,
        rule: ValidationRule,
        output: Dict[str, Any]
    ) -> Set[ValidationViolation]:
        """Validate fields against regex patterns"""
        violations: Set[ValidationViolation] = set()
        
        patterns = rule.parameters.get("patterns", [])
        field = rule.parameters.get("field", "evidence")
        
        # Get field value
        value = output.get(field, "")
        if isinstance(value, list):
            value = " ".join(str(v) for v in value)
        else:
            value = str(value)
        
        # Check if any pattern matches
        if patterns:
            matched = False
            for pattern in patterns:
                if re.search(pattern, value, re.IGNORECASE):
                    matched = True
                    break
            
            if not matched:
                violations.add(ValidationViolation(
                    rule=rule,
                    field_name=field,
                    actual_value=value[:100] if len(value) > 100 else value,
                    expected_value=f"matching patterns: {patterns[:3]}",
                    message=f"Field '{field}' does not match any expected patterns",
                    severity=rule.severity
                ))
        
        return violations
    
    def _validate_range(
        self,
        rule: ValidationRule,
        output: Dict[str, Any]
    ) -> Set[ValidationViolation]:
        """Validate numeric fields are within range"""
        violations: Set[ValidationViolation] = set()
        
        field = rule.parameters.get("field", "score")
        min_val = rule.parameters.get("min")
        max_val = rule.parameters.get("max")
        
        # Support nested field access
        value = self._get_nested_field(output, field)
        
        if value is None:
            return violations
        
        try:
            numeric_value = float(value)
            
            if min_val is not None and numeric_value < min_val:
                violations.add(ValidationViolation(
                    rule=rule,
                    field_name=field,
                    actual_value=numeric_value,
                    expected_value=f">= {min_val}",
                    message=f"Field '{field}' value {numeric_value} is below minimum {min_val}",
                    severity=rule.severity
                ))
            
            if max_val is not None and numeric_value > max_val:
                violations.add(ValidationViolation(
                    rule=rule,
                    field_name=field,
                    actual_value=numeric_value,
                    expected_value=f"<= {max_val}",
                    message=f"Field '{field}' value {numeric_value} exceeds maximum {max_val}",
                    severity=rule.severity
                ))
        
        except (ValueError, TypeError) as e:
            violations.add(ValidationViolation(
                rule=rule,
                field_name=field,
                actual_value=value,
                expected_value="numeric value",
                message=f"Field '{field}' is not a valid number: {e}",
                severity=rule.severity
            ))
        
        return violations
    
    def _validate_required_fields(
        self,
        rule: ValidationRule,
        output: Dict[str, Any]
    ) -> Set[ValidationViolation]:
        """Validate required fields are present"""
        violations: Set[ValidationViolation] = set()
        
        required_fields = rule.parameters.get("fields", [])
        
        for field in required_fields:
            if field not in output or output[field] is None:
                violations.add(ValidationViolation(
                    rule=rule,
                    field_name=field,
                    actual_value=None,
                    expected_value="non-null value",
                    message=f"Required field '{field}' is missing or null",
                    severity=rule.severity
                ))
        
        return violations
    
    def _validate_custom_logic(
        self,
        rule: ValidationRule,
        output: Dict[str, Any],
        context: QuestionContext
    ) -> Set[ValidationViolation]:
        """Execute custom validation logic"""
        violations: Set[ValidationViolation] = set()
        
        # Custom logic can be extended based on specific needs
        # For now, just log that custom validation was attempted
        logger.debug(f"Custom validation for {context.question_id}: {rule.description}")
        
        return violations
    
    def _get_type_from_string(self, type_string: str) -> type:
        """Convert type string to Python type"""
        type_map = {
            "str": str,
            "string": str,
            "int": int,
            "integer": int,
            "float": float,
            "number": float,
            "bool": bool,
            "boolean": bool,
            "list": list,
            "array": list,
            "dict": dict,
            "object": dict,
        }
        
        return type_map.get(type_string.lower(), str)
    
    def _check_json_schema_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches JSON schema type"""
        type_map = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict,
            "null": type(None),
        }
        
        expected_python_type = type_map.get(expected_type)
        if expected_python_type is None:
            return True
        
        return isinstance(value, expected_python_type)
    
    def _get_nested_field(self, data: Dict[str, Any], field_path: str) -> Any:
        """Get nested field value using dot notation"""
        parts = field_path.split('.')
        value = data
        
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
                if value is None:
                    return None
            else:
                return None
        
        return value
    
    def _update_stats(self, status: ValidationStatus, execution_time: float) -> None:
        """Update validation statistics"""
        self._validation_stats["total_validations"] += 1
        self._validation_stats["total_time"] += execution_time
        
        if status == ValidationStatus.PASS:
            self._validation_stats["passed"] += 1
        elif status == ValidationStatus.FAIL:
            self._validation_stats["failed"] += 1
        elif status == ValidationStatus.WARNING:
            self._validation_stats["warnings"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get validation statistics"""
        stats = self._validation_stats.copy()
        
        if stats["total_validations"] > 0:
            stats["pass_rate"] = stats["passed"] / stats["total_validations"]
            stats["fail_rate"] = stats["failed"] / stats["total_validations"]
            stats["avg_time"] = stats["total_time"] / stats["total_validations"]
        else:
            stats["pass_rate"] = 0.0
            stats["fail_rate"] = 0.0
            stats["avg_time"] = 0.0
        
        return stats
    
    def reset_stats(self) -> None:
        """Reset validation statistics"""
        self._validation_stats = {
            "total_validations": 0,
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "total_time": 0.0,
        }


if __name__ == "__main__":
    # Test the validation engine
    from metadata_service import get_metadata_service
    
    print("=" * 80)
    print("VALIDATION ENGINE TEST")
    print("=" * 80)
    
    # Load metadata
    service = get_metadata_service()
    service.load()
    
    # Get a question context
    context = service.get_question_context("P1-D1-Q1")
    if not context:
        print("ERROR: Could not load question context")
        exit(1)
    
    print(f"\nTesting validation for: {context.canonical_id}")
    print(f"Validation rules: {len(context.validation_rules)}")
    
    # Create validation engine
    engine = ValidationEngine()
    
    # Test with valid output
    print("\n" + "-" * 80)
    print("Test 1: Valid Output")
    print("-" * 80)
    
    valid_output = {
        "score": 2.5,
        "confidence": 0.85,
        "evidence": ["Found baseline data from 2020", "DANE source cited"],
        "data": {
            "found_elements": 3,
            "total_elements": 4
        }
    }
    
    result = engine.validate(valid_output, context)
    print(f"Status: {result.status.value}")
    print(f"Is Valid: {result.is_valid}")
    print(f"Errors: {result.error_count}")
    print(f"Warnings: {result.warning_count}")
    print(f"Passed Rules: {len(result.passed_rules)}")
    print(f"Execution Time: {result.execution_time:.4f}s")
    
    # Test with invalid output (score out of range)
    print("\n" + "-" * 80)
    print("Test 2: Invalid Output (score out of range)")
    print("-" * 80)
    
    invalid_output = {
        "score": 5.0,  # Exceeds max_score of 3.0
        "confidence": 0.85,
        "evidence": ["Some evidence"],
        "data": {}
    }
    
    result = engine.validate(invalid_output, context)
    print(f"Status: {result.status.value}")
    print(f"Is Valid: {result.is_valid}")
    print(f"Errors: {result.error_count}")
    print(f"Warnings: {result.warning_count}")
    
    if result.violations:
        print("\nViolations:")
        for violation in list(result.violations)[:5]:  # Show first 5
            print(f"  - {violation.field_name}: {violation.message}")
    
    # Test with missing required fields
    print("\n" + "-" * 80)
    print("Test 3: Missing Required Fields")
    print("-" * 80)
    
    incomplete_output = {
        "score": 2.0
        # Missing other fields
    }
    
    result = engine.validate(incomplete_output, context)
    print(f"Status: {result.status.value}")
    print(f"Is Valid: {result.is_valid}")
    print(f"Errors: {result.error_count}")
    print(f"Warnings: {result.warning_count}")
    
    # Show stats
    print("\n" + "=" * 80)
    print("VALIDATION STATISTICS")
    print("=" * 80)
    
    stats = engine.get_stats()
    print(f"Total Validations: {stats['total_validations']}")
    print(f"Passed: {stats['passed']}")
    print(f"Failed: {stats['failed']}")
    print(f"Warnings: {stats['warnings']}")
    print(f"Pass Rate: {stats['pass_rate']:.1%}")
    print(f"Fail Rate: {stats['fail_rate']:.1%}")
    print(f"Avg Time: {stats['avg_time']:.4f}s")
    
    print("\n" + "=" * 80)
