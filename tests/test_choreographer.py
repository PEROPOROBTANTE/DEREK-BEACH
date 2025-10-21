"""
Comprehensive Tests for Execution Choreographer
===============================================

Tests the DAG-based execution choreographer including:
- Dependency graph construction
- Execution order and wave-based processing
- Adapter method validation
- Circuit breaker integration
- Event emission (SubProcessCompletedEvent/FailedEvent)
- Result aggregation

Author: FARFAN Testing Team
Version: 1.0.0
Python: 3.11+
"""

import pytest
import time
from unittest.mock import Mock, MagicMock, patch, call
from typing import Dict, List, Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from choreographer import (
    ExecutionChoreographer,
    ExecutionResult,
    ExecutionStatus,
)


class TestExecutionChoreographerInitialization:
    """Test ExecutionChoreographer initialization"""
    
    def test_initialization_with_defaults(self):
        """Test choreographer initialization with default values"""
        choreographer = ExecutionChoreographer()
        
        assert choreographer.max_workers == 4
        assert choreographer.execution_graph is not None
        assert len(choreographer.adapter_registry) == 9
        assert choreographer.event_bus is not None
    
    def test_initialization_with_custom_workers(self):
        """Test choreographer with custom worker count"""
        choreographer = ExecutionChoreographer(max_workers=8)
        
        assert choreographer.max_workers == 8
    
    def test_initialization_with_custom_event_bus(self):
        """Test choreographer with custom event bus"""
        mock_event_bus = Mock()
        choreographer = ExecutionChoreographer(event_bus=mock_event_bus)
        
        assert choreographer.event_bus == mock_event_bus


class TestDependencyGraph:
    """Test dependency graph construction and properties"""
    
    def test_graph_has_all_adapters(self):
        """Test that dependency graph includes all 9 adapters"""
        choreographer = ExecutionChoreographer()
        
        expected_adapters = [
            "policy_segmenter",
            "policy_processor",
            "semantic_chunking_policy",
            "embedding_policy",
            "analyzer_one",
            "teoria_cambio",
            "dereck_beach",
            "contradiction_detection",
            "financial_viability",
        ]
        
        for adapter in expected_adapters:
            assert adapter in choreographer.execution_graph.nodes
    
    def test_graph_is_acyclic(self):
        """Test that dependency graph has no cycles (DAG)"""
        choreographer = ExecutionChoreographer()
        
        # Should not raise exception during initialization
        # (initialization checks for cycles)
        assert choreographer.execution_graph is not None
    
    def test_graph_has_correct_priorities(self):
        """Test that adapters have correct priority levels"""
        choreographer = ExecutionChoreographer()
        
        # Wave 1
        assert choreographer.get_adapter_priority("policy_segmenter") == 1
        assert choreographer.get_adapter_priority("policy_processor") == 1
        
        # Wave 2
        assert choreographer.get_adapter_priority("semantic_chunking_policy") == 2
        assert choreographer.get_adapter_priority("embedding_policy") == 2
        
        # Wave 3
        assert choreographer.get_adapter_priority("analyzer_one") == 3
        assert choreographer.get_adapter_priority("teoria_cambio") == 3
        
        # Wave 4
        assert choreographer.get_adapter_priority("dereck_beach") == 4
        assert choreographer.get_adapter_priority("contradiction_detection") == 4
        
        # Wave 5
        assert choreographer.get_adapter_priority("financial_viability") == 5
    
    def test_get_adapter_dependencies(self):
        """Test getting dependencies for specific adapters"""
        choreographer = ExecutionChoreographer()
        
        # Wave 1 adapters should have no dependencies
        assert choreographer.get_adapter_dependencies("policy_segmenter") == []
        assert choreographer.get_adapter_dependencies("policy_processor") == []
        
        # Wave 2 adapters depend on Wave 1
        semantic_deps = choreographer.get_adapter_dependencies("semantic_chunking_policy")
        assert "policy_segmenter" in semantic_deps
        assert "policy_processor" in semantic_deps
        
        # Wave 5 adapter depends on multiple earlier waves
        financial_deps = choreographer.get_adapter_dependencies("financial_viability")
        assert len(financial_deps) > 0
    
    def test_get_execution_order(self):
        """Test topological execution order"""
        choreographer = ExecutionChoreographer()
        
        execution_order = choreographer.get_execution_order()
        
        # Should have all 9 adapters
        assert len(execution_order) == 9
        
        # Wave 1 should come before Wave 2
        policy_seg_idx = execution_order.index("policy_segmenter")
        semantic_idx = execution_order.index("semantic_chunking_policy")
        assert policy_seg_idx < semantic_idx
        
        # Wave 5 should be last
        financial_idx = execution_order.index("financial_viability")
        assert financial_idx == len(execution_order) - 1


