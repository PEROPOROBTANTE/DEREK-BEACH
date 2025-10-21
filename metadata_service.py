# coding=utf-8
"""
Metadata Service - Central Configuration and Context Provider

Loads and manages metadata from cuestionario.json, rubric_scoring.json,
and execution_mapping.yaml. Provides complete question context enrichment.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
import json
import yaml

logger = logging.getLogger(__name__)


@dataclass
class QuestionContext:
    """Complete context for a question with all metadata"""
    question_id: str
    canonical_id: str  # P#-D#-Q# format
    dimension: str
    question_no: int
    policy_area: str
    template: str
    text: str
    scoring_modality: str
    max_score: float
    expected_elements: List[str] = field(default_factory=list)
    
    # Extended fields for context
    search_patterns: Dict[str, Any] = field(default_factory=dict)
    verification_patterns: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    error_strategy: str = "continue"
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    expected_format: str = ""
    
    # Execution information
    execution_chain: List[Dict[str, str]] = field(default_factory=list)
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScoringModality:
    """Scoring modality definition from rubric"""
    id: str
    description: str
    formula: str
    max_score: float
    expected_elements: int = 0
    conversion_table: Dict[str, float] = field(default_factory=dict)
    uses_thresholds: bool = False
    uses_quantitative_data: bool = False
    uses_custom_logic: bool = False
    uses_semantic_matching: bool = False
    similarity_threshold: float = 0.0


class MetadataService:
    """
    Central metadata service - single source of truth
    
    Features:
    - Loads and validates cuestionario.json with JSON schema
    - Loads and validates rubric_scoring.json
    - Loads and validates execution_mapping.yaml
    - Provides complete QuestionContext for any question
    - Ensures canonical ID consistency (P#-D#-Q#)
    - Cross-validates all configuration sources
    """

    def __init__(
        self,
        cuestionario_path: Optional[Path] = None,
        rubric_path: Optional[Path] = None,
        execution_mapping_path: Optional[Path] = None
    ):
        """
        Initialize metadata service
        
        Args:
            cuestionario_path: Path to cuestionario.json
            rubric_path: Path to rubric_scoring.json
            execution_mapping_path: Path to execution_mapping.yaml
        """
        self.cuestionario_path = cuestionario_path or Path("cuestionario.json")
        self.rubric_path = rubric_path or Path("rubric_scoring.json")
        self.execution_mapping_path = execution_mapping_path or Path("execution_mapping.yaml")
        
        # Storage
        self._questions: Dict[str, QuestionContext] = {}
        self._dimensions: Dict[str, Any] = {}
        self._policy_areas: Dict[str, Any] = {}
        self._scoring_modalities: Dict[str, ScoringModality] = {}
        self._execution_mapping: Dict[str, Any] = {}
        
        # Load all sources
        self._load_cuestionario()
        self._load_rubric()
        self._load_execution_mapping()
        
        # Cross-validate
        self._cross_validate()
        
        # Enrich questions with execution chains
        self._enrich_execution_chains()
        
        logger.info(
            f"MetadataService initialized: {len(self._questions)} questions, "
            f"{len(self._dimensions)} dimensions, {len(self._policy_areas)} policy areas, "
            f"{len(self._scoring_modalities)} scoring modalities"
        )

    def _load_cuestionario(self):
        """Load and validate cuestionario.json"""
        if not self.cuestionario_path.exists():
            raise FileNotFoundError(
                f"cuestionario.json not found at {self.cuestionario_path}"
            )
        
        try:
            with open(self.cuestionario_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self._validate_cuestionario_structure(data)
            self._load_dimensions_from_json(data)
            self._load_policy_areas_from_json(data)
            self._load_questions_from_json(data)
            
            logger.info(f"Loaded cuestionario from {self.cuestionario_path}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in cuestionario.json: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to load cuestionario.json: {e}")
            raise

    def _validate_cuestionario_structure(self, data: Dict[str, Any]):
        """Validate JSON structure and log issues"""
        required_keys = ["metadata", "dimensiones", "preguntas_base"]
        missing = [k for k in required_keys if k not in data]
        
        if missing:
            logger.warning(f"Missing recommended keys in cuestionario.json: {missing}")
        
        # Validate metadata
        if "metadata" in data:
            meta = data["metadata"]
            if meta.get("total_questions", 0) != 300:
                logger.warning(
                    f"Expected 300 questions, metadata shows {meta.get('total_questions')}"
                )

    def _load_dimensions_from_json(self, data: Dict[str, Any]):
        """Load dimension definitions"""
        dimensions_data = data.get("dimensiones", {})
        
        for dim_id, dim_info in dimensions_data.items():
            self._dimensions[dim_id] = {
                "id": dim_id,
                "nombre": dim_info.get("nombre", dim_id),
                "descripcion": dim_info.get("descripcion", ""),
                "preguntas": dim_info.get("preguntas", 5),
                "peso_por_punto": dim_info.get("peso_por_punto", {}),
                "umbral_minimo": dim_info.get("umbral_minimo", 0.5)
            }
        
        logger.debug(f"Loaded {len(self._dimensions)} dimensions")

    def _load_policy_areas_from_json(self, data: Dict[str, Any]):
        """Load policy area definitions"""
        # Check both "puntos_tematicos" and "puntos_decalogo"
        policy_data = data.get("puntos_tematicos", data.get("puntos_decalogo", {}))
        
        if not policy_data:
            # Generate default policy areas P1-P10
            for i in range(1, 11):
                policy_id = f"P{i}"
                self._policy_areas[policy_id] = {
                    "id": policy_id,
                    "titulo": f"Punto Temático {i}",
                    "palabras_clave": []
                }
            logger.warning("No policy areas found in JSON, using defaults P1-P10")
        else:
            for policy_id, policy_info in policy_data.items():
                self._policy_areas[policy_id] = {
                    "id": policy_id,
                    "titulo": policy_info.get("titulo", policy_info.get("nombre", policy_id)),
                    "palabras_clave": policy_info.get("palabras_clave", [])
                }
        
        logger.debug(f"Loaded {len(self._policy_areas)} policy areas")

    def _load_questions_from_json(self, data: Dict[str, Any]):
        """Load and process questions from preguntas_base"""
        questions_data = data.get("preguntas_base", [])
        
        if not questions_data:
            logger.error("No preguntas_base found in cuestionario.json")
            raise ValueError("preguntas_base is required in cuestionario.json")
        
        logger.debug(f"Found {len(questions_data)} questions in preguntas_base")
        
        # Check if questions already have policy area variations or need generation
        # If questions have {PUNTO_TEMATICO} placeholder, generate for each policy area
        # Otherwise, use questions as-is
        
        has_templates = any(
            "{PUNTO_TEMATICO}" in question_data.get("texto_template", "")
            or "{punto_tematico}" in question_data.get("texto_template", "")
            for question_data in questions_data[:5]  # Check first 5
        )
        
        if has_templates:
            # Template-based: Generate 30 base questions × 10 policy areas = 300
            logger.info("Detected template-based questions, generating for all policy areas")
            self._generate_questions_from_templates(questions_data)
        else:
            # Direct: Questions already include policy area variations (300 questions)
            logger.info("Loading questions directly from preguntas_base")
            self._load_questions_direct(questions_data)
        
        logger.info(f"Loaded {len(self._questions)} questions")

    def _generate_questions_from_templates(self, questions_data: List[Dict[str, Any]]):
        """Generate questions from templates for all policy areas"""
        for policy_num in range(1, 11):
            policy_id = f"P{policy_num}"
            policy_title = self._policy_areas.get(policy_id, {}).get("titulo", policy_id)
            
            for question_data in questions_data:
                self._create_question_context(question_data, policy_id, policy_title)

    def _load_questions_direct(self, questions_data: List[Dict[str, Any]]):
        """Load questions directly (already includes policy area variations)"""
        # Group by dimension and numero to identify base questions
        from collections import defaultdict
        question_groups = defaultdict(list)
        
        for question_data in questions_data:
            dimension = question_data.get("dimension", "")
            numero = question_data.get("numero", 1)
            key = f"{dimension}-Q{numero}"
            question_groups[key].append(question_data)
        
        # Assign policy areas based on position within groups
        for group_key, group_questions in question_groups.items():
            for idx, question_data in enumerate(group_questions):
                # Determine policy area from position (P1-P10)
                policy_num = (idx % 10) + 1
                policy_id = f"P{policy_num}"
                policy_title = self._policy_areas.get(policy_id, {}).get("titulo", policy_id)
                
                self._create_question_context(question_data, policy_id, policy_title)

    def _create_question_context(
        self,
        question_data: Dict[str, Any],
        policy_id: str,
        policy_title: str
    ):
        """Create a QuestionContext from question data"""
        base_id = question_data.get("id", "")
        dimension = question_data.get("dimension", "")
        question_no = question_data.get("numero", 1)
        
        template = question_data.get("texto_template", "")
        question_text = template.replace("{PUNTO_TEMATICO}", policy_title)
        question_text = question_text.replace("{punto_tematico}", policy_title.lower())
        
        canonical_id = f"{policy_id}-{dimension}-Q{question_no}"
        
        # Extract patterns and validation rules
        criterios = question_data.get("criterios_evaluacion", {})
        
        question = QuestionContext(
            question_id=base_id,
            canonical_id=canonical_id,
            dimension=dimension,
            question_no=question_no,
            policy_area=policy_id,
            template=template,
            text=question_text,
            scoring_modality=question_data.get("modalidad_scoring", "TYPE_A"),
            max_score=question_data.get("puntaje_maximo", 3.0),
            expected_elements=criterios.get("elementos_minimos_esperados", []),
            search_patterns=question_data.get("patrones_busqueda", {}),
            verification_patterns=question_data.get("patrones_verificacion", {}),
            dependencies=question_data.get("dependencias", []),
            error_strategy=question_data.get("estrategia_error", "continue"),
            validation_rules=criterios,
            expected_format=question_data.get("formato_esperado", ""),
            metadata={
                "policy_title": policy_title,
                "dimension_name": self._dimensions.get(dimension, {}).get("nombre", dimension),
                "es_critica": criterios.get("es_critica", False),
                "peso_ponderado": criterios.get("peso_ponderado", 1.0)
            }
        )
        
        self._questions[canonical_id] = question

    def _load_rubric(self):
        """Load and validate rubric_scoring.json"""
        if not self.rubric_path.exists():
            logger.warning(f"rubric_scoring.json not found at {self.rubric_path}")
            self._create_default_rubric()
            return
        
        try:
            with open(self.rubric_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            modalities_data = data.get("scoring_modalities", {})
            
            for modality_id, modality_info in modalities_data.items():
                self._scoring_modalities[modality_id] = ScoringModality(
                    id=modality_info.get("id", modality_id),
                    description=modality_info.get("description", ""),
                    formula=modality_info.get("formula", ""),
                    max_score=modality_info.get("max_score", 3.0),
                    expected_elements=modality_info.get("expected_elements", 0),
                    conversion_table=modality_info.get("conversion_table", {}),
                    uses_thresholds=modality_info.get("uses_thresholds", False),
                    uses_quantitative_data=modality_info.get("uses_quantitative_data", False),
                    uses_custom_logic=modality_info.get("uses_custom_logic", False),
                    uses_semantic_matching=modality_info.get("uses_semantic_matching", False),
                    similarity_threshold=modality_info.get("similarity_threshold", 0.0)
                )
            
            logger.info(f"Loaded {len(self._scoring_modalities)} scoring modalities from rubric")
            
        except Exception as e:
            logger.error(f"Failed to load rubric_scoring.json: {e}")
            self._create_default_rubric()

    def _create_default_rubric(self):
        """Create default scoring modalities"""
        self._scoring_modalities = {
            "TYPE_A": ScoringModality(
                id="count_4_elements",
                description="Count 4 elements and scale to 0-3",
                formula="(elements_found / 4) * 3",
                max_score=3.0,
                expected_elements=4,
                conversion_table={"0": 0.0, "1": 0.75, "2": 1.5, "3": 2.25, "4": 3.0}
            ),
            "TYPE_B": ScoringModality(
                id="count_3_elements",
                description="Count up to 3 elements",
                formula="min(elements_found, 3)",
                max_score=3.0,
                expected_elements=3
            ),
            "TYPE_C": ScoringModality(
                id="count_2_elements",
                description="Count 2 elements and scale to 0-3",
                formula="(elements_found / 2) * 3",
                max_score=3.0,
                expected_elements=2
            ),
            "TYPE_D": ScoringModality(
                id="ratio_quantitative",
                description="Calculate ratio and apply thresholds",
                formula="f(ratio) with thresholds",
                max_score=3.0,
                uses_thresholds=True,
                uses_quantitative_data=True
            )
        }
        logger.info("Using default scoring modalities")

    def _load_execution_mapping(self):
        """Load and validate execution_mapping.yaml"""
        if not self.execution_mapping_path.exists():
            logger.warning(
                f"execution_mapping.yaml not found at {self.execution_mapping_path}, "
                f"creating default mapping"
            )
            self._create_default_execution_mapping()
            return
        
        try:
            with open(self.execution_mapping_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            self._execution_mapping = data or {}
            logger.info(f"Loaded execution mapping from {self.execution_mapping_path}")
            
        except Exception as e:
            logger.error(f"Failed to load execution_mapping.yaml: {e}")
            self._create_default_execution_mapping()

    def _create_default_execution_mapping(self):
        """Create default dimension-based execution mapping"""
        self._execution_mapping = {
            "dimensions": {
                "D1": {
                    "module": "policy_processor",
                    "class": "IndustrialPolicyProcessor",
                    "method": "process",
                    "description": "Diagnóstico y Líneas Base"
                },
                "D2": {
                    "module": "causal_proccesor",
                    "class": "PolicyDocumentAnalyzer",
                    "method": "analyze_document",
                    "description": "Diseño de Intervención"
                },
                "D3": {
                    "module": "Analyzer_one",
                    "class": "MunicipalAnalyzer",
                    "method": "analyze",
                    "description": "Productos y Outputs"
                },
                "D4": {
                    "module": "teoria_cambio",
                    "class": "ModulosTeoriaCambio",
                    "method": "analizar_teoria_cambio",
                    "description": "Resultados y Outcomes"
                },
                "D5": {
                    "module": "dereck_beach",
                    "class": "DerekBeachAnalyzer",
                    "method": "analyze_causal_chain",
                    "description": "Impactos y Efectos"
                },
                "D6": {
                    "module": "teoria_cambio",
                    "class": "ModulosTeoriaCambio",
                    "method": "validar_coherencia_causal",
                    "description": "Teoría de Cambio"
                }
            }
        }
        logger.info("Using default execution mapping")

    def _cross_validate(self):
        """Cross-validate all configuration sources"""
        issues = []
        
        # Validate that all questions have valid scoring modalities
        for qid, question in self._questions.items():
            if question.scoring_modality not in self._scoring_modalities:
                issues.append(
                    f"Question {qid} uses undefined scoring modality: {question.scoring_modality}"
                )
        
        # Validate dimensions
        dimensions_in_questions = set(q.dimension for q in self._questions.values())
        dimensions_defined = set(self._dimensions.keys())
        
        undefined_dims = dimensions_in_questions - dimensions_defined
        if undefined_dims:
            issues.append(f"Questions reference undefined dimensions: {undefined_dims}")
        
        # Validate policy areas
        policy_areas_in_questions = set(q.policy_area for q in self._questions.values())
        policy_areas_defined = set(self._policy_areas.keys())
        
        undefined_policies = policy_areas_in_questions - policy_areas_defined
        if undefined_policies:
            issues.append(f"Questions reference undefined policy areas: {undefined_policies}")
        
        if issues:
            logger.warning(f"Cross-validation issues found:\n" + "\n".join(f"  - {i}" for i in issues))
        else:
            logger.info("Cross-validation passed: all references are valid")

    def _enrich_execution_chains(self):
        """Enrich all questions with execution chains from mapping"""
        for question_id, question in self._questions.items():
            dimension = question.dimension
            
            # Check for question-specific override first
            question_overrides = self._execution_mapping.get("question_overrides", {}) or {}
            if question_overrides and question_id in question_overrides:
                override_info = question_overrides[question_id]
                question.execution_chain = [{
                    "module": override_info.get("module", ""),
                    "class": override_info.get("class", ""),
                    "method": override_info.get("method", ""),
                    "description": override_info.get("description", ""),
                    "confidence": override_info.get("confidence", 0.8)
                }]
            # Otherwise use dimension default
            elif dimension:
                execution_info = self._execution_mapping.get("dimensions", {}).get(dimension, {})
                if execution_info:
                    question.execution_chain = [{
                        "module": execution_info.get("module", ""),
                        "class": execution_info.get("class", ""),
                        "method": execution_info.get("method", ""),
                        "description": execution_info.get("description", ""),
                        "confidence": execution_info.get("confidence", 0.8)
                    }]
        
        logger.debug("Enriched questions with execution chains")

    def get_question_context(self, question_id: str) -> Optional[QuestionContext]:
        """
        Get complete context for a question
        
        Args:
            question_id: Canonical question ID (P#-D#-Q#) or base ID
            
        Returns:
            Complete QuestionContext or None if not found
        """
        # Try direct lookup with canonical ID
        if question_id in self._questions:
            return self._questions[question_id]
        
        # Try to find by base ID
        for q in self._questions.values():
            if q.question_id == question_id:
                return q
        
        logger.warning(f"Question not found: {question_id}")
        return None

    def get_all_questions(self) -> Dict[str, QuestionContext]:
        """Get all questions"""
        return self._questions.copy()

    def get_questions_by_dimension(self, dimension: str) -> List[QuestionContext]:
        """Get all questions for a dimension"""
        return [
            q for q in self._questions.values()
            if q.dimension == dimension
        ]

    def get_questions_by_policy_area(self, policy_area: str) -> List[QuestionContext]:
        """Get all questions for a policy area"""
        return [
            q for q in self._questions.values()
            if q.policy_area == policy_area
        ]

    def get_scoring_modality(self, modality_id: str) -> Optional[ScoringModality]:
        """Get scoring modality definition"""
        return self._scoring_modalities.get(modality_id)

    def get_dimension_info(self, dimension_id: str) -> Optional[Dict[str, Any]]:
        """Get dimension information"""
        return self._dimensions.get(dimension_id)

    def get_policy_area_info(self, policy_area_id: str) -> Optional[Dict[str, Any]]:
        """Get policy area information"""
        return self._policy_areas.get(policy_area_id)

    def validate_questionnaire(self) -> Dict[str, Any]:
        """
        Validate questionnaire completeness
        
        Returns:
            Validation report with any issues found
        """
        issues = []
        
        # Expected: 30 base questions × 10 policy areas = 300
        expected_count = 300
        if len(self._questions) != expected_count:
            issues.append(
                f"Expected {expected_count} questions, found {len(self._questions)}"
            )
        
        # Check dimension coverage (should have 50 questions per dimension)
        for dim_id in self._dimensions.keys():
            dim_questions = self.get_questions_by_dimension(dim_id)
            expected_per_dim = 50  # 5 questions × 10 policy areas
            if len(dim_questions) != expected_per_dim:
                issues.append(
                    f"Dimension {dim_id}: expected {expected_per_dim} questions, "
                    f"found {len(dim_questions)}"
                )
        
        # Check policy area coverage (should have 30 questions per policy area)
        for policy_id in self._policy_areas.keys():
            policy_questions = self.get_questions_by_policy_area(policy_id)
            expected_per_policy = 30  # 30 base questions
            if len(policy_questions) != expected_per_policy:
                issues.append(
                    f"Policy area {policy_id}: expected {expected_per_policy} questions, "
                    f"found {len(policy_questions)}"
                )
        
        return {
            "valid": len(issues) == 0,
            "total_questions": len(self._questions),
            "total_dimensions": len(self._dimensions),
            "total_policy_areas": len(self._policy_areas),
            "total_scoring_modalities": len(self._scoring_modalities),
            "issues": issues
        }


if __name__ == "__main__":
    # Example usage
    service = MetadataService()
    
    print("=" * 80)
    print("METADATA SERVICE")
    print("=" * 80)
    print(f"\nStatistics:")
    print(f"  Total questions: {len(service.get_all_questions())}")
    print(f"  Dimensions: {len(service._dimensions)}")
    print(f"  Policy areas: {len(service._policy_areas)}")
    print(f"  Scoring modalities: {len(service._scoring_modalities)}")
    
    # Validation
    validation = service.validate_questionnaire()
    print(f"\nValidation: {'✓ PASS' if validation['valid'] else '✗ FAIL'}")
    if validation['issues']:
        print("Issues:")
        for issue in validation['issues']:
            print(f"  - {issue}")
    
    # Example: Get question context
    print("\nExample: Get question context for P1-D1-Q1")
    context = service.get_question_context("P1-D1-Q1")
    if context:
        print(f"  Canonical ID: {context.canonical_id}")
        print(f"  Text: {context.text[:100]}...")
        print(f"  Scoring: {context.scoring_modality}")
        print(f"  Execution chain: {context.execution_chain}")
    
    print("=" * 80)
