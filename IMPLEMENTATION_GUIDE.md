# Implementation Guide: Module Adapter Completion

## Quick Start

This guide provides step-by-step instructions to achieve 100% adapter coverage for all three audited modules.

---

## Current Status

| Module | Coverage | Missing Items | Priority |
|--------|----------|---------------|----------|
| causal_proccesor.py | 100% | 0 | ✅ Complete |
| Analyzer_one.py | 33.3% | 26 | 🔴 Critical |
| contradiction_deteccion.py | 53.2% | 22 | 🟡 High |

---

## Implementation Steps

### Step 1: Backup Current Code

```bash
cd /home/runner/work/DEREK-BEACH/DEREK-BEACH
cp modules_adapters.py modules_adapters.py.backup
```

### Step 2: Review Generated Analyzer Adapter

The corrected AnalyzerOneAdapter has been auto-generated:

```bash
# Review the generated code
cat analyzer_one_adapter_generated.py

# Key sections to verify:
# 1. Import statements (lines 84-97)
# 2. Method dispatch (execute method)
# 3. Implementation stubs for each method
```

### Step 3: Integration Options

#### Option A: Direct Replacement (Recommended for Analyzer_one.py)

```python
# In modules_adapters.py, find AnalyzerOneAdapter class (around line 1905)
# Replace entire class with content from analyzer_one_adapter_generated.py
# Ensure proper indentation and imports
```

#### Option B: Incremental Addition (Recommended for contradiction_deteccion.py)

Add missing methods one section at a time:

1. **Phase 1: High Priority (Core Methods)**
   - Analyzer_one.py: analyze_document, extract_semantic_cube, analyze_performance
   - contradiction_deteccion.py: _initialize_pdm_patterns, helper methods

2. **Phase 2: Medium Priority (Utilities)**
   - Analyzer_one.py: load_pdf, load_docx, export methods
   - contradiction_deteccion.py: calculation methods

3. **Phase 3: Low Priority (Internal Helpers)**
   - All remaining internal methods

### Step 4: Verification

After each change, run verification:

```bash
python verify_modules_inventory_complete.py
```

Expected output after completion:
```
Summary:
  ✓ causal_proccesor.py: 100.0% coverage
  ✓ Analyzer_one.py: 100.0% coverage
  ✓ contradiction_deteccion.py: 100.0% coverage
```

---

## Detailed Implementation: Analyzer_one.py

### Missing Items Checklist

#### 1. Add Missing DataClass (1 item)

```python
# In modules_adapters.py imports section
from Analyzer_one import (
    ValueChainLink,  # ADD THIS LINE
    MunicipalOntology,
    # ... rest of imports
)

# In _load_module method
self.ValueChainLink = ValueChainLink  # ADD THIS LINE
```

#### 2. Add Missing Methods (26 items)

For each class, add method dispatch and implementation. Example:

```python
# In execute() method, add dispatch:
elif method_name == "extract_semantic_cube":
    result = self._execute_semanticanalyzer_extract_semantic_cube(*args, **kwargs)

# Add implementation:
def _execute_semanticanalyzer_extract_semantic_cube(
    self, analyzer=None, document_segments=None, **kwargs
) -> ModuleResult:
    """Execute SemanticAnalyzer.extract_semantic_cube()"""
    if analyzer is None:
        analyzer = self.SemanticAnalyzer(self.MunicipalOntology())
    if document_segments is None:
        document_segments = []
    
    result = analyzer.extract_semantic_cube(document_segments)
    
    return ModuleResult(
        module_name=self.module_name,
        class_name="SemanticAnalyzer",
        method_name="extract_semantic_cube",
        status="success",
        data=result,
        evidence=[{"type": "semantic_cube_extraction"}],
        confidence=result.get("measures", {}).get("overall_coherence", 0.7),
        execution_time=0.0,
    )
```

#### 3. Add Top-Level Functions (2 items)

```python
# In execute() method:
elif method_name == "example_usage":
    result = self._execute_example_usage(*args, **kwargs)
elif method_name == "main":
    result = self._execute_main(*args, **kwargs)

# Implementations:
def _execute_example_usage(self, **kwargs) -> ModuleResult:
    """Execute example_usage()"""
    result = self.example_usage()
    return ModuleResult(
        module_name=self.module_name,
        class_name="Global",
        method_name="example_usage",
        status="success",
        data={"result": result},
        evidence=[{"type": "example_execution"}],
        confidence=0.9,
        execution_time=0.0,
    )

def _execute_main(self, **kwargs) -> ModuleResult:
    """Execute main()"""
    # Note: main() runs interactive CLI, may not be suitable for adapter
    return ModuleResult(
        module_name=self.module_name,
        class_name="Global",
        method_name="main",
        status="success",
        data={"message": "main() execution deferred (interactive)"},
        evidence=[{"type": "main_function"}],
        confidence=1.0,
        execution_time=0.0,
    )
```

---

## Detailed Implementation: contradiction_deteccion.py

### Missing Items Checklist (22 methods)

#### 1. TemporalLogicVerifier (1 method)

