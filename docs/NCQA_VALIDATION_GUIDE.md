# 🏥 NCQA Integration & Validation Guide

This guide explains the newly implemented NCQA validation system, which ensures your generated HEDIS mockups are compliant with official specifications, test case scenarios, and Value Set Directories (VSD).

## 🚀 Overview

The system now enforces compliance at three levels:

1.  **Config Validation**: Checks if your measure configuration (YAML) matches NCQA structure.
2.  **Data Compliance**: Validates generated data against NCQA rules (Age, Dates).
3.  **Scenario Fidelity**: Ensures the output matches the *intent* of your Test Case (e.g., Compliant vs. Non-Compliant).
4.  **VSD Verification**: Confirms that every clinical code used exists in the official Value Set Directory.

---

## 🛠️ How to Use

### 1. Web Interface
1.  Go to the main page.
2.  Under **Performance Options**, ensure **"🔍 Validate against NCQA Spec"** is CHECKED.
3.  (Optional) Upload an official NCQA PDF in the "NCQA Specification Converter" section to generate a config file.

### 2. PDF to YAML Conversion
If you have an official NCQA PDF (e.g., `PSA_Spec.pdf`), you can convert it to a rule file:
1.  Upload the PDF in the **"NCQA Specification Converter"** box.
2.  Select the **Measure** (e.g., PSA).
3.  Click **"🔄 Convert PDF to YAML"**.
4.  The system extracts rules (Age range, Continuous Enrollment, etc.) and saves them to `config/ncqa/{MEASURE}_NCQA.yaml`.

### 3. Running Validation Manually
The validation runs automatically during "Generate Mockup". You can see the results in the console output or the generated report:
- `output/{MEASURE}_Compliance_Report.txt`

---

## 🔍 Validation Rules Dictionary

| Check Type | What it Checks | Failure Condition |
| :--- | :--- | :--- |
| **Age** | `MEMBER_IN.AGE` | Member age is outside the limit (e.g., < 50 or > 75 for PSA). |
| **Enrollment** | `ENROLLMENT_IN` | `Start Code` > `End Date` or gaps in continuous enrollment. |
| **Scenario** | `Test Case vs. Output` | Member marked "Compliant" in Test Case has **NO** data in clinical tables. |
| **VSD Codes** | `_CODE` vs `VSD` | Clinical event uses a code that is empty, 'None', or 'MANUAL' when VSD is available. |

---

## ⚠️ Troubleshooting Validation Errors

### "Found X members expected to be compliant but have NO clinical events"
- **Cause:** The Test Case says these members should be compliant, but the generator failed to create a row in the clinical table (e.g., `PSA_TEST`).
- **Fix:** Check `config/{MEASURE}.yaml` to ensure the `clinical_events` rules match the scenario column names.

### "Found invalid/empty code in table X for Value Set Y"
- **Cause:** The VSD Manager exists but couldn't find a code for the requested Value Set.
- **Fix:**
    1. Check if your VSD Excel file is loaded.
    2. Check if the Value Set Name in `config/{MEASURE}.yaml` matches the VSD file exactly.
    3. Update the VSD file with missing codes.

### "Found X members with age outside allowed range"
- **Cause:** The Test Case specified an age (e.g., 45) that violates NCQA rules (e.g., 50-75).
- **Fix:** Update the Test Case ages to be within range, OR update `config/ncqa/{MEASURE}_NCQA.yaml` if the rule is wrong.

---

## 📂 Key Files

- **Logic:** `src/ncqa_compliance.py`
- **Validator:** `src/ncqa_validator.py`
- **Converter:** `scripts/convert_ncqa_pdfs.py`
- **Tests:** `tests/test_ncqa_integration.py`
