"""
Metadata Service for Policy Analysis
=====================================

Loads, validates, and provides access to:
- cuestionario.json: 300 questions with validation rules
- execution_mapping.yaml: Execution chains and dependencies
- rubric_scoring.json: Scoring modalities and conversion tables

Creates enriched QuestionContext objects for components to use.

Author: FARFAN Integration Team
Version: 1.0.0
Python: 3.11+
"""

import json
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from events.question_context import (
    QuestionContext,
    ValidationRule,
    ScoringModality,
)

logger = logging.getLogger(__name__)


@dataclass
class MetadataValidationResult:
    """Result of metadata validation"""
    
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    discrepancies: List[str]
    
    def __str__(self) -> str:
        lines = ["Metadata Validation Result:"]
        lines.append(f"  Valid: {self.is_valid}")
        if self.errors:
            lines.append(f"  Errors ({len(self.errors)}):")
            for error in self.errors:
                lines.append(f"    - {error}")
        if self.warnings:
            lines.append(f"  Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                lines.append(f"    - {warning}")
        if self.discrepancies:
            lines.append(f"  Discrepancies ({len(self.discrepancies)}):")
            for disc in self.discrepancies:
                lines.append(f"    - {disc}")
        return "\n".join(lines)


class MetadataService:
    """
    Service for loading and managing metadata files
    
    Responsibilities:
    - Load cuestionario.json, execution_mapping.yaml, rubric_scoring.json
    - Validate alignment between files
    - Cross-reference questions, dimensions, scoring modalities
    - Cache QuestionContext objects
    - Provide API for retrieving enriched context
    """
    
    def __init__(
        self,
        base_path: Optional[Path] = None,
        cuestionario_path: Optional[Path] = None,
        execution_mapping_path: Optional[Path] = None,
        rubric_scoring_path: Optional[Path] = None,
    ):
        """
        Initialize metadata service
        
        Args:
            base_path: Base directory for metadata files
            cuestionario_path: Explicit path to cuestionario.json
            execution_mapping_path: Explicit path to execution_mapping.yaml
            rubric_scoring_path: Explicit path to rubric_scoring.json
        """
        self.base_path = base_path or Path(__file__).parent
        
        self.cuestionario_path = (
            cuestionario_path or self.base_path / "cuestionario.json"
        )
        self.execution_mapping_path = (
            execution_mapping_path or self.base_path / "execution_mapping.yaml"
        )
        self.rubric_scoring_path = (
            rubric_scoring_path or self.base_path / "rubric_scoring.json"
        )
        
        # Loaded metadata
        self.cuestionario: Dict[str, Any] = {}
        self.execution_mapping: Dict[str, Any] = {}
        self.rubric_scoring: Dict[str, Any] = {}
        
        # Cached contexts
        self._question_context_cache: Dict[str, QuestionContext] = {}
        
        # Validation result
        self.validation_result: Optional[MetadataValidationResult] = None
        
        logger.info("MetadataService initialized")
    
    def load_all(self) -> MetadataValidationResult:
        """
        Load and validate all metadata files
        
        Returns:
            Validation result
        """
        logger.info("Loading all metadata files")
        
        errors = []
        warnings = []
        discrepancies = []
        
        # Load cuestionario.json
        try:
            self.cuestionario = self._load_cuestionario()
            logger.info(
                f"Loaded cuestionario.json: "
                f"{self.cuestionario.get('metadata', {}).get('total_questions', 0)} questions"
            )
        except Exception as e:
            errors.append(f"Failed to load cuestionario.json: {e}")
        
        # Load execution_mapping.yaml
        try:
            self.execution_mapping = self._load_execution_mapping()
            logger.info(
                f"Loaded execution_mapping.yaml: "
                f"{len(self.execution_mapping.get('adapter_registry', {}))} adapters"
            )
        except Exception as e:
            errors.append(f"Failed to load execution_mapping.yaml: {e}")
        
        # Load rubric_scoring.json
        try:
            self.rubric_scoring = self._load_rubric_scoring()
            logger.info(
                f"Loaded rubric_scoring.json: "
                f"{len(self.rubric_scoring.get('scoring_modalities', {}))} modalities"
            )
        except Exception as e:
            errors.append(f"Failed to load rubric_scoring.json: {e}")
        
        # Validate alignment if all files loaded
        if not errors:
            validation_errors, validation_warnings, validation_discrepancies = (
                self._validate_alignment()
            )
            errors.extend(validation_errors)
            warnings.extend(validation_warnings)
            discrepancies.extend(validation_discrepancies)
        
        self.validation_result = MetadataValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            discrepancies=discrepancies,
        )
        
        if self.validation_result.is_valid:
            logger.info("All metadata files loaded and validated successfully")
        else:
            logger.error(f"Metadata validation failed: {self.validation_result}")
        
        return self.validation_result
    
    def _load_cuestionario(self) -> Dict[str, Any]:
        """Load cuestionario.json"""
        if not self.cuestionario_path.exists():
            raise FileNotFoundError(
                f"cuestionario.json not found at {self.cuestionario_path}"
            )
        
        with open(self.cuestionario_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _load_execution_mapping(self) -> Dict[str, Any]:
        """Load execution_mapping.yaml"""
        if not self.execution_mapping_path.exists():
            raise FileNotFoundError(
                f"execution_mapping.yaml not found at {self.execution_mapping_path}"
            )
        
        with open(self.execution_mapping_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _load_rubric_scoring(self) -> Dict[str, Any]:
        """Load rubric_scoring.json"""
        if not self.rubric_scoring_path.exists():
            raise FileNotFoundError(
                f"rubric_scoring.json not found at {self.rubric_scoring_path}"
            )
        
        with open(self.rubric_scoring_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _validate_alignment(self) -> tuple[List[str], List[str], List[str]]:
        """
        Validate alignment between metadata files
        
        Returns:
            Tuple of (errors, warnings, discrepancies)
        """
        errors = []
        warnings = []
        discrepancies = []
        
        # Check dimensions are consistent
        cuest_dimensions = set(self.cuestionario.get('dimensiones', {}).keys())
        mapping_dimensions = set()
        for chain in self.execution_mapping.get('execution_chains', {}).values():
            if isinstance(chain, dict):
                # Extract dimension from key (e.g., "D1" from execution_chains)
                pass
        
        # Check scoring modalities referenced in mapping exist in rubric
        scoring_modalities = set(
            self.rubric_scoring.get('scoring_modalities', {}).keys()
        )
        
        for dimension, chain_config in self.execution_mapping.get(
            'execution_chains', {}
        ).items():
            if isinstance(chain_config, dict):
                default_chain = chain_config.get('default_chain', [])
                for step in default_chain:
                    scoring_mod = step.get('scoring_modality')
                    if scoring_mod and scoring_mod not in scoring_modalities:
                        discrepancies.append(
                            f"Dimension {dimension} references unknown scoring "
                            f"modality: {scoring_mod}"
                        )
        
        # Validate adapters exist
        adapters_in_registry = set(
            self.execution_mapping.get('adapter_registry', {}).keys()
        )
        
        for dimension, chain_config in self.execution_mapping.get(
            'execution_chains', {}
        ).items():
            if isinstance(chain_config, dict):
                default_chain = chain_config.get('default_chain', [])
                for step in default_chain:
                    adapter = step.get('adapter')
                    if adapter and adapter not in adapters_in_registry:
                        errors.append(
                            f"Dimension {dimension} references unknown adapter: "
                            f"{adapter}"
                        )
        
        return errors, warnings, discrepancies
    
    def get_question_context(self, question_id: str) -> Optional[QuestionContext]:
        """
        Get enriched QuestionContext for a question
        
        Args:
            question_id: Question ID (e.g., "P1-D1-Q1" or "D1")
            
        Returns:
            QuestionContext or None if not found
        """
        # Check cache
        if question_id in self._question_context_cache:
            return self._question_context_cache[question_id]
        
        # Build context
        context = self._build_question_context(question_id)
        
        if context:
            self._question_context_cache[question_id] = context
        
        return context
    
    def _build_question_context(self, question_id: str) -> Optional[QuestionContext]:
        """
        Build QuestionContext from metadata files
        
        Args:
            question_id: Question ID
            
        Returns:
            QuestionContext or None
        """
        # Extract dimension from question_id
        dimension = self._extract_dimension(question_id)
        if not dimension:
            logger.warning(f"Could not extract dimension from {question_id}")
            return None
        
        # Get execution chain for dimension
        exec_chains = self.execution_mapping.get('execution_chains', {})
        chain_config = exec_chains.get(dimension, {})
        
        if not chain_config:
            logger.warning(f"No execution chain for dimension {dimension}")
            return None
        
        default_chain = chain_config.get('default_chain', [])
        
        # Extract validation rules and scoring info from chain
        validation_rules = []
        scoring_modality = None
        expected_elements = 0
        
        for step in default_chain:
            # Extract validation rules
            step_val_rules = step.get('validation_rules', [])
            if isinstance(step_val_rules, list):
                for rule in step_val_rules:
                    if isinstance(rule, dict):
                        # Rule is a dict with single key-value
                        for rule_name, rule_value in rule.items():
                            template = self.execution_mapping.get(
                                'validation_rule_templates', {}
                            ).get(rule_name, {})
                            
                            validation_rules.append(
                                ValidationRule(
                                    rule_name=rule_name,
                                    rule_type=template.get('type', 'string'),
                                    operator=template.get('operator', '=='),
                                    value=rule_value,
                                    error_message=template.get(
                                        'error_message',
                                        f"Validation failed: {rule_name}"
                                    ),
                                )
                            )
            
            # Extract scoring modality
            scoring_mod = step.get('scoring_modality')
            if scoring_mod:
                try:
                    scoring_modality = ScoringModality(
                        self.rubric_scoring.get('scoring_modalities', {})
                        .get(scoring_mod, {})
                        .get('id', scoring_mod)
                    )
                except ValueError:
                    logger.warning(f"Unknown scoring modality: {scoring_mod}")
            
            # Extract expected elements
            expected_elem = step.get('expected_elements', 0)
            if expected_elem > expected_elements:
                expected_elements = expected_elem
        
        # Get required adapters
        required_adapters = [
            step.get('adapter') for step in default_chain
            if step.get('adapter')
        ]
        
        # Build context
        context = QuestionContext(
            question_id=question_id,
            dimension=dimension,
            question_text=chain_config.get('description', ''),
            scoring_modality=scoring_modality,
            expected_elements=expected_elements,
            validation_rules=validation_rules,
            execution_chain=default_chain,
            required_adapters=required_adapters,
            error_strategy=self.execution_mapping.get('error_strategies', {})
                .get('validation_failure', {})
                .get('action', 'emit_validation_failed_event'),
        )
        
        return context
    
    def _extract_dimension(self, question_id: str) -> Optional[str]:
        """Extract dimension from question ID"""
        import re
        match = re.search(r'D[1-6]', question_id)
        return match.group(0) if match else None
    
    def get_all_question_ids(self) -> List[str]:
        """Get all question IDs from cuestionario"""
        question_ids = []
        
        for dimension_id in self.cuestionario.get('dimensiones', {}).keys():
            question_ids.append(dimension_id)
        
        return question_ids
    
    def get_execution_chain(self, question_id: str) -> List[Dict[str, Any]]:
        """
        Get execution chain for a question
        
        Args:
            question_id: Question ID
            
        Returns:
            List of execution steps
        """
        context = self.get_question_context(question_id)
        return context.execution_chain if context else []
    
    def get_adapter_registry(self) -> Dict[str, Any]:
        """Get adapter registry"""
        return self.execution_mapping.get('adapter_registry', {})
    
    def get_scoring_modality(self, modality_type: str) -> Optional[Dict[str, Any]]:
        """
        Get scoring modality details
        
        Args:
            modality_type: Type of scoring modality (e.g., "TYPE_A")
            
        Returns:
            Scoring modality configuration or None
        """
        return self.rubric_scoring.get('scoring_modalities', {}).get(modality_type)
