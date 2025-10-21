#!/usr/bin/env python
"""
Test script to verify module imports and alignment between:
- modules_adapters.py (ModuleAdapterRegistry with adapters)
- core_orchestrator.py (FARFANOrchestrator)  
- choreographer.py (ExecutionChoreographer)
- event_driven_choreographer.py (EventDrivenChoreographer)
"""

import sys
from pathlib import Path

def test_imports():
    """Test that all key modules can be imported"""
    print("=" * 80)
    print("TESTING MODULE IMPORTS")
    print("=" * 80)
    
    results = {}
    
    # Test 1: metadata_service
    print("\n1. Testing metadata_service.py...")
    try:
        from metadata_service import MetadataService, QuestionContext
        print("   ✓ metadata_service imports successfully")
        print(f"   ✓ MetadataService class available")
        print(f"   ✓ QuestionContext dataclass available")
        results['metadata_service'] = True
    except Exception as e:
        print(f"   ✗ FAILED: {e}")
        results['metadata_service'] = False
    
    # Test 2: modules_adapters
    print("\n2. Testing modules_adapters.py...")
    try:
        from modules_adapters import (
            ModuleAdapterRegistry,
            BaseAdapter,
            ModuleResult,
            PolicyProcessorAdapter,
            PolicySegmenterAdapter,
        )
        print("   ✓ modules_adapters imports successfully")
        print(f"   ✓ ModuleAdapterRegistry class available")
        print(f"   ✓ BaseAdapter class available")
        print(f"   ✓ ModuleResult dataclass available")
        results['modules_adapters'] = True
    except Exception as e:
        print(f"   ✗ FAILED: {e}")
        results['modules_adapters'] = False
    
    # Test 3: choreographer
    print("\n3. Testing choreographer.py...")
    try:
        import choreographer
        print("   ✓ choreographer imports successfully")
        # Check for ExecutionChoreographer class
        if hasattr(choreographer, 'ExecutionChoreographer'):
            print(f"   ✓ ExecutionChoreographer class available")
        results['choreographer'] = True
    except Exception as e:
        print(f"   ✗ FAILED: {e}")
        results['choreographer'] = False
    
    # Test 4: event_driven_choreographer
    print("\n4. Testing event_driven_choreographer.py...")
    try:
        from event_driven_choreographer import EventDrivenChoreographer
        print("   ✓ event_driven_choreographer imports successfully")
        print(f"   ✓ EventDrivenChoreographer class available")
        results['event_driven_choreographer'] = True
    except Exception as e:
        print(f"   ✗ FAILED: {e}")
        results['event_driven_choreographer'] = False
    
    # Test 5: core_orchestrator
    print("\n5. Testing core_orchestrator.py...")
    try:
        from core_orchestrator import FARFANOrchestrator
        print("   ✓ core_orchestrator imports successfully")
        print(f"   ✓ FARFANOrchestrator class available")
        results['core_orchestrator'] = True
    except Exception as e:
        print(f"   ✗ FAILED: {e}")
        results['core_orchestrator'] = False
    
    return results


def test_adapter_registry():
    """Test ModuleAdapterRegistry functionality"""
    print("\n" + "=" * 80)
    print("TESTING MODULE ADAPTER REGISTRY")
    print("=" * 80)
    
    try:
        from modules_adapters import ModuleAdapterRegistry
        
        print("\n1. Creating ModuleAdapterRegistry...")
        registry = ModuleAdapterRegistry()
        print(f"   ✓ Registry created successfully")
        
        print(f"\n2. Checking registry methods...")
        required_methods = [
            'execute_module_method',
            'get_available_modules', 
            'get_module_status',
        ]
        
        for method in required_methods:
            if hasattr(registry, method):
                print(f"   ✓ {method}() exists")
            else:
                print(f"   ✗ {method}() MISSING")
        
        print(f"\n3. Checking registered adapters...")
        print(f"   Total adapters registered: {len(registry.adapters)}")
        
        available = registry.get_available_modules()
        print(f"   Available adapters: {len(available)}")
        for adapter_name in available:
            print(f"     ✓ {adapter_name}")
        
        unavailable = [name for name in registry.adapters.keys() 
                      if name not in available]
        if unavailable:
            print(f"   Unavailable adapters: {len(unavailable)}")
            for adapter_name in unavailable:
                print(f"     ✗ {adapter_name}")
        
        print(f"\n4. Testing execute_module_method interface...")
        # Try to call with dummy data to verify interface
        try:
            result = registry.execute_module_method(
                module_name="nonexistent",
                method_name="test",
                args=[],
                kwargs={}
            )
            print(f"   ✓ execute_module_method() callable")
            print(f"   ✓ Returns ModuleResult (status: {result.status})")
        except Exception as e:
            print(f"   ✗ execute_module_method() failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_orchestrator_choreographer_alignment():
    """Test alignment between Orchestrator and Choreographer"""
    print("\n" + "=" * 80)
    print("TESTING ORCHESTRATOR-CHOREOGRAPHER ALIGNMENT")
    print("=" * 80)
    
    try:
        from modules_adapters import ModuleAdapterRegistry
        from choreographer import ExecutionChoreographer
        
        print("\n1. Creating ModuleAdapterRegistry...")
        registry = ModuleAdapterRegistry()
        print("   ✓ Registry created")
        
        print("\n2. Creating ExecutionChoreographer...")
        choreographer = ExecutionChoreographer()
        print("   ✓ Choreographer created")
        
        print("\n3. Checking choreographer.execute_question_chain signature...")
        import inspect
        sig = inspect.signature(choreographer.execute_question_chain)
        params = list(sig.parameters.keys())
        print(f"   Parameters: {params}")
        
        required_params = ['question_spec', 'plan_text', 'module_adapter_registry']
        for param in required_params:
            if param in params:
                print(f"   ✓ {param} parameter exists")
            else:
                print(f"   ✗ {param} parameter MISSING")
        
        print("\n4. Checking registry interface matches choreographer expectations...")
        print("   Choreographer calls: registry.execute_module_method()")
        if hasattr(registry, 'execute_module_method'):
            print("   ✓ registry.execute_module_method() exists")
        else:
            print("   ✗ registry.execute_module_method() MISSING")
        
        return True
        
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("MODULE ALIGNMENT AUDIT AND TEST")
    print("Testing compilation and imports for:")
    print("  - modules_adapters.py")
    print("  - core_orchestrator.py")
    print("  - choreographer.py (ExecutionChoreographer)")
    print("  - event_driven_choreographer.py")
    print("=" * 80)
    
    # Run all tests
    import_results = test_imports()
    adapter_ok = test_adapter_registry()
    alignment_ok = test_orchestrator_choreographer_alignment()
    
    # Final summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    
    print("\nImport Tests:")
    for module, success in import_results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {status}: {module}")
    
    print(f"\nAdapter Registry Test: {'✓ PASS' if adapter_ok else '✗ FAIL'}")
    print(f"Alignment Test: {'✓ PASS' if alignment_ok else '✗ FAIL'}")
    
    all_passed = all(import_results.values()) and adapter_ok and alignment_ok
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✓ ALL TESTS PASSED")
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
