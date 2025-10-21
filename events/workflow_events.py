"""
Workflow Events for Event-Driven Choreography
==============================================

Defines all workflow events used in the policy analysis choreography.
Each event is immutable and carries QuestionContext for validation.

Author: FARFAN Integration Team
Version: 1.0.0
Python: 3.11+
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from .base_events import BaseEvent, EventType, EventStatus
from .question_context import QuestionContext


@dataclass(frozen=True)
class AnalysisRequestedEvent(BaseEvent):
    """
    Initial event requesting policy analysis for specific questions
    
    Attributes:
        document_reference: Path or ID of document to analyze
        target_question_ids: List of question IDs to analyze
        plan_name: Name of the policy plan
        plan_text: Full text of the policy document
    """
    
    event_type: EventType = EventType.ANALYSIS_REQUESTED
    document_reference: str = ""
    target_question_ids: List[str] = field(default_factory=list)
    plan_name: str = ""
    plan_text: str = ""


@dataclass(frozen=True)
class EnrichedAnalysisStepEvent(BaseEvent):
    """
    Analysis step enriched with QuestionContext
    
    Published by metadata enricher or components that fetch context
    
    Attributes:
        question_context: Rich context for the question
        document_reference: Reference to document being analyzed
        step_name: Name of this execution step
    """
    
    event_type: EventType = EventType.ENRICHED_ANALYSIS_STEP
    question_context: Optional[Dict[str, Any]] = None
    document_reference: str = ""
    step_name: str = ""


@dataclass(frozen=True)
class ChunkingCompleteEvent(BaseEvent):
    """
    Chunking/segmentation completed successfully
    
    Attributes:
        chunks: List of document chunks
        chunk_count: Number of chunks created
        chunk_metadata: Metadata about chunking process
        question_context_subset: Relevant QuestionContext fields
    """
    
    event_type: EventType = EventType.CHUNKING_COMPLETE
    chunks: List[Dict[str, Any]] = field(default_factory=list)
    chunk_count: int = 0
    chunk_metadata: Dict[str, Any] = field(default_factory=dict)
    question_context_subset: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class CausalExtractionCompleteEvent(BaseEvent):
    """
    Causal link extraction completed
    
    Attributes:
        causal_links: Extracted causal relationships
        causal_graph: Graph representation of causal links
        confidence: Confidence in extraction
        bayesian_support: Bayesian confidence scores
    """
    
    event_type: EventType = EventType.CAUSAL_EXTRACTION_COMPLETE
    causal_links: List[Dict[str, Any]] = field(default_factory=list)
    causal_graph: Optional[Dict[str, Any]] = None
    confidence: float = 0.0
    bayesian_support: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class FinancialAuditCompleteEvent(BaseEvent):
    """
    Financial analysis/audit completed
    
    Attributes:
        audit_results: Financial audit findings
        viability_score: Overall viability score
        resource_allocation: Resource allocation analysis
        budget_coherence: Budget coherence metrics
    """
    
    event_type: EventType = EventType.FINANCIAL_AUDIT_COMPLETE
    audit_results: Dict[str, Any] = field(default_factory=dict)
    viability_score: float = 0.0
    resource_allocation: Optional[Dict[str, Any]] = None
    budget_coherence: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class MicroScoreCompleteEvent(BaseEvent):
    """
    MICRO-level scoring completed (individual question)
    
    Attributes:
        score: Calculated score
        elements_found: Number of elements found
        elements_expected: Number of elements expected
        scoring_modality: Scoring method used
        evidence: Supporting evidence
    """
    
    event_type: EventType = EventType.MICRO_SCORE_COMPLETE
    score: float = 0.0
    elements_found: int = 0
    elements_expected: int = 0
    scoring_modality: str = ""
    evidence: List[Dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class MesoScoreCompleteEvent(BaseEvent):
    """
    MESO-level scoring completed (dimension or policy area cluster)
    
    Attributes:
        cluster_id: Dimension or policy area ID
        cluster_score: Aggregated score for cluster
        question_scores: Individual question scores in cluster
        coherence_metrics: Coherence metrics for cluster
    """
    
    event_type: EventType = EventType.MESO_SCORE_COMPLETE
    cluster_id: str = ""
    cluster_score: float = 0.0
    question_scores: Dict[str, float] = field(default_factory=dict)
    coherence_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MacroScoreCompleteEvent(BaseEvent):
    """
    MACRO-level scoring completed (overall plan alignment)
    
    Attributes:
        macro_score: Overall plan score
        dimension_scores: Scores by dimension
        policy_area_scores: Scores by policy area
        decalogo_alignment: Alignment with Decálogo framework
    """
    
    event_type: EventType = EventType.MACRO_SCORE_COMPLETE
    macro_score: float = 0.0
    dimension_scores: Dict[str, float] = field(default_factory=dict)
    policy_area_scores: Dict[str, float] = field(default_factory=dict)
    decalogo_alignment: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class FinalReportReadyEvent(BaseEvent):
    """
    Final report assembly completed
    
    Attributes:
        report_id: Unique report identifier
        micro_results: MICRO-level results
        meso_results: MESO-level results
        macro_results: MACRO-level results
        report_path: Path to generated report
        generation_metadata: Report generation metadata
    """
    
    event_type: EventType = EventType.FINAL_REPORT_READY
    report_id: str = ""
    micro_results: Dict[str, Any] = field(default_factory=dict)
    meso_results: Dict[str, Any] = field(default_factory=dict)
    macro_results: Dict[str, Any] = field(default_factory=dict)
    report_path: str = ""
    generation_metadata: Dict[str, Any] = field(default_factory=dict)


# Component-specific workflow events

@dataclass(frozen=True)
class SegmentationCompleteEvent(BaseEvent):
    """Document segmentation completed"""
    
    event_type: EventType = EventType.SEGMENTATION_COMPLETE
    segments: List[Dict[str, Any]] = field(default_factory=list)
    boundaries: List[int] = field(default_factory=list)


@dataclass(frozen=True)
class PreprocessingCompleteEvent(BaseEvent):
    """Document preprocessing completed"""
    
    event_type: EventType = EventType.PREPROCESSING_COMPLETE
    normalized_text: str = ""
    processed_document: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EmbeddingCompleteEvent(BaseEvent):
    """Embedding generation completed"""
    
    event_type: EventType = EventType.EMBEDDING_COMPLETE
    embeddings: List[List[float]] = field(default_factory=list)
    similarity_scores: Optional[Dict[str, float]] = None


@dataclass(frozen=True)
class SemanticAnalysisCompleteEvent(BaseEvent):
    """Semantic analysis completed"""
    
    event_type: EventType = EventType.SEMANTIC_ANALYSIS_COMPLETE
    semantic_chunks: List[Dict[str, Any]] = field(default_factory=list)
    chunk_embeddings: Optional[List[List[float]]] = None


@dataclass(frozen=True)
class MunicipalAnalysisCompleteEvent(BaseEvent):
    """Municipal development analysis completed"""
    
    event_type: EventType = EventType.MUNICIPAL_ANALYSIS_COMPLETE
    municipal_analysis: Dict[str, Any] = field(default_factory=dict)
    quality_metrics: Dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class TheoryChangeCompleteEvent(BaseEvent):
    """Theory of change analysis completed"""
    
    event_type: EventType = EventType.THEORY_CHANGE_COMPLETE
    causal_graph: Dict[str, Any] = field(default_factory=dict)
    bayesian_confidence: float = 0.0


@dataclass(frozen=True)
class DerekBeachCompleteEvent(BaseEvent):
    """Derek Beach causal analysis completed"""
    
    event_type: EventType = EventType.DEREK_BEACH_COMPLETE
    causal_links: List[Dict[str, Any]] = field(default_factory=list)
    cdaf_analysis: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ContradictionDetectionCompleteEvent(BaseEvent):
    """Contradiction detection completed"""
    
    event_type: EventType = EventType.CONTRADICTION_DETECTION_COMPLETE
    contradictions: List[Dict[str, Any]] = field(default_factory=list)
    alignment_score: float = 0.0
