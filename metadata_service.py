"""
Metadata Service - Centralized Management of cuestionario.json
===============================================================

Loads and caches cuestionario.json, provides query interface for question-specific
metadata, and enriches raw metadata into strongly-typed QuestionContext objects.

Key Features:
- Lazy loading and caching of cuestionario.json
- Strongly-typed QuestionContext dataclass with validation rules
- Query interface for question metadata by various criteria
- Version tracking for deterministic execution
- Thread-safe singleton pattern

Author: FARFAN 3.0 - Industrial Orchestrator
Version: 1.0.0
Python: 3.10+
"""

import json
import logging
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ValidationRuleType(Enum):
    """Types of validation rules"""
    TYPE_CHECK = "type_check"
    SCHEMA_VALIDATION = "schema_validation"
    REGEX_MATCH = "regex_match"
    RANGE_CHECK = "range_check"
    REQUIRED_FIELDS = "required_fields"
    CUSTOM_LOGIC = "custom_logic"


class ErrorStrategy(Enum):
    """Error handling strategies"""
    RETRY = "retry"
    FALLBACK = "fallback"
    FAIL_FAST = "fail_fast"
    SKIP = "skip"
    COMPENSATE = "compensate"


@dataclass(frozen=True)
class ValidationRule:
    """Immutable validation rule definition"""
    rule_type: ValidationRuleType
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    severity: str = "error"  # error, warning, info
    
    def __hash__(self):
        # Make hashable by converting dict to frozenset, handling lists
        def make_hashable(obj):
            if isinstance(obj, list):
                return tuple(make_hashable(item) for item in obj)
            elif isinstance(obj, dict):
                return frozenset((k, make_hashable(v)) for k, v in obj.items())
            elif isinstance(obj, set):
                return frozenset(make_hashable(item) for item in obj)
            return obj
        
        params_frozen = make_hashable(self.parameters) if self.parameters else frozenset()
        return hash((self.rule_type, self.description, params_frozen, self.severity))


@dataclass(frozen=True)
class QuestionContext:
    """
    Immutable, strongly-typed question context enriched from cuestionario.json
    
    This dataclass encapsulates all metadata needed for deterministic
    execution of a single question analysis.
    """
    # Core identifiers
    question_id: str
    dimension: str
    policy_area: str
    question_number: int
    
    # Question content
    text: str
    template: str
    
    # Scoring configuration
    scoring_modality: str
    max_score: float
    expected_elements: List[str] = field(default_factory=list)
    
    # Validation rules
    validation_rules: Set[ValidationRule] = field(default_factory=set)
    
    # Dependencies
    dependencies: List[str] = field(default_factory=list)  # Other question IDs
    
    # Execution configuration
    error_strategy: ErrorStrategy = ErrorStrategy.RETRY
    timeout_seconds: int = 300
    retry_attempts: int = 3
    
    # Metadata
    version: str = "2.0.0"
    is_critical: bool = False
    minimum_score: float = 0.5
    weight: float = 1.0
    
    # Additional context
    expected_format: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __hash__(self):
        # Make hashable for use in sets/dicts
        return hash((self.question_id, self.version))
    
    @property
    def canonical_id(self) -> str:
        """Returns standardized ID format P#-D#-Q#"""
        return f"{self.policy_area}-{self.dimension}-Q{self.question_number}"


