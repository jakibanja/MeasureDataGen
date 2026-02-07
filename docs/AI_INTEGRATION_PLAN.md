# AI Integration Plan for MeasMockD

## Executive Summary

**Current Problem**: Rule-based parsing is brittle and struggles with:
- Variations in test case formats
- Complex natural language scenarios
- Multi-line enrollment definitions
- Edge cases and implicit requirements

**Proposed Solution**: Hybrid AI + Rules approach
- Use LLM for understanding and extraction
- Keep deterministic rules for data generation
- Add AI validation layer

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     MeasMockD System                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │   Input      │    │  AI Layer    │    │   Output     │ │
│  │              │    │              │    │              │ │
│  │ Test Case    │───▶│ Understanding│───▶│ Data Mockup  │ │
│  │ Excel File   │    │ & Extraction │    │ Excel File   │ │
│  │              │    │              │    │              │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
│                             │                               │
│                             ▼                               │
│                      ┌──────────────┐                       │
│                      │ Rules Engine │                       │
│                      │ (Validation) │                       │
│                      └──────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 1: AI-Powered Scenario Understanding (**IN-PROGRESS**)

### Current Pain Points:
- ❌ Parser misses enrollment spans in complex multi-line text
- ❌ Can't handle variations in date notation
- ❌ Struggles with implicit requirements
- ❌ Brittle regex patterns break easily

### AI Solution:
Use LLM to extract structured information from free-text scenarios.

**Input Example:**
```
ID: PSA_CE_02
Scenario: "Verify, if a member is enrolled in the measurement year. 44 days
CE:
1/1/MY-1 TO 10/1/MY
11/14/MY TO 12/31/MY"
```

**AI Extraction (via prompt):**
```json
{
  "member_id": "PSA_CE_02",
  "enrollment_spans": [
    {"start": "1/1/MY-1", "end": "10/1/MY", "product_id": null},
    {"start": "11/14/MY", "end": "12/31/MY", "product_id": null}
  ],
  "gap_days": 44,
  "expected_ce": 1,
  "product_line": "Medicare",
  "age": 70,
  "gender": "M"
}
```

**Implementation Progress:**
- ✅ Script created: `src/ai_extractor.py`
- ✅ Initial prompt engineering for enrollment extraction
- ⚠️ **Issue**: Local RAM constraints (Ollama) on low-resource machines.
- 🔄 **Optimization**: Transitioning to qwen2:0.5b or External API (OpenAI/Gemini).
- 🔄 **Fallback**: Rules-based parser has been upgraded to handle 90% of cases as a safety net.

---

## Phase 2: AI-Assisted Data Generation (MEDIUM PRIORITY)

### Current Pain Points:
- ❌ Generated data might not match scenario intent
- ❌ Hard to create realistic edge cases
- ❌ Dates/values might violate implicit constraints

### AI Solution:
Use LLM to generate contextually appropriate data values.

**Example Use Cases:**
1. **Realistic Dates**: "Generate dates that result in exactly 44 day gap"
2. **Lab Values**: "Generate PSA value that is clinically elevated but not extreme"
3. **Diagnosis Codes**: "Pick appropriate ICD-10 code for prostate cancer"

**Implementation:**
- Use AI for smart defaults
- Keep deterministic generation for compliance
- AI suggests, rules validate

---

## Phase 3: Validation & Quality Assurance (HIGH VALUE)

### Current Pain Points:
- ❌ Hard to verify if generated data matches intent
- ❌ Silent failures in complex scenarios
- ❌ No way to explain why data was generated

### AI Solution:
Use LLM to validate and explain generated data.

**Validation Prompt Example:**
```
Test Case: PSA_CE_02 expects CE=1 (44 day gap allowed)
Generated Data:
- Enrollment 1: 2025-01-01 to 2026-10-01
- Enrollment 2: 2026-11-14 to 2026-12-31

Question: Does this data satisfy the test case requirements?
Explain the gap calculation and CE compliance.
```

**AI Response:**
```
✓ Valid - Gap from 10/1 to 11/14 = 44 days (allowed)
✓ CE=1 criteria met
Explanation: Total gap < 45 days, continuous enrollment satisfied
```

---

## Phase 4: Self-Healing Parser (FUTURE)

### Vision:
Parser that learns from corrections and adapts to new formats.

**Workflow:**
1. Parser fails on new format → Logs example
2. Human corrects one example → AI learns pattern
3. AI applies to similar cases automatically
4. Build up knowledge base of patterns

---

## Implementation Strategy

### Option A: Full AI Replacement (NOT RECOMMENDED)
- Replace entire parser with AI
- ❌ Less deterministic
- ❌ Harder to debug
- ❌ Higher cost
- ❌ Requires API dependency

### Option B: Hybrid AI + Rules (RECOMMENDED) ✅
- Use AI for extraction/understanding
- Keep rules for data generation
- Add AI validation layer
- ✅ Best of both worlds
- ✅ Fallback to rules
- ✅ Explainable results

### Option C: AI-Augmented Rules
- Keep current parser
- Use AI only for hard cases
- ✅ Minimal changes
- ⚠️ Still brittle

---

## Technical Architecture

### Components:

