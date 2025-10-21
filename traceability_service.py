"""
Traceability Service for Event-Driven Choreography
===================================================

Maintains bidirectional traceability maps:
- Question ID <-> Event Sequence
- Event <-> Component <-> Source Code
- Identifies orphan methods and unmapped questions

Author: FARFAN Integration Team
Version: 1.0.0
Python: 3.11+
"""

import logging
import inspect
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass, field

from events.base_events import BaseEvent, EventType

logger = logging.getLogger(__name__)


@dataclass
class ComponentMapping:
    """
    Maps a component to its source code
    
    Attributes:
        component_name: Name of the component/adapter
        module_path: Path to source module
        class_name: Class implementing the component
        methods: List of method names
        subscribed_events: Events this component subscribes to
        published_events: Events this component publishes
    """
    
    component_name: str
    module_path: str
    class_name: str
    methods: List[str] = field(default_factory=list)
    subscribed_events: List[EventType] = field(default_factory=list)
    published_events: List[EventType] = field(default_factory=list)


@dataclass
class QuestionTrace:
    """
    Traces a question through event flow
    
    Attributes:
        question_id: Question identifier
        correlation_id: Correlation ID for this question's workflow
        events: List of event IDs in order
        components: Set of components that processed this question
        status: Overall status (pending, processing, completed, failed)
        start_time: When processing started
        end_time: When processing completed
    """
    
    question_id: str
    correlation_id: str
    events: List[str] = field(default_factory=list)
    components: Set[str] = field(default_factory=set)
    status: str = "pending"
    start_time: Optional[str] = None
    end_time: Optional[str] = None


