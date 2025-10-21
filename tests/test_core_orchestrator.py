"""
Comprehensive Tests for FARFAN Core Orchestrator
================================================

Tests the complete FARFAN orchestration including:
- Single plan analysis
- Document loading (PDF, TXT, DOCX)
- MICRO/MESO/MACRO generation
- Batch processing
- Orchestrator status and statistics
- Report generation

Author: FARFAN Testing Team
Version: 1.0.0
Python: 3.11+
"""

import pytest
import time
from unittest.mock import Mock, MagicMock, patch, call, mock_open
from typing import Dict, List, Any
from pathlib import Path
import tempfile
import json

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core_orchestrator import FARFANOrchestrator


class TestOrchestratorInitialization:
    """Test FARFANOrchestrator initialization"""
    
    def test_initialization_with_registry_and_parser(self):
        """Test orchestrator initialization with registry and parser"""
        mock_registry = Mock()
        mock_registry.adapters = {"adapter1": Mock(), "adapter2": Mock()}
        mock_parser = Mock()
        
        orchestrator = FARFANOrchestrator(
            module_adapter_registry=mock_registry,
            questionnaire_parser=mock_parser
        )
        
        assert orchestrator.module_registry == mock_registry
        assert orchestrator.questionnaire_parser == mock_parser
        assert orchestrator.choreographer is not None
        assert orchestrator.circuit_breaker is not None
        assert orchestrator.report_assembler is not None
    
    def test_initialization_with_custom_config(self):
        """Test orchestrator initialization with custom config"""
        mock_registry = Mock()
        mock_registry.adapters = {}
        mock_parser = Mock()
        
        config = {"setting1": "value1", "setting2": "value2"}
        
        orchestrator = FARFANOrchestrator(
            module_adapter_registry=mock_registry,
            questionnaire_parser=mock_parser,
            config=config
        )
        
        assert orchestrator.config == config
    
    def test_initialization_tracks_adapter_count(self):
        """Test that initialization tracks adapter count"""
        mock_registry = Mock()
        mock_registry.adapters = {
            "adapter1": Mock(),
            "adapter2": Mock(),
            "adapter3": Mock()
        }
        mock_parser = Mock()
        
        orchestrator = FARFANOrchestrator(
            module_adapter_registry=mock_registry,
            questionnaire_parser=mock_parser
        )
        
        assert len(mock_registry.adapters) == 3


class TestDocumentLoading:
    """Test document loading functionality"""
    
    def test_load_txt_document(self):
        """Test loading TXT document"""
        mock_registry = Mock()
        mock_registry.adapters = {}
        orchestrator = FARFANOrchestrator(
            module_adapter_registry=mock_registry,
            questionnaire_parser=Mock()
        )
        
        # Create temporary TXT file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is a test document.\nWith multiple lines.")
            temp_path = Path(f.name)
        
        try:
            text = orchestrator._load_plan_document(temp_path)
            
            assert "This is a test document" in text
            assert "With multiple lines" in text
        finally:
            temp_path.unlink()
    
    def test_load_nonexistent_document(self):
        """Test loading non-existent document raises error"""
        mock_registry = Mock()
        mock_registry.adapters = {}
        orchestrator = FARFANOrchestrator(
            module_adapter_registry=mock_registry,
            questionnaire_parser=Mock()
        )
        
        with pytest.raises(FileNotFoundError):
            orchestrator._load_plan_document(Path("/nonexistent/file.txt"))
    
    def test_load_unsupported_format(self):
        """Test loading unsupported file format raises error"""
        mock_registry = Mock()
        mock_registry.adapters = {}
        orchestrator = FARFANOrchestrator(
            module_adapter_registry=mock_registry,
            questionnaire_parser=Mock()
        )
        
        # Create temporary file with unsupported extension
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(ValueError, match="Unsupported file format"):
                orchestrator._load_plan_document(temp_path)
        finally:
            temp_path.unlink()