class TestAdapterRegistry:
    """Test adapter registry initialization"""
    
    def test_adapter_registry_completeness(self):
        """Test that adapter registry has all 9 adapters"""
        choreographer = ExecutionChoreographer()
        
        assert len(choreographer.adapter_registry) == 9
        
        expected_adapters = [
            "teoria_cambio",
            "analyzer_one",
            "dereck_beach",
            "embedding_policy",
            "semantic_chunking_policy",
            "contradiction_detection",
            "financial_viability",
            "policy_processor",
            "policy_segmenter",
        ]
        
        for adapter in expected_adapters:
            assert adapter in choreographer.adapter_registry
    
    def test_adapter_class_names(self):
        """Test that adapter registry has correct class names"""
        choreographer = ExecutionChoreographer()
        
        assert choreographer.adapter_registry["teoria_cambio"] == "ModulosAdapter"
        assert choreographer.adapter_registry["analyzer_one"] == "AnalyzerOneAdapter"
        assert choreographer.adapter_registry["dereck_beach"] == "DerekBeachAdapter"


class TestQuestionChainExecution:
    """Test question chain execution"""
    
    def test_execute_empty_chain(self):
        """Test executing question with empty chain"""
        choreographer = ExecutionChoreographer()
        
        question_spec = Mock()
        question_spec.canonical_id = "P1-D1-Q1"
        question_spec.execution_chain = []
        
        results = choreographer.execute_question_chain(
            question_spec=question_spec,
            plan_text="Test plan",
            module_adapter_registry=Mock()
        )
        
        assert results == {}
    
    def test_execute_chain_with_single_step(self):
        """Test executing chain with single step"""
        choreographer = ExecutionChoreographer()
        
        question_spec = Mock()
        question_spec.canonical_id = "P1-D1-Q1"
        question_spec.execution_chain = [
            {
                "adapter": "policy_processor",
                "method": "process_text",
                "args": [],
                "kwargs": {}
            }
        ]
        
        # Mock registry
        mock_registry = Mock()
        mock_registry.execute_module_method = Mock(return_value=Mock(
            trace_id="trace_123",
            status=Mock(),
            evidence="test evidence",
            error_message=None,
            execution_time=0.1,
            adapter_class="PolicyProcessorAdapter",
            confidence=0.9
        ))
        
        # Mock status enum
        from unittest.mock import PropertyMock
        type(mock_registry.execute_module_method.return_value.status).name = PropertyMock(return_value="SUCCESS")
        
        mock_registry.list_adapter_methods = Mock(return_value=["process_text"])
        
        results = choreographer.execute_question_chain(
            question_spec=question_spec,
            plan_text="Test plan",
            module_adapter_registry=mock_registry
        )
        
        assert len(results) == 1
        assert "policy_processor.process_text" in results
    
    def test_execute_chain_with_multiple_steps(self):
        """Test executing chain with multiple steps"""
        choreographer = ExecutionChoreographer()
        
        question_spec = Mock()
        question_spec.canonical_id = "P1-D1-Q1"
        question_spec.execution_chain = [
            {
                "adapter": "policy_processor",
                "method": "process_text",
                "args": [],
                "kwargs": {}
            },
            {
                "adapter": "analyzer_one",
                "method": "analyze",
                "args": [],
                "kwargs": {}
            }
        ]
        
        # Mock registry
        mock_registry = Mock()
        mock_result = Mock(
            trace_id="trace_123",
            evidence="test evidence",
            error_message=None,
            execution_time=0.1,
            adapter_class="Adapter",
            confidence=0.9
        )
        type(mock_result).status = PropertyMock(return_value=Mock(name="SUCCESS"))
        
        mock_registry.execute_module_method = Mock(return_value=mock_result)
        mock_registry.list_adapter_methods = Mock(return_value=["process_text", "analyze"])
        
        results = choreographer.execute_question_chain(
            question_spec=question_spec,
            plan_text="Test plan",
            module_adapter_registry=mock_registry
        )
        
        assert len(results) == 2
        assert "policy_processor.process_text" in results
        assert "analyzer_one.analyze" in results
    
    def test_execute_chain_with_invalid_adapter(self):
        """Test executing chain with non-existent adapter"""
        choreographer = ExecutionChoreographer()
        
        question_spec = Mock()
        question_spec.canonical_id = "P1-D1-Q1"
        question_spec.execution_chain = [
            {
                "adapter": "nonexistent_adapter",
                "method": "some_method",
                "args": [],
                "kwargs": {}
            }
        ]
        
        # Mock registry that doesn't have the adapter
        mock_registry = Mock()
        mock_registry.list_adapter_methods = Mock(side_effect=Exception("Adapter not found"))
        
        results = choreographer.execute_question_chain(
            question_spec=question_spec,
            plan_text="Test plan",
            module_adapter_registry=mock_registry
        )
        
        assert len(results) == 1
        result = results["nonexistent_adapter.some_method"]
        assert result.status == ExecutionStatus.SKIPPED


