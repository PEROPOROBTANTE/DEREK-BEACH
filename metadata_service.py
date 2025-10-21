# coding=utf-8
"""
Metadata Service - Central Configuration and Context Provider.

Loads and manages metadata from:
- cuestionario.json
- rubric_scoring.json
- execution_mapping.yaml

Provides complete QuestionContext enrichment and cross-validation.
"""

import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class QuestionContext:
    """Complete context for a question with all metadata."""
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

    # Extended fields
    search_patterns: Dict[str, Any] = field(default_factory=dict)
    verification_patterns: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    error_strategy: str = "continue"
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    expected_format: str = ""

    # Execution information
    execution_chain: List[Dict[str, Any]] = field(default_factory=list)

    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScoringModality:
    """Scoring modality definition from rubric."""
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
    Central metadata service - single source of truth.

    Responsibilities:
    - Load and validate questionnaire (cuestionario.json)
    - Load scoring rubric (rubric_scoring.json)
    - Load execution mapping (execution_mapping.yaml)
    - Build enriched QuestionContext objects (300 expected)
    - Cross-validate referential integrity
    """

    def __init__(
        self,
        cuestionario_path: Optional[Path] = None,
        rubric_path: Optional[Path] = None,
        execution_mapping_path: Optional[Path] = None
    ):
        self.cuestionario_path = cuestionario_path or Path("cuestionario.json")
        self.rubric_path = rubric_path or Path("rubric_scoring.json")
        self.execution_mapping_path = execution_mapping_path or Path("execution_mapping.yaml")

        # Internal stores
        self._questions: Dict[str, QuestionContext] = {}
        self._dimensions: Dict[str, Any] = {}
        self._policy_areas: Dict[str, Any] = {}
        self._scoring_modalities: Dict[str, ScoringModality] = {}
        self._execution_mapping: Dict[str, Any] = {}

        # Orchestration
        self._load_cuestionario()
        self._load_rubric()
        self._load_execution_mapping()
        self._cross_validate()
        self._enrich_execution_chains()

        logger.info(
            "MetadataService initialized: %d questions | %d dimensions | %d policy areas | %d scoring modalities",
            len(self._questions),
            len(self._dimensions),
            len(self._policy_areas),
            len(self._scoring_modalities),
        )

    # -------------------------------------------------------------------------
    # Loaders
    # -------------------------------------------------------------------------
    def _load_cuestionario(self) -> None:
        """Load and validate cuestionario.json."""
        if not self.cuestionario_path.exists():
            raise FileNotFoundError(f"cuestionario.json not found at {self.cuestionario_path}")

        try:
            with self.cuestionario_path.open('r', encoding='utf-8') as fh:
                data = json.load(fh)
            self._validate_cuestionario_structure(data)
            self._load_dimensions_from_json(data)
            self._load_policy_areas_from_json(data)
            self._load_questions_from_json(data)
            logger.info("Loaded cuestionario from %s", self.cuestionario_path)
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON in cuestionario.json: %s", e)
            raise
        except Exception as e:
            logger.error("Failed to load cuestionario.json: %s", e)
            raise

    def _validate_cuestionario_structure(self, data: Dict[str, Any]) -> None:
        required = ["metadata", "dimensiones", "preguntas_base"]
        missing = [k for k in required if k not in data]
        if missing:
            logger.warning("Missing recommended keys in cuestionario.json: %s", missing)

        meta = data.get("metadata", {})
        total = meta.get("total_questions", 0)
        if total not in (300, 0):
            logger.warning("Unexpected total_questions value in metadata: %s", total)

    def _load_dimensions_from_json(self, data: Dict[str, Any]) -> None:
        for dim_id, dim_info in data.get("dimensiones", {}).items():
            self._dimensions[dim_id] = {
                "id": dim_id,
                "nombre": dim_info.get("nombre", dim_id),
                "descripcion": dim_info.get("descripcion", ""),
                "preguntas": dim_info.get("preguntas", 5),
                "peso_por_punto": dim_info.get("peso_por_punto", {}),
                "umbral_minimo": dim_info.get("umbral_minimo", 0.5),
            }
        logger.debug("Loaded %d dimensions", len(self._dimensions))

    def _load_policy_areas_from_json(self, data: Dict[str, Any]) -> None:
        policy_data = data.get("puntos_tematicos", data.get("puntos_decalogo", {}))
        if not policy_data:
            for i in range(1, 11):
                pid = f"P{i}"
                self._policy_areas[pid] = {
                    "id": pid,
                    "titulo": f"Punto Temático {i}",
                    "palabras_clave": [],
                }
            logger.warning("No policy areas found; generated defaults P1-P10")
        else:
            for pid, info in policy_data.items():
                self._policy_areas[pid] = {
                    "id": pid,
                    "titulo": info.get("titulo", info.get("nombre", pid)),
                    "palabras_clave": info.get("palabras_clave", []),
                }
        logger.debug("Loaded %d policy areas", len(self._policy_areas))

    def _load_questions_from_json(self, data: Dict[str, Any]) -> None:
        questions = data.get("preguntas_base", [])
        if not questions:
            logger.error("preguntas_base missing in cuestionario.json")
            raise ValueError("preguntas_base is required in cuestionario.json")

        logger.debug("Found %d base question entries", len(questions))

        has_templates = any(
            ("{PUNTO_TEMATICO}" in q.get("texto_template", "") or
             "{punto_tematico}" in q.get("texto_template", ""))
            for q in questions[:5]
        )

        if has_templates:
            logger.info("Template-based generation engaged")
            self._generate_questions_from_templates(questions)
        else:
            logger.info("Direct loading of fully enumerated questions")
            self._load_questions_direct(questions)

        logger.info("Question registry now holds %d entries", len(self._questions))

    def _generate_questions_from_templates(self, questions_data: List[Dict[str, Any]]) -> None:
        for policy_num in range(1, 11):
            pid = f"P{policy_num}"
            ptitle = self._policy_areas.get(pid, {}).get("titulo", pid)
            for qdata in questions_data:
                self._create_question_context(qdata, pid, ptitle)

    def _load_questions_direct(self, questions_data: List[Dict[str, Any]]) -> None:
        groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for qdata in questions_data:
            dimension = qdata.get("dimension", "")
            numero = qdata.get("numero", 1)
            groups[f"{dimension}-Q{numero}"].append(qdata)

        for variants in groups.values():
            for idx, qdata in enumerate(variants):
                policy_num = (idx % 10) + 1
                pid = f"P{policy_num}"
                ptitle = self._policy_areas.get(pid, {}).get("titulo", pid)
                self._create_question_context(qdata, pid, ptitle)

    def _create_question_context(
        self,
        question_data: Dict[str, Any],
        policy_id: str,
        policy_title: str
    ) -> None:
        base_id = question_data.get("id", "")
        dimension = question_data.get("dimension", "")
        qno = question_data.get("numero", 1)
        template = question_data.get("texto_template", "")

        text = template.replace("{PUNTO_TEMATICO}", policy_title)
        text = text.replace("{punto_tematico}", policy_title.lower())

        canonical_id = f"{policy_id}-{dimension}-Q{qno}"
        criterios = question_data.get("criterios_evaluacion", {})

        ctx = QuestionContext(
            question_id=base_id,
            canonical_id=canonical_id,
            dimension=dimension,
            question_no=qno,
            policy_area=policy_id,
            template=template,
            text=text,
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
                "peso_ponderado": criterios.get("peso_ponderado", 1.0),
            }
        )
        self._questions[canonical_id] = ctx

    # -------------------------------------------------------------------------
    # Rubric
    # -------------------------------------------------------------------------
    def _load_rubric(self) -> None:
        if not self.rubric_path.exists():
            logger.warning("rubric_scoring.json missing; using defaults")
            self._create_default_rubric()
            return

        try:
            with self.rubric_path.open('r', encoding='utf-8') as fh:
                data = json.load(fh)
            modalities = data.get("scoring_modalities", {})
            for mid, minfo in modalities.items():
                self._scoring_modalities[mid] = ScoringModality(
                    id=minfo.get("id", mid),
                    description=minfo.get("description", ""),
                    formula=minfo.get("formula", ""),
                    max_score=minfo.get("max_score", 3.0),
                    expected_elements=minfo.get("expected_elements", 0),
                    conversion_table=minfo.get("conversion_table", {}),
                    uses_thresholds=minfo.get("uses_thresholds", False),
                    uses_quantitative_data=minfo.get("uses_quantitative_data", False),
                    uses_custom_logic=minfo.get("uses_custom_logic", False),
                    uses_semantic_matching=minfo.get("uses_semantic_matching", False),
                    similarity_threshold=minfo.get("similarity_threshold", 0.0),
                )
            logger.info("Loaded %d scoring modalities", len(self._scoring_modalities))
        except Exception as e:
            logger.error("Failed loading rubric_scoring.json: %s", e)
            self._create_default_rubric()

    def _create_default_rubric(self) -> None:
        self._scoring_modalities = {
            "TYPE_A": ScoringModality(
                id="count_4_elements",
                description="Count 4 elements scaled to 0–3",
                formula="(elements_found / 4) * 3",
                max_score=3.0,
                expected_elements=4,
                conversion_table={"0": 0.0, "1": 0.75, "2": 1.5, "3": 2.25, "4": 3.0},
            ),
            "TYPE_B": ScoringModality(
                id="count_3_elements",
                description="Count up to 3 elements",
                formula="min(elements_found, 3)",
                max_score=3.0,
                expected_elements=3,
            ),
            "TYPE_C": ScoringModality(
                id="count_2_elements",
                description="Count 2 elements scaled to 0–3",
                formula="(elements_found / 2) * 3",
                max_score=3.0,
                expected_elements=2,
            ),
            "TYPE_D": ScoringModality(
                id="ratio_quantitative",
                description="Calculate ratio using thresholds",
                formula="threshold_function(ratio)",
                max_score=3.0,
                uses_thresholds=True,
                uses_quantitative_data=True,
            ),
        }
        logger.info("Default scoring modalities loaded (%d)", len(self._scoring_modalities))

    # -------------------------------------------------------------------------
    # Execution Mapping
    # -------------------------------------------------------------------------
    def _load_execution_mapping(self) -> None:
        if not self.execution_mapping_path.exists():
            logger.warning("execution_mapping.yaml missing; using defaults")
            self._create_default_execution_mapping()
            return
        try:
            with self.execution_mapping_path.open('r', encoding='utf-8') as fh:
                data = yaml.safe_load(fh) or {}
            self._execution_mapping = data
            logger.info("Loaded execution mapping")
        except Exception as e:
            logger.error("Failed loading execution_mapping.yaml: %s", e)
            self._create_default_execution_mapping()

    def _create_default_execution_mapping(self) -> None:
        self._execution_mapping = {
            "dimensions": {
                "D1": {
                    "module": "policy_processor",
                    "class": "IndustrialPolicyProcessor",
                    "method": "process",
                    "description": "Diagnóstico y Líneas Base",
                },
                "D2": {
                    "module": "causal_proccesor",
                    "class": "PolicyDocumentAnalyzer",
                    "method": "analyze_document",
                    "description": "Diseño de Intervención",
                },
                "D3": {
                    "module": "Analyzer_one",
                    "class": "MunicipalAnalyzer",
                    "method": "analyze",
                    "description": "Productos y Outputs",
                },
                "D4": {
                    "module": "teoria_cambio",
                    "class": "ModulosTeoriaCambio",
                    "method": "analizar_teoria_cambio",
                    "description": "Resultados y Outcomes",
                },
                "D5": {
                    "module": "dereck_beach",
                    "class": "DerekBeachAnalyzer",
                    "method": "analyze_causal_chain",
                    "description": "Impactos y Efectos",
                },
                "D6": {
                    "module": "teoria_cambio",
                    "class": "ModulosTeoriaCambio",
                    "method": "validar_coherencia_causal",
                    "description": "Teoría de Cambio",
                },
            }
        }
        logger.info("Default execution mapping loaded")

    # -------------------------------------------------------------------------
    # Cross-validation & Enrichment
    # -------------------------------------------------------------------------
    def _cross_validate(self) -> None:
        issues: List[str] = []
        for cid, q in self._questions.items():
            if q.scoring_modality not in self._scoring_modalities:
                issues.append(f"{cid}: undefined scoring modality {q.scoring_modality}")

        dims_in_use = {q.dimension for q in self._questions.values()}
        undefined_dims = dims_in_use - set(self._dimensions.keys())
        if undefined_dims:
            issues.append(f"Undefined dimensions referenced: {sorted(undefined_dims)}")

        policies_in_use = {q.policy_area for q in self._questions.values()}
        undefined_policies = policies_in_use - set(self._policy_areas.keys())
        if undefined_policies:
            issues.append(f"Undefined policy areas referenced: {sorted(undefined_policies)}")

        if issues:
            logger.warning("Cross-validation issues:\n%s", "\n".join(f"  - {i}" for i in issues))
        else:
            logger.info("Cross-validation passed without issues")

    def _enrich_execution_chains(self) -> None:
        overrides = self._execution_mapping.get("question_overrides", {}) or {}
        dim_map = self._execution_mapping.get("dimensions", {}) or {}
        for cid, q in self._questions.items():
            if cid in overrides:
                info = overrides[cid]
            else:
                info = dim_map.get(q.dimension, {})
            if info:
                q.execution_chain = [{
                    "module": info.get("module", ""),
                    "class": info.get("class", ""),
                    "method": info.get("method", ""),
                    "description": info.get("description", ""),
                    "confidence": info.get("confidence", 0.8),
                }]
        logger.debug("Execution chains populated")

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------
    def get_question_context(self, question_id: str) -> Optional[QuestionContext]:
        if question_id in self._questions:
            return self._questions[question_id]
        for q in self._questions.values():
            if q.question_id == question_id:
                return q
        logger.warning("Question not found: %s", question_id)
        return None

    def get_all_questions(self) -> Dict[str, QuestionContext]:
        return dict(self._questions)

    def get_questions_by_dimension(self, dimension: str) -> List[QuestionContext]:
        return [q for q in self._questions.values() if q.dimension == dimension]

    def get_questions_by_policy_area(self, policy_area: str) -> List[QuestionContext]:
        return [q for q in self._questions.values() if q.policy_area == policy_area]

    def get_scoring_modality(self, modality_id: str) -> Optional[ScoringModality]:
        return self._scoring_modalities.get(modality_id)

    def get_dimension_info(self, dimension_id: str) -> Optional[Dict[str, Any]]:
        return self._dimensions.get(dimension_id)

    def get_policy_area_info(self, policy_area_id: str) -> Optional[Dict[str, Any]]:
        return self._policy_areas.get(policy_area_id)

    def validate_questionnaire(self) -> Dict[str, Any]:
        issues: List[str] = []
        expected_total = 300
        if len(self._questions) != expected_total:
            issues.append(f"Expected {expected_total} questions, found {len(self._questions)}")

        for dim_id in self._dimensions.keys():
            dim_qs = self.get_questions_by_dimension(dim_id)
            expected_dim = 50  # 5 base × 10 policy areas
            if len(dim_qs) != expected_dim:
                issues.append(f"Dimension {dim_id}: expected {expected_dim}, found {len(dim_qs)}")

        for policy_id in self._policy_areas.keys():
            p_qs = self.get_questions_by_policy_area(policy_id)
            expected_policy = 30  # 30 base
            if len(p_qs) != expected_policy:
                issues.append(f"Policy area {policy_id}: expected {expected_policy}, found {len(p_qs)}")

        return {
            "valid": not issues,
            "total_questions": len(self._questions),
            "total_dimensions": len(self._dimensions),
            "total_policy_areas": len(self._policy_areas),
            "total_scoring_modalities": len(self._scoring_modalities),
            "issues": issues,
        }


# Singleton accessor if external modules rely on it
_METADATA_SERVICE_SINGLETON: Optional[MetadataService] = None


def get_metadata_service() -> MetadataService:
    global _METADATA_SERVICE_SINGLETON
    if _METADATA_SERVICE_SINGLETON is None:
        _METADATA_SERVICE_SINGLETON = MetadataService()
    return _METADATA_SERVICE_SINGLETON


if __name__ == "__main__":
    svc = MetadataService()
    print("=" * 80)
    print("METADATA SERVICE")
    print("=" * 80)
    print("\nStatistics:")
    print(f"  Total questions: {len(svc.get_all_questions())}")
    print(f"  Dimensions: {len(svc._dimensions)}")
    print(f"  Policy areas: {len(svc._policy_areas)}")
    print(f"  Scoring modalities: {len(svc._scoring_modalities)}")

    report = svc.validate_questionnaire()
    print(f"\nValidation: {'✓ PASS' if report['valid'] else '✗ FAIL'}")
    if report["issues"]:
        print("Issues:")
        for issue in report["issues"]:
            print(f"  - {issue}")

    example_id = "P1-D1-Q1"
    ctx = svc.get_question_context(example_id)
    print(f"\nExample context: {example_id}")
    if ctx:
        print(f"  Canonical: {ctx.canonical_id}")
        print(f"  Text: {ctx.text[:100]}...")
        print(f"  Scoring: {ctx.scoring_modality}")
        print(f"  Execution chain: {ctx.execution_chain}")
    print("=" * 80)