@dataclass
class OrphanAnalysis:
    """
    Analysis of orphan methods and unmapped questions
    
    Attributes:
        orphan_methods: Methods in code not called by any event flow
        unmapped_questions: Questions without execution traces
        underutilized_components: Components with low event traffic
        recommendations: Recommendations for improvement
    """
    
    orphan_methods: List[Tuple[str, str]] = field(default_factory=list)  # (component, method)
    unmapped_questions: List[str] = field(default_factory=list)
    underutilized_components: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class TraceabilityService:
    """
    Service for tracking and analyzing event-question-component-code relationships
    
    Features:
    - Listen to all events to build trace
    - Map questions to event sequences
    - Map events to components and source code
    - Identify orphan methods
    - Identify unmapped questions
    - Generate traceability reports
    """
    
    def __init__(self, metadata_service: Optional[Any] = None):
        """
        Initialize traceability service
        
        Args:
            metadata_service: MetadataService instance for question metadata
        """
        self.metadata_service = metadata_service
        
        # Traceability maps
        self.question_traces: Dict[str, QuestionTrace] = {}
        self.correlation_traces: Dict[str, QuestionTrace] = {}
        self.component_mappings: Dict[str, ComponentMapping] = {}
        
        # Event tracking
        self.event_to_component: Dict[str, str] = {}  # event_id -> component_name
        self.event_sequences: Dict[str, List[str]] = defaultdict(list)  # correlation_id -> [event_ids]
        
        # Method invocation tracking
        self.method_invocations: Dict[str, Set[str]] = defaultdict(set)  # component -> {methods}
        
        logger.info("TraceabilityService initialized")
    
    def record_event(
        self,
        event: BaseEvent,
        component_name: Optional[str] = None,
        method_name: Optional[str] = None
    ) -> None:
        """
        Record an event in the traceability system
        
        Args:
            event: Event that occurred
            component_name: Component that emitted the event
            method_name: Method that emitted the event
        """
        # Track event sequence by correlation
        self.event_sequences[event.correlation_id].append(event.event_id)
        
        # Track event to component mapping
        if component_name:
            self.event_to_component[event.event_id] = component_name
            
            # Track method invocation
            if method_name:
                self.method_invocations[component_name].add(method_name)
        
        # Track question traces
        if event.question_id:
            if event.question_id not in self.question_traces:
                self.question_traces[event.question_id] = QuestionTrace(
                    question_id=event.question_id,
                    correlation_id=event.correlation_id,
                    start_time=event.timestamp,
                )
            
            trace = self.question_traces[event.question_id]
            trace.events.append(event.event_id)
            if component_name:
                trace.components.add(component_name)
            
            # Update status based on event type
            if event.event_type == EventType.ANALYSIS_REQUESTED:
                trace.status = "processing"
            elif event.event_type == EventType.FINAL_REPORT_READY:
                trace.status = "completed"
                trace.end_time = event.timestamp
            elif event.event_type in [
                EventType.VALIDATION_FAILED,
                EventType.PROCESSING_FAILED,
                EventType.PRECONDITION_FAILED,
            ]:
                trace.status = "failed"
        
        # Map by correlation ID
        if event.correlation_id not in self.correlation_traces and event.question_id:
            self.correlation_traces[event.correlation_id] = (
                self.question_traces[event.question_id]
            )
    
    def register_component(
        self,
        component_name: str,
        module_path: str,
        class_name: str,
        subscribed_events: Optional[List[EventType]] = None,
        published_events: Optional[List[EventType]] = None,
    ) -> None:
        """
        Register a component in the traceability system
        
        Args:
            component_name: Name of component
            module_path: Path to source module
            class_name: Class implementing component
            subscribed_events: Events component subscribes to
            published_events: Events component publishes
        """
        # Get methods from class using introspection
        methods = self._introspect_methods(module_path, class_name)
        
        self.component_mappings[component_name] = ComponentMapping(
            component_name=component_name,
            module_path=module_path,
            class_name=class_name,
            methods=methods,
            subscribed_events=subscribed_events or [],
            published_events=published_events or [],
        )
        
        logger.debug(f"Registered component {component_name} with {len(methods)} methods")
    
    def _introspect_methods(self, module_path: str, class_name: str) -> List[str]:
        """
        Introspect methods from a class
        
        Args:
            module_path: Path to module file
            class_name: Class to introspect
            
        Returns:
            List of method names
        """
        methods = []
        
        try:
            # Import module dynamically
            import importlib.util
            spec = importlib.util.spec_from_file_location("temp_module", module_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Get class
                if hasattr(module, class_name):
                    cls = getattr(module, class_name)
                    
                    # Get methods
                    for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
                        if not name.startswith('_'):
                            methods.append(name)
        except Exception as e:
            logger.warning(f"Could not introspect {class_name} in {module_path}: {e}")
        
        return methods
    
    def get_question_trace(self, question_id: str) -> Optional[QuestionTrace]:
        """Get trace for a specific question"""
        return self.question_traces.get(question_id)
    
    def get_correlation_trace(self, correlation_id: str) -> Optional[QuestionTrace]:
        """Get trace by correlation ID"""
        return self.correlation_traces.get(correlation_id)
    
    def get_event_flow(self, question_id: str) -> List[Tuple[str, str, str]]:
        """
        Get event flow for a question
        
        Returns:
            List of (event_id, event_type, component_name) tuples
        """
        trace = self.question_traces.get(question_id)
        if not trace:
            return []
        
        flow = []
        for event_id in trace.events:
            component = self.event_to_component.get(event_id, "unknown")
            flow.append((event_id, "event", component))
        
        return flow
    
    def analyze_orphans(self) -> OrphanAnalysis:
        """
        Analyze orphan methods and unmapped questions
        
        Returns:
            OrphanAnalysis with findings
        """
        orphan_methods = []
        unmapped_questions = []
        underutilized_components = []
        recommendations = []
        
        # Find orphan methods (methods not invoked by any event flow)
        for component_name, mapping in self.component_mappings.items():
            invoked = self.method_invocations.get(component_name, set())
            for method in mapping.methods:
                if method not in invoked:
                    orphan_methods.append((component_name, method))
        
        # Find unmapped questions (questions without traces)
        if self.metadata_service:
            all_questions = self.metadata_service.get_all_question_ids()
            for question_id in all_questions:
                if question_id not in self.question_traces:
                    unmapped_questions.append(question_id)
        
        # Find underutilized components
        for component_name, mapping in self.component_mappings.items():
            invoked = self.method_invocations.get(component_name, set())
            if len(invoked) == 0:
                underutilized_components.append(component_name)
            elif len(invoked) < len(mapping.methods) * 0.5:
                underutilized_components.append(component_name)
        
        # Generate recommendations
        if orphan_methods:
            recommendations.append(
                f"Found {len(orphan_methods)} orphan methods. "
                "Consider removing unused code or adding event flows to use them."
            )
        
        if unmapped_questions:
            recommendations.append(
                f"Found {len(unmapped_questions)} unmapped questions. "
                "Add execution chains in execution_mapping.yaml."
            )
        
        if underutilized_components:
            recommendations.append(
                f"Found {len(underutilized_components)} underutilized components. "
                "Review component usage and consider consolidation."
            )
        
        return OrphanAnalysis(
            orphan_methods=orphan_methods,
            unmapped_questions=unmapped_questions,
            underutilized_components=underutilized_components,
            recommendations=recommendations,
        )
    
    def generate_traceability_matrix(self) -> Dict[str, Any]:
        """
        Generate traceability matrix
        
        Returns:
            Dict with traceability information
        """
        matrix = {
            "questions": {},
            "components": {},
            "events": {},
            "statistics": {
                "total_questions": len(self.question_traces),
                "total_components": len(self.component_mappings),
                "total_events": sum(len(events) for events in self.event_sequences.values()),
                "completed_questions": len([
                    t for t in self.question_traces.values()
                    if t.status == "completed"
                ]),
                "failed_questions": len([
                    t for t in self.question_traces.values()
                    if t.status == "failed"
                ]),
            },
        }
        
        # Add question traces
        for question_id, trace in self.question_traces.items():
            matrix["questions"][question_id] = {
                "status": trace.status,
                "events": len(trace.events),
                "components": list(trace.components),
                "correlation_id": trace.correlation_id,
            }
        
        # Add component info
        for component_name, mapping in self.component_mappings.items():
            invoked = self.method_invocations.get(component_name, set())
            matrix["components"][component_name] = {
                "class": mapping.class_name,
                "module": mapping.module_path,
                "total_methods": len(mapping.methods),
                "invoked_methods": len(invoked),
                "utilization": len(invoked) / max(len(mapping.methods), 1),
                "subscribed_events": [e.value for e in mapping.subscribed_events],
                "published_events": [e.value for e in mapping.published_events],
            }
        
        return matrix
    
    def generate_report(self) -> str:
        """
        Generate human-readable traceability report
        
        Returns:
            Formatted report string
        """
        lines = ["=" * 80]
        lines.append("TRACEABILITY REPORT")
        lines.append("=" * 80)
        lines.append("")
        
        # Statistics
        matrix = self.generate_traceability_matrix()
        stats = matrix["statistics"]
        
        lines.append("STATISTICS:")
        lines.append(f"  Total Questions: {stats['total_questions']}")
        lines.append(f"  Completed: {stats['completed_questions']}")
        lines.append(f"  Failed: {stats['failed_questions']}")
        lines.append(f"  Total Components: {stats['total_components']}")
        lines.append(f"  Total Events: {stats['total_events']}")
        lines.append("")
        
        # Orphan analysis
        orphans = self.analyze_orphans()
        
        lines.append("ORPHAN ANALYSIS:")
        lines.append(f"  Orphan Methods: {len(orphans.orphan_methods)}")
        if orphans.orphan_methods[:5]:
            for component, method in orphans.orphan_methods[:5]:
                lines.append(f"    - {component}.{method}")
            if len(orphans.orphan_methods) > 5:
                lines.append(f"    ... and {len(orphans.orphan_methods) - 5} more")
        
        lines.append(f"  Unmapped Questions: {len(orphans.unmapped_questions)}")
        if orphans.unmapped_questions[:5]:
            for question_id in orphans.unmapped_questions[:5]:
                lines.append(f"    - {question_id}")
            if len(orphans.unmapped_questions) > 5:
                lines.append(f"    ... and {len(orphans.unmapped_questions) - 5} more")
        
        lines.append("")
        
        # Recommendations
        if orphans.recommendations:
            lines.append("RECOMMENDATIONS:")
            for rec in orphans.recommendations:
                lines.append(f"  - {rec}")
        
        lines.append("")
        lines.append("=" * 80)
        
        return "\n".join(lines)
