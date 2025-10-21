# DEREK-BEACH: FARFAN 3.0 Policy Analysis System

Event-driven choreography implementation for analyzing Municipal Development Plans (PDM) across 300 questions, 6 dimensions, and 10 policy areas.

## Overview

This repository implements an industrial-grade, event-driven choreography system for policy analysis. The system coordinates 9 specialized adapters through asynchronous events to perform comprehensive analysis of policy documents.

### Key Features

- **Event-Driven Architecture:** Decentralized coordination via immutable events
- **Distributed Validation:** Components validate inputs against QuestionContext rules
- **End-to-End Traceability:** Complete event-to-question-to-code mapping
- **Deterministic Execution:** Reproducible results with seeded randomness
- **Industrial-Grade Resilience:** Idempotent components, circuit breakers, error handling
- **100% Module Preservation:** New architecture added without modifying existing code

## Quick Start

### Prerequisites

- Python 3.11+
- PyYAML
- pytest (for testing)

### Installation

```bash
# Clone the repository
git clone https://github.com/PEROPOROBTANTE/DEREK-BEACH.git
cd DEREK-BEACH

# Install dependencies
pip install pyyaml pytest pytest-cov
```

### Validation

Validate the choreography implementation:

```bash
python3 validate_choreography.py
```

### Running Tests

Run the comprehensive test suite:

```bash
pytest tests/validation/test_interface_contracts.py -v
```

Expected output:
```
========================== 26 passed in 0.74s ==========================
```

## Architecture

### Core Components

1. **Event Schemas** (`events/`): Immutable, versioned event contracts
2. **EventBus** (`event_bus.py`): Asynchronous pub/sub infrastructure
3. **MetadataService** (`metadata_service.py`): Loads and validates metadata files
4. **QuestionContext** (`events/question_context.py`): Rich context for validation
5. **TraceabilityService** (`traceability_service.py`): Event-question-code mapping
6. **EventDrivenChoreographer** (`event_driven_choreographer.py`): Coordinates workflow

### Event Flow

```
AnalysisRequestedEvent
  ↓
[Wave 1] policy_segmenter, policy_processor
  ↓
[Wave 2] semantic_chunking_policy, embedding_policy  
  ↓
[Wave 3] analyzer_one, teoria_cambio
  ↓
[Wave 4] dereck_beach, contradiction_detection
  ↓
[Wave 5] financial_viability
  ↓
FinalReportReadyEvent
```

### Metadata Files

- **cuestionario.json**: 300 questions with validation rules
- **execution_mapping.yaml**: Execution chains and adapter dependencies
- **rubric_scoring.json**: Scoring modalities (TYPE_A through TYPE_F)

## Documentation

### Primary Documentation

- **[CHOREOGRAPHY_PROTOCOL.md](CHOREOGRAPHY_PROTOCOL.md)**: Complete protocol specification
  - Event schemas and contracts
  - Component responsibilities
  - Event flow diagrams
  - Validation protocol
  - Deployment guidelines

- **[INTERFACE_CONTRACT_AUDIT_REPORT.md](INTERFACE_CONTRACT_AUDIT_REPORT.md)**: Comprehensive audit
  - Test results (26/26 passed)
  - Module balance report (100% preservation)
  - Risk assessment
  - Maintenance guidelines

### Additional Documentation

- **[REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md)**: Previous refactoring history

## Usage Examples

### Starting an Analysis

```python
from metadata_service import MetadataService
from event_driven_choreographer import EventDrivenChoreographer, ChoreographyConfig

# Initialize services
metadata_service = MetadataService()
metadata_service.load_all()

config = ChoreographyConfig(
    enable_traceability=True,
    deterministic_seed=42,
)

choreographer = EventDrivenChoreographer(
    metadata_service=metadata_service,
    config=config,
)

# Start analysis
correlation_id = choreographer.start_analysis(
    document_reference="/path/to/plan.pdf",
    target_question_ids=["D1-Q1", "D2-Q1", "D3-Q1"],
    plan_name="Municipal Development Plan 2024",
    plan_text="<plan content>",
)

# Check status
status = choreographer.get_analysis_status(correlation_id)
print(status)
```