class MetadataService:
    """
    Thread-safe singleton service for cuestionario.json metadata management
    
    Features:
    - Lazy loading with caching
    - Thread-safe access
    - Version tracking for deterministic execution
    - Rich query interface
    - Automatic QuestionContext enrichment
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern implementation"""
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, cuestionario_path: Optional[Path] = None):
        """
        Initialize metadata service
        
        Args:
            cuestionario_path: Path to cuestionario.json (default: repo root)
        """
        # Only initialize once
        if hasattr(self, '_initialized'):
            return
            
        self.cuestionario_path = cuestionario_path or Path(__file__).parent / "cuestionario.json"
        self._raw_data: Optional[Dict[str, Any]] = None
        self._question_contexts: Dict[str, QuestionContext] = {}
        self._dimensions: Dict[str, Any] = {}
        self._policy_areas: Dict[str, Any] = {}
        self._version: str = "unknown"
        self._initialized = True
        
        logger.info(f"MetadataService initialized with path: {self.cuestionario_path}")
    
    def load(self) -> None:
        """
        Load and cache cuestionario.json
        
        Thread-safe lazy loading with validation
        """
        with self._lock:
            if self._raw_data is not None:
                logger.debug("cuestionario.json already loaded, using cache")
                return
            
            if not self.cuestionario_path.exists():
                raise FileNotFoundError(
                    f"cuestionario.json not found at {self.cuestionario_path}"
                )
            
            try:
                with open(self.cuestionario_path, 'r', encoding='utf-8') as f:
                    self._raw_data = json.load(f)
                
                # Extract version
                metadata = self._raw_data.get("metadata", {})
                self._version = metadata.get("version", "unknown")
                
                # Load dimensions
                self._load_dimensions()
                
                # Load policy areas
                self._load_policy_areas()
                
                # Enrich question contexts
                self._enrich_question_contexts()
                
                logger.info(
                    f"Loaded cuestionario.json v{self._version}: "
                    f"{len(self._question_contexts)} questions, "
                    f"{len(self._dimensions)} dimensions, "
                    f"{len(self._policy_areas)} policy areas"
                )
                
            except Exception as e:
                logger.error(f"Failed to load cuestionario.json: {e}", exc_info=True)
                raise
    
    def _load_dimensions(self) -> None:
        """Extract dimension definitions"""
        dimensions_data = self._raw_data.get("dimensiones", {})
        
        for dim_id, dim_info in dimensions_data.items():
            self._dimensions[dim_id] = {
                "id": dim_id,
                "nombre": dim_info.get("nombre", dim_id),
                "descripcion": dim_info.get("descripcion", ""),
                "peso_por_punto": dim_info.get("peso_por_punto", {}),
                "preguntas": dim_info.get("preguntas", 5),
                "umbral_minimo": dim_info.get("umbral_minimo", 0.5),
            }
    
    def _load_policy_areas(self) -> None:
        """Extract policy area definitions"""
        # Check both potential keys
        policy_data = self._raw_data.get("puntos_tematicos", {})
        if not policy_data:
            policy_data = self._raw_data.get("puntos_decalogo", {})
        
        for policy_id, policy_info in policy_data.items():
            self._policy_areas[policy_id] = {
                "id": policy_id,
                "titulo": policy_info.get("titulo", policy_id),
                "descripcion": policy_info.get("descripcion", ""),
                "palabras_clave": policy_info.get("palabras_clave", []),
            }
    
    def _enrich_question_contexts(self) -> None:
        """
        Enrich raw question data into strongly-typed QuestionContext objects
        
        Generates 300 questions from templates and policy areas
        """
        preguntas_base = self._raw_data.get("preguntas_base", [])
        
        if not preguntas_base:
            logger.warning("No preguntas_base found in cuestionario.json")
            return
        
        # Generate questions for each policy area
        for policy_num in range(1, 11):  # P1-P10
            policy_id = f"P{policy_num}"
            policy_info = self._policy_areas.get(policy_id, {})
            policy_title = policy_info.get("titulo", policy_id)
            
            for pregunta in preguntas_base:
                dimension = pregunta.get("dimension", "")
                question_no = pregunta.get("numero", 1)
                question_id_base = pregunta.get("id", f"{dimension}-Q{question_no}")
                
                # Generate question text from template
                template = pregunta.get("texto_template", "")
                question_text = template.replace("{PUNTO_TEMATICO}", policy_title)
                
                # Create canonical ID
                question_id = f"{policy_id}-{question_id_base}"
                
                # Extract validation rules
                validation_rules = self._extract_validation_rules(pregunta)
                
                # Extract dependencies
                dependencies = pregunta.get("dependencies", [])
                if isinstance(dependencies, dict):
                    dependencies = dependencies.get("prerequisite_questions", [])
                
                # Determine error strategy
                error_strategy = self._determine_error_strategy(pregunta)
                
                # Get dimension metadata
                dim_info = self._dimensions.get(dimension, {})
                peso_por_punto = dim_info.get("peso_por_punto", {})
                weight = peso_por_punto.get(policy_id, 1.0)
                
                # Check if critical
                decalogo_mapping = dim_info.get("decalogo_dimension_mapping", {})
                policy_mapping = decalogo_mapping.get(policy_id, {})
                is_critical = policy_mapping.get("is_critical", False)
                minimum_score = policy_mapping.get("minimum_score", 0.5)
                
                # Create QuestionContext
                context = QuestionContext(
                    question_id=question_id,
                    dimension=dimension,
                    policy_area=policy_id,
                    question_number=question_no,
                    text=question_text,
                    template=template,
                    scoring_modality=pregunta.get("scoring_modality", "TYPE_A"),
                    max_score=pregunta.get("max_score", 3.0),
                    expected_elements=pregunta.get("expected_elements", []),
                    validation_rules=validation_rules,
                    dependencies=dependencies,
                    error_strategy=error_strategy,
                    timeout_seconds=pregunta.get("timeout_seconds", 300),
                    retry_attempts=pregunta.get("retry_attempts", 3),
                    version=self._version,
                    is_critical=is_critical,
                    minimum_score=minimum_score,
                    weight=weight,
                    expected_format=pregunta.get("expected_format", {}),
                    constraints=pregunta.get("criterios_evaluacion", {}),
                    metadata={
                        "policy_title": policy_title,
                        "dimension_name": dim_info.get("nombre", dimension),
                        "patrones_verificacion": pregunta.get("patrones_verificacion", []),
                        "criterios_evaluacion": pregunta.get("criterios_evaluacion", {}),
                    }
                )
                
                self._question_contexts[question_id] = context
    
    def _extract_validation_rules(self, pregunta: Dict[str, Any]) -> Set[ValidationRule]:
        """Extract validation rules from question definition"""
        rules: Set[ValidationRule] = set()
        
        # Required fields validation
        criterios = pregunta.get("criterios_evaluacion", {})
        if criterios:
            rules.add(ValidationRule(
                rule_type=ValidationRuleType.REQUIRED_FIELDS,
                description="Validate required evaluation criteria",
                parameters={"fields": list(criterios.keys())},
                severity="error"
            ))
        
        # Score range validation
        max_score = pregunta.get("max_score", 3.0)
        rules.add(ValidationRule(
            rule_type=ValidationRuleType.RANGE_CHECK,
            description="Validate score is within range",
            parameters={"min": 0.0, "max": max_score},
            severity="error"
        ))
        
        # Pattern validation if specified
        patrones = pregunta.get("patrones_verificacion", [])
        if patrones:
            rules.add(ValidationRule(
                rule_type=ValidationRuleType.REGEX_MATCH,
                description="Validate evidence matches expected patterns",
                parameters={"patterns": patrones},
                severity="warning"
            ))
        
        return rules
    
    def _determine_error_strategy(self, pregunta: Dict[str, Any]) -> ErrorStrategy:
        """Determine error handling strategy for a question"""
        # Critical questions fail fast
        if pregunta.get("is_critical", False):
            return ErrorStrategy.FAIL_FAST
        
        # Questions with fallback options use fallback
        if pregunta.get("has_fallback", False):
            return ErrorStrategy.FALLBACK
        
        # Default to retry
        return ErrorStrategy.RETRY
    
    def get_question_context(self, question_id: str) -> Optional[QuestionContext]:
        """
        Get enriched QuestionContext for a specific question
        
        Args:
            question_id: Question identifier (e.g., "P1-D1-Q1")
            
        Returns:
            QuestionContext if found, None otherwise
        """
        self.load()  # Ensure data is loaded
        return self._question_contexts.get(question_id)
    
    def get_all_question_contexts(self) -> Dict[str, QuestionContext]:
        """Get all question contexts"""
        self.load()
        return self._question_contexts.copy()
    
    def get_contexts_by_dimension(self, dimension: str) -> List[QuestionContext]:
        """Get all question contexts for a dimension"""
        self.load()
        return [
            ctx for ctx in self._question_contexts.values()
            if ctx.dimension == dimension
        ]
    
    def get_contexts_by_policy_area(self, policy_area: str) -> List[QuestionContext]:
        """Get all question contexts for a policy area"""
        self.load()
        return [
            ctx for ctx in self._question_contexts.values()
            if ctx.policy_area == policy_area
        ]
    
    def get_critical_questions(self) -> List[QuestionContext]:
        """Get all critical question contexts"""
        self.load()
        return [
            ctx for ctx in self._question_contexts.values()
            if ctx.is_critical
        ]
    
    def get_question_dependencies(self, question_id: str) -> List[QuestionContext]:
        """Get QuestionContext objects for all dependencies of a question"""
        self.load()
        context = self.get_question_context(question_id)
        if not context:
            return []
        
        dependencies = []
        for dep_id in context.dependencies:
            dep_context = self.get_question_context(dep_id)
            if dep_context:
                dependencies.append(dep_context)
        
        return dependencies
    
    def get_version(self) -> str:
        """Get cuestionario.json version"""
        self.load()
        return self._version
    
    def get_dimension_info(self, dimension: str) -> Optional[Dict[str, Any]]:
        """Get dimension metadata"""
        self.load()
        return self._dimensions.get(dimension)
    
    def get_policy_area_info(self, policy_area: str) -> Optional[Dict[str, Any]]:
        """Get policy area metadata"""
        self.load()
        return self._policy_areas.get(policy_area)
    
    def validate_questionnaire(self) -> Dict[str, Any]:
        """
        Validate questionnaire completeness and consistency
        
        Returns:
            Validation report with issues found
        """
        self.load()
        issues = []
        
        # Check expected count (10 policy areas × 30 base questions)
        expected_count = 300
        if len(self._question_contexts) != expected_count:
            issues.append(
                f"Expected {expected_count} questions, found {len(self._question_contexts)}"
            )
        
        # Check dimension coverage
        for dim_id in ["D1", "D2", "D3", "D4", "D5", "D6"]:
            dim_questions = self.get_contexts_by_dimension(dim_id)
            expected_per_dim = 50  # 10 policy areas × 5 questions
            if len(dim_questions) != expected_per_dim:
                issues.append(
                    f"Dimension {dim_id}: expected {expected_per_dim} questions, "
                    f"found {len(dim_questions)}"
                )
        
        # Check policy area coverage
        for policy_num in range(1, 11):
            policy_id = f"P{policy_num}"
            policy_questions = self.get_contexts_by_policy_area(policy_id)
            expected_per_policy = 30  # 6 dimensions × 5 questions
            if len(policy_questions) != expected_per_policy:
                issues.append(
                    f"Policy area {policy_id}: expected {expected_per_policy} questions, "
                    f"found {len(policy_questions)}"
                )
        
        return {
            "valid": len(issues) == 0,
            "version": self._version,
            "total_questions": len(self._question_contexts),
            "dimensions": len(self._dimensions),
            "policy_areas": len(self._policy_areas),
            "issues": issues
        }


