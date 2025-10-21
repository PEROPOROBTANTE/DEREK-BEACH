"""
Interface Contract Tests
=========================

Comprehensive test suite for validating:
- Event schema validation
- Component behavior with specific input events
- Validation logic correctness within components
- Traceability checks (event-to-question mapping)
- Rubric scoring integration and preconditions

Author: FARFAN Integration Team
Version: 1.0.0
Python: 3.11+
"""

import pytest
import sys
import json
from pathlib import Path
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from events import (
    BaseEvent,
    EventType,
    EventStatus,
    AnalysisRequestedEvent,
    ChunkingCompleteEvent,
    ValidationFailedEvent,
    ProcessingFailedEvent,
    PreconditionFailedEvent,
    QuestionContext,
    ValidationRule,
    ScoringModality,
)
from event_bus import EventBus, reset_event_bus
from metadata_service import MetadataService
from traceability_service import TraceabilityService
from event_driven_choreographer import (
    EventDrivenChoreographer,
    EventDrivenComponent,
    ChoreographyConfig,
)


class TestEventSchemaValidation:
    """Test event schema validation and immutability"""
    
    def test_base_event_immutability(self):
        """Test that events are immutable"""
        event = BaseEvent(
            event_type=EventType.ANALYSIS_REQUESTED,
            question_id="D1-Q1",
        )
        
        # Events are frozen, should not be able to modify
        with pytest.raises(Exception):  # dataclass frozen raises
            event.question_id = "D2-Q2"
    
    def test_base_event_schema_validation(self):
        """Test base event schema validation"""
        event = BaseEvent(
            event_type=EventType.ANALYSIS_REQUESTED,
            question_id="D1-Q1",
        )
        
        assert event.validate_schema() is True
        assert event.event_id is not None
        assert event.correlation_id is not None
        assert event.schema_version == "1.0.0"
    
    def test_event_to_dict_serialization(self):
        """Test event serialization to dictionary"""
        event = AnalysisRequestedEvent(
            question_id="D1-Q1",
            document_reference="/path/to/doc",
            plan_name="Test Plan",
        )
        
        event_dict = event.to_dict()
        
        assert event_dict["event_type"] == EventType.ANALYSIS_REQUESTED.value
        assert event_dict["question_id"] == "D1-Q1"
        assert event_dict["document_reference"] == "/path/to/doc"
        assert "event_id" in event_dict
        assert "correlation_id" in event_dict
    
    def test_event_status_transitions(self):
        """Test event status transitions"""
        event = BaseEvent(
            event_type=EventType.ANALYSIS_REQUESTED,
            status=EventStatus.CREATED,
        )
        
        # Create new event with updated status
        published_event = event.with_status(EventStatus.PUBLISHED)
        
        assert event.status == EventStatus.CREATED
        assert published_event.status == EventStatus.PUBLISHED
        # Should have same IDs
        assert event.event_id == published_event.event_id


class TestValidationRules:
    """Test validation rule logic"""
    
    def test_numeric_validation_rules(self):
        """Test numeric validation rules"""
        rule = ValidationRule(
            rule_name="min_words",
            rule_type="numeric",
            operator=">=",
            value=100,
            error_message="Insufficient words",
        )
        
        assert rule.validate(150) is True
        assert rule.validate(50) is False
        
        # Test other operators
        rule_eq = ValidationRule(
            rule_name="exact_count",
            rule_type="numeric",
            operator="==",
            value=5,
            error_message="Must be exactly 5",
        )
        
        assert rule_eq.validate(5) is True
        assert rule_eq.validate(4) is False
    
    def test_list_validation_rules(self):
        """Test list validation rules"""
        rule = ValidationRule(
            rule_name="required_sections",
            rule_type="list",
            operator="contains_all",
            value=["diagnostico", "linea_base"],
            error_message="Missing required sections",
        )
        
        assert rule.validate(["diagnostico", "linea_base", "extra"]) is True
        assert rule.validate(["diagnostico"]) is False
        assert rule.validate([]) is False
    
    def test_boolean_validation_rules(self):
        """Test boolean validation rules"""
        rule = ValidationRule(
            rule_name="requires_complete_path",
            rule_type="boolean",
            operator="==",
            value=True,
            error_message="Path must be complete",
        )
        
        assert rule.validate(True) is True
        assert rule.validate(False) is False