### Creating Custom Components

```python
from event_driven_choreographer import EventDrivenComponent
from events import ChunkingCompleteEvent, EventType

class MyAnalyzerComponent(EventDrivenComponent):
    def validate_input(self, event, question_context):
        """Validate event data"""
        errors = []
        if question_context:
            errors = question_context.validate_input({
                "chunks": getattr(event, 'chunks', []),
            })
        return errors
    
    def process(self, event, question_context):
        """Process the event"""
        # Your analysis logic here
        chunks = event.chunks
        result = analyze_chunks(chunks)
        return result
    
    def emit_events(self, original_event, result, question_context):
        """Emit result events"""
        complete_event = MyAnalysisCompleteEvent(
            correlation_id=original_event.correlation_id,
            question_id=original_event.question_id,
            analysis_result=result,
        )
        self.event_bus.publish(complete_event)
```

### Subscribing to Events

```python
from event_bus import get_event_bus
from events import EventType

bus = get_event_bus()

def handle_micro_score(event):
    print(f"Score for {event.question_id}: {event.score}")

bus.subscribe(
    subscriber_id="score_logger",
    event_types=[EventType.MICRO_SCORE_COMPLETE],
    callback=handle_micro_score,
)
```

## Testing

### Running All Tests

```bash
pytest tests/validation/test_interface_contracts.py -v
```

### Running Specific Test Categories

```bash
# Event schema tests
pytest tests/validation/test_interface_contracts.py::TestEventSchemaValidation -v

# Validation rules tests
pytest tests/validation/test_interface_contracts.py::TestValidationRules -v

# Traceability tests
pytest tests/validation/test_interface_contracts.py::TestTraceabilityService -v
```

### Coverage Report

```bash
pytest tests/validation/test_interface_contracts.py --cov=events --cov=event_bus --cov=metadata_service --cov-report=html
```

## Project Structure

```
DEREK-BEACH/
├── events/                          # Event schemas
│   ├── __init__.py
│   ├── base_events.py              # Base event classes
│   ├── question_context.py         # QuestionContext data structures
│   ├── workflow_events.py          # Workflow event schemas
│   └── error_events.py             # Error event schemas
├── tests/                          # Test suite
│   └── validation/
│       └── test_interface_contracts.py  # Contract validation tests
├── event_bus.py                    # Event bus infrastructure
├── metadata_service.py             # Metadata loading/validation
├── traceability_service.py         # Traceability tracking
├── event_driven_choreographer.py   # Event-driven coordinator
├── execution_mapping.yaml          # Execution chains configuration
├── cuestionario.json              # 300 questions
├── rubric_scoring.json            # Scoring modalities
├── validate_choreography.py        # Validation script
├── CHOREOGRAPHY_PROTOCOL.md        # Protocol documentation
├── INTERFACE_CONTRACT_AUDIT_REPORT.md  # Audit report
└── [existing modules]              # Original adapter implementations
```

## Maintenance

### Schema Evolution

When adding new event types or modifying schemas:

1. Increment schema version in event definition
2. Update CHOREOGRAPHY_PROTOCOL.md
3. Add tests for new events
4. Update consumers to handle new version

See **Maintenance Guidelines** section in INTERFACE_CONTRACT_AUDIT_REPORT.md for details.

### Monitoring

Generate traceability reports:

```python
from traceability_service import TraceabilityService

service = TraceabilityService()
# ... record events ...
print(service.generate_report())
```

Check for orphan methods:

```python
analysis = service.analyze_orphans()
print(f"Orphan methods: {len(analysis.orphan_methods)}")
print(f"Unmapped questions: {len(analysis.unmapped_questions)}")
```

## Contributing

1. All new components must extend `EventDrivenComponent`
2. All events must be immutable and inherit from `BaseEvent`
3. Add tests for new functionality
4. Update CHOREOGRAPHY_PROTOCOL.md with changes
5. Ensure 100% module preservation (no modifications to existing files)

## License

[Add license information]

## Authors

- FARFAN Integration Team
- Original implementation by JCRR

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-10-21 | Initial event-driven choreography implementation |
| 0.x | 2024-2025 | Original adapter-based implementation |