class TestCircuitBreakerIntegration:
    """Test circuit breaker integration"""
    
    def test_execute_with_circuit_breaker_open(self):
        """Test execution when circuit breaker is open"""
        choreographer = ExecutionChoreographer()
        
        question_spec = Mock()
        question_spec.canonical_id = "P1-D1-Q1"
        question_spec.execution_chain = [
            {
                "adapter": "policy_processor",
                "method": "process_text",
                "args": [],
                "kwargs": {}
            }
        ]
        
        # Mock circuit breaker that prevents execution
        mock_circuit_breaker = Mock()
        mock_circuit_breaker.can_execute = Mock(return_value=False)
        
        mock_registry = Mock()
        mock_registry.list_adapter_methods = Mock(return_value=["process_text"])
        
        results = choreographer.execute_question_chain(
            question_spec=question_spec,
            plan_text="Test plan",
            module_adapter_registry=mock_registry,
            circuit_breaker=mock_circuit_breaker
        )
        
        assert len(results) == 1
        result = results["policy_processor.process_text"]
        assert result.status == ExecutionStatus.SKIPPED
        assert "Circuit breaker open" in result.error
    
    def test_execute_with_circuit_breaker_success(self):
        """Test circuit breaker records success"""
        choreographer = ExecutionChoreographer()
        
        question_spec = Mock()
        question_spec.canonical_id = "P1-D1-Q1"
        question_spec.execution_chain = [
            {
                "adapter": "policy_processor",
                "method": "process_text",
                "args": [],
                "kwargs": {}
            }
        ]
        
        # Mock circuit breaker
        mock_circuit_breaker = Mock()
        mock_circuit_breaker.can_execute = Mock(return_value=True)
        mock_circuit_breaker.record_success = Mock()
        
        # Mock registry
        mock_registry = Mock()
        mock_result = Mock(
            trace_id="trace_123",
            evidence="test",
            error_message=None,
            execution_time=0.1,
            adapter_class="Adapter",
            confidence=0.9
        )
        type(mock_result).status = PropertyMock(return_value=Mock(name="SUCCESS"))
        
        mock_registry.execute_module_method = Mock(return_value=mock_result)
        mock_registry.list_adapter_methods = Mock(return_value=["process_text"])
        
        results = choreographer.execute_question_chain(
            question_spec=question_spec,
            plan_text="Test plan",
            module_adapter_registry=mock_registry,
            circuit_breaker=mock_circuit_breaker
        )
        
        # Verify circuit breaker recorded success
        mock_circuit_breaker.record_success.assert_called_once_with("policy_processor")