```python
# Add dispatch for _are_mutually_exclusive
elif method_name == "temporallogicverifier_are_mutually_exclusive":
    result = self._execute_temporallogicverifier_are_mutually_exclusive(*args, **kwargs)

# Implementation
def _execute_temporallogicverifier_are_mutually_exclusive(
    self, verifier=None, stmt_a=None, stmt_b=None, **kwargs
) -> ModuleResult:
    """Execute TemporalLogicVerifier._are_mutually_exclusive()"""
    if verifier is None:
        verifier = self.TemporalLogicVerifier()
    
    result = verifier._are_mutually_exclusive(stmt_a, stmt_b)
    
    return ModuleResult(
        module_name=self.module_name,
        class_name="TemporalLogicVerifier",
        method_name="_are_mutually_exclusive",
        status="success",
        data={"are_mutually_exclusive": result},
        evidence=[{"type": "mutual_exclusivity_check"}],
        confidence=0.9,
        execution_time=0.0,
    )
```

#### 2. PolicyContradictionDetector (21 methods)

Group by functional area:

**Extraction Methods (4):**
- _extract_temporal_markers
- _extract_quantitative_claims
- _parse_number
- _extract_resource_mentions

**Calculation Methods (6):**
- _calculate_global_semantic_coherence
- _calculate_objective_alignment
- _calculate_graph_fragmentation
- _calculate_contradiction_entropy
- _calculate_syntactic_complexity
- _get_dependency_depth

**Classification/Utility Methods (11):**
- _initialize_pdm_patterns
- _identify_affected_sections
- _determine_semantic_role
- _identify_dependencies
- _get_context_window
- _calculate_similarity
- _classify_contradiction
- _get_domain_weight
- _suggest_resolutions
- _are_comparable_claims
- _text_similarity
- _calculate_numerical_divergence
- _statistical_significance_test
- _has_logical_conflict
- _are_conflicting_allocations

---

## Testing Strategy

### 1. Unit Tests

Create test file `tests/test_adapter_coverage.py`:

```python
import pytest
from modules_adapters import ModuleAdapterRegistry

def test_analyzer_one_coverage():
    """Test all Analyzer_one methods are accessible"""
    registry = ModuleAdapterRegistry()
    adapter = registry.adapters["analyzer_one"]
    
    assert adapter.available, "Analyzer_one should be available"
    
    # Test critical methods
    result = adapter.execute("extract_semantic_cube", 
                            args=[],
                            kwargs={"document_segments": ["test"]})
    assert result.status == "success"

def test_contradiction_detection_coverage():
    """Test all contradiction detection methods are accessible"""
    registry = ModuleAdapterRegistry()
    adapter = registry.adapters["contradiction_detection"]
    
    assert adapter.available, "Contradiction detection should be available"
    
    # Test new methods
    result = adapter.execute("_extract_temporal_markers",
                            args=[],
                            kwargs={"text": "test"})
    assert result.status == "success"
```

### 2. Integration Tests

```python
def test_end_to_end_analyzer():
    """Test complete analysis workflow"""
    registry = ModuleAdapterRegistry()
    
    # Load document
    result = registry.execute_module_method(
        "analyzer_one",
        "load_document",
        args=["test_doc.txt"],
        kwargs={}
    )
    
    # Analyze
    result = registry.execute_module_method(
        "analyzer_one",
        "analyze_document",
        args=["test_doc.txt"],
        kwargs={}
    )
    
    assert result.status == "success"
    assert "semantic_cube" in result.data
```

### 3. Verification Tests

```bash
# Run after each phase
python verify_modules_inventory_complete.py

# Should show increasing coverage:
# Phase 1 completion: 60% coverage
# Phase 2 completion: 80% coverage
# Phase 3 completion: 100% coverage
```

---

## Rollback Plan

If issues arise:

```bash
# Restore backup
cp modules_adapters.py.backup modules_adapters.py

# Verify restoration
python verify_modules_inventory_complete.py
```

---

## Success Criteria

✅ **Phase 1 Complete:**
- Analyzer_one.py: 60%+ coverage
- contradiction_deteccion.py: 70%+ coverage
- All critical methods working

✅ **Phase 2 Complete:**
- Analyzer_one.py: 80%+ coverage
- contradiction_deteccion.py: 90%+ coverage
- All utility methods working

✅ **Phase 3 Complete:**
- All modules: 100% coverage
- All tests passing
- Documentation updated

---

## Timeline Estimate

| Phase | Duration | Effort |
|-------|----------|--------|
| Phase 1 (Critical) | 2-3 hours | High |
| Phase 2 (Utilities) | 2-3 hours | Medium |
| Phase 3 (Helpers) | 1-2 hours | Low |
| Testing | 1-2 hours | Medium |
| **Total** | **6-10 hours** | **Moderate** |

---

## Support Resources

### Documentation
- `ADAPTER_INCLUSION_AUDIT_REPORT.md` - Detailed findings
- `VERIFICATION_REPORT_COMPLETE.md` - Technical verification results
- `verification_results.json` - Machine-readable data

### Tools
- `verify_modules_inventory_complete.py` - Verification script
- `generate_analyzer_adapter.py` - Code generator
- `analyzer_one_adapter_generated.py` - Reference implementation

### Contact
For questions or issues during implementation:
1. Review audit report for specific item details
2. Check verification results JSON for exact coverage
3. Reference generated adapter code for examples

---

## Post-Implementation

After achieving 100% coverage:

1. **Add to CI/CD:**
   ```yaml
   # In .github/workflows/test.yml
   - name: Verify Adapter Coverage
     run: python verify_modules_inventory_complete.py
   ```

2. **Update Documentation:**
   - Add adapter architecture diagram
   - Document method naming conventions
   - Create adapter development guide

3. **Continuous Monitoring:**
   - Run verification on every PR
   - Track coverage metrics
   - Alert on regressions

---

**Implementation Status:** 📋 **READY TO BEGIN**  
**Next Action:** Review generated code and begin Phase 1 integration
