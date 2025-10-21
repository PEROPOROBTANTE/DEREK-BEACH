#!/usr/bin/env python3
"""
Validation Script for Event-Driven Choreography
================================================

Quick script to validate the choreography implementation:
- Load and validate metadata files
- Check event schemas
- Generate traceability report
- Run basic smoke tests

Usage:
    python3 validate_choreography.py

Author: FARFAN Integration Team
Version: 1.0.0
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from metadata_service import MetadataService
from event_bus import get_event_bus
from traceability_service import TraceabilityService
from event_driven_choreographer import EventDrivenChoreographer, ChoreographyConfig
from events import AnalysisRequestedEvent, EventType


def validate_metadata():
    """Validate metadata files"""
    print("=" * 80)
    print("VALIDATING METADATA FILES")
    print("=" * 80)
    
    service = MetadataService()
    result = service.load_all()
    
    print(result)
    
    if result.is_valid:
        print("\n✅ Metadata validation PASSED")
    else:
        print("\n⚠️  Metadata validation has warnings")
    
    # Show loaded data stats
    print(f"\nExecution Mapping:")
    print(f"  - Adapters: {len(service.execution_mapping.get('adapter_registry', {}))}")
    print(f"  - Execution Chains: {len(service.execution_mapping.get('execution_chains', {}))}")
    
    print(f"\nRubric Scoring:")
    print(f"  - Scoring Modalities: {len(service.rubric_scoring.get('scoring_modalities', {}))}")
    
    return service


def validate_event_bus():
    """Validate event bus functionality"""
    print("\n" + "=" * 80)
    print("VALIDATING EVENT BUS")
    print("=" * 80)
    
    bus = get_event_bus()
    
    # Test pub/sub
    received = []
    
    def callback(event):
        received.append(event)
    
    bus.subscribe(
        subscriber_id="test_validator",
        event_types=[EventType.ANALYSIS_REQUESTED],
        callback=callback,
    )
    
    # Publish test event
    test_event = AnalysisRequestedEvent(
        question_id="D1-Q1",
        document_reference="/test/doc",
        plan_name="Test Plan",
        plan_text="Test content",
    )
    
    bus.publish(test_event)
    
    # Give async time to process
    import time
    time.sleep(0.2)
    
    if len(received) > 0:
        print("✅ Event pub/sub working")
        print(f"   - Published: 1 event")
        print(f"   - Received: {len(received)} event(s)")
    else:
        print("❌ Event pub/sub NOT working")
        return False
    
    # Check stats
    stats = bus.get_stats()
    print(f"\nEvent Bus Stats:")
    print(f"  - Total Events: {stats['total_events']}")
    print(f"  - Active Subscriptions: {stats['active_subscriptions']}")
    
    return True


def validate_choreographer(metadata_service):
    """Validate choreographer"""
    print("\n" + "=" * 80)
    print("VALIDATING EVENT-DRIVEN CHOREOGRAPHER")
    print("=" * 80)
    
    config = ChoreographyConfig(
        enable_traceability=True,
        deterministic_seed=42,
    )
    
    choreographer = EventDrivenChoreographer(
        metadata_service=metadata_service,
        config=config,
    )
    
    print("✅ Choreographer initialized")
    print(f"   - Traceability: {config.enable_traceability}")
    print(f"   - Deterministic Seed: {config.deterministic_seed}")
    
    # Test starting analysis
    correlation_id = choreographer.start_analysis(
        document_reference="/test/doc",
        target_question_ids=["D1-Q1", "D2-Q1"],
        plan_name="Test Plan",
        plan_text="Test content for validation",
    )
    
    print(f"\n✅ Analysis workflow started")
    print(f"   - Correlation ID: {correlation_id[:8]}...")
    print(f"   - Questions: 2")
    
    # Give time for events to process
    import time
    time.sleep(0.2)
    
    # Check status
    status = choreographer.get_analysis_status(correlation_id)
    print(f"\nWorkflow Status:")
    for key, value in status.items():
        print(f"  - {key}: {value}")
    
    return choreographer


def generate_traceability_report(choreographer):
    """Generate traceability report"""
    print("\n" + "=" * 80)
    print("TRACEABILITY REPORT")
    print("=" * 80)
    
    if choreographer.traceability_service:
        report = choreographer.get_traceability_report()
        print(report)
    else:
        print("⚠️  Traceability not enabled")


def run_validation():
    """Run complete validation"""
    print("\n" + "=" * 80)
    print("EVENT-DRIVEN CHOREOGRAPHY VALIDATION")
    print("=" * 80)
    print()
    
    try:
        # 1. Validate metadata
        metadata_service = validate_metadata()
        
        # 2. Validate event bus
        bus_ok = validate_event_bus()
        
        if not bus_ok:
            print("\n❌ Validation FAILED - Event bus not working")
            return False
        
        # 3. Validate choreographer
        choreographer = validate_choreographer(metadata_service)
        
        # 4. Generate reports
        generate_traceability_report(choreographer)
        
        print("\n" + "=" * 80)
        print("✅ VALIDATION COMPLETE")
        print("=" * 80)
        print()
        print("Next Steps:")
        print("  1. Run automated tests: pytest tests/validation/test_interface_contracts.py")
        print("  2. Review CHOREOGRAPHY_PROTOCOL.md for detailed documentation")
        print("  3. Review INTERFACE_CONTRACT_AUDIT_REPORT.md for audit results")
        print()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Validation FAILED with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_validation()
    sys.exit(0 if success else 1)