class TestArgumentPreparation:
    """Test argument preparation"""
    
    def test_prepare_simple_arguments(self):
        """Test preparing simple literal arguments"""
        choreographer = ExecutionChoreographer()
        
        args_spec = ["value1", "value2", 123]
        previous_results = {}
        
        prepared = choreographer._prepare_arguments(args_spec, previous_results, "plan text")
        
        assert prepared == ["value1", "value2", 123]
    
    def test_prepare_arguments_with_plan_text(self):
        """Test preparing arguments with plan_text reference"""
        choreographer = ExecutionChoreographer()
        
        args_spec = [{"source": "plan_text"}]
        previous_results = {}
        plan_text = "This is the plan"
        
        prepared = choreographer._prepare_arguments(args_spec, previous_results, plan_text)
        
        assert prepared == [plan_text]
    
    def test_prepare_arguments_with_previous_result(self):
        """Test preparing arguments referencing previous results"""
        choreographer = ExecutionChoreographer()
        
        mock_result = Mock()
        mock_result.output = {"data": "previous output"}
        
        args_spec = [{"source": "step1.method1"}]
        previous_results = {"step1.method1": mock_result}
        
        prepared = choreographer._prepare_arguments(args_spec, previous_results, "plan")
        
        assert prepared == [{"data": "previous output"}]
    
    def test_prepare_kwargs_arguments(self):
        """Test preparing keyword arguments"""
        choreographer = ExecutionChoreographer()
        
        kwargs_spec = {
            "text": {"source": "plan_text"},
            "limit": {"value": 100}
        }
        previous_results = {}
        plan_text = "Plan content"
        
        prepared = choreographer._prepare_arguments(kwargs_spec, previous_results, plan_text)
        
        assert prepared == {"text": plan_text, "limit": 100}


class TestResultAggregation:
    """Test result aggregation"""
    
    def test_aggregate_empty_results(self):
        """Test aggregating empty results"""
        choreographer = ExecutionChoreographer()
        
        aggregated = choreographer.aggregate_results({})
        
        assert aggregated["total_steps"] == 0
        assert aggregated["successful_steps"] == 0
        assert aggregated["failed_steps"] == 0
    
    def test_aggregate_successful_results(self):
        """Test aggregating successful results"""
        choreographer = ExecutionChoreographer()
        
        results = {
            "step1": ExecutionResult(
                module_name="module1",
                adapter_class="Adapter1",
                method_name="method1",
                status=ExecutionStatus.COMPLETED,
                output={"result": "data"},
                execution_time=0.5,
                confidence=0.8
            ),
            "step2": ExecutionResult(
                module_name="module2",
                adapter_class="Adapter2",
                method_name="method2",
                status=ExecutionStatus.COMPLETED,
                output={"result": "data2"},
                execution_time=0.3,
                confidence=0.9
            )
        }
        
        aggregated = choreographer.aggregate_results(results)
        
        assert aggregated["total_steps"] == 2
        assert aggregated["successful_steps"] == 2
        assert aggregated["failed_steps"] == 0
        assert aggregated["total_execution_time"] == 0.8
        assert aggregated["avg_confidence"] == 0.85
    
    def test_aggregate_mixed_results(self):
        """Test aggregating mixed success/failure results"""
        choreographer = ExecutionChoreographer()
        
        results = {
            "step1": ExecutionResult(
                module_name="module1",
                adapter_class="Adapter1",
                method_name="method1",
                status=ExecutionStatus.COMPLETED,
                execution_time=0.5,
                confidence=0.8
            ),
            "step2": ExecutionResult(
                module_name="module2",
                adapter_class="Adapter2",
                method_name="method2",
                status=ExecutionStatus.FAILED,
                error="Test error",
                execution_time=0.2,
                confidence=0.0
            )
        }
        
        aggregated = choreographer.aggregate_results(results)
        
        assert aggregated["total_steps"] == 2
        assert aggregated["successful_steps"] == 1
        assert aggregated["failed_steps"] == 1