# Singleton instance getter
def get_metadata_service(cuestionario_path: Optional[Path] = None) -> MetadataService:
    """Get or create the singleton MetadataService instance"""
    return MetadataService(cuestionario_path)


if __name__ == "__main__":
    # Test the metadata service
    service = get_metadata_service()
    service.load()
    
    print("=" * 80)
    print("METADATA SERVICE TEST")
    print("=" * 80)
    
    # Validation
    validation = service.validate_questionnaire()
    print(f"\n✓ Version: {validation['version']}")
    print(f"✓ Total questions: {validation['total_questions']}")
    print(f"✓ Dimensions: {validation['dimensions']}")
    print(f"✓ Policy areas: {validation['policy_areas']}")
    print(f"✓ Valid: {validation['valid']}")
    
    if validation['issues']:
        print("\nIssues found:")
        for issue in validation['issues']:
            print(f"  - {issue}")
    
    # Test question context retrieval
    print("\n" + "=" * 80)
    print("SAMPLE QUESTION CONTEXT")
    print("=" * 80)
    
    context = service.get_question_context("P1-D1-Q1")
    if context:
        print(f"\nQuestion ID: {context.question_id}")
        print(f"Canonical ID: {context.canonical_id}")
        print(f"Dimension: {context.dimension}")
        print(f"Policy Area: {context.policy_area}")
        print(f"Scoring Modality: {context.scoring_modality}")
        print(f"Max Score: {context.max_score}")
        print(f"Is Critical: {context.is_critical}")
        print(f"Weight: {context.weight}")
        print(f"Validation Rules: {len(context.validation_rules)}")
        print(f"Dependencies: {context.dependencies}")
        print(f"Error Strategy: {context.error_strategy.value}")
    
    # Test critical questions
    print("\n" + "=" * 80)
    print("CRITICAL QUESTIONS")
    print("=" * 80)
    
    critical = service.get_critical_questions()
    print(f"\nFound {len(critical)} critical questions")
    if critical:
        print("\nFirst 5 critical questions:")
        for ctx in critical[:5]:
            print(f"  - {ctx.canonical_id}: {ctx.text[:60]}...")
    
    print("\n" + "=" * 80)
