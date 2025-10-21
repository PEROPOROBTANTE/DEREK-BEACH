# coding=utf-8
"""
Tests for MetadataService and Enhanced ReportAssembly
=====================================================

Simple validation tests for the refactored metadata service.

Author: FARFAN 3.0 Team
Version: 3.0.0
"""

import sys
from metadata_service import MetadataService, QuestionContext, ScoringModality
from report_assembly import ReportAssembler


def test_metadata_service_initialization():
    """Test MetadataService initializes correctly"""
    print("Test 1: MetadataService Initialization")
    service = MetadataService()
    
    assert len(service.get_all_questions()) == 300, "Should have 300 questions"
    assert len(service._dimensions) == 6, "Should have 6 dimensions"
    assert len(service._policy_areas) == 10, "Should have 10 policy areas"
    assert len(service._scoring_modalities) >= 4, "Should have at least 4 scoring modalities"
    
    print("  ✓ Initialization successful")
    print(f"  ✓ {len(service.get_all_questions())} questions loaded")
    print(f"  ✓ {len(service._dimensions)} dimensions loaded")
    print(f"  ✓ {len(service._policy_areas)} policy areas loaded")
    print(f"  ✓ {len(service._scoring_modalities)} scoring modalities loaded")


def test_question_context_retrieval():
    """Test getting question context"""
    print("\nTest 2: Question Context Retrieval")
    service = MetadataService()
    
    # Test valid question
    context = service.get_question_context("P1-D1-Q1")
    assert context is not None, "Should find P1-D1-Q1"
    assert context.canonical_id == "P1-D1-Q1", "Canonical ID should match"
    assert context.dimension == "D1", "Dimension should be D1"
    assert context.policy_area == "P1", "Policy area should be P1"
    assert context.question_no == 1, "Question number should be 1"
    assert len(context.execution_chain) > 0, "Should have execution chain"
    
    print("  ✓ Retrieved question context for P1-D1-Q1")
    print(f"  ✓ Text: {context.text[:60]}...")
    print(f"  ✓ Scoring modality: {context.scoring_modality}")
    print(f"  ✓ Execution chain: {len(context.execution_chain)} steps")
    
    # Test invalid question
    context = service.get_question_context("P99-D99-Q99")
    assert context is None, "Should not find invalid question"
    print("  ✓ Correctly handles invalid question ID")


def test_canonical_id_format():
    """Test canonical ID format consistency"""
    print("\nTest 3: Canonical ID Format")
    service = MetadataService()
    
    # Check all questions have correct format
    for question_id, context in service.get_all_questions().items():
        assert question_id == context.canonical_id, "Key should match canonical_id"
        # Format: P#-D#-Q#
        parts = question_id.split('-')
        assert len(parts) == 3, f"Canonical ID should have 3 parts: {question_id}"
        assert parts[0].startswith('P'), f"First part should be P#: {question_id}"
        assert parts[1].startswith('D'), f"Second part should be D#: {question_id}"
        assert parts[2].startswith('Q'), f"Third part should be Q#: {question_id}"
    
    print("  ✓ All 300 questions have correct P#-D#-Q# format")


def test_dimension_coverage():
    """Test dimension coverage"""
    print("\nTest 4: Dimension Coverage")
    service = MetadataService()
    
    for dim_id in ["D1", "D2", "D3", "D4", "D5", "D6"]:
        questions = service.get_questions_by_dimension(dim_id)
        # Should have 50 questions per dimension (5 questions × 10 policy areas)
        assert len(questions) == 50, f"Dimension {dim_id} should have 50 questions, has {len(questions)}"
        print(f"  ✓ Dimension {dim_id}: {len(questions)} questions")