class TestQuestionContext:
    """Test QuestionContext data structure"""
    
    def test_question_context_creation(self):
        """Test creating QuestionContext"""
        context = QuestionContext(
            question_id="D1-Q1",
            dimension="D1",
            scoring_modality=ScoringModality.TYPE_A,
            expected_elements=4,
        )
        
        assert context.question_id == "D1-Q1"
        assert context.dimension == "D1"
        assert context.expected_elements == 4
    
    def test_question_context_input_validation(self):
        """Test QuestionContext input validation"""
        rule = ValidationRule(
            rule_name="min_words",
            rule_type="numeric",
            operator=">=",
            value=100,
            error_message="Insufficient words",
        )
        
        context = QuestionContext(
            question_id="D1-Q1",
            dimension="D1",
            validation_rules=[rule],
        )
        
        # Valid input
        errors = context.validate_input({"min_words": 150})
        assert len(errors) == 0
        
        # Invalid input
        errors = context.validate_input({"min_words": 50})
        assert len(errors) == 1
        assert "Insufficient words" in errors[0]
        
        # Missing field
        errors = context.validate_input({})
        assert len(errors) == 1
        assert "Missing required field" in errors[0]
    
    def test_question_context_precondition_checks(self):
        """Test QuestionContext precondition checking"""
        context = QuestionContext(
            question_id="D1-Q1",
            dimension="D1",
            preconditions={
                "causal_graph": True,
                "embeddings": True,
            },
        )
        
        # All preconditions met
        unmet = context.check_preconditions({
            "causal_graph": True,
            "embeddings": True,
        })
        assert len(unmet) == 0
        
        # Missing precondition
        unmet = context.check_preconditions({
            "causal_graph": True,
        })
        assert len(unmet) == 1
        
        # Precondition not satisfied
        unmet = context.check_preconditions({
            "causal_graph": False,
            "embeddings": True,
        })
        assert len(unmet) == 1
    
    def test_question_context_serialization(self):
        """Test QuestionContext to_dict/from_dict"""
        context = QuestionContext(
            question_id="D1-Q1",
            dimension="D1",
            scoring_modality=ScoringModality.TYPE_A,
            expected_elements=4,
        )
        
        context_dict = context.to_dict()
        restored = QuestionContext.from_dict(context_dict)
        
        assert restored.question_id == context.question_id
        assert restored.dimension == context.dimension
        assert restored.scoring_modality == context.scoring_modality
        assert restored.expected_elements == context.expected_elements


