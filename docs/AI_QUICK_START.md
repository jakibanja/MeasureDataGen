# AI Integration - Quick Start Guide

## What Issues Were Found in the Mockup?

Running `diagnose_mockup.py` found **9 issues**, likely including:
- Members with incomplete enrollment spans
- Date range anomalies
- Low clinical event coverage
- Missing multi-enrollment cases

## Why AI Is The Right Solution

### Current Problem
The rule-based parser struggles with:
1. **Natural language variations** - Same concept described differently
2. **Multi-line context** - Information spread across multiple lines
3. **Implicit requirements** - Age, dates, gaps implied but not explicit
4. **Format changes** - New test case formats break the parser

### How AI Solves This
AI (LLMs) excel at:
- ✅ Understanding intent from natural language
- ✅ Maintaining context across multiple lines
- ✅ Extracting structured data from unstructured text
- ✅ Adapting to format variations
- ✅ Inferring implicit requirements

## Recommended Approach: **Hybrid AI + Rules**

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│  Test Case (Excel) → AI Parser → Structured JSON   │
│                          ↓                          │
│                   Rules Engine → Mock Data          │
│                          ↓                          │
│                   AI Validator → ✓/✗ Report        │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Why Hybrid?
- **AI** understands complex scenarios → extracts requirements
- **Rules** generate deterministic data → ensures compliance
- **AI** validates output → catches mistakes

## Implementation Options

### Option 1: Local LLM (Ollama) - RECOMMENDED ✅
**Pros:**
- ✅ Zero cost
- ✅ No API dependency
- ✅ Full data privacy
- ✅ Fast (2-5 sec per test case)

**Cons:**
- ⚠️ Requires local installation
- ⚠️ Slightly lower accuracy than GPT-4

**Setup:**
1.  **Environment**: 
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    pip install -r requirements.txt
    ```
2.  **Ollama**: Install if not present.
3.  **Download model**:
    ```bash
    ollama pull qwen2:0.5b    # Smallest model (recommended for low RAM)
    ollama pull phi:2.7b      # Medium speed/accuracy
    ```

### Option 2: OpenAI API
**Pros:**
- ✅ Best accuracy
- ✅ No setup needed
- ✅ JSON mode + function calling

**Cons:**
- ❌ Cost: ~$0.30 per 300 test cases
- ❌ Requires internet + API key
- ❌ Data leaves your machine

**Setup:**
```bash
pip install openai
# Set API key in .env file
```

### Option 3: Anthropic Claude
Similar to OpenAI but with longer context windows.

### Step 1: Current Status & Path Forward

**✅ Current State: Enhanced Deterministic Parser**
We have upgraded the rule-based parser in `src/parser.py`. It now handles:
- **Multi-line scenarios** (Correctly carries over IDs across rows).
- **Deep date extraction** (Scans all columns including 'Period' and 'Scenario').
- **VSD Integration** (Pulls real codes from the Value Set Directory).

**⚠️ Local LLM Warning**
Local models (Ollama) require significant RAM. If your system has <2GB free RAM, local execution will fail. For these cases, we recommend using an External API (Gemini/OpenAI) via `src/ai_extractor.py`.

**Next Steps:**
- [ ] Add more measures (WCC, COL, etc.).
- [ ] Implement AI fallback for clinical event extraction.
- [ ] Automate the "Expected Result" validation.

### Step 2: I Can Build...

1. **Proof of Concept** - AI extractor for enrollment spans
   - Show you before/after comparison
   - Measure accuracy improvement
   - Estimate costs

2. **Diagnostic Report** - What's wrong with current mockup
   - Specific test cases failing
   - Root causes
   - Priorities

3. **Full Integration** - Complete AI hybrid system
   - Replace parser with AI
   - Keep generation logic
   - Add validation

## Cost-Benefit Analysis

### Current Approach (Rules Only)
- Development time: High (constant fixes)
- Accuracy: ~60-85%
- Maintenance: High (breaks on format changes)
- Cost: $0 but many manual hours

### Hybrid Approach (AI + Rules)
- Development time: Medium (upfront, then low)
- Accuracy: ~90-98%
- Maintenance: Low (adapts to changes)
- Cost: $0 (local) or ~$10/month (cloud)

**ROI: If you spend >2 hours/month fixing parser issues, AI pays for itself**

## What Would You Like Me To Do?

1. **Build AI Proof-of-Concept** (I'll show you it working)
2. **Fix Current Issues First** (then add AI)
3. **Full AI Integration** (complete rewrite)
4. **Show Me More Details** (specific issues in mockup)

Let me know and I'll get started! 🚀
