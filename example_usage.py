# coding=utf-8
"""
Example Usage - MetadataService and Enhanced ReportAssembly
===========================================================

This example demonstrates how to use the new MetadataService and enhanced
ReportAssembly with the refactored architecture.

Author: FARFAN 3.0 Team
Version: 3.0.0
"""

import logging
from metadata_service import MetadataService, QuestionContext
from report_assembly import ReportAssembler, MicroLevelAnswer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def example_metadata_service():
    """Example: Using MetadataService"""
    print("=" * 80)
    print("EXAMPLE 1: MetadataService - Question Context Retrieval")
    print("=" * 80)
    
    # Initialize metadata service
    service = MetadataService()
    
    # Get complete context for a question
    question_id = "P1-D1-Q1"
    context = service.get_question_context(question_id)
    
    if context:
        print(f"\nQuestion: {question_id}")
        print(f"  Canonical ID: {context.canonical_id}")
        print(f"  Dimension: {context.dimension}")
        print(f"  Policy Area: {context.policy_area}")
        print(f"  Scoring Modality: {context.scoring_modality}")
        print(f"  Max Score: {context.max_score}")
        print(f"  Text: {context.text[:100]}...")
        print(f"  Execution Chain: {len(context.execution_chain)} steps")
        if context.execution_chain:
            for i, step in enumerate(context.execution_chain, 1):
                print(f"    Step {i}: {step['module']}.{step['class']}.{step['method']}")
    
    # Get scoring modality details
    print("\n" + "-" * 80)
    print("Scoring Modality Details:")
    modality = service.get_scoring_modality("TYPE_A")
    if modality:
        print(f"  ID: {modality.id}")
        print(f"  Description: {modality.description}")
        print(f"  Formula: {modality.formula}")
        print(f"  Max Score: {modality.max_score}")
        print(f"  Expected Elements: {modality.expected_elements}")
    
    # Get dimension info
    print("\n" + "-" * 80)
    print("Dimension Information:")
    dim_info = service.get_dimension_info("D1")
    if dim_info:
        print(f"  ID: {dim_info['id']}")
        print(f"  Name: {dim_info['nombre']}")
        print(f"  Description: {dim_info['descripcion'][:80]}...")
        print(f"  Questions per dimension: {dim_info['preguntas']}")
        print(f"  Minimum threshold: {dim_info['umbral_minimo']}")
    
    print("=" * 80 + "\n")


def example_report_assembly():
    """Example: Using enhanced ReportAssembly"""
    print("=" * 80)
    print("EXAMPLE 2: Enhanced ReportAssembly - Scoring Modalities")
    print("=" * 80)
    
    # Initialize report assembler
    assembler = ReportAssembler()
    
    # Show rubric levels
    print("\nRubric Levels (Question-level, 0-3 scale):")
    for level, (min_score, max_score) in assembler.question_rubric.items():
        print(f"  {level:15s}: {min_score:.2f} - {max_score:.2f}")
    
    print("\nRubric Levels (Dimension/Overall, 0-100% scale):")
    for level, (min_pct, max_pct) in assembler.rubric_levels.items():
        print(f"  {level:15s}: {min_pct}% - {max_pct}%")
    
    # Example scoring modalities
    print("\n" + "-" * 80)
    print("Supported Scoring Modalities:")
    modalities = [
        ("TYPE_A", "Binary presence/absence (4 elements)"),
        ("TYPE_B", "Weighted sum of multiple elements"),
        ("TYPE_C", "Quality assessment with rubric"),
        ("TYPE_D", "Numerical threshold matching"),
        ("TYPE_E", "Logical rule-based scoring (NEW)"),
        ("TYPE_F", "Semantic analysis with similarity (NEW)")
    ]
    for mod_id, description in modalities:
        print(f"  {mod_id}: {description}")
    
    print("=" * 80 + "\n")