class TestSinglePlanAnalysis:
    """Test single plan analysis"""
    
    @patch.object(FARFANOrchestrator, '_load_plan_document')
    def test_analyze_single_plan_success(self, mock_load):
        """Test successful single plan analysis"""
        mock_load.return_value = "Test plan text content"
        
        mock_registry = Mock()
        mock_registry.adapters = {}
        
        mock_parser = Mock()
        mock_question = Mock()
        mock_question.canonical_id = "P1-D1-Q1"
        mock_parser.parse_all_questions = Mock(return_value=[mock_question])
        
        orchestrator = FARFANOrchestrator(
            module_adapter_registry=mock_registry,
            questionnaire_parser=mock_parser
        )
        
        # Mock choreographer execution
        orchestrator.choreographer.execute_question_chain = Mock(
            return_value={
                "adapter1.method1": Mock(
                    status="COMPLETED",
                    output={"result": "data"}
                )
            }
        )
        
        # Mock report assembler
        mock_micro_answer = Mock()
        mock_micro_answer.metadata = {"policy_area": "P1"}
        mock_micro_answer.qualitative_note = "BUENO"
        orchestrator.report_assembler.generate_micro_answer = Mock(
            return_value=mock_micro_answer
        )
        orchestrator.report_assembler.generate_meso_cluster = Mock(return_value=Mock())
        
        mock_macro = Mock()
        mock_macro.overall_score = 75.0
        mock_macro.plan_classification = "BUENO"
        mock_macro.convergence_by_dimension = {}
        mock_macro.critical_gaps = []
        mock_macro.strategic_recommendations = []
        orchestrator.report_assembler.generate_macro_convergence = Mock(
            return_value=mock_macro
        )
        orchestrator.report_assembler.export_report = Mock()
        
        with tempfile.NamedTemporaryFile(suffix='.txt') as f:
            plan_path = Path(f.name)
            
            result = orchestrator.analyze_single_plan(
                plan_path=plan_path,
                plan_name="Test Plan"
            )
        
        assert result["success"] is True
        assert result["plan_name"] == "Test Plan"
        assert "micro_answers" in result
        assert "meso_clusters" in result
        assert "macro_convergence" in result
    
    @patch.object(FARFANOrchestrator, '_load_plan_document')
    def test_analyze_single_plan_with_question_filter(self, mock_load):
        """Test single plan analysis with filtered questions"""
        mock_load.return_value = "Test plan text"
        
        mock_registry = Mock()
        mock_registry.adapters = {}
        
        mock_parser = Mock()
        questions = []
        for i in range(1, 6):
            q = Mock()
            q.canonical_id = f"P1-D1-Q{i}"
            questions.append(q)
        mock_parser.parse_all_questions = Mock(return_value=questions)
        
        orchestrator = FARFANOrchestrator(
            module_adapter_registry=mock_registry,
            questionnaire_parser=mock_parser
        )
        
        # Mock methods
        orchestrator.choreographer.execute_question_chain = Mock(return_value={})
        
        mock_micro = Mock()
        mock_micro.metadata = {"policy_area": "P1"}
        mock_micro.qualitative_note = "BUENO"
        orchestrator.report_assembler.generate_micro_answer = Mock(return_value=mock_micro)
        orchestrator.report_assembler.generate_meso_cluster = Mock(return_value=Mock())
        
        mock_macro = Mock()
        mock_macro.overall_score = 75.0
        mock_macro.plan_classification = "BUENO"
        mock_macro.convergence_by_dimension = {}
        mock_macro.critical_gaps = []
        mock_macro.strategic_recommendations = []
        orchestrator.report_assembler.generate_macro_convergence = Mock(return_value=mock_macro)
        orchestrator.report_assembler.export_report = Mock()
        
        with tempfile.NamedTemporaryFile(suffix='.txt') as f:
            plan_path = Path(f.name)
            
            result = orchestrator.analyze_single_plan(
                plan_path=plan_path,
                questions_to_analyze=["P1-D1-Q1", "P1-D1-Q2"]
            )
        
        # Should only process 2 questions
        assert len(result["micro_answers"]) == 2
    
    @patch.object(FARFANOrchestrator, '_load_plan_document')
    def test_analyze_single_plan_handles_errors(self, mock_load):
        """Test single plan analysis handles errors gracefully"""
        mock_load.side_effect = Exception("Loading error")
        
        mock_registry = Mock()
        mock_registry.adapters = {}
        
        orchestrator = FARFANOrchestrator(
            module_adapter_registry=mock_registry,
            questionnaire_parser=Mock()
        )
        
        with tempfile.NamedTemporaryFile(suffix='.txt') as f:
            plan_path = Path(f.name)
            
            result = orchestrator.analyze_single_plan(
                plan_path=plan_path,
                plan_name="Test Plan"
            )
        
        assert result["success"] is False
        assert "error" in result
        assert "Loading error" in result["error"]