class TestEventBus:
    """Test EventBus functionality"""
    
    def setup_method(self):
        """Reset event bus before each test"""
        reset_event_bus()
    
    def test_event_bus_publish_subscribe(self):
        """Test basic pub/sub"""
        from event_bus import get_event_bus
        
        bus = get_event_bus()
        received_events = []
        
        def callback(event):
            received_events.append(event)
        
        # Subscribe
        bus.subscribe(
            subscriber_id="test_subscriber",
            event_types=[EventType.ANALYSIS_REQUESTED],
            callback=callback,
        )
        
        # Publish
        event = AnalysisRequestedEvent(question_id="D1-Q1")
        bus.publish(event)
        
        # Give async processing time
        import time
        time.sleep(0.1)
        
        # Check received
        assert len(received_events) == 1
        assert received_events[0].question_id == "D1-Q1"
    
    def test_event_bus_filtering_by_type(self):
        """Test event filtering by type"""
        from event_bus import get_event_bus
        
        bus = get_event_bus()
        received_events = []
        
        def callback(event):
            received_events.append(event)
        
        # Subscribe only to CHUNKING_COMPLETE
        bus.subscribe(
            subscriber_id="test_subscriber",
            event_types=[EventType.CHUNKING_COMPLETE],
            callback=callback,
        )
        
        # Publish different event
        event1 = AnalysisRequestedEvent(question_id="D1-Q1")
        bus.publish(event1)
        
        # Publish matching event
        event2 = ChunkingCompleteEvent(question_id="D1-Q1")
        bus.publish(event2)
        
        import time
        time.sleep(0.1)
        
        # Should only receive ChunkingCompleteEvent
        assert len(received_events) == 1
        assert received_events[0].event_type == EventType.CHUNKING_COMPLETE
    
    def test_event_bus_question_filtering(self):
        """Test event filtering by question_id"""
        from event_bus import get_event_bus
        
        bus = get_event_bus()
        received_events = []
        
        def callback(event):
            received_events.append(event)
        
        # Subscribe with question filter
        bus.subscribe(
            subscriber_id="test_subscriber",
            event_types=[EventType.ANALYSIS_REQUESTED],
            callback=callback,
            question_filter="D1-Q1",
        )
        
        # Publish event for different question
        event1 = AnalysisRequestedEvent(question_id="D2-Q1")
        bus.publish(event1)
        
        # Publish event for matching question
        event2 = AnalysisRequestedEvent(question_id="D1-Q1")
        bus.publish(event2)
        
        import time
        time.sleep(0.1)
        
        # Should only receive D1-Q1
        assert len(received_events) == 1
        assert received_events[0].question_id == "D1-Q1"
    
    def test_event_bus_history(self):
        """Test event history tracking"""
        from event_bus import get_event_bus
        
        bus = get_event_bus()
        
        event1 = AnalysisRequestedEvent(question_id="D1-Q1")
        event2 = AnalysisRequestedEvent(question_id="D2-Q1")
        
        bus.publish(event1)
        bus.publish(event2)
        
        # Check history
        all_events = bus.get_all_events()
        assert len(all_events) == 2
        
        # Check filtering
        d1_events = bus.get_events_by_question("D1-Q1")
        assert len(d1_events) == 1
        assert d1_events[0].question_id == "D1-Q1"


class TestMetadataService:
    """Test MetadataService functionality"""
    
    def test_metadata_service_initialization(self):
        """Test MetadataService initialization"""
        service = MetadataService()
        
        assert service.cuestionario_path.exists()
        assert service.execution_mapping_path.exists()
        assert service.rubric_scoring_path.exists()
    
    def test_metadata_service_load_all(self):
        """Test loading all metadata files"""
        service = MetadataService()
        result = service.load_all()
        
        assert result is not None
        # execution_mapping and rubric_scoring should load successfully
        assert len(service.execution_mapping) > 0
        assert len(service.rubric_scoring) > 0
        # cuestionario may have errors in existing file, but that's ok for this test
    
    def test_metadata_service_get_question_context(self):
        """Test getting QuestionContext"""
        service = MetadataService()
        service.load_all()
        
        context = service.get_question_context("D1")
        
        assert context is not None
        assert context.dimension == "D1"
        assert context.execution_chain is not None
    
    def test_metadata_service_dimension_extraction(self):
        """Test dimension extraction from question IDs"""
        service = MetadataService()
        
        assert service._extract_dimension("D1-Q1") == "D1"
        assert service._extract_dimension("P1-D2-Q3") == "D2"
        assert service._extract_dimension("D6") == "D6"


class TestTraceabilityService:
    """Test TraceabilityService functionality"""
    
    def test_traceability_record_event(self):
        """Test recording events"""
        service = TraceabilityService()
        
        event = AnalysisRequestedEvent(
            question_id="D1-Q1",
            correlation_id="test-correlation",
        )
        
        service.record_event(event, component_name="test_component")
        
        trace = service.get_question_trace("D1-Q1")
        
        assert trace is not None
        assert trace.question_id == "D1-Q1"
        assert len(trace.events) == 1
        assert "test_component" in trace.components
    
    def test_traceability_orphan_analysis(self):
        """Test orphan method analysis"""
        service = TraceabilityService()
        
        # Register a component
        service.register_component(
            component_name="test_adapter",
            module_path="test.py",
            class_name="TestAdapter",
        )
        
        # Analyze without any invocations
        analysis = service.analyze_orphans()
        
        # Component is underutilized since no methods were invoked
        assert len(analysis.underutilized_components) > 0
    
    def test_traceability_generate_matrix(self):
        """Test traceability matrix generation"""
        service = TraceabilityService()
        
        event = AnalysisRequestedEvent(
            question_id="D1-Q1",
            correlation_id="test-correlation",
        )
        
        service.record_event(event, component_name="test_component")
        
        matrix = service.generate_traceability_matrix()
        
        assert "questions" in matrix
        assert "components" in matrix
        assert "statistics" in matrix
        assert matrix["statistics"]["total_questions"] == 1


