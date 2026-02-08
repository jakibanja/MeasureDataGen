# Using the Test Case Reformatter

## Problem

When generating mockups, you might see warnings like:
```
⚠️  No enrollment spans found for PSA_CE_02_01. Triggering AI Extractor...
```

This means the regex parser couldn't extract enrollment data and had to fall back to AI, which:
- **Slows down generation** (AI extraction takes time)
- **May be less accurate** (AI might misinterpret data)
- **Happens on every generation** (no caching for AI extraction)

## Solution: Pre-format Your Test Cases

The `TestCaseReformatter` solves this by:
1. **One-time AI processing** - Extract data once, reuse forever
2. **Standardized format** - Creates clean Excel files the parser loves
3. **Faster generation** - No AI fallback needed during mockup generation

## How to Use

### Step 1: Run the Reformatter

```bash
python src/reformatter.py path/to/your/messy_testcase.xlsx
```

Or from Python:
```python
from src.reformatter import TestCaseReformatter

reformatter = TestCaseReformatter()
clean_file = reformatter.reformat_file(
    'data/PSA_MY2026_TestCase.xlsx',
    'data/PSA_MY2026_TestCase_Clean.xlsx'
)
```

### Step 2: Use the Clean File

```python
from main import run_measure_gen_custom

result = run_measure_gen_custom(
    measure_name='PSA',
    testcase_path='data/PSA_MY2026_TestCase_Clean.xlsx',  # Use cleaned file
    vsd_path='path/to/vsd.xlsx'
)
```

## What the Reformatter Does

### Input (Messy Format):
```
| ID | Scenario | Expected |
|----|----------|----------|
| PSA_CE_02 | Member enrolled commercial, age 55-65, PSA test done | Numerator |
```

### Output (Clean Format):
```
| ID | Structured_Enrollment | Product_Line | DOB | Gender | Expected_Compliance |
|----|----------------------|--------------|-----|--------|---------------------|
| PSA_CE_02 | 01/01/MY - 12/31/MY Product=COMM | Commercial | Age 60 | M | {"numerator": true} |
```

## Benefits

| Aspect | Without Reformatter | With Reformatter |
|--------|-------------------|------------------|
| **Parsing** | Regex fails → AI fallback | Regex succeeds immediately |
| **Speed** | Slow (AI on every run) | Fast (no AI needed) |
| **Accuracy** | Variable (AI interpretation) | Consistent (pre-validated) |
| **Debugging** | Hard (data scattered) | Easy (structured format) |

## When to Use

### ✅ Use Reformatter When:
- Test cases are in messy/inconsistent format
- Getting "No enrollment spans found" warnings
- Data is in narrative/paragraph format
- Headers don't match expected patterns
- Multiple formats mixed in one file

### ⏭️ Skip Reformatter When:
- Test cases already in clean, structured format
- Regex parser works without warnings
- Data follows standard column patterns
- No AI fallback warnings appear

## Example Workflow

### Before (Slow):
```
1. Run generation
2. Parser tries regex → fails
3. Falls back to AI (slow!)
4. Extracts data
5. Generates mockup
Total: 30-50 seconds per generation
```

### After (Fast):
```
1. Run reformatter once (one-time cost)
2. Use clean file for all generations
3. Parser uses regex → succeeds
4. No AI fallback needed
5. Generates mockup
Total: 2-6 seconds per generation
```

## Command Reference

### Reformat a single file:
```bash
python src/reformatter.py data/PSA_MY2026_TestCase.xlsx
```

### Reformat with custom output:
```python
from src.reformatter import TestCaseReformatter

reformatter = TestCaseReformatter()
reformatter.reformat_file(
    input_path='data/messy_testcase.xlsx',
    output_path='data/clean_testcase.xlsx'
)
```

### Reformat multiple files:
```python
from src.reformatter import TestCaseReformatter
import glob

reformatter = TestCaseReformatter()

for file in glob.glob('data/*_TestCase.xlsx'):
    print(f"Reformatting {file}...")
    reformatter.reformat_file(file)
```

## Output Structure

The reformatter creates these columns:

- **ID**: Test case identifier
- **Scenario**: Original scenario text (for reference)
- **Structured_Enrollment**: Clean enrollment spans
- **Product_Line**: Medicare/Commercial/Medicaid/Exchange
- **DOB**: Age in "Age X" format
- **Gender**: M/F
- **Expected_Compliance**: JSON of expected results
- **Extracted_Events**: JSON of clinical events
- **Overrides**: JSON of field overrides

## Troubleshooting

### Issue: "AI Extractor initialization failed"
**Solution**: Make sure tinyllama is installed and accessible via Ollama

### Issue: Reformatter is slow
**Expected**: First run is slow (AI processing), but you only do it once

### Issue: Output file has errors
**Solution**: Review the AI-extracted data and manually correct if needed

## Next Steps

1. **Reformat your test cases** using the reformatter
2. **Update your generation scripts** to use the clean files
3. **Enjoy faster generation** without AI fallback warnings!

See `docs/PERFORMANCE_IMPROVEMENTS.md` for more optimization tips.
