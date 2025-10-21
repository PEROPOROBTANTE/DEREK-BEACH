# FARFAN 3.0 - Canonical Notation Specification

## Overview

This document specifies the **canonical notation system** used throughout the DEREK-BEACH (FARFAN 3.0) repository for identifying questions, dimensions, and policy areas.

**Version**: 2.0 (Updated October 2025)  
**Status**: ✅ Implemented and Verified

---

## Canonical Notation Format

### Primary Format: `P#-D#-Q#`

All questions in the system use the three-part identifier:

```
P#-D#-Q#
```

Where:
- **P#**: Policy Area (10 areas: P1-P10)
- **D#**: Dimension (6 dimensions: D1-D6)
- **Q#**: Question Number (5 per dimension: Q1-Q5)

**Total**: 300 questions (10 × 6 × 5 = 300)

---

## Policy Areas (P1-P10) - "Decálogo"

The 10 thematic policy areas defined in Colombia's territorial development framework:

| Code | Policy Area | Spanish Name |
|------|-------------|--------------|
| **P1** | Women's Rights & Gender Equality | Derechos de las mujeres e igualdad de género |
| **P2** | Violence Prevention & Conflict Protection | Prevención de la violencia y protección frente al conflicto |
| **P3** | Environment, Climate & Disaster Management | Ambiente sano, cambio climático, prevención y atención a desastres |
| **P4** | Economic, Social & Cultural Rights | Derechos económicos, sociales y culturales |
| **P5** | Victims' Rights & Peacebuilding | Derechos de las víctimas y construcción de paz |
| **P6** | Children, Youth & Adolescent Rights | Derecho al buen futuro de la niñez, adolescencia y juventud |
| **P7** | Land & Territory | Tierras y territorios |
| **P8** | Human Rights Defenders & Leaders | Líderes y defensores de derechos humanos |
| **P9** | Rights of Persons Deprived of Liberty | Crisis de derechos de personas privadas de la libertad |
| **P10** | Cross-border Migration | Migración transfronteriza |

**Source**: `puntos_decalogo` section in `cuestionario.json`

---

## Dimensions (D1-D6) - Analysis Framework

The 6 analytical dimensions for evaluating policy plans:

| Code | Dimension | Description |
|------|-----------|-------------|
| **D1** | Inputs (Diagnosis & Baselines) | Evaluates quality of territorial diagnosis, quantitative baselines, gap identification, and resource sufficiency |
| **D2** | Activities (Intervention Design) | Evaluates formalization of activities with clear structure, responsibilities, schedules, costs, and causal mechanisms |
| **D3** | Products (Verifiable Outputs) | Evaluates specification of products (goods/services) with verifiable indicators, formulas, sources, and budget traceability |
| **D4** | Results (Measurable Outcomes) | Evaluates definition of results (changes in target population) with metrics, baselines, targets, and causal linkage |
| **D5** | Impacts (Long-term Effects) | Evaluates projection of impacts (structural transformations) with transmission routes, temporal lags, and systemic risk considerations |
| **D6** | Causality (Explicit Theory of Change) | Evaluates articulation of theories of change, identification of root causes, mediators, moderators, and verifiable assumptions |

**Source**: `dimensiones` section in `cuestionario.json`

---

## Question Numbering (Q1-Q5)

Each dimension has **5 base questions** (Q1-Q5), numbered **per-dimension**:

- **Per-dimension numbering**: Q1-Q5 repeats for each dimension
- **NOT global numbering**: Questions are NOT numbered 1-30 globally

### Example for Policy Area P1 (Gender Equality):

```
P1-D1-Q1  (Question 1 of Dimension 1 for Policy Area 1)
P1-D1-Q2  (Question 2 of Dimension 1 for Policy Area 1)
P1-D1-Q3  (Question 3 of Dimension 1 for Policy Area 1)
P1-D1-Q4  (Question 4 of Dimension 1 for Policy Area 1)
P1-D1-Q5  (Question 5 of Dimension 1 for Policy Area 1)
P1-D2-Q1  (Question 1 of Dimension 2 for Policy Area 1)
P1-D2-Q2  (Question 2 of Dimension 2 for Policy Area 1)
...
P1-D6-Q5  (Question 5 of Dimension 6 for Policy Area 1)
```

Total for P1: 6 dimensions × 5 questions = **30 questions**

---

## Complete Question Space

### Distribution

