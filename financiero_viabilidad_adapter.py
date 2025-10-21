# -*- coding: utf-8 -*-
"""
Financial Viability and Tables Module Adapter
==============================================

Adapter for financiero_viabilidad_tablas.py to integrate with module_controller.py.
Provides standardized interface for:
- PDETMunicipalPlanAnalyzer
- Table extraction
- Financial analysis
- Causal DAG construction
- Counterfactual scenarios

This adapter wraps the PDET analysis functionality to work with the
DEREK-BEACH orchestration framework.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

try:
    from financiero_viabilidad_tablas import (
        PDETMunicipalPlanAnalyzer,
        PDETAnalysisException,
        validate_pdf_path,
        setup_logging as setup_pdet_logging
    )
    FINANCIERO_AVAILABLE = True
except ImportError as e:
    FINANCIERO_AVAILABLE = False
    IMPORT_ERROR = str(e)

logger = logging.getLogger(__name__)


@dataclass
class FinancialAnalysisResult:
    """Result from financial analysis"""
    status: str
    total_budget: float
    financial_indicators: List[Dict[str, Any]]
    funding_sources: Dict[str, Any]
    sustainability_score: float
    risk_assessment: Dict[str, Any]
    execution_time: float
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CausalAnalysisResult:
    """Result from causal analysis"""
    status: str
    causal_dag: Dict[str, Any]
    causal_effects: List[Dict[str, Any]]
    counterfactuals: List[Dict[str, Any]]
    sensitivity_analysis: Dict[str, Any]
    quality_score: Dict[str, Any]
    execution_time: float
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class FinancieroViabilidadAdapter:
    """
    Adapter for financiero_viabilidad_tablas.py module
    
    Provides standardized interface for the orchestrator to use
    financial analysis and causal inference capabilities.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize adapter
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.available = FINANCIERO_AVAILABLE
        
        if not self.available:
            logger.warning(
                f"Financiero viabilidad module not available: {IMPORT_ERROR}"
            )
            return
        
        # Extract configuration
        self.use_gpu = self.config.get("use_gpu", True)
        self.language = self.config.get("language", "es")
        self.confidence_threshold = self.config.get("confidence_threshold", 0.7)
        
        self.analyzer = None
        
        logger.info("FinancieroViabilidadAdapter initialized")
    
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get adapter capabilities
        
        Returns:
            Dictionary describing available methods and features
        """
        return {
            "name": "financiero_viabilidad",
            "version": "5.0",
            "available": self.available,
            "methods": [
                "analyze_municipal_plan",
                "extract_tables",
                "analyze_financial_feasibility",
                "identify_responsible_entities",
                "construct_causal_dag",
                "estimate_causal_effects",
                "generate_counterfactuals",
                "sensitivity_analysis",
                "calculate_quality_score"
            ],
            "features": {
                "pdf_table_extraction": True,
                "financial_analysis": True,
                "bayesian_risk_inference": True,
                "causal_dag_construction": True,
                "causal_effect_estimation": True,
                "counterfactual_generation": True,
                "sensitivity_analysis": True,
                "quality_scoring": True
            },
            "supported_formats": ["pdf"],
            "language": "es"
        }
    
    def _ensure_analyzer(self):
        """Lazy load analyzer on first use"""
        if not self.available:
            raise RuntimeError(
                f"Financiero viabilidad module not available: {IMPORT_ERROR}"
            )
        
        if self.analyzer is None:
            self.analyzer = PDETMunicipalPlanAnalyzer(
                use_gpu=self.use_gpu,
                language=self.language,
                confidence_threshold=self.confidence_threshold
            )
            logger.info("PDETMunicipalPlanAnalyzer loaded")
    
    async def analyze_municipal_plan(
        self,
        pdf_path: str,
        output_dir: Optional[str] = None,
        question_context: Optional[Any] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Complete analysis of municipal development plan
        
        Args:
            pdf_path: Path to PDF file
            output_dir: Optional directory for outputs
            question_context: Optional QuestionContext from orchestrator
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with complete analysis results
        """
        start_time = datetime.now()
        
        try:
            self._ensure_analyzer()
            
            # Validate path
            pdf_path = str(validate_pdf_path(pdf_path))
            
            logger.info(f"Analyzing municipal plan: {pdf_path}")
            
            # Run complete analysis
            results = await self.analyzer.analyze_municipal_plan(
                pdf_path=pdf_path,
                output_dir=output_dir
            )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            results["status"] = "success"
            results["execution_time"] = execution_time
            
            if question_context:
                results["question_context"] = {
                    "question_id": getattr(question_context, "question_id", None),
                    "dimension": getattr(question_context, "dimension", None)
                }
            
            logger.info(
                f"Analysis complete in {execution_time:.2f}s: "
                f"Quality score {results['quality_score']['overall_score']:.2f}/10"
            )
            
            return results
            
        except PDETAnalysisException as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"PDET analysis error: {e}")
            
            return {
                "status": "failed",
                "error": str(e),
                "error_type": "PDETAnalysisException",
                "execution_time": execution_time
            }
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Analysis failed: {e}", exc_info=True)
            
            return {
                "status": "failed",
                "error": str(e),
                "error_type": type(e).__name__,
                "execution_time": execution_time
            }
    
    async def extract_tables(
        self,
        pdf_path: str,
        question_context: Optional[Any] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Extract tables from PDF
        
        Args:
            pdf_path: Path to PDF file
            question_context: Optional QuestionContext
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with extracted tables
        """
        start_time = datetime.now()
        
        try:
            self._ensure_analyzer()
            
            pdf_path = str(validate_pdf_path(pdf_path))
            
            logger.info(f"Extracting tables from: {pdf_path}")
            
            tables = await self.analyzer.extract_tables(pdf_path)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Convert tables to serializable format
            tables_data = []
            for table in tables:
                tables_data.append({
                    "page_number": table.page_number,
                    "table_type": table.table_type,
                    "extraction_method": table.extraction_method,
                    "confidence_score": table.confidence_score,
                    "is_fragmented": table.is_fragmented,
                    "rows": len(table.df),
                    "columns": len(table.df.columns),
                    "preview": table.df.head(3).to_dict() if not table.df.empty else {}
                })
            
            return {
                "status": "success",
                "tables": tables_data,
                "n_tables": len(tables),
                "execution_time": execution_time,
                "metadata": {
                    "pdf_path": pdf_path,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Table extraction failed: {e}", exc_info=True)
            
            return {
                "status": "failed",
                "tables": [],
                "n_tables": 0,
                "execution_time": execution_time,
                "errors": [str(e)]
            }
    
    def analyze_financial_feasibility(
        self,
        tables: List[Any],
        text: str,
        question_context: Optional[Any] = None,
        **kwargs
    ) -> FinancialAnalysisResult:
        """
        Analyze financial feasibility
        
        Args:
            tables: List of ExtractedTable objects
            text: Full document text
            question_context: Optional QuestionContext
            **kwargs: Additional parameters
            
        Returns:
            FinancialAnalysisResult with analysis
        """
        start_time = datetime.now()
        
        try:
            self._ensure_analyzer()
            
            logger.info("Analyzing financial feasibility")
            
            result = self.analyzer.analyze_financial_feasibility(tables, text)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return FinancialAnalysisResult(
                status="success",
                total_budget=float(result["total_budget"]),
                financial_indicators=result["financial_indicators"],
                funding_sources=result["funding_sources"],
                sustainability_score=result["sustainability_score"],
                risk_assessment=result["risk_assessment"],
                execution_time=execution_time,
                metadata={
                    "n_tables": len(tables),
                    "text_length": len(text),
                    "timestamp": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Financial analysis failed: {e}", exc_info=True)
            
            return FinancialAnalysisResult(
                status="failed",
                total_budget=0.0,
                financial_indicators=[],
                funding_sources={},
                sustainability_score=0.0,
                risk_assessment={},
                execution_time=execution_time,
                errors=[str(e)]
            )
    
    def construct_causal_dag(
        self,
        text: str,
        tables: List[Any],
        financial_analysis: Dict[str, Any],
        question_context: Optional[Any] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Construct causal directed acyclic graph
        
        Args:
            text: Document text
            tables: Extracted tables
            financial_analysis: Financial analysis results
            question_context: Optional QuestionContext
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with DAG structure
        """
        start_time = datetime.now()
        
        try:
            self._ensure_analyzer()
            
            logger.info("Constructing causal DAG")
            
            dag = self.analyzer.construct_causal_dag(text, tables, financial_analysis)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "status": "success",
                "nodes": len(dag.nodes),
                "edges": len(dag.edges),
                "pillar_nodes": [
                    n for n, node in dag.nodes.items() 
                    if node.node_type == 'pilar'
                ],
                "outcome_nodes": [
                    n for n, node in dag.nodes.items() 
                    if node.node_type == 'outcome'
                ],
                "execution_time": execution_time,
                "metadata": {
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"DAG construction failed: {e}", exc_info=True)
            
            return {
                "status": "failed",
                "nodes": 0,
                "edges": 0,
                "execution_time": execution_time,
                "errors": [str(e)]
            }


# Factory function for module_controller
def create_adapter(config: Optional[Dict[str, Any]] = None) -> FinancieroViabilidadAdapter:
    """
    Factory function to create adapter instance
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        FinancieroViabilidadAdapter instance
    """
    return FinancieroViabilidadAdapter(config)


if __name__ == "__main__":
    # Test the adapter
    print("=" * 80)
    print("FINANCIERO VIABILIDAD ADAPTER TEST")
    print("=" * 80)
    
    adapter = create_adapter(config={"use_gpu": False})
    
    print(f"\nAdapter available: {adapter.available}")
    
    if adapter.available:
        capabilities = adapter.get_capabilities()
        print(f"\nCapabilities:")
        print(f"  Name: {capabilities['name']}")
        print(f"  Version: {capabilities['version']}")
        print(f"  Methods: {len(capabilities['methods'])}")
        print(f"  Features: {len(capabilities['features'])}")
        print(f"  Supported formats: {capabilities['supported_formats']}")
    else:
        print("\nAdapter not available - dependencies missing")
        print("Install required packages:")
        print("  pip install camelot-py tabula-py pdfplumber PyMuPDF")
        print("  pip install spacy sentence-transformers pymc arviz")
        print("  python -m spacy download es_dep_news_trf")
    
    print("\n" + "=" * 80)
