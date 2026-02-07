# NCQA PDF Parser - Test & Demo

## Usage

### Command Line
```bash
python src/ncqa_parser.py path/to/PSA_Specification.pdf
```

### Web UI
1. Navigate to http://localhost:5000
2. Select measure (PSA/WCC/IMA)
3. Upload NCQA PDF in "NCQA Specification PDF" field
4. System auto-generates config/{MEASURE}.yaml
5. Review and edit the generated config
6. Upload test case and generate mockup!

## Example Output

### Input: PSA_HEDIS_MY2026_Spec.pdf

### Generated: config/PSA.yaml
```yaml
measure_name: PSA
description: PSA HEDIS Measure (Auto-generated from PDF)
rules:
  age_range: [66, 100]
  age_as_of: December 31
  anchor_date_type: calendar_end
  continuous_enrollment:
    period_months: 12
    allowable_gap_days: 45
    no_gap_on_last_day: true
  initial_population:
    - event: Outpatient Visit
      value_set_names:
        - Outpatient
      table: PSA_VISIT_IN
  exclusions:
    - name: Hospice
      value_set_names:
        - Hospice Encounter
        - Hospice Intervention
    - name: Death
      criteria: Death during measurement period
  clinical_events:
    numerator_components:
      - name: PSA Test
        value_set_names:
          - PSA Lab Test
        table: PSA_LAB_IN
```

## What Gets Extracted

### ✅ Automatically Detected
- Measure name (e.g., PSA, WCC, IMA)
- Age range (e.g., 66-100 years)
- Continuous enrollment period (e.g., 12 months)
- Common exclusions (Hospice, Death)

### ⚠️ Requires Manual Review
- Value set names (may need refinement)
- Numerator components (basic structure generated)
- Table mappings (defaults to {MEASURE}_LAB_IN, etc.)

## Limitations & Future Enhancements

### Current Limitations
1. **Basic Text Extraction**: Uses regex patterns, may miss complex formatting
2. **Generic Numerator**: Creates placeholder numerator components
3. **No AI Integration**: Doesn't use LLM for deep understanding (yet)

### Future Enhancements
1. **AI-Powered Extraction**: Use tinyllama/GPT to understand spec semantics
2. **Table Detection**: Extract value set tables from PDF
3. **Multi-Page Analysis**: Better handling of complex multi-page specs
4. **Validation**: Cross-check extracted rules against VSD

## Troubleshooting

### Issue: "Could not identify measure name"
**Solution:** PDF might use non-standard formatting. Enter measure name manually when prompted.

### Issue: "Age range not found"
**Solution:** Check if PDF uses different terminology. Edit generated config manually.

### Issue: "PyPDF2 extraction failed"
**Solution:** PDF might be scanned/image-based. Try OCR or manual config creation.

## Next Steps

After auto-generation:
1. **Review** `config/{MEASURE}.yaml`
2. **Edit** value set names to match VSD exactly
3. **Add** specific numerator components
4. **Test** with a sample test case
5. **Iterate** based on results

---

**Status:** Implemented (Basic Version)  
**Next Enhancement:** AI-powered semantic extraction