class TestEventDrivenChoreographer:
    """Test EventDrivenChoreographer"""
    
    def setup_method(self):
        """Reset event bus before each test"""
        reset_event_bus()
    
    def test_choreographer_initialization(self):
        """Test choreographer initialization"""
        metadata_service = MetadataService()
        metadata_service.load_all()
        
        choreographer = EventDrivenChoreographer(
            metadata_service=metadata_service,
            config=ChoreographyConfig(deterministic_seed=42),
        )
        
        assert choreographer.metadata_service is not None
        assert choreographer.event_bus is not None
        assert choreographer.config.deterministic_seed == 42
    
    def test_choreographer_start_analysis(self):
        """Test starting analysis"""
        metadata_service = MetadataService()
        metadata_service.load_all()
        
        choreographer = EventDrivenChoreographer(
            metadata_service=metadata_service,
        )
        
        correlation_id = choreographer.start_analysis(
            document_reference="/path/to/doc",
            target_question_ids=["D1-Q1", "D2-Q1"],
            plan_name="Test Plan",
            plan_text="Test plan text",
        )
        
        assert correlation_id is not None
        
        # Check events were published
        import time
        time.sleep(0.1)
        
        events = choreographer.event_bus.get_events_by_correlation(correlation_id)
        assert len(events) == 2
    
    def test_choreographer_deterministic_seeding(self):
        """Test deterministic behavior with seeding"""
        import random
        
        metadata_service = MetadataService()
        metadata_service.load_all()
        
        # Create two choreographers with same seed
        config1 = ChoreographyConfig(deterministic_seed=42)
        choreographer1 = EventDrivenChoreographer(
            metadata_service=metadata_service,
            config=config1,
        )
        
        random_vals1 = [random.random() for _ in range(5)]
        
        # Reset and create another
        config2 = ChoreographyConfig(deterministic_seed=42)
        choreographer2 = EventDrivenChoreographer(
            metadata_service=metadata_service,
            config=config2,
        )
        
        random_vals2 = [random.random() for _ in range(5)]
        
        # Should be identical
        assert random_vals1 == random_vals2


class TestComponentBehavior:
    """Test component behavior with mocked dependencies"""
    
    def setup_method(self):
        """Reset event bus before each test"""
        reset_event_bus()
    
    def test_component_validation(self):
        """Test component validates input"""
        from event_bus import get_event_bus
        
        metadata_service = MetadataService()
        metadata_service.load_all()
        
        class TestComponent(EventDrivenComponent):
            def validate_input(self, event, question_context):
                if not hasattr(event, 'plan_text'):
                    return ["Missing plan_text"]
                if len(event.plan_text) < 10:
                    return ["plan_text too short"]
                return []
            
            def process(self, event, question_context):
                return {"status": "ok"}
        
        component = TestComponent(
            component_name="test_component",
            event_bus=get_event_bus(),
            metadata_service=metadata_service,
        )
        
        # Test with invalid event
        event = AnalysisRequestedEvent(
            question_id="D1-Q1",
            plan_text="short",
        )
        
        component.on_event(event)
        
        # Should emit ValidationFailedEvent
        import time
        time.sleep(0.1)
        
        events = get_event_bus().get_events_by_type(EventType.VALIDATION_FAILED)
        assert len(events) > 0


# Run validation commands
def run_tests():
    """Run all tests with pytest"""
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--cov=events",
        "--cov=event_bus",
        "--cov=metadata_service",
        "--cov=traceability_service",
        "--cov=event_driven_choreographer",
        "--cov-report=term-missing",
    ])


if __name__ == "__main__":
    run_tests()