class TestMESOClusterGeneration:
    """Test MESO cluster generation"""
    
    def test_generate_meso_clusters_by_policy(self):
        """Test MESO cluster generation groups by policy area"""
        mock_registry = Mock()
        mock_registry.adapters = {}
        
        orchestrator = FARFANOrchestrator(
            module_adapter_registry=mock_registry,
            questionnaire_parser=Mock()
        )
        
        # Create mock MICRO answers with different policy areas
        micro_answers = []
        for policy in ["P1", "P2", "P1", "P3", "P2"]:
            answer = Mock()
            answer.metadata = {"policy_area": policy}
            micro_answers.append(answer)
        
        # Mock report assembler
        orchestrator.report_assembler.generate_meso_cluster = Mock(
            side_effect=lambda **kwargs: Mock(cluster_name=kwargs["cluster_name"])
        )
        
        clusters = orchestrator._generate_meso_clusters(micro_answers)
        
        # Should have 3 clusters (P1, P2, P3)
        assert len(clusters) == 3
    
    def test_generate_meso_clusters_empty_answers(self):
        """Test MESO cluster generation with empty answers"""
        mock_registry = Mock()
        mock_registry.adapters = {}
        
        orchestrator = FARFANOrchestrator(
            module_adapter_registry=mock_registry,
            questionnaire_parser=Mock()
        )
        
        clusters = orchestrator._generate_meso_clusters([])
        
        assert clusters == []


class TestExecutionResultConversion:
    """Test execution result conversion"""
    
    def test_convert_execution_results_with_to_dict(self):
        """Test converting results that have to_dict method"""
        mock_registry = Mock()
        mock_registry.adapters = {}
        
        orchestrator = FARFANOrchestrator(
            module_adapter_registry=mock_registry,
            questionnaire_parser=Mock()
        )
        
        mock_result = Mock()
        mock_result.to_dict = Mock(return_value={
            "module_name": "test",
            "status": "completed",
            "data": {"result": "success"}
        })
        
        execution_results = {"adapter1.method1": mock_result}
        
        converted = orchestrator._convert_execution_results(execution_results)
        
        assert "adapter1.method1" in converted
        assert converted["adapter1.method1"]["status"] == "completed"
    
    def test_convert_execution_results_without_to_dict(self):
        """Test converting results without to_dict method"""
        mock_registry = Mock()
        mock_registry.adapters = {}
        
        orchestrator = FARFANOrchestrator(
            module_adapter_registry=mock_registry,
            questionnaire_parser=Mock()
        )
        
        mock_result = Mock(spec=[])
        mock_result.module_name = "test_module"
        mock_result.status = "completed"
        mock_result.output = {"data": "value"}
        
        execution_results = {"adapter1.method1": mock_result}
        
        converted = orchestrator._convert_execution_results(execution_results)
        
        assert "adapter1.method1" in converted
        assert converted["adapter1.method1"]["module_name"] == "test_module"


