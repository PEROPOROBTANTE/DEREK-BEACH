# -*- coding: utf-8 -*-
"""
Semantic Chunking Policy Module Adapter
=======================================

Adapter for semantic_chunking_policy.py to integrate with module_controller.py.
Provides standardized interface for:
- PolicyDocumentAnalyzer
- BayesianEvidenceIntegrator
- SemanticProcessor

This adapter wraps the semantic chunking functionality to work with the
DEREK-BEACH orchestration framework.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

try:
    from semantic_chunking_policy import (
        PolicyDocumentAnalyzer,
        BayesianEvidenceIntegrator,
        SemanticProcessor,
        SemanticConfig,
        CausalDimension,
        PDMSection
    )
    SEMANTIC_AVAILABLE = True
except ImportError as e:
    SEMANTIC_AVAILABLE = False
    IMPORT_ERROR = str(e)

logger = logging.getLogger(__name__)


@dataclass
class SemanticAnalysisResult:
    """Result from semantic analysis"""
    status: str
    summary: Dict[str, Any]
    causal_dimensions: Dict[str, Dict[str, Any]]
    key_excerpts: Dict[str, List[str]]
    execution_time: float
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class SemanticChunkingAdapter:
    """
    Adapter for semantic_chunking_policy.py module
    
    Provides standardized interface for the orchestrator to use
    semantic chunking and policy analysis capabilities.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize adapter
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.available = SEMANTIC_AVAILABLE
        
        if not self.available:
            logger.warning(
                f"Semantic chunking module not available: {IMPORT_ERROR}"
            )
            return
        
        # Create semantic config from adapter config
        semantic_config_params = {
            "chunk_size": self.config.get("chunk_size", 768),
            "chunk_overlap": self.config.get("chunk_overlap", 128),
            "similarity_threshold": self.config.get("similarity_threshold", 0.82),
            "min_evidence_chunks": self.config.get("min_evidence_chunks", 3),
            "bayesian_prior_strength": self.config.get("bayesian_prior_strength", 0.5),
            "device": self.config.get("device", None),
            "batch_size": self.config.get("batch_size", 32),
            "fp16": self.config.get("fp16", True)
        }
        
        self.semantic_config = SemanticConfig(**semantic_config_params)
        self.analyzer = None
        
        logger.info("SemanticChunkingAdapter initialized")
    
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get adapter capabilities
        
        Returns:
            Dictionary describing available methods and features
        """
        return {
            "name": "semantic_chunking",
            "version": "1.0",
            "available": self.available,
            "methods": [
                "analyze_policy_document",
                "chunk_text",
                "integrate_evidence",
                "compute_causal_strength"
            ],
            "features": {
                "policy_aware_chunking": True,
                "bayesian_evidence_integration": True,
                "causal_dimension_analysis": True,
                "pdm_structure_detection": True
            },
            "supported_dimensions": [dim.value for dim in CausalDimension] if SEMANTIC_AVAILABLE else [],
            "supported_sections": [sec.value for sec in PDMSection] if SEMANTIC_AVAILABLE else []
        }
    
    def _ensure_analyzer(self):
        """Lazy load analyzer on first use"""
        if not self.available:
            raise RuntimeError(
                f"Semantic chunking module not available: {IMPORT_ERROR}"
            )
        
        if self.analyzer is None:
            self.analyzer = PolicyDocumentAnalyzer(self.semantic_config)
            logger.info("PolicyDocumentAnalyzer loaded")
    
    def analyze_policy_document(
        self,
        text: str,
        question_context: Optional[Any] = None,
        **kwargs
    ) -> SemanticAnalysisResult:
        """
        Analyze a policy document with semantic chunking
        
        Args:
            text: Policy document text to analyze
            question_context: Optional QuestionContext from orchestrator
            **kwargs: Additional parameters
            
        Returns:
            SemanticAnalysisResult with analysis results
        """
        start_time = datetime.now()
        
        try:
            self._ensure_analyzer()
            
            logger.info(f"Analyzing policy document ({len(text)} chars)")
            
            # Run analysis
            results = self.analyzer.analyze(text)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Create result
            result = SemanticAnalysisResult(
                status="success",
                summary=results["summary"],
                causal_dimensions=results["causal_dimensions"],
                key_excerpts=results["key_excerpts"],
                execution_time=execution_time,
                metadata={
                    "text_length": len(text),
                    "timestamp": datetime.now().isoformat(),
                    "config": {
                        "chunk_size": self.semantic_config.chunk_size,
                        "similarity_threshold": self.semantic_config.similarity_threshold
                    }
                }
            )
            
            if question_context:
                result.metadata["question_id"] = getattr(question_context, "question_id", None)
                result.metadata["dimension"] = getattr(question_context, "dimension", None)
            
            logger.info(
                f"Analysis complete in {execution_time:.2f}s: "
                f"{results['summary']['total_chunks']} chunks, "
                f"{results['summary']['sections_detected']} sections"
            )
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Analysis failed: {e}", exc_info=True)
            
            return SemanticAnalysisResult(
                status="failed",
                summary={},
                causal_dimensions={},
                key_excerpts={},
                execution_time=execution_time,
                errors=[str(e)]
            )
    
    def chunk_text(
        self,
        text: str,
        preserve_structure: bool = True,
        question_context: Optional[Any] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Chunk text with policy-aware semantic chunking
        
        Args:
            text: Text to chunk
            preserve_structure: Whether to preserve PDM structure
            question_context: Optional QuestionContext
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with chunks and metadata
        """
        start_time = datetime.now()
        
        try:
            if not self.available:
                raise RuntimeError(f"Module not available: {IMPORT_ERROR}")
            
            processor = SemanticProcessor(self.semantic_config)
            chunks = processor.chunk_text(text, preserve_structure=preserve_structure)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Remove embeddings from output (too large)
            chunks_without_embeddings = []
            for chunk in chunks:
                chunk_copy = {k: v for k, v in chunk.items() if k != "embedding"}
                chunk_copy["embedding_shape"] = chunk["embedding"].shape if "embedding" in chunk else None
                chunks_without_embeddings.append(chunk_copy)
            
            return {
                "status": "success",
                "chunks": chunks_without_embeddings,
                "n_chunks": len(chunks),
                "execution_time": execution_time,
                "metadata": {
                    "text_length": len(text),
                    "preserve_structure": preserve_structure,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Chunking failed: {e}", exc_info=True)
            
            return {
                "status": "failed",
                "chunks": [],
                "n_chunks": 0,
                "execution_time": execution_time,
                "errors": [str(e)]
            }
    
    def integrate_evidence(
        self,
        similarities: List[float],
        chunk_metadata: List[Dict[str, Any]],
        prior_concentration: float = 0.5,
        question_context: Optional[Any] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Integrate evidence using Bayesian methods
        
        Args:
            similarities: List of similarity scores
            chunk_metadata: Metadata for each chunk
            prior_concentration: Bayesian prior strength
            question_context: Optional QuestionContext
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with evidence integration results
        """
        start_time = datetime.now()
        
        try:
            if not self.available:
                raise RuntimeError(f"Module not available: {IMPORT_ERROR}")
            
            import numpy as np
            
            integrator = BayesianEvidenceIntegrator(prior_concentration=prior_concentration)
            sims = np.array(similarities, dtype=np.float64)
            
            result = integrator.integrate_evidence(sims, chunk_metadata)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "status": "success",
                "evidence": result,
                "execution_time": execution_time,
                "metadata": {
                    "n_similarities": len(similarities),
                    "prior_concentration": prior_concentration,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Evidence integration failed: {e}", exc_info=True)
            
            return {
                "status": "failed",
                "evidence": {},
                "execution_time": execution_time,
                "errors": [str(e)]
            }
    
    def compute_causal_strength(
        self,
        cause_embedding: List[float],
        effect_embedding: List[float],
        context_embedding: List[float],
        prior_concentration: float = 0.5,
        question_context: Optional[Any] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Compute causal strength between cause and effect
        
        Args:
            cause_embedding: Embedding vector for cause
            effect_embedding: Embedding vector for effect
            context_embedding: Embedding vector for context
            prior_concentration: Bayesian prior strength
            question_context: Optional QuestionContext
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with causal strength result
        """
        start_time = datetime.now()
        
        try:
            if not self.available:
                raise RuntimeError(f"Module not available: {IMPORT_ERROR}")
            
            import numpy as np
            
            integrator = BayesianEvidenceIntegrator(prior_concentration=prior_concentration)
            
            cause_emb = np.array(cause_embedding, dtype=np.float32)
            effect_emb = np.array(effect_embedding, dtype=np.float32)
            context_emb = np.array(context_embedding, dtype=np.float32)
            
            strength = integrator.causal_strength(cause_emb, effect_emb, context_emb)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "status": "success",
                "causal_strength": float(strength),
                "execution_time": execution_time,
                "metadata": {
                    "embedding_dims": len(cause_embedding),
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Causal strength computation failed: {e}", exc_info=True)
            
            return {
                "status": "failed",
                "causal_strength": 0.0,
                "execution_time": execution_time,
                "errors": [str(e)]
            }


# Factory function for module_controller
def create_adapter(config: Optional[Dict[str, Any]] = None) -> SemanticChunkingAdapter:
    """
    Factory function to create adapter instance
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        SemanticChunkingAdapter instance
    """
    return SemanticChunkingAdapter(config)


if __name__ == "__main__":
    # Test the adapter
    print("=" * 80)
    print("SEMANTIC CHUNKING ADAPTER TEST")
    print("=" * 80)
    
    adapter = create_adapter()
    
    print(f"\nAdapter available: {adapter.available}")
    
    if adapter.available:
        capabilities = adapter.get_capabilities()
        print(f"\nCapabilities:")
        print(f"  Name: {capabilities['name']}")
        print(f"  Version: {capabilities['version']}")
        print(f"  Methods: {len(capabilities['methods'])}")
        print(f"  Features: {list(capabilities['features'].keys())}")
        print(f"  Supported dimensions: {len(capabilities['supported_dimensions'])}")
        
        # Test with sample text
        sample_text = """
        PLAN DE DESARROLLO MUNICIPAL 2024-2027
        
        1. DIAGNÓSTICO
        El municipio cuenta con 45,000 habitantes.
        
        2. PLAN DE INVERSIONES
        Educación: $8,500 millones
        Salud: $6,200 millones
        """
        
        print(f"\nTesting chunking with sample PDM...")
        result = adapter.chunk_text(sample_text)
        print(f"  Status: {result['status']}")
        print(f"  Chunks: {result['n_chunks']}")
        print(f"  Time: {result['execution_time']:.3f}s")
    else:
        print("\nAdapter not available - dependencies missing")
        print("Install: pip install torch transformers sentence-transformers")
    
    print("\n" + "=" * 80)