| Level | Count | Description |
|-------|-------|-------------|
| **Total Questions** | 300 | Complete question set |
| **Per Policy Area** | 30 | Questions for each P# |
| **Per Dimension** | 50 | Questions for each D# (across all policy areas) |
| **Per (Policy, Dimension)** | 5 | Questions for each P#-D# pair |

### Examples from Complete Set

```
P1-D1-Q1   Gender equality - Diagnosis - Question 1
P1-D1-Q2   Gender equality - Diagnosis - Question 2
P1-D2-Q1   Gender equality - Activities - Question 1
P2-D1-Q1   Violence prevention - Diagnosis - Question 1
P5-D3-Q3   Victims' rights - Products - Question 3
P10-D6-Q5  Migration - Causality - Question 5
```

---

## File Structure

### cuestionario.json

**Key**: `preguntas` (previously `preguntas_base`)

**Structure**: Array of 300 question objects

```json
{
  "id": "P1-D1-Q1",
  "dimension": "D1",
  "numero": 1,
  "texto_template": "¿El diagnóstico presenta datos numéricos...",
  "metadata": {
    "policy_area": "P1",
    "original_id": "D1-Q1"
  }
}
```

### rubric_scoring.json

**Key**: `questions`

**Structure**: Array of 300 question objects

```json
{
  "id": "P1-D1-Q1",
  "dimension": "D1",
  "question_no": 1,
  "policy_area": "P1",
  "policy_area_name": "Derechos de las mujeres e igualdad de género",
  "template": "¿El diagnóstico presenta líneas base...",
  "scoring_modality": "TYPE_A",
  "max_score": 3.0
}
```

---

## Multi-Level Reporting

The notation system supports three reporting levels:

### 1. MICRO Level (Individual Questions)

- **Granularity**: Single question
- **ID Format**: `P#-D#-Q#`
- **Example**: `P1-D1-Q1`
- **Count**: 300 individual answers

### 2. MESO Level (Clusters)

Aggregation by policy area and/or dimension:

#### By Policy Area
- **Granularity**: All questions for one policy area
- **ID Pattern**: `P#-*-*`
- **Example**: All P1 questions (P1-D1-Q1, P1-D1-Q2, ..., P1-D6-Q5)
- **Count**: 10 clusters (one per policy area)

#### By Dimension
- **Granularity**: All questions for one dimension
- **ID Pattern**: `*-D#-*`
- **Example**: All D1 questions (P1-D1-Q1, P2-D1-Q1, ..., P10-D1-Q5)
- **Count**: 6 clusters (one per dimension)

#### By Policy-Dimension Intersection
- **Granularity**: Questions for one (policy, dimension) pair
- **ID Pattern**: `P#-D#-*`
- **Example**: P1-D1 questions (P1-D1-Q1, P1-D1-Q2, ..., P1-D1-Q5)
- **Count**: 60 clusters (10 × 6)

### 3. MACRO Level (Overall)

- **Granularity**: Complete plan
- **Aggregation**: All 300 questions
- **Metrics**: Overall score, convergence with Decálogo framework

---

## Python Code Integration

### QuestionSpec Class

```python
@dataclass
class QuestionSpec:
    question_id: str        # "P1-D1-Q1"
    dimension: str          # "D1"
    question_no: int        # 1
    policy_area: str        # "P1"
    template: str
    text: str
    scoring_modality: str
    max_score: float
    
    @property
    def canonical_id(self) -> str:
        """Returns P#-D#-Q# notation"""
        return f"{self.policy_area}-{self.dimension}-Q{self.question_no}"
```

### Usage in QuestionnaireParser

```python
from questionnaire_parser import QuestionnaireParser

parser = QuestionnaireParser("cuestionario.json")

# Get specific question
question = parser.get_question("P1-D1-Q1")

# Access properties
print(question.canonical_id)   # "P1-D1-Q1"
print(question.policy_area)    # "P1"
print(question.dimension)      # "D1"
print(question.question_no)    # 1

# Filter by policy area
p1_questions = [q for q in parser.get_all_questions().values() 
                if q.policy_area == "P1"]  # 30 questions

# Filter by dimension
d1_questions = [q for q in parser.get_all_questions().values() 
                if q.dimension == "D1"]  # 50 questions
```

---

## Migration from Old Notation

### Old Format (Deprecated)

```
D#-Q#  (e.g., D1-Q1, D2-Q3)
```

**Problems with old format**:
- ❌ Ambiguous: Same ID for 10 different questions (one per policy area)
- ❌ No policy area traceability
- ❌ Cannot support MESO-level clustering by policy area
- ❌ Global numbering in rubric_scoring.json conflicted with per-dimension numbering