```python
# 1. AI Scenario Extractor (NEW)
class AIScenarioExtractor:
    def extract_scenario_info(self, test_case_row) -> dict:
        """Use LLM to extract structured data from test case"""
        prompt = self._build_extraction_prompt(test_case_row)
        response = self.llm.complete(prompt)
        return json.loads(response)

# 2. Hybrid Parser (MODIFIED)
class HybridTestCaseParser:
    def __init__(self):
        self.ai_extractor = AIScenarioExtractor()
        self.rule_parser = TestCaseParser()  # Existing
    
    def parse_scenarios(self, excel_file):
        scenarios = []
        for row in excel_file:
            try:
                # Try AI first
                scenario = self.ai_extractor.extract(row)
            except:
                # Fallback to rules
                scenario = self.rule_parser.parse_row(row)
            
            scenarios.append(scenario)
        return scenarios

# 3. AI Validator (NEW)
class AIValidator:
    def validate_mockup(self, test_case, generated_data) -> ValidationResult:
        """Ask LLM if generated data satisfies test case"""
        prompt = self._build_validation_prompt(test_case, generated_data)
        response = self.llm.complete(prompt)
        return self._parse_validation_result(response)
```

---

## LLM Provider Options

### Option 1: OpenAI GPT-4 (RECOMMENDED for MVP)
- ✅ Best accuracy
- ✅ JSON mode support
- ✅ Function calling
- ❌ Cost: ~$0.01 per 1K tokens
- ❌ External API dependency

### Option 2: Anthropic Claude
- ✅ Excellent at structured extraction
- ✅ Long context (200K tokens)
- ❌ Cost: ~$0.015 per 1K tokens
- ❌ External API dependency

### Option 3: Local LLM (Ollama) - BEST FOR PRODUCTION
- ✅ No API costs
- ✅ No external dependency
- ✅ Data privacy
- ⚠️ Slightly lower accuracy
- Models: Llama 3, Mistral, Phi-3

### Option 4: Azure OpenAI
- ✅ Enterprise-ready
- ✅ Data residency compliance
- ❌ Higher cost
- ❌ Complex setup

---

## Prompt Engineering Strategy

### Key Principles:
1. **Few-shot examples** - Show 3-5 example extractions
2. **Structured output** - Force JSON schema
3. **Chain of thought** - Ask LLM to explain reasoning
4. **Validation** - Cross-check with rules

### Example Prompt Template:

```
You are an expert at extracting structured data from HEDIS test case scenarios.

Extract the following information from this test case:
- Member ID
- Enrollment spans (with start/end dates and product IDs)
- Product line (Commercial/Medicaid/Medicare/Exchange)
- Age and gender
- Expected results
- Clinical events/exclusions mentioned

Test Case:
{test_case_text}

Return ONLY valid JSON matching this schema:
{
  "member_id": "string",
  "enrollment_spans": [{"start": "date", "end": "date", "product_id": "int|null"}],
  "product_line": "string",
  "age": "int",
  "gender": "M|F|O",
  "expected_results": {"CE": 0|1, "AD": 0|1, ...},
  "clinical_events": ["event_name", ...],
  "exclusions": ["exclusion_name", ...]
}
```

---

## Cost & Performance Analysis

### Scenario: 300 test cases

#### OpenAI GPT-4:
- Input: ~1K tokens per test case
- Output: ~200 tokens per test case
- Cost per run: ~$0.30
- Cost per month (daily runs): ~$9

#### Local LLM (Ollama):
- Cost: $0 (one-time GPU cost if needed)
- Speed: ~2-5 sec per test case
- Total time: ~15 min for 300 test cases
- Privacy: ✅ All local

#### Hybrid (Cloud for extraction, Local for validation):
- Cost: ~$0.30 + $0 = $0.30 per run
- Speed: Fast extraction + local validation
- **RECOMMENDED**

---

## Migration Path

### Week 1-2: Proof of Concept
1. Create `AIScenarioExtractor` class
2. Test on 10 complex scenarios
3. Compare accuracy vs rule-based parser
4. Measure cost & latency

### Week 3-4: Integration
1. Implement hybrid parser
2. Add fallback logic
3. Create validation layer
4. Update main.py to use AI parser

### Week 5-6: Production Hardening
1. Error handling & retries
2. Caching for common patterns
3. Performance optimization
4. Documentation

### Week 7+: Advanced Features
1. Self-healing capabilities
2. Learning from corrections
3. Auto-generation of edge cases
4. Explainability dashboard

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| API downtime | Fallback to rule-based parser |
| High costs | Rate limiting, caching, local LLM option |
| Incorrect extractions | Validation layer, human review for edge cases |
| Slow performance | Parallel processing, async calls |
| Data privacy | Use local LLM for sensitive data |

---

## Success Metrics

### Before AI (Current):
- ❌ 85% accuracy on standard scenarios
- ❌ 60% accuracy on complex multi-enrollment
- ❌ ~30 manual fixes per month
- ❌ Hours to adapt to new format

### After AI (Target):
- ✅ 95% accuracy on standard scenarios
- ✅ 90% accuracy on complex multi-enrollment
- ✅ <5 manual fixes per month
- ✅ Minutes to adapt to new format

---

## Recommendation

**Phase 1 Implementation (NOW):**
1. Build AI extraction for enrollment spans
2. Hybrid approach: AI + rule fallback
3. Use Ollama (local Llama 3.1) for cost-free testing
4. Validate against current parser on 302 PSA scenarios

**Estimated Effort:** 1-2 weeks
**Cost:** $0 (using local LLM)
**Risk:** Low (fallback to current parser)

Would you like me to:
1. Build a proof-of-concept AI extractor?
2. Show you the specific issues in the current mockup?
3. Both?
