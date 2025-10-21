# Module Adapters Framework

## Overview

This file provides adapter classes for 9 different policy analysis modules. Each adapter acts as a bridge between the central system and external analysis modules.

## Important: No Simulations or Mocks

**This framework requires real implementations.** All simulation code has been removed. Each adapter will only be marked as "available" if the corresponding external module can be successfully imported.

## Required External Modules

For the adapters to function, the following Python modules must be installed and available:

### 1. policy_processor
**Status:** NOT AVAILABLE (module does not exist)
- **Classes:** ProcessorConfig, BayesianEvidenceScorer, PolicyTextProcessor, EvidenceBundle, IndustrialPolicyProcessor, AdvancedTextSanitizer, ResilientFileHandler, PolicyAnalysisPipeline
- **Methods:** 34 total methods
- **Purpose:** Industrial policy processing system with Bayesian evidence scoring

### 2. policy_segmenter
**Status:** NOT AVAILABLE (module does not exist)
- **Classes:** SpanishSentenceSegmenter, BayesianBoundaryScorer, StructureDetector, DPSegmentOptimizer, DocumentSegmenter
- **Methods:** 33 total methods
- **Purpose:** Document segmentation system with Spanish language support

### 3. teoria_cambio
**Status:** NOT AVAILABLE (module does not exist)
- **Classes:** TeoriaCambio, AdvancedDAGValidator, IndustrialGradeValidator, CategoriaCausal, GraphType, ValidacionResultado, ValidationMetric, AdvancedGraphNode, MonteCarloAdvancedResult
- **Methods:** 51 total methods
- **Purpose:** Theory of change validation framework with causal analysis

### 4. analyzer_one
**Status:** NOT AVAILABLE (module does not exist)
- **Classes:** TextProcessor, EntityExtractor, SemanticAnalyzer, ReportGenerator
- **Methods:** 39 total methods
- **Purpose:** Policy analysis system with text processing and entity extraction

### 5. derek_beach
**Status:** NOT AVAILABLE (module does not exist)
- **Classes:** ProblemAnalysis, PolicyFormulation, ImplementationPlanning, EvaluationFramework, ProcessTracingAnalyzer
- **Methods:** 89 total methods
- **Purpose:** Derek Beach methodology for public policy analysis

### 6. embedding_policy
**Status:** NOT AVAILABLE (module does not exist)
- **Classes:** EmbeddingGenerator, PolicyComparer, ClusterAnalyzer, SemanticSearcher
- **Methods:** 37 total methods
- **Purpose:** Policy analysis using semantic embeddings

### 7. semantic_chunking_policy
**Status:** NOT AVAILABLE (module does not exist)
- **Classes:** SemanticChunker, ChunkMerger, BoundaryDetector
- **Methods:** 18 total methods
- **Purpose:** Semantic document chunking for policy analysis

### 8. contradiction_detection
**Status:** NOT AVAILABLE (module does not exist)
- **Classes:** ContradictionType, PolicyDimension, PolicyStatement, ContradictionEvidence, PolicyContradictionDetector, BayesianConfidenceCalculator, TemporalLogicVerifier
- **Methods:** 52 total methods
- **Purpose:** Detection of contradictions in policy documents

### 9. financiero_viabilidad_tablas
**Status:** NOT AVAILABLE (module does not exist)
- **Classes:** PDETMunicipalPlanAnalyzer
- **Methods:** 60 total methods (20 implemented, 40 stubs)
- **Purpose:** Financial viability analysis for municipal development plans

## Usage

```python
from modules_adapters import ModuleAdapterRegistry

# Create registry - will automatically attempt to load all adapters
registry = ModuleAdapterRegistry()

# Check which adapters are available
available = registry.get_available_modules()
print(f"Available adapters: {available}")

# Check status of all adapters
status = registry.get_module_status()
for module_name, is_available in status.items():
    status_str = "✓ Available" if is_available else "✗ Not Available"
    print(f"{module_name}: {status_str}")

# Execute a method on an available adapter
if "policy_processor" in available:
    result = registry.execute_module_method(
        module_name="policy_processor",
        method_name="process",
        args=[],
        kwargs={"text": "Sample policy text"}
    )
```

## Implementation Requirements

To make an adapter functional:

1. Create the external module with the required classes
2. Implement all required methods in those classes
3. Ensure the module is in the Python path
4. The adapter will automatically detect and load the module

## Data Sources

The framework is designed to work with real data from:
- **cuestionario.json**: Questionnaire data for policy analysis (file must be provided)
- **Academic journals**: Calibration data from A-rated journal publications
- **Real policy documents**: Actual municipal development plans and policy texts

## Performance Considerations

- All adapters use lazy loading - modules are only imported when the adapter is instantiated
- Failed imports are caught gracefully and logged
- Unavailable adapters do not block the system
- Method execution is logged with timing information

## Maintenance

When adding a new adapter:
1. Follow the BaseAdapter pattern
2. Implement `_load_module()` to import required classes
3. Implement `execute()` to dispatch method calls
4. Add proper error handling and logging
5. Register the adapter in `ModuleAdapterRegistry._register_all_adapters()`

## Notes

- **No simulation code**: All `random` calls have been removed
- **Real implementations only**: Adapters require actual module imports
- **Honest status reporting**: Adapters correctly report availability
- **Production ready**: Code is ready for integration with real modules