### New Format (Current)

```
P#-D#-Q#  (e.g., P1-D1-Q1, P5-D3-Q2)
```

**Benefits**:
- ✅ Unique ID for each of 300 questions
- ✅ Policy area explicitly encoded
- ✅ MESO-level clustering supported
- ✅ Consistent across all files
- ✅ Aligns with Python code expectations

### Backward Compatibility

The `questionnaire_parser.py` maintains backward compatibility:
- Detects if questions use P# prefix
- Falls back to template generation if old format detected
- Accepts both `puntos_tematicos` and `puntos_decalogo` keys

---

## Validation Rules

### Question ID Validation

A valid question ID MUST:
1. Match pattern: `P[1-9]|P10-D[1-6]-Q[1-5]`
2. Reference existing policy area (P1-P10)
3. Reference existing dimension (D1-D6)
4. Use per-dimension numbering (Q1-Q5)

### Examples

**Valid**:
- ✅ `P1-D1-Q1`
- ✅ `P10-D6-Q5`
- ✅ `P5-D3-Q3`

**Invalid**:
- ❌ `D1-Q1` (missing policy area)
- ❌ `P11-D1-Q1` (invalid policy area)
- ❌ `P1-D7-Q1` (invalid dimension)
- ❌ `P1-D1-Q6` (invalid question number)
- ❌ `P1-D2-Q10` (wrong numbering system)

---

## Consistency Verification

### Automated Checks

Run the verification script:

```bash
python /tmp/analyze_notation.py
```

Expected output:
```
✓ CONSISTENT: Dimension keys (D1-D6)
✓ CONSISTENT: Policy area keys (P1-P10)
✓ CONSISTENT: Question notation (P#-D#-Q#)
✓ All 300 question IDs match between files
```

### Manual Verification

```python
import json

# Load files
with open('cuestionario.json') as f:
    cues = json.load(f)

with open('rubric_scoring.json') as f:
    rubric = json.load(f)

# Check IDs
cues_ids = {q['id'] for q in cues['preguntas']}
rubric_ids = {q['id'] for q in rubric['questions']}

assert cues_ids == rubric_ids, "Question ID mismatch!"
assert len(cues_ids) == 300, "Expected 300 questions"
print("✓ Notation verified")
```

---

## FAQ

### Q: Why P#-D#-Q# instead of just D#-Q#?

**A**: Policy area prefix (P#) is essential for:
- Unique identification of all 300 questions
- MESO-level clustering and reporting
- Traceability from question to policy area
- Supporting the 10-point "Decálogo" framework

### Q: Why per-dimension numbering (Q1-Q5) instead of global (Q1-Q30)?

**A**: Per-dimension numbering is more semantically meaningful:
- Each dimension conceptually has 5 questions
- Easier to understand (D1-Q1 is "first question of dimension 1")
- Consistent with base template structure
- Aligns with cuestionario.json organization

### Q: Are there exactly 5 questions per dimension?

**A**: Yes, this is by design:
- Each dimension evaluates 5 key aspects
- Total: 6 dimensions × 5 questions = 30 base questions
- Expanded: 30 base × 10 policy areas = 300 total questions

### Q: Can I add new policy areas or dimensions?

**A**: Yes, but update:
1. cuestionario.json (add to `puntos_decalogo` or `dimensiones`)
2. rubric_scoring.json (expand questions)
3. Code that validates ranges (P1-P10, D1-D6, Q1-Q5)
4. This documentation

---

## Change Log

### Version 2.0 (October 2025)
- ✅ Implemented P#-D#-Q# notation across all files
- ✅ Fixed cuestionario.json key (`preguntas_base` → `preguntas`)
- ✅ Expanded rubric_scoring.json (30 → 300 questions)
- ✅ Updated questionnaire_parser.py
- ✅ Created backup files
- ✅ Verified consistency

### Version 1.0 (Original)
- ❌ Used D#-Q# notation (ambiguous)
- ❌ Mixed numbering systems
- ❌ Key name mismatches

---

## References

- `cuestionario.json`: Master question database
- `rubric_scoring.json`: Scoring modalities and question templates
- `questionnaire_parser.py`: Question loading and parsing logic
- `report_assembly.py`: Multi-level reporting implementation
- `core_orchestrator.py`: Pipeline orchestration

---

**Document Version**: 1.0  
**Last Updated**: October 21, 2025  
**Maintained By**: FARFAN 3.0 Integration Team