def example_integration():
    """Example: Full integration workflow"""
    print("=" * 80)
    print("EXAMPLE 3: Full Integration Workflow")
    print("=" * 80)
    
    # Initialize services
    metadata_service = MetadataService()
    report_assembler = ReportAssembler()
    
    print("\n1. Get question context from MetadataService")
    question_id = "P2-D2-Q8"
    context = metadata_service.get_question_context(question_id)
    
    if context:
        print(f"   ✓ Retrieved context for {context.canonical_id}")
        print(f"   - Scoring: {context.scoring_modality}")
        print(f"   - Expected elements: {len(context.expected_elements)}")
        print(f"   - Execution chain: {len(context.execution_chain)} steps")
    
    print("\n2. Simulate execution results")
    # This would come from actual module execution
    execution_results = {
        "policy_processor": {
            "status": "success",
            "confidence": 0.85,
            "data": {
                "indicators_found": 3,
                "sources_verified": ["DANE", "DNP"]
            },
            "evidence": ["Evidence excerpt 1", "Evidence excerpt 2"]
        },
        "causal_proccesor": {
            "status": "success",
            "confidence": 0.78,
            "data": {
                "causal_chains": 2,
                "mechanisms_identified": 4
            },
            "evidence": ["Causal mechanism A", "Causal mechanism B"]
        }
    }
    print(f"   ✓ Simulated execution of {len(execution_results)} modules")
    
    print("\n3. Generate MICRO-level answer")
    # Note: This is a mock - real usage would pass actual question_spec
    # and plan_text from document processing
    print("   (Would generate MicroLevelAnswer with:")
    print("    - Quantitative score based on scoring modality")
    print("    - Qualitative note (EXCELENTE/BUENO/etc.)")
    print("    - Evidence excerpts from plan document")
    print("    - Complete execution chain traceability")
    print("    - Confidence metrics)")
    
    print("\n4. Aggregate to MESO and MACRO levels")
    print("   (Would aggregate MicroLevelAnswers to:")
    print("    - MESO: Cluster-level analysis by policy areas")
    print("    - MACRO: Overall convergence with Decálogo)")
    
    print("\n" + "=" * 80)
    print("Integration complete! See metadata_service.py and report_assembly.py")
    print("for full implementation details.")
    print("=" * 80 + "\n")


def example_migration_guide():
    """Example: Migration from old to new architecture"""
    print("=" * 80)
    print("MIGRATION GUIDE: From QuestionnaireParser/QuestionRouter to MetadataService")
    print("=" * 80)
    
    print("\nOLD APPROACH (Deprecated):")
    print("-" * 80)
    print("""
    from questionnaire_parser import QuestionnaireParser
    from question_router import QuestionRouter
    
    # Two separate services
    parser = QuestionnaireParser()
    router = QuestionRouter()
    
    # Get question
    question = parser.get_question("P1-D1-Q1")
    
    # Get routing
    route = router.route_question("P1-D1-Q1")
    
    # Limited context - no execution chains, no integrated validation
    """)
    
    print("\nNEW APPROACH (Recommended):")
    print("-" * 80)
    print("""
    from metadata_service import MetadataService
    
    # Single unified service
    service = MetadataService()
    
    # Get complete context with execution chain
    context = service.get_question_context("P1-D1-Q1")
    
    # Rich context includes:
    # - Question text and metadata
    # - Scoring modality with rubric details
    # - Search and verification patterns
    # - Execution chain with module routing
    # - Validation rules and dependencies
    # - Cross-validated against all config sources
    """)
    
    print("\nKEY BENEFITS:")
    print("-" * 80)
    print("  ✓ Single source of truth for all metadata")
    print("  ✓ Integrated execution chain traceability")
    print("  ✓ Cross-validation between all config files")
    print("  ✓ Rich context with search patterns and rules")
    print("  ✓ Scoring modality details from rubric")
    print("  ✓ YAML-based execution mapping (version controlled)")
    print("  ✓ Better type safety with dataclasses")
    
    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    # Run all examples
    example_metadata_service()
    example_report_assembly()
    example_integration()
    example_migration_guide()
    
    print("\n" + "=" * 80)
    print("All examples completed successfully!")
    print("=" * 80)