class TestExecutionStatsTracking:
    """Test execution statistics tracking"""
    
    def test_update_execution_stats(self):
        """Test updating execution statistics"""
        mock_registry = Mock()
        mock_registry.adapters = {}
        
        orchestrator = FARFANOrchestrator(
            module_adapter_registry=mock_registry,
            questionnaire_parser=Mock()
        )
        
        mock_result1 = Mock()
        mock_result1.module_name = "adapter1"
        mock_result1.status = "COMPLETED"
        mock_result1.execution_time = 0.5
        
        mock_result2 = Mock()
        mock_result2.module_name = "adapter2"
        mock_result2.status = "FAILED"
        mock_result2.execution_time = 0.3
        
        execution_results = {
            "adapter1.method1": mock_result1,
            "adapter2.method2": mock_result2
        }
        
        orchestrator._update_execution_stats(execution_results)
        
        # Check stats were updated
        assert orchestrator.execution_stats["adapter_performance"]["adapter1"]["calls"] == 1
        assert orchestrator.execution_stats["adapter_performance"]["adapter1"]["successes"] == 1
        assert orchestrator.execution_stats["adapter_performance"]["adapter2"]["failures"] == 1


class TestExecutionSummaryGeneration:
    """Test execution summary generation"""
    
    def test_generate_execution_summary(self):
        """Test generating execution summary"""
        mock_registry = Mock()
        mock_registry.adapters = {}
        
        orchestrator = FARFANOrchestrator(
            module_adapter_registry=mock_registry,
            questionnaire_parser=Mock()
        )
        
        # Mock micro answers
        micro_answers = []
        for note in ["EXCELENTE", "BUENO", "BUENO", "ACEPTABLE"]:
            answer = Mock()
            answer.qualitative_note = note
            micro_answers.append(answer)
        
        # Mock meso clusters
        meso_clusters = [Mock(), Mock()]
        
        # Mock macro convergence
        macro_convergence = Mock()
        macro_convergence.overall_score = 75.5
        macro_convergence.plan_classification = "BUENO"
        macro_convergence.convergence_by_dimension = {"D1": 80.0, "D2": 70.0}
        macro_convergence.critical_gaps = ["Gap 1", "Gap 2"]
        macro_convergence.strategic_recommendations = ["Rec 1", "Rec 2", "Rec 3"]
        
        summary = orchestrator._generate_execution_summary(
            plan_name="Test Plan",
            micro_answers=micro_answers,
            meso_clusters=meso_clusters,
            macro_convergence=macro_convergence,
            execution_time=10.5
        )
        
        assert summary["plan_name"] == "Test Plan"
        assert summary["total_execution_time"] == 10.5
        assert summary["questions_analyzed"] == 4
        assert summary["clusters_generated"] == 2
        assert summary["overall_score"] == 75.5
        assert summary["score_distribution"]["BUENO"] == 2
        assert len(summary["top_recommendations"]) == 3


