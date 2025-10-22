"""
Comprehensive Integration Tests for policy_segmenter.py
========================================================

Real integration tests (NO MOCKS) covering:
- BayesianBoundaryScorer with real embeddings
- DPSegmentOptimizer with real boundary scores
- DocumentSegmenter with PDM documents
- SpanishSentenceSegmenter with Spanish text
- StructureDetector with structured content
- All helper functions and edge cases

Execution traces logged to JSON-lines format.
Structured error handling throughout.
Reproducibility via seed fixing.

Author: FARFAN 3.0 - PDM Analysis System
"""

import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pytest

# Import module under test
from policy_segmenter import (
    BayesianBoundaryScorer,
    DocumentSegmenter,
    DPSegmentOptimizer,
    SegmentationStats,
    SegmentMetrics,
    SegmenterConfig,
    SectionType,
    SpanishSentenceSegmenter,
    StructureDetector,
    create_segmenter,
    example_pdm_segmentation,
)

# ============================================================================
# TEST CONFIGURATION
# ============================================================================

# Seed for reproducibility
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

# Trace log file
TRACE_LOG_FILE = Path("test_policy_segmenter_traces.jsonl")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ============================================================================
# TRACE LOGGING
# ============================================================================


class TraceLogger:
    """JSON-lines trace logger for test execution."""

    def __init__(self, filepath: Path):
        self.filepath = filepath
        # Clear file at start
        with open(filepath, "w") as f:
            pass

    def log(
        self,
        origin: str,
        input_summary: str,
        output_summary: str,
        status: str,
        duration_ms: float,
        seed: int = RANDOM_SEED,
        **kwargs,
    ):
        """Log test execution trace."""
        trace = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "origin": origin,
            "input_summary": input_summary,
            "output_summary": output_summary,
            "seed": seed,
            "duration_ms": round(duration_ms, 2),
            "status": status,
            **kwargs,
        }

        with open(self.filepath, "a") as f:
            f.write(json.dumps(trace) + "\n")


trace_logger = TraceLogger(TRACE_LOG_FILE)


# ============================================================================
# ERROR HANDLING
# ============================================================================


def normalize_error(exception: Exception, origin: str, stage: str) -> dict[str, Any]:
    """
    Normalize exception to structured error format.

    Returns:
        {"origin": "Class.method", "message": "...", "type": "...", "stage": "...", "trace": "short"}
    """
    import traceback

    return {
        "origin": origin,
        "message": str(exception),
        "type": type(exception).__name__,
        "stage": stage,
        "trace": traceback.format_exc().split("\n")[-3:-1],  # Last 2 lines
    }


# ============================================================================
# TEST FIXTURES
# ============================================================================


@pytest.fixture
def sample_spanish_text() -> str:
    """Sample Spanish text with various linguistic features."""
    return """
    El Dr. García presentó el diagnóstico municipal en enero. 
    La población alcanza los 75,320 habitantes según DANE 2023.
    Se identificaron 2,340 familias vulnerables. La tasa de desempleo es del 12.5%.
    
    ¿Cuáles son las estrategias prioritarias? El municipio implementará tres programas.
    Programa 1: Formación técnica y desarrollo de habilidades.
    Programa 2: Microcréditos productivos con tasa preferencial del 8% EA.
    Programa 3: Fortalecimiento empresarial.
    
    Los objetivos estratégicos incluyen: reducir brechas de género, mejorar infraestructura, 
    y fortalecer la participación ciudadana. El presupuesto asignado es de $450 millones.
    """


@pytest.fixture
def pdm_document() -> str:
    """Realistic PDM document excerpt."""
    return """
    PLAN DE DESARROLLO MUNICIPAL 2024-2027
    MUNICIPIO DE CAJICÁ, CUNDINAMARCA
    
    1. DIAGNÓSTICO MUNICIPAL
    
    El municipio de Cajicá presenta una población de 75,320 habitantes según 
    proyecciones DANE 2023. La caracterización socioeconómica evidencia que 
    el 18.5% de la población se encuentra en situación de vulnerabilidad. 
    Se identificaron 2,340 familias con necesidades básicas insatisfechas.
    
    La brecha de género en participación laboral alcanza el 23.7%, siendo 
    particularmente pronunciada en zonas rurales donde llega al 31.2%. 
    El diagnóstico territorial revela déficit en infraestructura educativa, 
    con 12 instituciones requiriendo intervención urgente.
    
    2. OBJETIVO ESTRATÉGICO: DERECHOS DE LAS MUJERES E IGUALDAD DE GÉNERO
    
    Reducir las brechas de género en el municipio mediante la implementación 
    de políticas públicas integrales que promuevan la autonomía económica, 
    la participación política y la prevención de violencias basadas en género.
    
    2.1 LÍNEA BASE Y RECURSOS ASIGNADOS
    
    Indicador de línea base: Tasa de participación laboral femenina 42.3%
    Meta cuatrienio: Alcanzar 55.8% (incremento del 32%)
    Presupuesto asignado: $450 millones de pesos para el período 2024-2027
    Fuentes de financiación: 60% recursos propios, 40% transferencias SGP
    
    2.2 DISEÑO DE INTERVENCIÓN
    
    Se implementarán tres programas complementarios:
    
    Programa 1: Formación técnica y desarrollo de habilidades
    - 500 mujeres beneficiarias en cursos técnicos laborales
    - Duración: 6 meses por cohorte, 4 cohortes en el cuatrienio
    - Inversión: $180 millones
    
    Programa 2: Microcréditos productivos
    - Línea de crédito con tasa preferencial 8% EA
    - 320 microcréditos otorgados entre $3 y $8 millones
    - Fondo rotatorio: $280 millones
    
    Programa 3: Fortalecimiento empresarial
    - Acompañamiento a 150 emprendimientos liderados por mujeres
    - Asesoría técnica, jurídica y comercial
    - Red de mentoras empresariales con 25 voluntarias
    
    2.3 PRODUCTOS ESPERADOS
    
    Output 1: 500 mujeres certificadas en competencias técnicas laborales
    Verificación: Certificados expedidos por SENA o instituciones homologadas
    Responsable: Secretaría de Desarrollo Económico
    
    Output 2: 320 microcréditos desembolsados a mujeres emprendedoras
    Verificación: Contratos de crédito firmados y recursos desembolsados
    Responsable: Oficina de Apoyo al Emprendimiento
    """


