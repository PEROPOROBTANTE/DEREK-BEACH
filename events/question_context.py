"""
Question Context Data Structures
=================================

Strongly-typed QuestionContext derived from metadata files
(cuestionario.json, execution_mapping.yaml, rubric_scoring.json).

Used for distributed validation and component behavior guidance.

Author: FARFAN Integration Team
Version: 1.0.0
Python: 3.11+
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class ScoringModality(Enum):
    """Scoring modalities from rubric_scoring.json"""
    
    TYPE_A = "count_4_elements"  # 4 elements scaled to 0-3
    TYPE_B = "count_3_elements"  # 3 elements, each worth 1 point
    TYPE_C = "count_2_elements"  # 2 elements scaled to 0-3
    TYPE_D = "count_3_scaled"    # 3 elements with custom scaling
    TYPE_E = "count_5_weighted"  # 5 elements with weights
    TYPE_F = "binary_3_point"    # Binary yes/no worth 3 points


@dataclass
class ValidationRule:
    """
    Single validation rule for distributed validation
    
    Attributes:
        rule_name: Name of the validation rule (e.g., "min_words")
        rule_type: Type of validation (numeric, list, boolean, etc.)
        operator: Comparison operator (>=, <=, ==, contains_all, etc.)
        value: Expected value or threshold
        error_message: Message to emit on validation failure
    """
    
    rule_name: str
    rule_type: str
    operator: str
    value: Any
    error_message: str
    
    def validate(self, actual_value: Any) -> bool:
        """
        Execute validation rule against actual value
        
        Args:
            actual_value: The value to validate
            
        Returns:
            True if validation passes, False otherwise
        """
        if self.rule_type == "numeric":
            if self.operator == ">=":
                return actual_value >= self.value
            elif self.operator == "<=":
                return actual_value <= self.value
            elif self.operator == "==":
                return actual_value == self.value
            elif self.operator == ">":
                return actual_value > self.value
            elif self.operator == "<":
                return actual_value < self.value
        
        elif self.rule_type == "list":
            if self.operator == "contains_all":
                return all(item in actual_value for item in self.value)
            elif self.operator == "contains_any":
                return any(item in actual_value for item in self.value)
        
        elif self.rule_type == "boolean":
            return bool(actual_value) == bool(self.value)
        
        return False


@dataclass
class QuestionContext:
    """
    Rich context for a question derived from all metadata sources
    
    This is the core data structure that components use to:
    - Validate their inputs/outputs
    - Determine scoring modalities
    - Understand expected elements
    - Check preconditions
    
    Attributes:
        question_id: Unique question identifier (e.g., "P1-D1-Q1")
        dimension: Dimension code (D1-D6)
        policy_area: Policy area code (P1-P10)
        question_number: Question number within dimension
        question_text: Full question text from cuestionario.json
        scoring_modality: How to score this question (TYPE_A-F)
        expected_elements: Number of elements expected for scoring
        max_score: Maximum possible score
        validation_rules: List of validation rules to apply
        execution_chain: List of execution steps from mapping
        required_adapters: Adapters that must run for this question
        preconditions: Preconditions that must be met before scoring
        error_strategy: Error handling strategy for this question
        weight: Weight of this question in dimension scoring
        is_critical: Whether this is a critical question
        minimum_score: Minimum acceptable score
        metadata: Additional metadata from cuestionario.json
    """
    
    question_id: str
    dimension: str
    policy_area: Optional[str] = None
    question_number: Optional[int] = None
    question_text: str = ""
    
    # Scoring configuration
    scoring_modality: Optional[ScoringModality] = None
    expected_elements: int = 0
    max_score: float = 3.0
    
    # Validation
    validation_rules: List[ValidationRule] = field(default_factory=list)
    
    # Execution
    execution_chain: List[Dict[str, Any]] = field(default_factory=list)
    required_adapters: List[str] = field(default_factory=list)
    preconditions: Dict[str, Any] = field(default_factory=dict)
    error_strategy: str = "emit_validation_failed_event"
    
    # Weighting
    weight: float = 1.0
    is_critical: bool = False
    minimum_score: float = 0.0
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def validate_input(self, input_data: Dict[str, Any]) -> List[str]:
        """
        Validate input data against all validation rules
        
        Args:
            input_data: Dictionary of input data to validate
            
        Returns:
            List of error messages (empty if all validations pass)
        """
        errors = []
        
        for rule in self.validation_rules:
            if rule.rule_name not in input_data:
                errors.append(f"Missing required field: {rule.rule_name}")
                continue
            
            value = input_data[rule.rule_name]
            if not rule.validate(value):
                errors.append(rule.error_message)
        
        return errors
    
    def check_preconditions(self, available_data: Dict[str, Any]) -> List[str]:
        """
        Check if all preconditions are met for processing
        
        Args:
            available_data: Dictionary of available data elements
            
        Returns:
            List of unmet preconditions (empty if all met)
        """
        unmet = []
        
        for precond_key, precond_value in self.preconditions.items():
            if precond_key not in available_data:
                unmet.append(f"Missing precondition: {precond_key}")
            elif isinstance(precond_value, bool) and not available_data[precond_key]:
                unmet.append(f"Precondition not satisfied: {precond_key}")
        
        return unmet
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for event payloads"""
        return {
            "question_id": self.question_id,
            "dimension": self.dimension,
            "policy_area": self.policy_area,
            "question_number": self.question_number,
            "question_text": self.question_text,
            "scoring_modality": self.scoring_modality.value if self.scoring_modality else None,
            "expected_elements": self.expected_elements,
            "max_score": self.max_score,
            "validation_rules": [
                {
                    "rule_name": r.rule_name,
                    "rule_type": r.rule_type,
                    "operator": r.operator,
                    "value": r.value,
                    "error_message": r.error_message,
                }
                for r in self.validation_rules
            ],
            "execution_chain": self.execution_chain,
            "required_adapters": self.required_adapters,
            "preconditions": self.preconditions,
            "error_strategy": self.error_strategy,
            "weight": self.weight,
            "is_critical": self.is_critical,
            "minimum_score": self.minimum_score,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QuestionContext':
        """Create QuestionContext from dictionary"""
        # Convert validation rules
        validation_rules = []
        for rule_data in data.get("validation_rules", []):
            validation_rules.append(ValidationRule(**rule_data))
        
        # Convert scoring modality
        scoring_modality = None
        if data.get("scoring_modality"):
            try:
                scoring_modality = ScoringModality(data["scoring_modality"])
            except ValueError:
                pass
        
        return cls(
            question_id=data["question_id"],
            dimension=data["dimension"],
            policy_area=data.get("policy_area"),
            question_number=data.get("question_number"),
            question_text=data.get("question_text", ""),
            scoring_modality=scoring_modality,
            expected_elements=data.get("expected_elements", 0),
            max_score=data.get("max_score", 3.0),
            validation_rules=validation_rules,
            execution_chain=data.get("execution_chain", []),
            required_adapters=data.get("required_adapters", []),
            preconditions=data.get("preconditions", {}),
            error_strategy=data.get("error_strategy", "emit_validation_failed_event"),
            weight=data.get("weight", 1.0),
            is_critical=data.get("is_critical", False),
            minimum_score=data.get("minimum_score", 0.0),
            metadata=data.get("metadata", {}),
        )
