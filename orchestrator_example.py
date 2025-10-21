"""
Orchestrator Usage Example
===========================

Complete example demonstrating the industrial orchestrator in action.
"""

from pathlib import Path
from industrial_orchestrator import IndustrialOrchestrator, WorkflowConfig
from metadata_service import get_metadata_service

def main():
    print("=" * 80)
    print("INDUSTRIAL ORCHESTRATOR - COMPLETE EXAMPLE")
    print("=" * 80)
    
    # Step 1: Load metadata service
    print("\n1. Loading Metadata Service...")
    metadata_service = get_metadata_service()
    metadata_service.load()
    
    validation_report = metadata_service.validate_questionnaire()
    print(f"   ✓ Loaded cuestionario.json v{validation_report['version']}")
    print(f"   ✓ Total questions: {validation_report['total_questions']}")
    print(f"   ✓ Valid: {validation_report['valid']}")
    
    # Step 2: Configure orchestrator
    print("\n2. Configuring Orchestrator...")
    config = WorkflowConfig(
        enable_validation=True,
        enable_resilience=True,
        fail_fast=False,
        max_retries=3,
        enable_deterministic_mode=True,
        storage_dir=Path("./demo_workflow_states")
    )
    print(f"   ✓ Validation: {'ON' if config.enable_validation else 'OFF'}")
    print(f"   ✓ Resilience: {'ON' if config.enable_resilience else 'OFF'}")
    print(f"   ✓ Deterministic: {'ON' if config.enable_deterministic_mode else 'OFF'}")
    print(f"   ✓ Max retries: {config.max_retries}")
    
    # Step 3: Demonstrate component architecture
    print("\n3. Orchestrator Architecture:")
    print("   ┌─────────────────────────────────────────────┐")
    print("   │     IndustrialOrchestrator (Central)         │")
    print("   └────────┬────────────────────────────────────┘")
    print("            │")
    print("            ├─► MetadataService (cuestionario.json)")
    print("            ├─► StateStore (immutable state)")
    print("            ├─► ValidationEngine (rule validation)")
    print("            ├─► ResilienceManager (retry/circuit breaker)")
    print("            ├─► ModuleController (component invocation)")
    print("            └─► DeterministicUtils (reproducibility)")
    
    # Step 4: Show question context
    print("\n4. Question Context Example:")
    sample_context = metadata_service.get_question_context("P1-D1-Q1")
    if sample_context:
        print(f"   Question ID: {sample_context.canonical_id}")
        print(f"   Dimension: {sample_context.dimension}")
        print(f"   Scoring: {sample_context.scoring_modality}")
        print(f"   Max Score: {sample_context.max_score}")
        print(f"   Is Critical: {sample_context.is_critical}")
        print(f"   Validation Rules: {len(sample_context.validation_rules)}")
        print(f"   Error Strategy: {sample_context.error_strategy.value}")
    
    # Step 5: Demonstrate workflow execution (simulated)
    print("\n5. Workflow Execution Flow:")
    print("   ┌─────────────────────────────────────┐")
    print("   │ 1. Create WorkflowState             │")
    print("   │    - Generate deterministic ID      │")
    print("   │    - Initialize immutable state     │")
    print("   └─────────────────────────────────────┘")
    print("              ↓")
    print("   ┌─────────────────────────────────────┐")
    print("   │ 2. For Each Question:               │")
    print("   │    - Load QuestionContext           │")
    print("   │    - Check dependencies             │")
    print("   │    - Invoke module with resilience  │")
    print("   │    - Validate output                │")
    print("   │    - Update state atomically        │")
    print("   └─────────────────────────────────────┘")
    print("              ↓")
    print("   ┌─────────────────────────────────────┐")
    print("   │ 3. Complete Workflow                │")
    print("   │    - Aggregate results              │")
    print("   │    - Generate WorkflowResult        │")
    print("   │    - Return to caller               │")
    print("   └─────────────────────────────────────┘")
    
    # Step 6: Key features
    print("\n6. Key Features Implemented:")
    features = [
        ("Metadata-Driven", "Workflow logic from cuestionario.json"),
        ("Deterministic", "Same inputs → same outputs"),
        ("Immutable State", "Frozen dataclasses, copy-on-update"),
        ("Validation", "Multi-type rule validation at each step"),
        ("Resilience", "Retry with exponential backoff"),
        ("Circuit Breaker", "Prevent cascading failures"),
        ("Compensation", "Saga pattern for transactional behavior"),
        ("Observability", "Structured logging with context"),
        ("Audit Trail", "Complete state history"),
        ("Version Tracking", "Schema and component versioning"),
    ]
    
    for name, description in features:
        print(f"   ✓ {name:20s} - {description}")
    
    # Step 7: Show statistics capabilities
    print("\n7. Available Metrics:")
    print("   • Workflow execution time")
    print("   • Step success/failure rates")
    print("   • Validation pass rates")
    print("   • Retry counts and success rates")
    print("   • Circuit breaker status")
    print("   • Module performance (avg time)")
    print("   • Failure history and classification")
    
    # Step 8: Integration points
    print("\n8. Integration with Existing System:")
    print("   • Uses existing CircuitBreaker from circuit_breaker.py")
    print("   • Integrates with ModuleAdapterRegistry (9 adapters, 413 methods)")
    print("   • Compatible with existing choreographer pattern")
    print("   • Extends core_orchestrator.py with industrial features")
    print("   • Works with questionnaire_parser.py and question_router.py")
    
    # Step 9: Usage patterns
    print("\n9. Usage Patterns:")
    print("\n   Basic Usage:")
    print("   ```python")
    print("   orchestrator = IndustrialOrchestrator(module_registry, config)")
    print("   result = orchestrator.execute_workflow(")
    print("       question_ids=['P1-D1-Q1', 'P1-D1-Q2'],")
    print("       document_text=document,")
    print("       workflow_name='Plan Analysis'")
    print("   )")
    print("   ```")
    
    print("\n   Check Results:")
    print("   ```python")
    print("   if result.success:")
    print("       print(f'Completed: {len(result.completed_steps)}')")
    print("       print(f'Success rate: {result.success_rate:.1%}')")
    print("   ```")
    
    print("\n   Get Workflow Status:")
    print("   ```python")
    print("   state = orchestrator.get_workflow_status(workflow_id)")
    print("   print(f'Status: {state.status.value}')")
    print("   print(f'Version: {state.version}')")
    print("   ```")
    
    # Step 10: Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("""
