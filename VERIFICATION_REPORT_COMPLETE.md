================================================================================
MODULE ADAPTER VERIFICATION REPORT
================================================================================

### causal_proccesor.py
Coverage: 100.0%

✓ Present Classes (6):
  - CausalDimension
  - PDMSection
  - SemanticConfig
  - SemanticProcessor
    Methods: __init__, _lazy_load, chunk_text, _detect_pdm_structure, _detect_table, _detect_numerical_data, _embed_batch, embed_single
  - BayesianEvidenceIntegrator
    Methods: __init__, integrate_evidence, _similarity_to_probability, _compute_reliability_weights, _null_evidence, causal_strength
  - PolicyDocumentAnalyzer
    Methods: __init__, _init_dimension_embeddings, analyze, _extract_key_excerpts

--------------------------------------------------------------------------------

### Analyzer_one.py
Coverage: 33.3%

✓ Present Classes (9):
  - MunicipalOntology
    Methods: __init__
  - SemanticAnalyzer
    Methods: __init__, _process_segment
  - PerformanceAnalyzer
    Methods: __init__, _generate_recommendations
  - TextMiningEngine
    Methods: __init__
  - MunicipalAnalyzer
    Methods: __init__
  - DocumentProcessor
  - ResultsExporter
  - ConfigurationManager
    Methods: __init__
  - BatchProcessor
    Methods: __init__

✗ Missing Classes (1):
  - ValueChainLink

⚠ Missing Methods:
  SemanticAnalyzer:
    - extract_semantic_cube
    - _empty_semantic_cube
    - _vectorize_segments
    - _classify_value_chain_link
    - _classify_policy_domain
    - _classify_cross_cutting_themes
    - _calculate_semantic_complexity
  PerformanceAnalyzer:
    - analyze_performance
    - _calculate_throughput_metrics
    - _detect_bottlenecks
    - _calculate_loss_functions
  TextMiningEngine:
    - diagnose_critical_links
    - _identify_critical_links
    - _analyze_link_text
    - _assess_risks
    - _generate_interventions
  MunicipalAnalyzer:
    - analyze_document
    - _load_document
    - _generate_summary
  DocumentProcessor:
    - load_pdf
    - load_docx
    - segment_text
  ResultsExporter:
    - export_to_json
    - export_to_excel
    - export_summary_report
  ConfigurationManager:
    - load_config
    - save_config
  BatchProcessor:
    - process_directory
    - export_batch_results
    - _create_batch_summary

--------------------------------------------------------------------------------

### contradiction_deteccion.py
Coverage: 53.2%

✓ Present Classes (7):
  - ContradictionType
  - PolicyDimension
  - PolicyStatement
  - ContradictionEvidence
  - BayesianConfidenceCalculator
    Methods: __init__, calculate_posterior
  - TemporalLogicVerifier
    Methods: __init__, verify_temporal_consistency, _build_timeline, _parse_temporal_marker, _has_temporal_conflict, _extract_resources, _check_deadline_constraints, _should_precede, _classify_temporal_type
  - PolicyContradictionDetector
    Methods: __init__, detect, _extract_policy_statements, _generate_embeddings, _build_knowledge_graph, _detect_semantic_contradictions, _detect_numerical_inconsistencies, _detect_temporal_conflicts, _detect_logical_incompatibilities, _detect_resource_conflicts, _calculate_coherence_metrics, _calculate_confidence_interval, _generate_resolution_recommendations, _serialize_contradiction, _get_graph_statistics

⚠ Missing Methods:
  TemporalLogicVerifier:
    - _are_mutually_exclusive
  PolicyContradictionDetector:
    - _initialize_pdm_patterns
    - _calculate_global_semantic_coherence
    - _calculate_objective_alignment
    - _calculate_graph_fragmentation
    - _calculate_contradiction_entropy
    - _calculate_syntactic_complexity
    - _get_dependency_depth
    - _identify_affected_sections
    - _extract_temporal_markers
    - _extract_quantitative_claims
    - _parse_number
    - _extract_resource_mentions
    - _determine_semantic_role
    - _identify_dependencies
    - _get_context_window
    - _calculate_similarity
    - _classify_contradiction
    - _get_domain_weight
    - _suggest_resolutions
    - _are_comparable_claims
    - _text_similarity
    - _calculate_numerical_divergence
    - _statistical_significance_test
    - _has_logical_conflict
    - _are_conflicting_allocations

--------------------------------------------------------------------------------