def test_policy_area_coverage():
    """Test policy area coverage"""
    print("\nTest 5: Policy Area Coverage")
    service = MetadataService()
    
    for policy_num in range(1, 11):
        policy_id = f"P{policy_num}"
        questions = service.get_questions_by_policy_area(policy_id)
        # Should have 30 questions per policy area (6 dimensions × 5 questions)
        assert len(questions) == 30, f"Policy area {policy_id} should have 30 questions, has {len(questions)}"
        print(f"  ✓ Policy area {policy_id}: {len(questions)} questions")


def test_scoring_modalities():
    """Test scoring modality retrieval"""
    print("\nTest 6: Scoring Modalities")
    service = MetadataService()
    
    modalities = ["TYPE_A", "TYPE_B", "TYPE_C", "TYPE_D"]
    for mod_id in modalities:
        modality = service.get_scoring_modality(mod_id)
        assert modality is not None, f"Should find {mod_id}"
        assert modality.id is not None, f"{mod_id} should have id"
        assert modality.max_score == 3.0, f"{mod_id} should have max_score 3.0"
        print(f"  ✓ {mod_id}: {modality.description}")


def test_execution_chain():
    """Test execution chain integration"""
    print("\nTest 7: Execution Chain Integration")
    service = MetadataService()
    
    # Check that questions have execution chains
    questions_with_chain = 0
    for context in service.get_all_questions().values():
        if context.execution_chain:
            questions_with_chain += 1
            # Verify execution chain structure
            for step in context.execution_chain:
                assert "module" in step, "Execution step should have module"
                assert "class" in step, "Execution step should have class"
                assert "method" in step, "Execution step should have method"
    
    print(f"  ✓ {questions_with_chain} questions have execution chains")
    
    # Test specific dimension mappings
    d1_questions = service.get_questions_by_dimension("D1")
    if d1_questions:
        example = d1_questions[0]
        assert len(example.execution_chain) > 0, "D1 questions should have execution chain"
        assert "policy_processor" in example.execution_chain[0]["module"], "D1 should route to policy_processor"
        print(f"  ✓ D1 routes to: {example.execution_chain[0]['module']}")


def test_report_assembler():
    """Test ReportAssembler with new scoring types"""
    print("\nTest 8: ReportAssembler Scoring Types")
    assembler = ReportAssembler()
    
    # Test rubric levels
    assert "EXCELENTE" in assembler.rubric_levels, "Should have EXCELENTE level"
    assert "BUENO" in assembler.rubric_levels, "Should have BUENO level"
    
    print("  ✓ Rubric levels configured correctly")
    
    # Test that TYPE_E and TYPE_F scoring methods exist
    assert hasattr(assembler, '_score_type_e'), "Should have _score_type_e method"
    assert hasattr(assembler, '_score_type_f'), "Should have _score_type_f method"
    
    print("  ✓ TYPE_E scoring method available")
    print("  ✓ TYPE_F scoring method available")


def test_validation():
    """Test validation"""
    print("\nTest 9: Validation")
    service = MetadataService()
    
    validation = service.validate_questionnaire()
    assert validation["valid"] == True, "Validation should pass"
    assert validation["total_questions"] == 300, "Should have 300 questions"
    
    print("  ✓ Questionnaire validation passed")
    print(f"  ✓ Total questions: {validation['total_questions']}")
    print(f"  ✓ Total dimensions: {validation['total_dimensions']}")
    print(f"  ✓ Total policy areas: {validation['total_policy_areas']}")
    
    if validation["issues"]:
        print("  ⚠ Issues found:")
        for issue in validation["issues"]:
            print(f"    - {issue}")


def run_all_tests():
    """Run all tests"""
    print("=" * 80)
    print("METADATA SERVICE AND REPORT ASSEMBLY TESTS")
    print("=" * 80 + "\n")
    
    tests = [
        test_metadata_service_initialization,
        test_question_context_retrieval,
        test_canonical_id_format,
        test_dimension_coverage,
        test_policy_area_coverage,
        test_scoring_modalities,
        test_execution_chain,
        test_report_assembler,
        test_validation
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  ✗ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            failed += 1
    
    print("\n" + "=" * 80)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 80)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