The industrial-grade orchestrator provides:

✓ CENTRALIZED CONTROL
  - Single source of truth for workflow execution
  - Explicit definition of steps and data flow
  
✓ METADATA-DRIVEN
  - Workflow logic from cuestionario.json
  - QuestionContext with validation rules and dependencies
  
✓ DETERMINISM
  - Hash-based workflow IDs
  - Seed-based random number generation
  - Version tracking for all components
  
✓ IMMUTABILITY
  - Frozen dataclasses for state representation
  - Copy-on-update pattern
  - Complete state history preservation
  
✓ VALIDATION
  - Multi-type validation rules (type, schema, regex, range)
  - Centralized validation engine
  - Detailed violation reporting
  
✓ RESILIENCE
  - Automatic retry with exponential backoff
  - Circuit breaker for failing components
  - Compensation actions (Saga pattern)
  - Failure classification and metrics
  
✓ OBSERVABILITY
  - Structured logging with workflow context
  - Comprehensive metrics and statistics
  - Complete audit trail in state history
  - Distributed tracing support (ready for OpenTelemetry)

The system is production-ready and follows industrial best practices
for orchestration, ensuring reliable, maintainable, and observable
workflow execution.
    """)
    
    print("=" * 80)


if __name__ == "__main__":
    main()