@pytest.fixture
def config_default() -> SegmenterConfig:
    """Default segmenter configuration."""
    return SegmenterConfig()


@pytest.fixture
def config_custom() -> SegmenterConfig:
    """Custom segmenter configuration."""
    return SegmenterConfig(
        target_char_min=600,
        target_char_max=800,
        target_sentences=2,
        max_segment_chars=1000,
        min_segment_chars=300,
    )


# ============================================================================
# TESTS: SectionType (Enum)
# ============================================================================


class TestSectionType:
    """Test SectionType enum."""

    def test_enum_members(self):
        """Test all enum members are defined."""
        start = time.time()
        origin = "SectionType.test_enum_members"

        try:
            # Verify all expected members
            expected_members = {
                "DIAGNOSTIC", "BASELINE", "RESOURCES", "CAPACITY", "BUDGET", "PARTICIPATION",
                "ACTIVITY", "MECHANISM", "INTERVENTION", "STRATEGY", "TIMELINE",
                "PRODUCT", "OUTPUT",
                "RESULT", "OUTCOME", "INDICATOR", "MONITORING",
                "IMPACT", "LONG_TERM_EFFECT",
                "CAUSAL_THEORY", "CAUSAL_LINK",
                "VISION", "OBJECTIVE", "RESPONSIBILITY",
            }

            actual_members = {member.name for member in SectionType}
            assert actual_members == expected_members, f"Missing or extra members: {actual_members ^ expected_members}"

            # Verify values are strings
            for member in SectionType:
                assert isinstance(member.value, str)

            duration_ms = (time.time() - start) * 1000
            trace_logger.log(
                origin=origin,
                input_summary="24 expected enum members",
                output_summary=f"Verified {len(actual_members)} members",
                status="success",
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            error = normalize_error(e, origin, "verification")
            trace_logger.log(
                origin=origin,
                input_summary="24 expected enum members",
                output_summary="Failed",
                status="error",
                duration_ms=duration_ms,
                error=error,
            )
            raise


# ============================================================================
# TESTS: Dataclasses
# ============================================================================


class TestDataclasses:
    """Test dataclasses."""

    def test_segment_metrics_immutable(self):
        """Test SegmentMetrics is immutable."""
        start = time.time()
        origin = "SegmentMetrics.test_immutability"

        try:
            metrics = SegmentMetrics(
                char_count=100,
                sentence_count=3,
                word_count=20,
                token_count=20,
                semantic_coherence=0.8,
                boundary_confidence=0.9,
                section_type="diagnostic",
            )

            # Try to modify (should raise FrozenInstanceError)
            with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
                metrics.char_count = 200

            duration_ms = (time.time() - start) * 1000
            trace_logger.log(
                origin=origin,
                input_summary="SegmentMetrics instance",
                output_summary="Verified immutability",
                status="success",
                duration_ms=duration_ms,
            )

        except pytest.raises.Exception:
            # Expected exception
            duration_ms = (time.time() - start) * 1000
            trace_logger.log(
                origin=origin,
                input_summary="SegmentMetrics instance",
                output_summary="Verified immutability (expected exception caught)",
                status="success",
                duration_ms=duration_ms,
            )

    def test_segmentation_stats_defaults(self):
        """Test SegmentationStats default values."""
        start = time.time()
        origin = "SegmentationStats.test_defaults"

        try:
            stats = SegmentationStats()

            assert stats.total_segments == 0
            assert stats.avg_char_length == 0.0
            assert stats.avg_sentence_count == 0.0
            assert stats.char_distribution == {}
            assert stats.consistency_score == 0.0

            duration_ms = (time.time() - start) * 1000
            trace_logger.log(
                origin=origin,
                input_summary="Default SegmentationStats",
                output_summary="All defaults verified",
                status="success",
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            error = normalize_error(e, origin, "verification")
            trace_logger.log(
                origin=origin,
                input_summary="Default SegmentationStats",
                output_summary="Failed",
                status="error",
                duration_ms=duration_ms,
                error=error,
            )
            raise

    def test_segmenter_config_immutable(self):
        """Test SegmenterConfig is immutable."""
        start = time.time()
        origin = "SegmenterConfig.test_immutability"

        try:
            config = SegmenterConfig()

            # Try to modify (should raise FrozenInstanceError)
            with pytest.raises(Exception):
                config.target_char_min = 500

            duration_ms = (time.time() - start) * 1000
            trace_logger.log(
                origin=origin,
                input_summary="SegmenterConfig instance",
                output_summary="Verified immutability",
                status="success",
                duration_ms=duration_ms,
            )

        except pytest.raises.Exception:
            # Expected exception
            pass


# ============================================================================
# TESTS: SpanishSentenceSegmenter
# ============================================================================


class TestSpanishSentenceSegmenter:
    """Test Spanish sentence segmentation."""

    def test_empty_text(self):
        """Test with empty text."""
        start = time.time()
        origin = "SpanishSentenceSegmenter.segment"

        try:
            result = SpanishSentenceSegmenter.segment("")
            assert result == []

            duration_ms = (time.time() - start) * 1000
            trace_logger.log(
                origin=origin,
                input_summary="Empty string",
                output_summary="Returned empty list",
                status="success",
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            error = normalize_error(e, origin, "segmentation")
            trace_logger.log(
                origin=origin,
                input_summary="Empty string",
                output_summary="Failed",
                status="error",
                duration_ms=duration_ms,
                error=error,
            )
            raise

    def test_abbreviations(self, sample_spanish_text):
        """Test abbreviation handling."""
        start = time.time()
        origin = "SpanishSentenceSegmenter.segment"

        try:
            text = "El Dr. García y la Dra. López asistieron. Fue muy interesante."
            sentences = SpanishSentenceSegmenter.segment(text)

            # Should be 2 sentences, not 4 (abbreviations protected)
            assert len(sentences) == 2
            assert "Dr. García" in sentences[0] or "Dra. López" in sentences[0]

            duration_ms = (time.time() - start) * 1000
            trace_logger.log(
                origin=origin,
                input_summary="Text with abbreviations (Dr., Dra.)",
                output_summary=f"{len(sentences)} sentences extracted",
                status="success",
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            error = normalize_error(e, origin, "segmentation")
            trace_logger.log(
                origin=origin,
                input_summary="Text with abbreviations",
                output_summary="Failed",
                status="error",
                duration_ms=duration_ms,
                error=error,
            )
            raise

    def test_complex_spanish_text(self, sample_spanish_text):
        """Test with complex Spanish text."""
        start = time.time()
        origin = "SpanishSentenceSegmenter.segment"

        try:
            sentences = SpanishSentenceSegmenter.segment(sample_spanish_text)

            assert len(sentences) > 0
            # Verify all sentences meet minimum length
            for sent in sentences:
                assert len(sent) > 10

            duration_ms = (time.time() - start) * 1000
            trace_logger.log(
                origin=origin,
                input_summary=f"Complex Spanish text ({len(sample_spanish_text)} chars)",
                output_summary=f"{len(sentences)} sentences extracted",
                status="success",
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            error = normalize_error(e, origin, "segmentation")
            trace_logger.log(
                origin=origin,
                input_summary="Complex Spanish text",
                output_summary="Failed",
                status="error",
                duration_ms=duration_ms,
                error=error,
            )
            raise

    def test_protect_restore_roundtrip(self):
        """Test abbreviation protection/restoration roundtrip."""
        start = time.time()
        origin = "SpanishSentenceSegmenter._protect/_restore"

        try:
            text = "El Dr. García es el Sr. Director. La Sra. López es la Dra. Jefa."
            protected = SpanishSentenceSegmenter._protect_abbreviations(text)
            restored = SpanishSentenceSegmenter._restore_abbreviations(protected)

            assert restored == text, "Roundtrip failed"
            assert "©PROTECTED©" in protected, "Protection not applied"
            assert "©PROTECTED©" not in restored, "Restoration incomplete"

            duration_ms = (time.time() - start) * 1000
            trace_logger.log(
                origin=origin,
                input_summary=f"Text with 4 abbreviations ({len(text)} chars)",
                output_summary="Roundtrip successful",
                status="success",
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            error = normalize_error(e, origin, "transformation")
            trace_logger.log(
                origin=origin,
                input_summary="Text with abbreviations",
                output_summary="Failed",
                status="error",
                duration_ms=duration_ms,
                error=error,
            )
            raise


# ============================================================================
# TESTS: StructureDetector
# ============================================================================


class TestStructureDetector:
    """Test structure detection."""

    def test_table_detection(self):
        """Test table detection."""
        start = time.time()
        origin = "StructureDetector.detect_structures"

        try:
            text = "Como se muestra en la Tabla 1, los resultados son positivos. Tabla 2 presenta datos adicionales."
            structures = StructureDetector.detect_structures(text)

            assert structures["has_table"] is True
            assert len(structures["table_regions"]) == 2

            duration_ms = (time.time() - start) * 1000
            trace_logger.log(
                origin=origin,
                input_summary="Text with 2 table markers",
                output_summary=f"Detected {len(structures['table_regions'])} tables",
                status="success",
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            error = normalize_error(e, origin, "detection")
            trace_logger.log(
                origin=origin,
                input_summary="Text with tables",
                output_summary="Failed",
                status="error",
                duration_ms=duration_ms,
                error=error,
            )
            raise

    def test_list_detection(self):
        """Test list detection."""
        start = time.time()
        origin = "StructureDetector.detect_structures"

        try:
            text = """
            Objetivos principales:
            - Reducir pobreza
            - Mejorar educación
            - Fortalecer salud
            
            Otros puntos importantes.
            """
            structures = StructureDetector.detect_structures(text)

            assert structures["has_list"] is True

            duration_ms = (time.time() - start) * 1000
            trace_logger.log(
                origin=origin,
                input_summary="Text with bullet list",
                output_summary=f"List detected: {structures['has_list']}",
                status="success",
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            error = normalize_error(e, origin, "detection")
            trace_logger.log(
                origin=origin,
                input_summary="Text with lists",
                output_summary="Failed",
                status="error",
                duration_ms=duration_ms,
                error=error,
            )
            raise

    def test_comprehensive_structure_detection(self, pdm_document):
        """Test comprehensive structure detection on PDM document."""
        start = time.time()
        origin = "StructureDetector.detect_structures"

        try:
            structures = StructureDetector.detect_structures(pdm_document)

            # Verify all keys present
            required_keys = {
                "has_table", "has_list", "has_numbers",
                "section_headers", "table_regions", "list_regions"
            }
            assert required_keys.issubset(structures.keys())

            # Verify has_numbers (PDM has many numbers)
            assert structures["has_numbers"] is True

            duration_ms = (time.time() - start) * 1000
            trace_logger.log(
                origin=origin,
                input_summary=f"PDM document ({len(pdm_document)} chars)",
                output_summary=f"Structures: tables={structures['has_table']}, lists={structures['has_list']}, numbers={structures['has_numbers']}",
                status="success",
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            error = normalize_error(e, origin, "detection")
            trace_logger.log(
                origin=origin,
                input_summary="PDM document",
                output_summary="Failed",
                status="error",
                duration_ms=duration_ms,
                error=error,
            )
            raise


# ============================================================================
# TESTS: BayesianBoundaryScorer
# ============================================================================


class TestBayesianBoundaryScorer:
    """Test Bayesian boundary scoring with real embeddings."""

    @pytest.fixture
    def scorer(self):
        """Create BayesianBoundaryScorer with real model."""
        return BayesianBoundaryScorer("sentence-transformers/paraphrase-multilingual-mpnet-base-v2")

    def test_initialization(self, scorer):
        """Test scorer initialization."""
        start = time.time()
        origin = "BayesianBoundaryScorer.__init__"

        try:
            assert scorer.model is not None
            assert scorer.model.max_seq_length == 256
            assert scorer.alpha_prior == 2.0
            assert scorer.beta_prior == 2.0

            duration_ms = (time.time() - start) * 1000
            trace_logger.log(
                origin=origin,
                input_summary="Model: paraphrase-multilingual-mpnet-base-v2",
                output_summary="Scorer initialized successfully",
                status="success",
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            error = normalize_error(e, origin, "initialization")
            trace_logger.log(
                origin=origin,
                input_summary="Model initialization",
                output_summary="Failed",
                status="error",
                duration_ms=duration_ms,
                error=error,
            )
            raise

    def test_score_boundaries_basic(self, scorer):
        """Test boundary scoring with basic input."""
        start = time.time()
        origin = "BayesianBoundaryScorer.score_boundaries"

        try:
            sentences = [
                "El diagnóstico municipal evidencia problemas estructurales.",
                "La población vulnerable alcanza el 18.5% del total.",
                "Se requiere implementar programas de formación técnica.",
                "Los recursos asignados suman $450 millones de pesos.",
            ]

            boundary_scores, confidence_intervals = scorer.score_boundaries(sentences)

            # Verify shapes
            assert len(boundary_scores) == len(sentences) - 1
            assert confidence_intervals.shape == (len(sentences) - 1, 2)

            # Verify dtypes
            assert boundary_scores.dtype == np.float32
            assert confidence_intervals.dtype == np.float32

            # Verify ranges
            assert np.all((boundary_scores >= 0.0) & (boundary_scores <= 1.0))
            assert np.all((confidence_intervals >= 0.0) & (confidence_intervals <= 1.0))

            # Verify credible intervals
            assert np.all(confidence_intervals[:, 0] <= confidence_intervals[:, 1])

            duration_ms = (time.time() - start) * 1000
            trace_logger.log(
                origin=origin,
                input_summary=f"{len(sentences)} Spanish sentences",
                output_summary=f"Scores: shape={boundary_scores.shape}, mean={boundary_scores.mean():.3f}",
                status="success",
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            error = normalize_error(e, origin, "scoring")
            trace_logger.log(
                origin=origin,
                input_summary=f"{len(sentences)} sentences",
                output_summary="Failed",
                status="error",
                duration_ms=duration_ms,
                error=error,
            )
            raise

    def test_score_boundaries_edge_cases(self, scorer):
        """Test edge cases for boundary scoring."""
        start = time.time()
        origin = "BayesianBoundaryScorer.score_boundaries"

        try:
            # Empty list
            scores, intervals = scorer.score_boundaries([])
            assert len(scores) == 0
            assert len(intervals) == 0

            # Single sentence
            scores, intervals = scorer.score_boundaries(["Una sola oración."])
            assert len(scores) == 0
            assert len(intervals) == 0

            duration_ms = (time.time() - start) * 1000
            trace_logger.log(
                origin=origin,
                input_summary="Edge cases (empty, single sentence)",
                output_summary="All edge cases handled correctly",
                status="success",
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            error = normalize_error(e, origin, "edge_cases")
            trace_logger.log(
                origin=origin,
                input_summary="Edge cases",
                output_summary="Failed",
                status="error",
                duration_ms=duration_ms,
                error=error,
            )
            raise

    def test_semantic_boundary_scores(self, scorer):
        """Test semantic boundary scoring."""
        start = time.time()
        origin = "BayesianBoundaryScorer._semantic_boundary_scores"

        try:
            # Create embeddings for similar and dissimilar sentences
            similar_sentences = [
                "El diagnóstico municipal presenta datos demográficos.",
                "La caracterización demográfica muestra tendencias poblacionales.",
            ]
            
            embeddings = scorer.model.encode(
                similar_sentences,
                normalize_embeddings=True,
                convert_to_numpy=True,
            ).astype(np.float32)

            scores = scorer._semantic_boundary_scores(embeddings)

            # Should have low scores (similar sentences = weak boundary)
            assert len(scores) == 1
            assert 0.0 <= scores[0] <= 1.0

            duration_ms = (time.time() - start) * 1000
            trace_logger.log(
                origin=origin,
                input_summary=f"2 similar sentences -> {embeddings.shape} embeddings",
                output_summary=f"Semantic score: {scores[0]:.3f} (low = similar)",
                status="success",
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            error = normalize_error(e, origin, "semantic_scoring")
            trace_logger.log(
                origin=origin,
                input_summary="Embeddings",
                output_summary="Failed",
                status="error",
                duration_ms=duration_ms,
                error=error,
            )
            raise

    def test_structural_boundary_scores(self, scorer):
        """Test structural boundary scoring."""
        start = time.time()
        origin = "BayesianBoundaryScorer._structural_boundary_scores"

        try:
            sentences = [
                "Primera oración con punto.",
                "Segunda oración, también con punto final.",
                "¿Tercera con signo de interrogación?",
                "CAPÍTULO 1: DIAGNÓSTICO MUNICIPAL",
            ]

            scores = scorer._structural_boundary_scores(sentences)

            assert len(scores) == len(sentences) - 1
            assert np.all((scores >= 0.0) & (scores <= 1.0))

            # Section marker should boost score
            assert scores[-1] > 0.5  # After "CAPÍTULO" marker

            duration_ms = (time.time() - start) * 1000
            trace_logger.log(
                origin=origin,
                input_summary=f"{len(sentences)} sentences with varied punctuation",
                output_summary=f"Scores: {scores.tolist()}",
                status="success",
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            error = normalize_error(e, origin, "structural_scoring")
            trace_logger.log(
                origin=origin,
                input_summary="Sentences",
                output_summary="Failed",
                status="error",
                duration_ms=duration_ms,
                error=error,
            )
            raise

    def test_bayesian_posterior(self, scorer):
        """Test Bayesian posterior computation."""
        start = time.time()
        origin = "BayesianBoundaryScorer._bayesian_posterior"

        try:
            # Create test scores
            semantic_scores = np.array([0.3, 0.7, 0.5], dtype=np.float32)
            structural_scores = np.array([0.4, 0.8, 0.6], dtype=np.float32)

            posterior_means, credible_intervals = scorer._bayesian_posterior(
                semantic_scores, structural_scores
            )

            # Verify shapes
            assert len(posterior_means) == 3
            assert credible_intervals.shape == (3, 2)

            # Verify ranges
            assert np.all((posterior_means >= 0.0) & (posterior_means <= 1.0))
            assert np.all((credible_intervals >= 0.0) & (credible_intervals <= 1.0))

            # Verify intervals are valid
            assert np.all(credible_intervals[:, 0] <= posterior_means)
            assert np.all(posterior_means <= credible_intervals[:, 1])

            duration_ms = (time.time() - start) * 1000
            trace_logger.log(
                origin=origin,
                input_summary=f"3 boundary positions",
                output_summary=f"Posteriors: {posterior_means.tolist()}",
                status="success",
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            error = normalize_error(e, origin, "bayesian_computation")
            trace_logger.log(
                origin=origin,
                input_summary="Scores",
                output_summary="Failed",
                status="error",
                duration_ms=duration_ms,
                error=error,
            )
            raise


# ============================================================================
# TESTS: DPSegmentOptimizer
# ============================================================================


class TestDPSegmentOptimizer:
    """Test dynamic programming optimization."""

    def test_initialization(self, config_default):
        """Test optimizer initialization."""
        start = time.time()
        origin = "DPSegmentOptimizer.__init__"

        try:
            optimizer = DPSegmentOptimizer(config_default)

            assert optimizer.config == config_default
            assert optimizer.target_length_mid == (700 + 900) / 2

            duration_ms = (time.time() - start) * 1000
            trace_logger.log(
                origin=origin,
                input_summary="Default config",
                output_summary="Optimizer initialized",
                status="success",
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            error = normalize_error(e, origin, "initialization")
            trace_logger.log(
                origin=origin,
                input_summary="Config",
                output_summary="Failed",
                status="error",
                duration_ms=duration_ms,
                error=error,
            )
            raise

    def test_optimize_cuts_basic(self, config_default):
        """Test cut optimization with basic input."""
        start = time.time()
        origin = "DPSegmentOptimizer.optimize_cuts"

        try:
            optimizer = DPSegmentOptimizer(config_default)

            sentences = [
                "Primera oración de diagnóstico municipal.",
                "Segunda oración con datos poblacionales importantes.",
                "Tercera oración sobre infraestructura educativa.",
                "Cuarta oración con indicadores de género.",
                "Quinta oración sobre programas de intervención.",
                "Sexta oración con presupuesto asignado.",
            ]

            # Create boundary scores (higher = stronger boundary)
            boundary_scores = np.array([0.3, 0.7, 0.4, 0.8, 0.5], dtype=np.float32)

            cut_indices, global_confidence = optimizer.optimize_cuts(sentences, boundary_scores)

            # Verify results
            assert isinstance(cut_indices, list)
            assert len(cut_indices) > 0
            assert all(0 <= idx < len(sentences) for idx in cut_indices)
            assert cut_indices == sorted(cut_indices)  # Should be sorted
            assert 0.0 <= global_confidence <= 1.0

            duration_ms = (time.time() - start) * 1000
            trace_logger.log(
                origin=origin,
                input_summary=f"{len(sentences)} sentences, {len(boundary_scores)} scores",
                output_summary=f"Cuts: {cut_indices}, confidence: {global_confidence:.3f}",
                status="success",
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            error = normalize_error(e, origin, "optimization")
            trace_logger.log(
                origin=origin,
                input_summary="Sentences and scores",
                output_summary="Failed",
                status="error",
                duration_ms=duration_ms,
                error=error,
            )
            raise

    def test_optimize_cuts_empty(self, config_default):
        """Test with empty input."""
        start = time.time()
        origin = "DPSegmentOptimizer.optimize_cuts"

        try:
            optimizer = DPSegmentOptimizer(config_default)

            cut_indices, global_confidence = optimizer.optimize_cuts([], np.array([]))

            assert cut_indices == []
            assert global_confidence == 0.0

            duration_ms = (time.time() - start) * 1000
            trace_logger.log(
                origin=origin,
                input_summary="Empty input",
                output_summary="Returned empty cuts",
                status="success",
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            error = normalize_error(e, origin, "edge_case")
            trace_logger.log(
                origin=origin,
                input_summary="Empty input",
                output_summary="Failed",
                status="error",
                duration_ms=duration_ms,
                error=error,
            )
            raise

    def test_cumulative_chars(self, config_default):
        """Test cumulative character calculation."""
        start = time.time()
        origin = "DPSegmentOptimizer._cumulative_chars"

        try:
            optimizer = DPSegmentOptimizer(config_default)

            sentences = ["ABC", "DE", "FGHI"]  # 3, 2, 4 chars
            cumul = optimizer._cumulative_chars(sentences)

            # Expected: [0, 4, 7, 12] (adding 1 for space)
            assert cumul[0] == 0
            assert cumul[1] == 3 + 1
            assert cumul[2] == 3 + 1 + 2 + 1
            assert cumul[3] == 3 + 1 + 2 + 1 + 4 + 1

            duration_ms = (time.time() - start) * 1000
            trace_logger.log(
                origin=origin,
                input_summary=f"3 sentences: {sentences}",
                output_summary=f"Cumulative: {cumul}",
                status="success",
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            error = normalize_error(e, origin, "computation")
            trace_logger.log(
                origin=origin,
                input_summary="Sentences",
                output_summary="Failed",
                status="error",
                duration_ms=duration_ms,
                error=error,
            )
            raise

    def test_segment_cost(self, config_default):
        """Test segment cost calculation."""
        start = time.time()
        origin = "DPSegmentOptimizer._segment_cost"

        try:
            optimizer = DPSegmentOptimizer(config_default)

            sentences = ["A" * 100] * 10  # 10 sentences of 100 chars each
            cumul_chars = optimizer._cumulative_chars(sentences)
            boundary_scores = np.array([0.5] * 9, dtype=np.float32)

            # Test normal segment (should have finite, reasonable cost)
            cost_normal = optimizer._segment_cost(0, 2, cumul_chars, boundary_scores, sentences)
            assert 0.0 <= cost_normal < 1e6

            # Test oversized segment (should have very high cost)
            cost_oversized = optimizer._segment_cost(0, 9, cumul_chars, boundary_scores, sentences)
            assert cost_oversized >= 1e6

            duration_ms = (time.time() - start) * 1000
            trace_logger.log(
                origin=origin,
                input_summary="10 sentences of 100 chars",
                output_summary=f"Normal cost: {cost_normal:.2f}, Oversized: {cost_oversized:.0f}",
                status="success",
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            error = normalize_error(e, origin, "cost_computation")
            trace_logger.log(
                origin=origin,
                input_summary="Sentences",
                output_summary="Failed",
                status="error",
                duration_ms=duration_ms,
                error=error,
            )
            raise


# ============================================================================
# TESTS: DocumentSegmenter
# ============================================================================


class TestDocumentSegmenter:
    """Test complete document segmentation."""

    def test_initialization_default(self):
        """Test segmenter initialization with default config."""
        start = time.time()
        origin = "DocumentSegmenter.__init__"

        try:
            segmenter = DocumentSegmenter()

            assert segmenter.config is not None
            assert segmenter.sentence_segmenter is not None
            assert segmenter.boundary_scorer is not None
            assert segmenter.structure_detector is not None
            assert segmenter.optimizer is not None
            assert segmenter._last_segments == []
            assert segmenter._last_stats is None

            duration_ms = (time.time() - start) * 1000
            trace_logger.log(
                origin=origin,
                input_summary="Default config (None)",
                output_summary="Segmenter initialized with all components",
                status="success",
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            error = normalize_error(e, origin, "initialization")
            trace_logger.log(
                origin=origin,
                input_summary="Default config",
                output_summary="Failed",
                status="error",
                duration_ms=duration_ms,
                error=error,
            )
            raise

    def test_segment_empty_text(self):
        """Test segmentation with empty text."""
        start = time.time()
        origin = "DocumentSegmenter.segment"

        try:
            segmenter = DocumentSegmenter()
            segments = segmenter.segment("")

            assert segments == []

            duration_ms = (time.time() - start) * 1000
            trace_logger.log(
                origin=origin,
                input_summary="Empty text",
                output_summary="Returned empty list",
                status="success",
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            error = normalize_error(e, origin, "segmentation")
            trace_logger.log(
                origin=origin,
                input_summary="Empty text",
                output_summary="Failed",
                status="error",
                duration_ms=duration_ms,
                error=error,
            )
            raise

    def test_segment_pdm_document(self, pdm_document):
        """Test segmentation with real PDM document."""
        start = time.time()
        origin = "DocumentSegmenter.segment"

        try:
            segmenter = DocumentSegmenter()
            segments = segmenter.segment(pdm_document)

            # Verify segments structure
            assert len(segments) > 0
            for segment in segments:
                assert "text" in segment
                assert "metrics" in segment
                assert "segment_type" in segment
                
                # Verify metrics
                metrics = segment["metrics"]
                assert isinstance(metrics, SegmentMetrics)
                assert metrics.char_count > 0
                assert metrics.sentence_count > 0
                assert 0.0 <= metrics.semantic_coherence <= 1.0
                assert 0.0 <= metrics.boundary_confidence <= 1.0

            duration_ms = (time.time() - start) * 1000
            trace_logger.log(
                origin=origin,
                input_summary=f"PDM document ({len(pdm_document)} chars)",
                output_summary=f"{len(segments)} segments created, avg {np.mean([s['metrics'].char_count for s in segments]):.0f} chars",
                status="success",
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            error = normalize_error(e, origin, "segmentation")
            trace_logger.log(
                origin=origin,
                input_summary="PDM document",
                output_summary="Failed",
                status="error",
                duration_ms=duration_ms,
                error=error,
            )
            raise

    def test_get_segmentation_report(self, pdm_document):
        """Test segmentation report generation."""
        start = time.time()
        origin = "DocumentSegmenter.get_segmentation_report"

        try:
            segmenter = DocumentSegmenter()
            
            # Before segmentation
            report_before = segmenter.get_segmentation_report()
            assert "error" in report_before

            # After segmentation
            segments = segmenter.segment(pdm_document)
            report = segmenter.get_segmentation_report()

            # Verify report structure
            assert "summary" in report
            assert "quality_metrics" in report
            assert "distributions" in report

            # Verify summary
            assert report["summary"]["total_segments"] == len(segments)
            assert report["summary"]["avg_char_length"] > 0

            # Verify quality metrics
            assert 0.0 <= report["quality_metrics"]["consistency_score"] <= 1.0
            assert 0.0 <= report["quality_metrics"]["overall_quality"] <= 1.0

            duration_ms = (time.time() - start) * 1000
            trace_logger.log(
                origin=origin,
                input_summary=f"{len(segments)} segments",
                output_summary=f"Report generated: quality={report['quality_metrics']['overall_quality']:.3f}",
                status="success",
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            error = normalize_error(e, origin, "report_generation")
            trace_logger.log(
                origin=origin,
                input_summary="Segments",
                output_summary="Failed",
                status="error",
                duration_ms=duration_ms,
                error=error,
            )
            raise

    def test_normalize_text(self):
        """Test text normalization."""
        start = time.time()
        origin = "DocumentSegmenter._normalize_text"

        try:
            text = "  Multiple    spaces   and\n\n\n\nexcessive newlines  "
            normalized = DocumentSegmenter._normalize_text(text)

            assert "    " not in normalized  # No multiple spaces
            assert "\n\n\n" not in normalized  # Max 2 newlines
            assert not normalized.startswith(" ")  # No leading space
            assert not normalized.endswith(" ")  # No trailing space

            duration_ms = (time.time() - start) * 1000
            trace_logger.log(
                origin=origin,
                input_summary=f"Text with formatting issues ({len(text)} chars)",
                output_summary=f"Normalized ({len(normalized)} chars)",
                status="success",
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            error = normalize_error(e, origin, "normalization")
            trace_logger.log(
                origin=origin,
                input_summary="Text",
                output_summary="Failed",
                status="error",
                duration_ms=duration_ms,
                error=error,
            )
            raise


# ============================================================================
# TESTS: Factory Functions
# ============================================================================


class TestFactoryFunctions:
    """Test factory functions."""

    def test_create_segmenter_default(self):
        """Test create_segmenter with default parameters."""
        start = time.time()
        origin = "create_segmenter"

        try:
            segmenter = create_segmenter()

            assert isinstance(segmenter, DocumentSegmenter)
            assert segmenter.config.target_char_min == 700
            assert segmenter.config.target_char_max == 900

            duration_ms = (time.time() - start) * 1000
            trace_logger.log(
                origin=origin,
                input_summary="Default parameters",
                output_summary="DocumentSegmenter created",
                status="success",
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            error = normalize_error(e, origin, "factory")
            trace_logger.log(
                origin=origin,
                input_summary="Default parameters",
                output_summary="Failed",
                status="error",
                duration_ms=duration_ms,
                error=error,
            )
            raise

    def test_create_segmenter_custom(self):
        """Test create_segmenter with custom parameters."""
        start = time.time()
        origin = "create_segmenter"

        try:
            segmenter = create_segmenter(
                target_char_min=600,
                target_char_max=800,
                target_sentences=2,
            )

            assert isinstance(segmenter, DocumentSegmenter)
            assert segmenter.config.target_char_min == 600
            assert segmenter.config.target_char_max == 800
            assert segmenter.config.target_sentences == 2

            duration_ms = (time.time() - start) * 1000
            trace_logger.log(
                origin=origin,
                input_summary="Custom parameters (600-800 chars, 2 sents)",
                output_summary="DocumentSegmenter created with custom config",
                status="success",
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            error = normalize_error(e, origin, "factory")
            trace_logger.log(
                origin=origin,
                input_summary="Custom parameters",
                output_summary="Failed",
                status="error",
                duration_ms=duration_ms,
                error=error,
            )
            raise


# ============================================================================
# INTEGRATION TEST: Full Pipeline
# ============================================================================


class TestFullPipeline:
    """Integration test for complete pipeline."""

    def test_end_to_end_segmentation(self, pdm_document):
        """Test complete end-to-end segmentation pipeline."""
        start = time.time()
        origin = "DocumentSegmenter.full_pipeline"

        try:
            # Create segmenter
            segmenter = create_segmenter(
                target_char_min=700,
                target_char_max=900,
                target_sentences=3,
            )

            # Segment document
            segments = segmenter.segment(pdm_document)

            # Verify segments
            assert len(segments) > 0

            # Verify all segments meet constraints (after post-processing)
            for segment in segments:
                assert segment["metrics"].char_count >= segmenter.config.min_segment_chars
                assert segment["metrics"].char_count <= segmenter.config.max_segment_chars * 1.1  # Small tolerance

            # Get report
            report = segmenter.get_segmentation_report()
            assert report["quality_metrics"]["overall_quality"] > 0.0

            # Verify determinism (run again)
            segments2 = segmenter.segment(pdm_document)
            assert len(segments) == len(segments2)

            duration_ms = (time.time() - start) * 1000
            trace_logger.log(
                origin=origin,
                input_summary=f"PDM document ({len(pdm_document)} chars)",
                output_summary=f"Pipeline complete: {len(segments)} segments, quality={report['quality_metrics']['overall_quality']:.3f}",
                status="success",
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            error = normalize_error(e, origin, "pipeline")
            trace_logger.log(
                origin=origin,
                input_summary="PDM document",
                output_summary="Failed",
                status="error",
                duration_ms=duration_ms,
                error=error,
            )
            raise


# ============================================================================
# TEST RUNNER
# ============================================================================


if __name__ == "__main__":
    """Run tests with pytest."""
    print("=" * 80)
    print("POLICY SEGMENTER - COMPREHENSIVE INTEGRATION TESTS")
    print("=" * 80)
    print(f"Trace log: {TRACE_LOG_FILE}")
    print(f"Random seed: {RANDOM_SEED}")
    print("=" * 80)
    print()

    # Run pytest
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--color=yes",
    ])

    print()
    print("=" * 80)
    print(f"Tests complete. Traces written to: {TRACE_LOG_FILE}")
    print("=" * 80)

    sys.exit(exit_code)