class TestEventEmission:
    """Test event emission to orchestrator"""
    
    def test_execute_chain_emits_completion_event(self):
        """Test that successful execution emits completion event"""
        mock_event_bus = Mock()
        choreographer = ExecutionChoreographer(event_bus=mock_event_bus)
        
        question_spec = Mock()
        question_spec.canonical_id = "P1-D1-Q1"
        question_spec.execution_chain = [
            {
                "adapter": "policy_processor",
                "method": "process_text",
                "args": [],
                "kwargs": {}
            }
        ]
        
        # Mock successful execution
        mock_registry = Mock()
        mock_result = Mock(
            trace_id="trace_123",
            evidence="test",
            error_message=None,
            execution_time=0.1,
            adapter_class="Adapter",
            confidence=0.9
        )
        type(mock_result).status = PropertyMock(return_value=Mock(name="SUCCESS"))
        
        mock_registry.execute_module_method = Mock(return_value=mock_result)
        mock_registry.list_adapter_methods = Mock(return_value=["process_text"])
        
        # Provide context propagation
        from event_schemas import create_context_propagation
        context = create_context_propagation(
            correlation_id="corr_123",
            workflow_id="wf_123",
            question_ids=["P1-D1-Q1"]
        )
        
        results = choreographer.execute_question_chain(
            question_spec=question_spec,
            plan_text="Test plan",
            module_adapter_registry=mock_registry,
            context_propagation=context
        )
        
        # Verify event was published
        mock_event_bus.publish.assert_called_once()


class TestAdapterMethodValidation:
    """Test adapter method validation"""
    
    def test_validate_existing_adapter_method(self):
        """Test validation succeeds for existing adapter method"""
        choreographer = ExecutionChoreographer()
        
        mock_registry = Mock()
        mock_registry.list_adapter_methods = Mock(return_value=["method1", "method2"])
        
        is_valid = choreographer._validate_adapter_method(
            "test_adapter",
            "method1",
            mock_registry
        )
        
        assert is_valid is True
    
    def test_validate_nonexistent_method(self):
        """Test validation fails for non-existent method"""
        choreographer = ExecutionChoreographer()
        
        mock_registry = Mock()
        mock_registry.list_adapter_methods = Mock(return_value=["method1", "method2"])
        
        is_valid = choreographer._validate_adapter_method(
            "test_adapter",
            "nonexistent_method",
            mock_registry
        )
        
        assert is_valid is False
    
    def test_validate_nonexistent_adapter(self):
        """Test validation fails for non-existent adapter"""
        choreographer = ExecutionChoreographer()
        
        mock_registry = Mock()
        mock_registry.list_adapter_methods = Mock(side_effect=Exception("Adapter not found"))
        
        is_valid = choreographer._validate_adapter_method(
            "nonexistent_adapter",
            "method1",
            mock_registry
        )
        
        assert is_valid is False


class TestExecutionResult:
    """Test ExecutionResult dataclass"""
    
    def test_execution_result_creation(self):
        """Test creating execution result"""
        result = ExecutionResult(
            module_name="test_module",
            adapter_class="TestAdapter",
            method_name="test_method",
            status=ExecutionStatus.COMPLETED,
            output={"data": "test"},
            execution_time=0.5,
            confidence=0.9
        )
        
        assert result.module_name == "test_module"
        assert result.status == ExecutionStatus.COMPLETED
        assert result.confidence == 0.9
    
    def test_execution_result_to_dict(self):
        """Test converting execution result to dictionary"""
        result = ExecutionResult(
            module_name="test_module",
            adapter_class="TestAdapter",
            method_name="test_method",
            status=ExecutionStatus.COMPLETED,
            output={"data": "test"},
            execution_time=0.5,
            confidence=0.9,
            evidence_extracted={"evidence": ["item1", "item2"]}
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["module_name"] == "test_module"
        assert result_dict["status"] == "completed"
        assert result_dict["confidence"] == 0.9
        assert "evidence" in result_dict


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
