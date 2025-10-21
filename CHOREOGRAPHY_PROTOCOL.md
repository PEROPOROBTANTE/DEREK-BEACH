# Event-Driven Choreography Protocol

## FARFAN 3.0 Policy Analysis System

**Version:** 1.0.0  
**Date:** 2025-10-21  
**Author:** FARFAN Integration Team

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Core Principles](#core-principles)
3. [Architecture Overview](#architecture-overview)
4. [Event Schemas](#event-schemas)
5. [Component Responsibilities](#component-responsibilities)
6. [Event Flow Diagrams](#event-flow-diagrams)
7. [Validation Protocol](#validation-protocol)
8. [Error Handling](#error-handling)
9. [Traceability](#traceability)
10. [Deployment Guidelines](#deployment-guidelines)

---

## Executive Summary

This document defines the formal choreography protocol for the FARFAN 3.0 policy analysis system. The system implements a decentralized, event-driven architecture where 9 specialized components collaborate autonomously through asynchronous events to analyze policy documents across 6 dimensions and 10 policy areas.

### Key Characteristics

- **Decentralized Coordination:** No central orchestrator; components react independently to events
- **Strict Immutability:** All events are immutable with versioned schemas
- **Distributed Validation:** Each component validates its inputs against QuestionContext
- **End-to-End Traceability:** Complete event-to-question-to-code mapping
- **Deterministic Execution:** Reproducible results through deterministic seeding
- **Industrial-Grade Resilience:** Idempotent consumers, circuit breakers, dead-letter queues

---

## Core Principles

### 1. Decentralized Collaboration

Components subscribe to specific event types and process them independently. No component has knowledge of the complete workflow - each only understands its input events and output events.

```
Component A publishes Event X
  ↓
Event Bus delivers Event X to all subscribers
  ↓
Component B receives Event X → processes → publishes Event Y
Component C receives Event X → processes → publishes Event Z
```

### 2. Event-Driven Communication

All inter-component communication occurs through immutable, versioned events published to a shared event bus. Direct component-to-component calls are prohibited.

### 3. Deep Metadata Integration

Events carry `QuestionContext` objects derived from:
- `cuestionario.json`: 300 questions with validation rules
- `execution_mapping.yaml`: Execution chains and dependencies
- `rubric_scoring.json`: Scoring modalities and conversion tables

### 4. Guaranteed Determinism

- Deterministic seeding (default: 42) ensures reproducible results
- Components must be pure functions of their inputs
- Random operations use seeded generators

### 5. Strict Immutability

Events are frozen dataclasses - once created, they cannot be modified. Event schemas are versioned (currently 1.0.0) to support evolution without breaking consumers.

### 6. Distributed Validation

Validation logic resides within consuming components, not centrally. Components:
1. Receive event
2. Fetch or extract QuestionContext
3. Validate input against context.validation_rules
4. Emit ValidationFailedEvent if validation fails
5. Process only if validation succeeds

---

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                         Event Bus                           │
│  (In-memory or Kafka/RabbitMQ in production)               │
└─────────────────────────────────────────────────────────────┘
                    ↑            ↓
        ┌───────────┴────────────┴───────────┐
        ↑                                     ↓
┌───────────────┐                    ┌───────────────┐
│  Metadata     │                    │ Traceability  │
│  Service      │                    │   Service     │
│               │                    │               │
│ - cuestionario│                    │ - Event maps  │
│ - exec_mapping│                    │ - Orphan anal.│
│ - rubric_score│                    │ - Reports     │
└───────────────┘                    └───────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    9 Processing Components                   │
│                                                              │
│  Wave 1: policy_segmenter, policy_processor                 │
│  Wave 2: semantic_chunking_policy, embedding_policy         │
│  Wave 3: analyzer_one, teoria_cambio                        │
│  Wave 4: dereck_beach, contradiction_detection              │
│  Wave 5: financial_viability                                │
└─────────────────────────────────────────────────────────────┘
```

### Event Bus

The EventBus provides:
- **Publish/Subscribe:** Components subscribe to specific event types
- **Event History:** All events stored for traceability (configurable size)
- **Filtering:** By event type, question_id, correlation_id
- **Async Delivery:** Events delivered asynchronously to subscribers
- **Thread Safety:** Concurrent pub/sub operations

### Metadata Service

Responsibilities:
- Load and validate all metadata files
- Cross-reference questions, dimensions, scoring modalities
- Build enriched QuestionContext objects
- Cache contexts for performance
- Detect alignment discrepancies

### Traceability Service

Responsibilities:
- Subscribe to all events
- Build event-to-question-to-component maps
- Track method invocations
- Identify orphan methods
- Identify unmapped questions
- Generate traceability reports

---

## Event Schemas

### Base Event Schema

All events inherit from `BaseEvent`:

```python
@dataclass(frozen=True)
class BaseEvent:
    event_id: str                    # UUID
    event_type: EventType            # Enum of event types
    schema_version: str              # "1.0.0"
    correlation_id: str              # UUID linking related events
    question_id: Optional[str]       # Question being processed
    timestamp: str                   # ISO 8601 timestamp
    status: EventStatus              # created, published, processing, completed, failed
    metadata: Dict[str, Any]         # Additional metadata
```

### Workflow Events

#### AnalysisRequestedEvent

Initiates analysis workflow.

```python
@dataclass(frozen=True)
class AnalysisRequestedEvent(BaseEvent):
    event_type: EventType = EventType.ANALYSIS_REQUESTED
    document_reference: str          # Path or ID of document
    target_question_ids: List[str]   # Questions to analyze
    plan_name: str                   # Name of policy plan
    plan_text: str                   # Full document text
```

**Published by:** Client/Orchestrator  
**Subscribed by:** policy_segmenter, policy_processor

#### ChunkingCompleteEvent

Document chunking completed.

```python
@dataclass(frozen=True)
class ChunkingCompleteEvent(BaseEvent):
    event_type: EventType = EventType.CHUNKING_COMPLETE
    chunks: List[Dict[str, Any]]           # Document chunks
    chunk_count: int                       # Number of chunks
    chunk_metadata: Dict[str, Any]         # Metadata about chunking
    question_context_subset: Optional[Dict[str, Any]]  # Relevant context
```

**Published by:** semantic_chunking_policy  
**Subscribed by:** analyzer_one, teoria_cambio

#### CausalExtractionCompleteEvent

Causal link extraction completed.

```python
@dataclass(frozen=True)
class CausalExtractionCompleteEvent(BaseEvent):
    event_type: EventType = EventType.CAUSAL_EXTRACTION_COMPLETE
    causal_links: List[Dict[str, Any]]     # Extracted causal relationships
    causal_graph: Optional[Dict[str, Any]] # Graph representation
    confidence: float                       # Confidence in extraction
    bayesian_support: Optional[Dict[str, Any]]  # Bayesian scores
```

**Published by:** teoria_cambio, dereck_beach  
**Subscribed by:** dereck_beach, contradiction_detection, financial_viability

#### MicroScoreCompleteEvent

Question-level scoring completed.

```python
@dataclass(frozen=True)
class MicroScoreCompleteEvent(BaseEvent):
    event_type: EventType = EventType.MICRO_SCORE_COMPLETE
    score: float                           # Calculated score
    elements_found: int                    # Elements found
    elements_expected: int                 # Elements expected
    scoring_modality: str                  # TYPE_A, TYPE_B, etc.
    evidence: List[Dict[str, Any]]         # Supporting evidence
```

**Published by:** Scoring components (various)  
**Subscribed by:** Report aggregator

#### FinalReportReadyEvent

Complete report assembled.

```python
@dataclass(frozen=True)
class FinalReportReadyEvent(BaseEvent):
    event_type: EventType = EventType.FINAL_REPORT_READY
    report_id: str                         # Unique report ID
    micro_results: Dict[str, Any]          # Question-level results
    meso_results: Dict[str, Any]           # Dimension/area results
    macro_results: Dict[str, Any]          # Overall plan results
    report_path: str                       # Path to report
    generation_metadata: Dict[str, Any]    # Generation metadata
```

**Published by:** Report assembler  
**Subscribed by:** Client/Orchestrator

### Error Events

#### ValidationFailedEvent

Input validation failed.

```python
@dataclass(frozen=True)
class ValidationFailedEvent(BaseEvent):
    event_type: EventType = EventType.VALIDATION_FAILED
    component_name: str                    # Component that detected failure
    validation_errors: List[str]           # Error messages
    failed_rules: List[str]                # Rules that failed
    input_data_summary: Dict[str, Any]     # Summary of input
    remediation_hint: str                  # How to fix
```

**Published by:** Any component  
**Subscribed by:** Error handler, logging service

#### ProcessingFailedEvent

Processing error occurred.

```python
@dataclass(frozen=True)
class ProcessingFailedEvent(BaseEvent):
    event_type: EventType = EventType.PROCESSING_FAILED
    component_name: str                    # Component that failed
    error_type: str                        # Exception class name
    error_message: str                     # Error message
    stack_trace: Optional[str]             # Stack trace
    retry_count: int                       # Retry attempts
    can_retry: bool                        # Whether retryable
```

**Published by:** Any component  
**Subscribed by:** Error handler, retry coordinator

#### PreconditionFailedEvent

Preconditions not met.

```python
@dataclass(frozen=True)
class PreconditionFailedEvent(BaseEvent):
    event_type: EventType = EventType.PRECONDITION_FAILED
    component_name: str                    # Component checking
    unmet_preconditions: List[str]         # Unmet preconditions
    required_inputs: List[str]             # Required but missing
    available_inputs: List[str]            # Available inputs
    should_skip_downstream: bool           # Skip downstream?
```

**Published by:** Scoring components  
**Subscribed by:** Workflow coordinator

---

## Component Responsibilities

### Wave 1: Foundation (Priority 1)

#### policy_segmenter

**Subscribes to:** AnalysisRequestedEvent  
**Publishes:** SegmentationCompleteEvent

**Responsibilities:**
- Segment document by structural boundaries
- Detect sections, subsections, paragraphs
- Identify document structure (headings, lists, tables)

**Validation Rules:**
- Min document length: 100 words
- Valid encoding: UTF-8

#### policy_processor

**Subscribes to:** AnalysisRequestedEvent  
**Publishes:** PreprocessingCompleteEvent

**Responsibilities:**
- Normalize text (lowercase, remove special chars)
- Extract metadata (dates, entities, references)
- Prepare document for downstream processing

**Validation Rules:**
- Min document length: 100 words
- Required sections present

### Wave 2: Semantic Analysis (Priority 2)

#### semantic_chunking_policy

**Subscribes to:** SegmentationCompleteEvent, PreprocessingCompleteEvent  
**Publishes:** ChunkingCompleteEvent, SemanticAnalysisCompleteEvent

**Responsibilities:**
- Perform semantic chunking with structure awareness
- Detect boundaries based on semantic similarity
- Preserve important structural elements

**Validation Rules:**
- Min chunks: 3
- Max chunk size: 1000 tokens

#### embedding_policy

**Subscribes to:** PreprocessingCompleteEvent  
**Publishes:** EmbeddingCompleteEvent

**Responsibilities:**
- Generate embeddings using SentenceTransformer
- Compute similarity scores
- Cache embeddings for reuse

**Validation Rules:**
- Valid text input (not empty)
- Embedding dimension: 768

### Wave 3: Advanced Analysis (Priority 3)

#### analyzer_one

**Subscribes to:** ChunkingCompleteEvent, EmbeddingCompleteEvent  
**Publishes:** MunicipalAnalysisCompleteEvent

**Responsibilities:**
- Municipal development analysis
- Quality control checks
- Extract deliverables and impacts

**Validation Rules:**
- Semantic chunks available
- Embeddings available

#### teoria_cambio

**Subscribes to:** ChunkingCompleteEvent, EmbeddingCompleteEvent  
**Publishes:** TheoryChangeCompleteEvent, CausalExtractionCompleteEvent

**Responsibilities:**
- Build causal graph from theory of change
- Calculate Bayesian confidence
- Validate causal coherence

**Validation Rules:**
- Min causal links: 5
- Complete path required

### Wave 4: Specialized Analysis (Priority 4)

#### dereck_beach

**Subscribes to:** TheoryChangeCompleteEvent, CausalExtractionCompleteEvent  
**Publishes:** DerekBeachCompleteEvent

**Responsibilities:**
- CDAF causal analysis
- Mechanism identification
- Evidence strength assessment

**Validation Rules:**
- Causal graph available
- Min evidence strength: 0.6

#### contradiction_detection

**Subscribes to:** MunicipalAnalysisCompleteEvent, TheoryChangeCompleteEvent  
**Publishes:** ContradictionDetectionCompleteEvent

**Responsibilities:**
- Detect contradictions using transformers
- Calculate alignment scores
- Identify coherence issues

**Validation Rules:**
- Municipal analysis available
- Causal graph available

### Wave 5: Final Synthesis (Priority 5)

#### financial_viability

**Subscribes to:** All Wave 4 completion events  
**Publishes:** FinancialAuditCompleteEvent

**Responsibilities:**
- Financial viability assessment
- Resource allocation analysis
- Budget coherence evaluation

**Validation Rules:**
- All upstream analyses complete
- Min coherence score: 0.75

---

## Event Flow Diagrams

### Complete Workflow for Dimension 1 (D1)

```
Client
  │
  ├──> AnalysisRequestedEvent (question_id=D1-Q1)
  │
  ↓
policy_segmenter ────> SegmentationCompleteEvent
policy_processor ────> PreprocessingCompleteEvent
  │
  ↓
semantic_chunking_policy ──> ChunkingCompleteEvent
embedding_policy ──────────> EmbeddingCompleteEvent
  │
  ↓
analyzer_one ──────────────> MunicipalAnalysisCompleteEvent
  │
  ↓
financial_viability ────────> FinancialAuditCompleteEvent
  │                            MicroScoreCompleteEvent
  ↓
Report Aggregator ─────────> FinalReportReadyEvent
```

### Error Handling Flow

```
Component receives Event
  │
  ├──> Validate Input
  │      │
  │      ├──> Valid? ──> Process
  │      │
  │      └──> Invalid? ──> ValidationFailedEvent
  │
  └──> Process
         │
         ├──> Success? ──> Emit Result Event
         │
         └──> Error? ──> ProcessingFailedEvent
                          │
                          ├──> Retry? ──> Re-publish Input Event
                          │
                          └──> Dead Letter Queue
```

---

## Validation Protocol

### Distributed Validation Pattern

Each component follows this validation protocol:

```python
class ComponentValidator:
    def on_event(self, event: BaseEvent):
        # 1. Fetch QuestionContext
        context = metadata_service.get_question_context(event.question_id)
        
        # 2. Validate against rules
        errors = context.validate_input({
            "field1": extract_from_event(event),
            "field2": compute_field(event),
        })
        
        # 3. Emit failure if validation fails
        if errors:
            self.emit_validation_failed(event, errors)
            return
        
        # 4. Process only if valid
        result = self.process(event, context)
        self.emit_success(event, result)
```

### Validation Rule Types

#### Numeric Rules

```yaml
min_words:
  type: numeric
  operator: ">="
  value: 100
  error_message: "Document does not meet minimum word count"
```

#### List Rules

```yaml
required_sections:
  type: list
  operator: "contains_all"
  value: ["diagnostico", "linea_base"]
  error_message: "Document missing required sections"
```

#### Boolean Rules

```yaml
requires_complete_path:
  type: boolean
  value: true
  error_message: "Causal path is incomplete"
```

### Precondition Checking

Before scoring, components check preconditions:

```python
# Check all required inputs are available
unmet = context.check_preconditions({
    "causal_graph": has_causal_graph,
    "embeddings": has_embeddings,
    "municipal_analysis": has_municipal_analysis,
})

if unmet:
    # Emit PreconditionFailedEvent
    emit_precondition_failed(unmet)
    return
```

---

## Error Handling

### Error Strategies

Defined in `execution_mapping.yaml`:

```yaml
error_strategies:
  validation_failure:
    action: emit_validation_failed_event
    include_context: true
    dead_letter: false
    
  processing_failure:
    action: emit_processing_failed_event
    retry_count: 3
    retry_delay: 5
    dead_letter: true
    
  precondition_failure:
    action: emit_precondition_failed_event
    skip_downstream: true
    dead_letter: false
```

### Circuit Breaker Integration

Components integrate with circuit breaker:

```python
if circuit_breaker.is_open(component_name):
    # Circuit open - degrade gracefully
    emit_degraded_mode_event()
    return

try:
    result = component.process(event)
    circuit_breaker.record_success(component_name)
except Exception as e:
    circuit_breaker.record_failure(component_name)
    emit_processing_failed(e)
```

### Dead Letter Queue

Failed events after max retries go to dead letter queue:

```python
if retry_count >= max_retry_count:
    dead_letter_queue.enqueue(event, error)
    emit_dead_letter_event()
```

---

## Traceability

### Correlation IDs

Every workflow has a unique correlation ID that links all events:

```python
correlation_id = str(uuid.uuid4())

# All events in workflow carry same correlation_id
event1 = AnalysisRequestedEvent(correlation_id=correlation_id, ...)
event2 = ChunkingCompleteEvent(correlation_id=correlation_id, ...)
event3 = MicroScoreCompleteEvent(correlation_id=correlation_id, ...)
```

### Question-to-Event Mapping

TraceabilityService builds map:

```
Question D1-Q1:
  ├─ Event 1: AnalysisRequestedEvent (t=0ms)
  ├─ Event 2: SegmentationCompleteEvent (t=50ms)
  ├─ Event 3: ChunkingCompleteEvent (t=120ms)
  ├─ Event 4: MunicipalAnalysisCompleteEvent (t=450ms)
  └─ Event 5: MicroScoreCompleteEvent (t=600ms)
```

### Component-to-Code Mapping

TraceabilityService maps components to source:

```
Component: analyzer_one
  ├─ Module: modules_adapters.py
  ├─ Class: AnalyzerOneAdapter
  ├─ Methods: [analyze_diagnostic_quality, extract_deliverables, ...]
  ├─ Subscribed Events: [ChunkingCompleteEvent, EmbeddingCompleteEvent]
  └─ Published Events: [MunicipalAnalysisCompleteEvent]
```

### Orphan Detection

TraceabilityService identifies:
- **Orphan Methods:** Methods in code never invoked by any event flow
- **Unmapped Questions:** Questions without execution traces
- **Underutilized Components:** Components with low event traffic

---

## Deployment Guidelines

### Production Event Bus

Replace in-memory EventBus with production-grade message broker:

#### Kafka Configuration

```python
from kafka import KafkaProducer, KafkaConsumer

producer = KafkaProducer(
    bootstrap_servers=['kafka:9092'],
    value_serializer=lambda v: json.dumps(v.to_dict()).encode('utf-8')
)

consumer = KafkaConsumer(
    'analysis-events',
    bootstrap_servers=['kafka:9092'],
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)
```

#### RabbitMQ Configuration

```python
import pika

connection = pika.BlockingConnection(
    pika.ConnectionParameters('rabbitmq')
)
channel = connection.channel()
channel.exchange_declare(exchange='events', exchange_type='topic')
```

### Monitoring and Observability

#### Distributed Tracing

Integrate with OpenTelemetry:

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("process_event") as span:
    span.set_attribute("event_type", event.event_type.value)
    span.set_attribute("question_id", event.question_id)
    span.set_attribute("correlation_id", event.correlation_id)
    
    result = component.process(event)
```

#### Metrics

Track key metrics:

```python
from prometheus_client import Counter, Histogram

events_published = Counter('events_published_total', 'Total events published', ['event_type'])
processing_time = Histogram('event_processing_seconds', 'Event processing time', ['component'])
validation_failures = Counter('validation_failures_total', 'Validation failures', ['component'])
```

### Scaling Considerations

- **Horizontal Scaling:** Run multiple instances of each component
- **Event Partitioning:** Partition events by question_id for parallel processing
- **State Management:** Use external state store (Redis, PostgreSQL) for stateful components
- **Idempotency:** Ensure all components are idempotent (same input → same output)

---

## Appendix

### Event Type Reference

| Event Type | Schema Version | Published By | Subscribed By |
|-----------|----------------|--------------|---------------|
| AnalysisRequestedEvent | 1.0.0 | Client | policy_segmenter, policy_processor |
| SegmentationCompleteEvent | 1.0.0 | policy_segmenter | semantic_chunking_policy |
| PreprocessingCompleteEvent | 1.0.0 | policy_processor | semantic_chunking_policy, embedding_policy |
| ChunkingCompleteEvent | 1.0.0 | semantic_chunking_policy | analyzer_one, teoria_cambio |
| EmbeddingCompleteEvent | 1.0.0 | embedding_policy | analyzer_one, teoria_cambio |
| MunicipalAnalysisCompleteEvent | 1.0.0 | analyzer_one | contradiction_detection, financial_viability |
| TheoryChangeCompleteEvent | 1.0.0 | teoria_cambio | dereck_beach, contradiction_detection |
| DerekBeachCompleteEvent | 1.0.0 | dereck_beach | financial_viability |
| ContradictionDetectionCompleteEvent | 1.0.0 | contradiction_detection | financial_viability |
| FinancialAuditCompleteEvent | 1.0.0 | financial_viability | Report Aggregator |
| MicroScoreCompleteEvent | 1.0.0 | Various | Report Aggregator |
| FinalReportReadyEvent | 1.0.0 | Report Aggregator | Client |
| ValidationFailedEvent | 1.0.0 | Any | Error Handler |
| ProcessingFailedEvent | 1.0.0 | Any | Error Handler, Retry Coordinator |
| PreconditionFailedEvent | 1.0.0 | Any | Workflow Coordinator |

### Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-10-21 | Initial protocol definition |

---

**End of Choreography Protocol Document**
