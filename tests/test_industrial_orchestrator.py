"""
Comprehensive Tests for Industrial Orchestrator
===============================================

Tests the industrial-grade orchestrator including:
- Workflow initialization and configuration
- Workflow execution with metadata
- Step execution and state management
- Dependency checking
- Deterministic execution
- Resilience and validation

Author: FARFAN Testing Team
Version: 1.0.0
Python: 3.11+
"""

import pytest
import time
from unittest.mock import Mock, MagicMock, patch, call
from typing import Dict, List, Any
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from industrial_orchestrator import (
    IndustrialOrchestrator,
    WorkflowConfig,
    WorkflowResult,
)
from state_store import WorkflowStatus, StepStatus


class TestWorkflowConfig:
    """Test WorkflowConfig dataclass"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = WorkflowConfig()
        
        assert config.enable_validation is True
        assert config.enable_resilience is True
        assert config.fail_fast is False
        assert config.parallel_execution is False
        assert config.max_retries == 3
        assert config.timeout_seconds == 3600
        assert config.enable_deterministic_mode is True
    
    def test_custom_config(self):
        """Test custom configuration values"""
        config = WorkflowConfig(
            enable_validation=False,
            enable_resilience=False,
            fail_fast=True,
            max_retries=5,
            timeout_seconds=1800,
            enable_deterministic_mode=False
        )
        
        assert config.enable_validation is False
        assert config.enable_resilience is False
        assert config.fail_fast is True
        assert config.max_retries == 5
        assert config.timeout_seconds == 1800
        assert config.enable_deterministic_mode is False


class TestWorkflowResult:
    """Test WorkflowResult dataclass"""
    
    def test_workflow_result_creation(self):
        """Test creating workflow result"""
        result = WorkflowResult(
            workflow_id="wf_123",
            success=True,
            status=WorkflowStatus.COMPLETED,
            completed_steps=["Q1", "Q2"],
            failed_steps=[],
            skipped_steps=[],
            total_steps=2,
            execution_time=10.5,
            final_state=Mock(),
            step_results={}
        )
        
        assert result.workflow_id == "wf_123"
        assert result.success is True
        assert result.status == WorkflowStatus.COMPLETED
        assert len(result.completed_steps) == 2
    
    def test_success_rate_calculation(self):
        """Test success rate calculation"""
        result = WorkflowResult(
            workflow_id="wf_123",
            success=True,
            status=WorkflowStatus.COMPLETED,
            completed_steps=["Q1", "Q2", "Q3"],
            failed_steps=["Q4"],
            skipped_steps=["Q5"],
            total_steps=5,
            execution_time=10.5,
            final_state=Mock(),
            step_results={}
        )
        
        assert result.success_rate == 0.6  # 3/5
    
    def test_success_rate_with_zero_steps(self):
        """Test success rate with zero total steps"""
        result = WorkflowResult(
            workflow_id="wf_123",
            success=False,
            status=WorkflowStatus.FAILED,
            completed_steps=[],
            failed_steps=[],
            skipped_steps=[],
            total_steps=0,
            execution_time=0.0,
            final_state=Mock(),
            step_results={}
        )
        
        assert result.success_rate == 0.0


class TestOrchestratorInitialization:
    """Test IndustrialOrchestrator initialization"""
    
    @patch('industrial_orchestrator.get_metadata_service')
    def test_initialization_with_defaults(self, mock_get_metadata):
        """Test orchestrator initialization with defaults"""
        mock_metadata_service = Mock()
        mock_get_metadata.return_value = mock_metadata_service
        
        mock_registry = Mock()
        
        orchestrator = IndustrialOrchestrator(
            module_registry=mock_registry
        )
        
        assert orchestrator.module_controller is not None
        assert orchestrator.state_store is not None
        assert orchestrator.validation_engine is not None
        assert orchestrator.resilience_manager is not None
        mock_metadata_service.load.assert_called_once()
    
    @patch('industrial_orchestrator.get_metadata_service')
    def test_initialization_with_custom_config(self, mock_get_metadata):
        """Test orchestrator initialization with custom config"""
        mock_metadata_service = Mock()
        mock_get_metadata.return_value = mock_metadata_service
        
        mock_registry = Mock()
        config = WorkflowConfig(
            enable_validation=False,
            enable_resilience=False
        )
        
        orchestrator = IndustrialOrchestrator(
            module_registry=mock_registry,
            config=config
        )
        
        assert orchestrator.config.enable_validation is False
        assert orchestrator.config.enable_resilience is False
    
    @patch('industrial_orchestrator.get_metadata_service')
    def test_initialization_with_custom_metadata_service(self, mock_get_metadata):
        """Test orchestrator with custom metadata service"""
        custom_metadata_service = Mock()
        custom_metadata_service.load = Mock()
        
        mock_registry = Mock()
        
        orchestrator = IndustrialOrchestrator(
            module_registry=mock_registry,
            metadata_service=custom_metadata_service
        )
        
        assert orchestrator.metadata_service == custom_metadata_service
        custom_metadata_service.load.assert_called_once()


class TestWorkflowExecution:
    """Test workflow execution"""
    
    @patch('industrial_orchestrator.get_metadata_service')
    def test_execute_workflow_with_empty_questions(self, mock_get_metadata):
        """Test executing workflow with no questions"""
        mock_metadata_service = Mock()
        mock_metadata_service.get_version = Mock(return_value="1.0.0")
        mock_get_metadata.return_value = mock_metadata_service
        
        mock_registry = Mock()
        orchestrator = IndustrialOrchestrator(
            module_registry=mock_registry
        )
        
        result = orchestrator.execute_workflow(
            question_ids=[],
            document_text="Test document",
            workflow_name="Test Workflow"
        )
        
        assert result.total_steps == 0
        assert result.success is True
        assert len(result.completed_steps) == 0
    
    @patch('industrial_orchestrator.get_metadata_service')
    def test_execute_workflow_with_single_question(self, mock_get_metadata):
        """Test executing workflow with single question"""
        # Mock metadata service
        mock_metadata_service = Mock()
        mock_metadata_service.get_version = Mock(return_value="1.0.0")
        mock_question_context = Mock()
        mock_question_context.dimension = "D1"
        mock_question_context.version = "1.0"
        mock_question_context.dependencies = []
        mock_metadata_service.get_question_context = Mock(return_value=mock_question_context)
        mock_get_metadata.return_value = mock_metadata_service
        
        # Mock registry
        mock_registry = Mock()
        
        orchestrator = IndustrialOrchestrator(
            module_registry=mock_registry
        )
        
        # Mock module controller to return success
        mock_invocation_result = Mock()
        mock_invocation_result.is_success = True
        mock_invocation_result.is_validated = True
        mock_invocation_result.output = {"result": "success"}
        mock_invocation_result.errors = []
        mock_invocation_result.retry_count = 0
        orchestrator.module_controller.invoke = Mock(return_value=mock_invocation_result)
        
        result = orchestrator.execute_workflow(
            question_ids=["P1-D1-Q1"],
            document_text="Test document",
            workflow_name="Test Workflow"
        )
        
        assert result.total_steps == 1
        assert len(result.completed_steps) == 1
        assert "P1-D1-Q1" in result.completed_steps
        assert result.success is True
    
    @patch('industrial_orchestrator.get_metadata_service')
    def test_execute_workflow_with_multiple_questions(self, mock_get_metadata):
        """Test executing workflow with multiple questions"""
        # Mock metadata service
        mock_metadata_service = Mock()
        mock_metadata_service.get_version = Mock(return_value="1.0.0")
        mock_question_context = Mock()
        mock_question_context.dimension = "D1"
        mock_question_context.version = "1.0"
        mock_question_context.dependencies = []
        mock_metadata_service.get_question_context = Mock(return_value=mock_question_context)
        mock_get_metadata.return_value = mock_metadata_service
        
        # Mock registry
        mock_registry = Mock()
        
        orchestrator = IndustrialOrchestrator(
            module_registry=mock_registry
        )
        
        # Mock module controller to return success
        mock_invocation_result = Mock()
        mock_invocation_result.is_success = True
        mock_invocation_result.is_validated = True
        mock_invocation_result.output = {"result": "success"}
        mock_invocation_result.errors = []
        mock_invocation_result.retry_count = 0
        orchestrator.module_controller.invoke = Mock(return_value=mock_invocation_result)
        
        question_ids = ["P1-D1-Q1", "P1-D1-Q2", "P1-D2-Q1"]
        
        result = orchestrator.execute_workflow(
            question_ids=question_ids,
            document_text="Test document",
            workflow_name="Test Workflow"
        )
        
        assert result.total_steps == 3
        assert len(result.completed_steps) == 3
        assert result.success is True


class TestFailFastBehavior:
    """Test fail-fast behavior"""
    
    @patch('industrial_orchestrator.get_metadata_service')
    def test_fail_fast_stops_on_first_error(self, mock_get_metadata):
        """Test that fail-fast stops execution on first error"""
        # Mock metadata service
        mock_metadata_service = Mock()
        mock_metadata_service.get_version = Mock(return_value="1.0.0")
        mock_question_context = Mock()
        mock_question_context.dimension = "D1"
        mock_question_context.version = "1.0"
        mock_question_context.dependencies = []
        mock_metadata_service.get_question_context = Mock(return_value=mock_question_context)
        mock_get_metadata.return_value = mock_metadata_service
        
        # Mock registry
        mock_registry = Mock()
        
        config = WorkflowConfig(fail_fast=True)
        orchestrator = IndustrialOrchestrator(
            module_registry=mock_registry,
            config=config
        )
        
        # Mock module controller to return failure
        mock_invocation_result = Mock()
        mock_invocation_result.is_success = False
        mock_invocation_result.is_validated = False
        mock_invocation_result.output = {}
        mock_invocation_result.errors = ["Test error"]
        mock_invocation_result.retry_count = 0
        orchestrator.module_controller.invoke = Mock(return_value=mock_invocation_result)
        
        question_ids = ["P1-D1-Q1", "P1-D1-Q2", "P1-D2-Q1"]
        
        result = orchestrator.execute_workflow(
            question_ids=question_ids,
            document_text="Test document",
            workflow_name="Test Workflow"
        )
        
        # Should stop after first failure
        assert len(result.failed_steps) == 1
        assert len(result.completed_steps) == 0
    
    @patch('industrial_orchestrator.get_metadata_service')
    def test_without_fail_fast_continues_on_error(self, mock_get_metadata):
        """Test that without fail-fast, execution continues on error"""
        # Mock metadata service
        mock_metadata_service = Mock()
        mock_metadata_service.get_version = Mock(return_value="1.0.0")
        mock_question_context = Mock()
        mock_question_context.dimension = "D1"
        mock_question_context.version = "1.0"
        mock_question_context.dependencies = []
        mock_metadata_service.get_question_context = Mock(return_value=mock_question_context)
        mock_get_metadata.return_value = mock_metadata_service
        
        # Mock registry
        mock_registry = Mock()
        
        config = WorkflowConfig(fail_fast=False)
        orchestrator = IndustrialOrchestrator(
            module_registry=mock_registry,
            config=config
        )
        
        # Mock module controller to return failure
        mock_invocation_result = Mock()
        mock_invocation_result.is_success = False
        mock_invocation_result.is_validated = False
        mock_invocation_result.output = {}
        mock_invocation_result.errors = ["Test error"]
        mock_invocation_result.retry_count = 0
        orchestrator.module_controller.invoke = Mock(return_value=mock_invocation_result)
        
        question_ids = ["P1-D1-Q1", "P1-D1-Q2", "P1-D2-Q1"]
        
        result = orchestrator.execute_workflow(
            question_ids=question_ids,
            document_text="Test document",
            workflow_name="Test Workflow"
        )
        
        # Should process all questions despite failures
        assert len(result.failed_steps) == 3


class TestDependencyChecking:
    """Test dependency checking"""
    
    @patch('industrial_orchestrator.get_metadata_service')
    def test_check_dependencies_with_no_dependencies(self, mock_get_metadata):
        """Test dependency check with no dependencies"""
        mock_metadata_service = Mock()
        mock_get_metadata.return_value = mock_metadata_service
        
        mock_registry = Mock()
        orchestrator = IndustrialOrchestrator(
            module_registry=mock_registry
        )
        
        mock_context = Mock()
        mock_context.dependencies = []
        
        result = orchestrator._check_dependencies("wf_123", mock_context)
        
        assert result is True
    
    @patch('industrial_orchestrator.get_metadata_service')
    def test_check_dependencies_with_satisfied_dependencies(self, mock_get_metadata):
        """Test dependency check with satisfied dependencies"""
        mock_metadata_service = Mock()
        mock_get_metadata.return_value = mock_metadata_service
        
        mock_registry = Mock()
        orchestrator = IndustrialOrchestrator(
            module_registry=mock_registry
        )
        
        # Create workflow state with completed step
        workflow_id = "wf_123"
        orchestrator.state_store.create_workflow(workflow_id, {})
        
        # Mock state with completed dependencies
        mock_state = Mock()
        mock_state.completed_steps = ["Q1"]
        orchestrator.state_store.get_state = Mock(return_value=mock_state)
        
        mock_context = Mock()
        mock_context.dependencies = ["Q1"]
        
        result = orchestrator._check_dependencies(workflow_id, mock_context)
        
        assert result is True
    
    @patch('industrial_orchestrator.get_metadata_service')
    def test_check_dependencies_with_unsatisfied_dependencies(self, mock_get_metadata):
        """Test dependency check with unsatisfied dependencies"""
        mock_metadata_service = Mock()
        mock_get_metadata.return_value = mock_metadata_service
        
        mock_registry = Mock()
        orchestrator = IndustrialOrchestrator(
            module_registry=mock_registry
        )
        
        # Mock state without completed dependencies
        mock_state = Mock()
        mock_state.completed_steps = []
        orchestrator.state_store.get_state = Mock(return_value=mock_state)
        
        mock_context = Mock()
        mock_context.dependencies = ["Q1"]
        
        result = orchestrator._check_dependencies("wf_123", mock_context)
        
        assert result is False


class TestDeterministicExecution:
    """Test deterministic execution"""
    
    @patch('industrial_orchestrator.get_metadata_service')
    @patch('industrial_orchestrator.create_deterministic_id')
    def test_deterministic_workflow_id_generation(self, mock_create_id, mock_get_metadata):
        """Test deterministic workflow ID generation"""
        mock_create_id.return_value = "deterministic_wf_123"
        
        mock_metadata_service = Mock()
        mock_metadata_service.get_version = Mock(return_value="1.0.0")
        mock_get_metadata.return_value = mock_metadata_service
        
        mock_registry = Mock()
        
        config = WorkflowConfig(enable_deterministic_mode=True)
        orchestrator = IndustrialOrchestrator(
            module_registry=mock_registry,
            config=config
        )
        
        result = orchestrator.execute_workflow(
            question_ids=[],
            document_text="Test document",
            workflow_name="Test Workflow"
        )
        
        assert result.workflow_id == "deterministic_wf_123"
        mock_create_id.assert_called_once()
    
    @patch('industrial_orchestrator.get_metadata_service')
    def test_non_deterministic_workflow_id_generation(self, mock_get_metadata):
        """Test non-deterministic workflow ID generation"""
        mock_metadata_service = Mock()
        mock_metadata_service.get_version = Mock(return_value="1.0.0")
        mock_get_metadata.return_value = mock_metadata_service
        
        mock_registry = Mock()
        
        config = WorkflowConfig(enable_deterministic_mode=False)
        orchestrator = IndustrialOrchestrator(
            module_registry=mock_registry,
            config=config
        )
        
        result = orchestrator.execute_workflow(
            question_ids=[],
            document_text="Test document",
            workflow_name="Test Workflow"
        )
        
        # Should start with "workflow_"
        assert result.workflow_id.startswith("workflow_")


class TestQuestionRouting:
    """Test question routing"""
    
    @patch('industrial_orchestrator.get_metadata_service')
    def test_route_question_dimension_mapping(self, mock_get_metadata):
        """Test question routing based on dimension"""
        mock_metadata_service = Mock()
        mock_get_metadata.return_value = mock_metadata_service
        
        mock_registry = Mock()
        orchestrator = IndustrialOrchestrator(
            module_registry=mock_registry
        )
        
        # Test routing for each dimension
        test_cases = [
            ("D1", ("policy_processor", "extract_baseline_data")),
            ("D2", ("policy_processor", "analyze_activities")),
            ("D3", ("analyzer_one", "analyze_products")),
            ("D4", ("teoria_cambio", "analyze_results")),
            ("D5", ("dereck_beach", "analyze_impact")),
            ("D6", ("teoria_cambio", "validate_theory_of_change")),
        ]
        
        for dimension, expected_route in test_cases:
            mock_context = Mock()
            mock_context.dimension = dimension
            
            module_name, method_name = orchestrator._route_question(mock_context)
            
            assert (module_name, method_name) == expected_route


class TestWorkflowStatusQueries:
    """Test workflow status queries"""
    
    @patch('industrial_orchestrator.get_metadata_service')
    def test_get_workflow_status(self, mock_get_metadata):
        """Test getting workflow status"""
        mock_metadata_service = Mock()
        mock_get_metadata.return_value = mock_metadata_service
        
        mock_registry = Mock()
        orchestrator = IndustrialOrchestrator(
            module_registry=mock_registry
        )
        
        workflow_id = "wf_123"
        orchestrator.state_store.create_workflow(workflow_id, {})
        
        status = orchestrator.get_workflow_status(workflow_id)
        
        assert status is not None
        assert status.workflow_id == workflow_id
    
    @patch('industrial_orchestrator.get_metadata_service')
    def test_get_step_result(self, mock_get_metadata):
        """Test getting step result"""
        mock_metadata_service = Mock()
        mock_get_metadata.return_value = mock_metadata_service
        
        mock_registry = Mock()
        orchestrator = IndustrialOrchestrator(
            module_registry=mock_registry
        )
        
        workflow_id = "wf_123"
        step_id = "Q1"
        
        # Get step result (may be None if not exists)
        result = orchestrator.get_step_result(workflow_id, step_id)
        
        # Should return None or StepResult
        assert result is None or hasattr(result, 'step_id')


class TestStatistics:
    """Test statistics and metrics"""
    
    @patch('industrial_orchestrator.get_metadata_service')
    def test_get_statistics(self, mock_get_metadata):
        """Test getting orchestrator statistics"""
        mock_metadata_service = Mock()
        mock_get_metadata.return_value = mock_metadata_service
        
        mock_registry = Mock()
        orchestrator = IndustrialOrchestrator(
            module_registry=mock_registry
        )
        
        stats = orchestrator.get_statistics()
        
        assert "state_store" in stats
        assert "validation_engine" in stats
        assert "resilience_manager" in stats
        assert "module_controller" in stats
        assert "execution_history" in stats
        assert "total_workflows" in stats
    
    @patch('industrial_orchestrator.get_metadata_service')
    def test_execution_history_tracking(self, mock_get_metadata):
        """Test execution history is tracked"""
        mock_metadata_service = Mock()
        mock_metadata_service.get_version = Mock(return_value="1.0.0")
        mock_get_metadata.return_value = mock_metadata_service
        
        mock_registry = Mock()
        orchestrator = IndustrialOrchestrator(
            module_registry=mock_registry
        )
        
        # Execute workflows
        orchestrator.execute_workflow(
            question_ids=[],
            document_text="Test",
            workflow_name="Workflow 1"
        )
        
        orchestrator.execute_workflow(
            question_ids=[],
            document_text="Test",
            workflow_name="Workflow 2"
        )
        
        stats = orchestrator.get_statistics()
        
        assert stats["total_workflows"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