class TestBatchProcessing:
    """Test batch processing"""
    
    @patch.object(FARFANOrchestrator, 'analyze_single_plan')
    def test_analyze_batch_multiple_plans(self, mock_analyze):
        """Test analyzing multiple plans in batch"""
        mock_registry = Mock()
        mock_registry.adapters = {}
        
        orchestrator = FARFANOrchestrator(
            module_adapter_registry=mock_registry,
            questionnaire_parser=Mock()
        )
        
        # Mock successful analysis
        mock_analyze.return_value = {
            "success": True,
            "plan_name": "Plan",
            "micro_answers": [],
            "meso_clusters": [],
            "macro_convergence": Mock()
        }
        
        # Create temporary files
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_paths = []
            for i in range(3):
                path = Path(tmpdir) / f"plan_{i}.txt"
                path.write_text(f"Plan {i} content")
                plan_paths.append(path)
            
            results = orchestrator.analyze_batch(plan_paths)
        
        assert len(results) == 3
        assert mock_analyze.call_count == 3
    
    @patch.object(FARFANOrchestrator, 'analyze_single_plan')
    def test_analyze_batch_handles_failures(self, mock_analyze):
        """Test batch analysis continues on individual failures"""
        mock_registry = Mock()
        mock_registry.adapters = {}
        
        orchestrator = FARFANOrchestrator(
            module_adapter_registry=mock_registry,
            questionnaire_parser=Mock()
        )
        
        # Mock mixed results
        mock_analyze.side_effect = [
            {"success": True, "plan_name": "Plan1"},
            {"success": False, "error": "Error in plan 2"},
            {"success": True, "plan_name": "Plan3"}
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_paths = []
            for i in range(3):
                path = Path(tmpdir) / f"plan_{i}.txt"
                path.write_text(f"Plan {i}")
                plan_paths.append(path)
            
            results = orchestrator.analyze_batch(plan_paths)
        
        assert len(results) == 3
        assert results[0]["success"] is True
        assert results[1]["success"] is False
        assert results[2]["success"] is True


class TestOrchestratorStatus:
    """Test orchestrator status queries"""
    
    def test_get_orchestrator_status(self):
        """Test getting orchestrator status"""
        mock_registry = Mock()
        mock_registry.adapters = {"adapter1": Mock(), "adapter2": Mock()}
        mock_registry.get_available_modules = Mock(return_value=["adapter1", "adapter2"])
        
        orchestrator = FARFANOrchestrator(
            module_adapter_registry=mock_registry,
            questionnaire_parser=Mock()
        )
        
        # Mock circuit breaker status
        orchestrator.circuit_breaker.get_all_status = Mock(return_value={
            "adapter1": "closed",
            "adapter2": "closed"
        })
        
        status = orchestrator.get_orchestrator_status()
        
        assert "adapters_available" in status
        assert "total_adapters" in status
        assert "circuit_breaker_status" in status
        assert "execution_stats" in status
        assert status["questions_available"] == 300
        assert status["total_adapters"] == 2
    
    def test_execution_stats_accumulation(self):
        """Test that execution stats accumulate across analyses"""
        mock_registry = Mock()
        mock_registry.adapters = {}
        
        orchestrator = FARFANOrchestrator(
            module_adapter_registry=mock_registry,
            questionnaire_parser=Mock()
        )
        
        # Simulate multiple analyses
        orchestrator.execution_stats["total_plans_processed"] = 5
        orchestrator.execution_stats["total_questions_answered"] = 100
        orchestrator.execution_stats["total_execution_time"] = 250.5
        
        status = orchestrator.get_orchestrator_status()
        
        assert status["execution_stats"]["total_plans_processed"] == 5
        assert status["execution_stats"]["total_questions_answered"] == 100
        assert status["execution_stats"]["total_execution_time"] == 250.5


class TestIntegrationScenarios:
    """Test integration scenarios"""
    
    @patch.object(FARFANOrchestrator, '_load_plan_document')
    def test_full_pipeline_single_question(self, mock_load):
        """Test full pipeline with single question"""
        mock_load.return_value = "Test plan content"
        
        mock_registry = Mock()
        mock_registry.adapters = {}
        
        mock_parser = Mock()
        mock_question = Mock()
        mock_question.canonical_id = "P1-D1-Q1"
        mock_parser.parse_all_questions = Mock(return_value=[mock_question])
        
        orchestrator = FARFANOrchestrator(
            module_adapter_registry=mock_registry,
            questionnaire_parser=mock_parser
        )
        
        # Mock all components
        orchestrator.choreographer.execute_question_chain = Mock(return_value={})
        
        mock_micro = Mock()
        mock_micro.metadata = {"policy_area": "P1"}
        mock_micro.qualitative_note = "BUENO"
        orchestrator.report_assembler.generate_micro_answer = Mock(return_value=mock_micro)
        orchestrator.report_assembler.generate_meso_cluster = Mock(return_value=Mock())
        
        mock_macro = Mock()
        mock_macro.overall_score = 75.0
        mock_macro.plan_classification = "BUENO"
        mock_macro.convergence_by_dimension = {}
        mock_macro.critical_gaps = []
        mock_macro.strategic_recommendations = []
        orchestrator.report_assembler.generate_macro_convergence = Mock(return_value=mock_macro)
        orchestrator.report_assembler.export_report = Mock()
        
        with tempfile.NamedTemporaryFile(suffix='.txt') as f:
            plan_path = Path(f.name)
            
            result = orchestrator.analyze_single_plan(
                plan_path=plan_path,
                plan_name="Integration Test"
            )
        
        # Verify full pipeline executed
        assert result["success"] is True
        assert len(result["micro_answers"]) == 1
        assert len(result["meso_clusters"]) >= 1
        assert result["macro_convergence"].overall_score == 75.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
