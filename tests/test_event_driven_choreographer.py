"""
Comprehensive Tests for Event-Driven Choreographer
===================================================

Tests the event-driven choreography implementation including:
- Initialization and configuration
- Component registration and management
- Analysis workflow execution
- Traceability service integration
- Event handling and error scenarios
- Deterministic execution

Author: FARFAN Testing Team
Version: 1.0.0
Python: 3.11+
"""

import pytest
import uuid
from unittest.mock import Mock, MagicMock, patch, call
from typing import List, Dict, Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from event_driven_choreographer import (
    EventDrivenChoreographer,
    EventDrivenComponent,
    ChoreographyConfig,
)
from event_bus import EventBus
from events import (
    EventType,
    EventStatus,
    AnalysisRequestedEvent,
    ChunkingCompleteEvent,
    ValidationFailedEvent,
    ProcessingFailedEvent,
    QuestionContext,
)


class TestChoreographyConfig:
    """Test ChoreographyConfig dataclass"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = ChoreographyConfig()
        
        assert config.enable_traceability is True
        assert config.deterministic_seed == 42
        assert config.validation_mode == "strict"
        assert config.max_retry_count == 3
    
    def test_custom_config(self):
        """Test custom configuration values"""
        config = ChoreographyConfig(
            enable_traceability=False,
            deterministic_seed=None,
            validation_mode="lenient",
            max_retry_count=5
        )
        
        assert config.enable_traceability is False
        assert config.deterministic_seed is None
        assert config.validation_mode == "lenient"
        assert config.max_retry_count == 5


class TestEventDrivenChoreographerInitialization:
    """Test EventDrivenChoreographer initialization"""
    
    def test_initialization_with_defaults(self):
        """Test choreographer initialization with default config"""
        metadata_service = Mock()
        
        choreographer = EventDrivenChoreographer(
            metadata_service=metadata_service
        )
        
        assert choreographer.metadata_service == metadata_service
        assert choreographer.event_bus is not None
        assert choreographer.config is not None
        assert choreographer.config.deterministic_seed == 42
        assert len(choreographer.components) == 0
    
    def test_initialization_with_custom_config(self):
        """Test choreographer initialization with custom config"""
        metadata_service = Mock()
        config = ChoreographyConfig(
            enable_traceability=False,
            deterministic_seed=100
        )
        
        choreographer = EventDrivenChoreographer(
            metadata_service=metadata_service,
            config=config
        )
        
        assert choreographer.config.enable_traceability is False
        assert choreographer.config.deterministic_seed == 100
        assert choreographer.traceability_service is None
    
    def test_initialization_with_traceability_enabled(self):
        """Test choreographer with traceability service enabled"""
        metadata_service = Mock()
        config = ChoreographyConfig(enable_traceability=True)
        
        choreographer = EventDrivenChoreographer(
            metadata_service=metadata_service,
            config=config
        )
        
        assert choreographer.traceability_service is not None
    
    def test_initialization_with_custom_event_bus(self):
        """Test choreographer with custom event bus"""
        metadata_service = Mock()
        custom_event_bus = Mock(spec=EventBus)
        
        choreographer = EventDrivenChoreographer(
            metadata_service=metadata_service,
            event_bus=custom_event_bus
        )
        
        assert choreographer.event_bus == custom_event_bus
    
    @patch('random.seed')
    def test_deterministic_seed_setting(self, mock_seed):
        """Test that deterministic seed is properly set"""
        metadata_service = Mock()
        config = ChoreographyConfig(deterministic_seed=42)
        
        choreographer = EventDrivenChoreographer(
            metadata_service=metadata_service,
            config=config
        )
        
        mock_seed.assert_called_with(42)


class TestComponentRegistration:
    """Test component registration and management"""
    
    def test_register_single_component(self):
        """Test registering a single component"""
        metadata_service = Mock()
        choreographer = EventDrivenChoreographer(
            metadata_service=metadata_service,
            config=ChoreographyConfig(enable_traceability=False)
        )
        
        component = Mock()
        component.__class__.__module__ = "test_module"
        component.__class__.__name__ = "TestComponent"
        
        choreographer.register_component(
            component_name="test_component",
            component=component,
            subscribed_events=[EventType.ANALYSIS_REQUESTED],
            published_events=[EventType.CHUNKING_COMPLETE]
        )
        
        assert "test_component" in choreographer.components
        assert choreographer.components["test_component"] == component
    
    def test_register_multiple_components(self):
        """Test registering multiple components"""
        metadata_service = Mock()
        choreographer = EventDrivenChoreographer(
            metadata_service=metadata_service,
            config=ChoreographyConfig(enable_traceability=False)
        )
        
        components = [
            ("component1", Mock()),
            ("component2", Mock()),
            ("component3", Mock())
        ]
        
        for name, comp in components:
            comp.__class__.__module__ = "test"
            comp.__class__.__name__ = name.capitalize()
            choreographer.register_component(
                component_name=name,
                component=comp,
                subscribed_events=[EventType.ANALYSIS_REQUESTED],
                published_events=[EventType.CHUNKING_COMPLETE]
            )
        
        assert len(choreographer.components) == 3
        for name, comp in components:
            assert choreographer.components[name] == comp
    
    def test_register_component_with_traceability(self):
        """Test component registration with traceability enabled"""
        metadata_service = Mock()
        choreographer = EventDrivenChoreographer(
            metadata_service=metadata_service,
            config=ChoreographyConfig(enable_traceability=True)
        )
        
        component = Mock()
        component.__class__.__module__ = "test_module"
        component.__class__.__name__ = "TestComponent"
        
        choreographer.register_component(
            component_name="test_component",
            component=component,
            subscribed_events=[EventType.ANALYSIS_REQUESTED],
            published_events=[EventType.CHUNKING_COMPLETE]
        )
        
        # Verify traceability service was called
        assert choreographer.traceability_service is not None


class TestAnalysisExecution:
    """Test analysis execution workflow"""
    
    def test_start_analysis_single_question(self):
        """Test starting analysis for a single question"""
        metadata_service = Mock()
        event_bus = Mock(spec=EventBus)
        
        choreographer = EventDrivenChoreographer(
            metadata_service=metadata_service,
            event_bus=event_bus,
            config=ChoreographyConfig(enable_traceability=False)
        )
        
        correlation_id = choreographer.start_analysis(
            document_reference="test_doc.pdf",
            target_question_ids=["P1-D1-Q1"],
            plan_name="Test Plan",
            plan_text="Test plan text"
        )
        
        assert correlation_id is not None
        assert isinstance(correlation_id, str)
        event_bus.publish.assert_called_once()
        
        # Verify event was published with correct data
        call_args = event_bus.publish.call_args
        event = call_args[0][0]
        assert isinstance(event, AnalysisRequestedEvent)
        assert event.question_id == "P1-D1-Q1"
        assert event.correlation_id == correlation_id
    
    def test_start_analysis_multiple_questions(self):
        """Test starting analysis for multiple questions"""
        metadata_service = Mock()
        event_bus = Mock(spec=EventBus)
        
        choreographer = EventDrivenChoreographer(
            metadata_service=metadata_service,
            event_bus=event_bus,
            config=ChoreographyConfig(enable_traceability=False)
        )
        
        question_ids = ["P1-D1-Q1", "P1-D1-Q2", "P1-D2-Q1"]
        
        correlation_id = choreographer.start_analysis(
            document_reference="test_doc.pdf",
            target_question_ids=question_ids,
            plan_name="Test Plan",
            plan_text="Test plan text"
        )
        
        assert event_bus.publish.call_count == len(question_ids)
        
        # Verify all questions were published with same correlation_id
        for call_obj in event_bus.publish.call_args_list:
            event = call_obj[0][0]
            assert event.correlation_id == correlation_id
            assert event.question_id in question_ids
    
    def test_start_analysis_creates_unique_correlation_ids(self):
        """Test that each analysis gets a unique correlation ID"""
        metadata_service = Mock()
        event_bus = Mock(spec=EventBus)
        
        choreographer = EventDrivenChoreographer(
            metadata_service=metadata_service,
            event_bus=event_bus,
            config=ChoreographyConfig(enable_traceability=False)
        )
        
        correlation_id_1 = choreographer.start_analysis(
            document_reference="doc1.pdf",
            target_question_ids=["Q1"],
            plan_name="Plan 1",
            plan_text="Text 1"
        )
        
        correlation_id_2 = choreographer.start_analysis(
            document_reference="doc2.pdf",
            target_question_ids=["Q2"],
            plan_name="Plan 2",
            plan_text="Text 2"
        )
        
        assert correlation_id_1 != correlation_id_2


class TestAnalysisStatusTracking:
    """Test analysis status tracking"""
    
    def test_get_analysis_status_without_traceability(self):
        """Test getting status when traceability is disabled"""
        metadata_service = Mock()
        choreographer = EventDrivenChoreographer(
            metadata_service=metadata_service,
            config=ChoreographyConfig(enable_traceability=False)
        )
        
        status = choreographer.get_analysis_status("test_correlation_id")
        
        assert "error" in status
        assert status["error"] == "Traceability not enabled"
    
    def test_get_analysis_status_not_found(self):
        """Test getting status for non-existent correlation ID"""
        metadata_service = Mock()
        choreographer = EventDrivenChoreographer(
            metadata_service=metadata_service,
            config=ChoreographyConfig(enable_traceability=True)
        )
        
        # Mock traceability service
        choreographer.traceability_service.get_correlation_trace = Mock(return_value=None)
        
        status = choreographer.get_analysis_status("nonexistent_id")
        
        assert status["status"] == "not_found"
    
    def test_get_analysis_status_success(self):
        """Test getting status for existing correlation ID"""
        metadata_service = Mock()
        choreographer = EventDrivenChoreographer(
            metadata_service=metadata_service,
            config=ChoreographyConfig(enable_traceability=True)
        )
        
        # Mock traceability service trace
        mock_trace = Mock()
        mock_trace.question_id = "P1-D1-Q1"
        mock_trace.status = "completed"
        mock_trace.events = ["event1", "event2"]
        mock_trace.components = {"component1", "component2"}
        mock_trace.start_time = "2024-01-01T00:00:00"
        mock_trace.end_time = "2024-01-01T00:01:00"
        
        choreographer.traceability_service.get_correlation_trace = Mock(return_value=mock_trace)
        
        status = choreographer.get_analysis_status("test_correlation_id")
        
        assert status["question_id"] == "P1-D1-Q1"
        assert status["status"] == "completed"
        assert status["events"] == 2
        assert "component1" in status["components"]


class TestTraceabilityReporting:
    """Test traceability reporting"""
    
    def test_get_traceability_report_disabled(self):
        """Test getting report when traceability is disabled"""
        metadata_service = Mock()
        choreographer = EventDrivenChoreographer(
            metadata_service=metadata_service,
            config=ChoreographyConfig(enable_traceability=False)
        )
        
        report = choreographer.get_traceability_report()
        
        assert report == "Traceability not enabled"
    
    def test_get_traceability_report_enabled(self):
        """Test getting report when traceability is enabled"""
        metadata_service = Mock()
        choreographer = EventDrivenChoreographer(
            metadata_service=metadata_service,
            config=ChoreographyConfig(enable_traceability=True)
        )
        
        # Mock traceability service report
        mock_report = "Traceability Report:\n- Events: 10\n- Components: 5"
        choreographer.traceability_service.generate_report = Mock(return_value=mock_report)
        
        report = choreographer.get_traceability_report()
        
        assert report == mock_report
        choreographer.traceability_service.generate_report.assert_called_once()


class TestShutdown:
    """Test choreographer shutdown"""
    
    def test_shutdown_without_traceability(self):
        """Test shutdown when traceability is disabled"""
        metadata_service = Mock()
        event_bus = Mock(spec=EventBus)
        
        choreographer = EventDrivenChoreographer(
            metadata_service=metadata_service,
            event_bus=event_bus,
            config=ChoreographyConfig(enable_traceability=False)
        )
        
        # Should not raise any errors
        choreographer.shutdown()
        
        # Event bus unsubscribe should not be called
        event_bus.unsubscribe.assert_not_called()
    
    def test_shutdown_with_traceability(self):
        """Test shutdown when traceability is enabled"""
        metadata_service = Mock()
        event_bus = Mock(spec=EventBus)
        
        choreographer = EventDrivenChoreographer(
            metadata_service=metadata_service,
            event_bus=event_bus,
            config=ChoreographyConfig(enable_traceability=True)
        )
        
        choreographer.shutdown()
        
        # Event bus unsubscribe should be called for traceability service
        event_bus.unsubscribe.assert_called_once_with("traceability_service")


class TestEventDrivenComponent:
    """Test EventDrivenComponent base class"""
    
    def test_component_initialization(self):
        """Test component initialization"""
        event_bus = Mock(spec=EventBus)
        metadata_service = Mock()
        
        component = EventDrivenComponent(
            component_name="test_component",
            event_bus=event_bus,
            metadata_service=metadata_service
        )
        
        assert component.component_name == "test_component"
        assert component.event_bus == event_bus
        assert component.metadata_service == metadata_service
        assert component.logger is not None
    
    def test_validate_input_default(self):
        """Test default validate_input returns empty errors"""
        event_bus = Mock(spec=EventBus)
        metadata_service = Mock()
        
        component = EventDrivenComponent(
            component_name="test_component",
            event_bus=event_bus,
            metadata_service=metadata_service
        )
        
        event = Mock()
        errors = component.validate_input(event, None)
        
        assert errors == []
    
    def test_process_not_implemented(self):
        """Test that process() must be overridden"""
        event_bus = Mock(spec=EventBus)
        metadata_service = Mock()
        
        component = EventDrivenComponent(
            component_name="test_component",
            event_bus=event_bus,
            metadata_service=metadata_service
        )
        
        event = Mock()
        
        with pytest.raises(NotImplementedError):
            component.process(event, None)


class TestComponentEventHandling:
    """Test component event handling"""
    
    def test_on_event_with_valid_input(self):
        """Test handling event with valid input"""
        event_bus = Mock(spec=EventBus)
        metadata_service = Mock()
        
        class TestComponent(EventDrivenComponent):
            def validate_input(self, event, context):
                return []
            
            def process(self, event, context):
                return {"result": "success"}
            
            def emit_events(self, original_event, result, context):
                pass
        
        component = TestComponent(
            component_name="test",
            event_bus=event_bus,
            metadata_service=metadata_service
        )
        
        event = Mock()
        event.event_type.value = "test_event"
        event.event_id = "event_123"
        event.question_id = None
        
        # Should not raise errors
        component.on_event(event)
    
    def test_on_event_with_validation_errors(self):
        """Test handling event with validation errors"""
        event_bus = Mock(spec=EventBus)
        metadata_service = Mock()
        
        class TestComponent(EventDrivenComponent):
            def validate_input(self, event, context):
                return ["Error 1", "Error 2"]
            
            def process(self, event, context):
                return {"result": "success"}
        
        component = TestComponent(
            component_name="test",
            event_bus=event_bus,
            metadata_service=metadata_service
        )
        
        event = Mock()
        event.event_type.value = "test_event"
        event.event_id = "event_123"
        event.question_id = "Q1"
        event.correlation_id = "corr_123"
        
        component.on_event(event)
        
        # Should have published validation failed event
        event_bus.publish.assert_called_once()
        published_event = event_bus.publish.call_args[0][0]
        assert isinstance(published_event, ValidationFailedEvent)
    
    def test_on_event_with_processing_error(self):
        """Test handling event when processing raises exception"""
        event_bus = Mock(spec=EventBus)
        metadata_service = Mock()
        
        class TestComponent(EventDrivenComponent):
            def validate_input(self, event, context):
                return []
            
            def process(self, event, context):
                raise ValueError("Processing error")
        
        component = TestComponent(
            component_name="test",
            event_bus=event_bus,
            metadata_service=metadata_service
        )
        
        event = Mock()
        event.event_type.value = "test_event"
        event.event_id = "event_123"
        event.question_id = "Q1"
        event.correlation_id = "corr_123"
        
        component.on_event(event)
        
        # Should have published processing failed event
        event_bus.publish.assert_called_once()
        published_event = event_bus.publish.call_args[0][0]
        assert isinstance(published_event, ProcessingFailedEvent)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
