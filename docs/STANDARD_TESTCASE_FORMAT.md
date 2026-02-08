# Universal Standard Test Case Format

## 📋 Overview

This document defines the **universal standard format** for ALL HEDIS test case files (PSA, WCC, IMA, etc.). This single format works across all measures, eliminating the need for measure-specific templates.

---

## 🎯 Design Principles

1. **Universal** - One format for all measures (PSA, WCC, IMA, etc.)
2. **One row per member** - Each test case scenario is a single row
3. **Clear column headers** - Standardized, predictable column names
4. **Structured data** - Enrollment, visits, and events in separate columns
5. **No embedded logic** - Avoid complex formulas or concatenated data
6. **Extensible** - Easy to add new clinical events without changing structure

---

## 📊 Universal Column Structure

### **Core Columns (Required for ALL measures):**

| Column Name | Description | Example | Data Type |
|-------------|-------------|---------|-----------|
| `MEMBER_ID` | Unique member identifier | `PSA_CE_01`, `WCC_BMI_01` | Text |
| `AGE` | Member age as of Dec 31 | `70`, `5`, `18` | Integer |
| `GENDER` | Member gender | `M` or `F` | Text |
| `PRODUCT_LINE` | Primary product line | `Medicare`, `Commercial`, `Medicaid` | Text |

### **Enrollment Columns (Universal):**

| Column Name | Description | Example | Format |
|-------------|-------------|---------|--------|
| `ENROLLMENT_1_START` | First enrollment start date | `1/1/2025` or `1/1/MY-1` | Date |
| `ENROLLMENT_1_END` | First enrollment end date | `12/31/2026` or `12/31/MY` | Date |
| `ENROLLMENT_1_PRODUCT_ID` | Product ID for first enrollment | `1` | Integer (optional) |
| `ENROLLMENT_2_START` | Second enrollment start date | `1/1/2026` | Date (optional) |
| `ENROLLMENT_2_END` | Second enrollment end date | `6/30/2026` | Date (optional) |
| `ENROLLMENT_2_PRODUCT_ID` | Product ID for second enrollment | `2` | Integer (optional) |
| ... | Up to 10 enrollment periods | ... | ... |

### **Visit Columns (Universal):**

| Column Name | Description | Example | Format |
|-------------|-------------|---------|--------|
| `VISIT_1_DATE` | First visit date | `2/1/2026` or `2/1/MY` | Date |
| `VISIT_1_TYPE` | Visit type | `Outpatient`, `Inpatient`, `ED` | Text (optional) |
| `VISIT_1_CPT` | CPT code for visit | `99213` | Code (optional) |
| `VISIT_1_DIAG` | Diagnosis code | `Z00.00` | Code (optional) |
| `VISIT_2_DATE` | Second visit date | `6/15/2026` | Date (optional) |
| `VISIT_2_TYPE` | Second visit type | `Outpatient` | Text (optional) |
| ... | Up to 10 visits | ... | ... |

### **Clinical Event Columns (Universal for ALL measures):**

Instead of measure-specific columns (PSA_TEST, BMI_PERCENTILE, etc.), use **generic EVENT columns** that work for any measure:

| Column Name | Description | Example | Format |
|-------------|-------------|---------|--------|
| `EVENT_1_NAME` | Name of clinical event | `PSA Test`, `BMI Percentile`, `Immunization` | Text |
| `EVENT_1_VALUE` | Value/result (1=yes, 0=no, or numeric) | `1`, `85`, `Y` | Text/Number |
| `EVENT_1_DATE` | Event date | `6/1/2026` | Date (optional) |
| `EVENT_1_CODE` | Clinical code (CPT, LOINC, CVX, etc.) | `84153`, `Z68.52` | Code (optional) |
| `EVENT_2_NAME` | Second clinical event | `Hospice`, `Nutrition Counseling` | Text (optional) |
| `EVENT_2_VALUE` | Second event value | `1`, `Y` | Text/Number (optional) |
| `EVENT_2_DATE` | Second event date | `3/15/2026` | Date (optional) |
| ... | Up to 10 clinical events | ... | ... |

**Examples for different measures:**

**PSA Measure:**
- `EVENT_1_NAME` = `PSA Test`, `EVENT_1_VALUE` = `1`, `EVENT_1_DATE` = `6/1/MY`
- `EVENT_2_NAME` = `Hospice`, `EVENT_2_VALUE` = `1`
- `EVENT_3_NAME` = `Prostate Cancer`, `EVENT_3_VALUE` = `0`

**WCC Measure:**
- `EVENT_1_NAME` = `BMI Percentile`, `EVENT_1_VALUE` = `85`
- `EVENT_2_NAME` = `Nutrition Counseling`, `EVENT_2_VALUE` = `1`, `EVENT_2_DATE` = `3/1/MY`
- `EVENT_3_NAME` = `Physical Activity Counseling`, `EVENT_3_VALUE` = `1`

**IMA Measure:**
- `EVENT_1_NAME` = `DTaP Immunization`, `EVENT_1_VALUE` = `1`, `EVENT_1_CODE` = `90700`
- `EVENT_2_NAME` = `IPV Immunization`, `EVENT_2_VALUE` = `1`, `EVENT_2_CODE` = `90713`

### **Exclusion Columns (Universal):**

| Column Name | Description | Example | Format |
|-------------|-------------|---------|--------|
| `EXCLUSION_1_NAME` | Name of exclusion | `Hospice`, `Pregnancy`, `Deceased` | Text |
| `EXCLUSION_1_VALUE` | Exclusion present (1=yes, 0=no) | `1`, `Y` | Text/Number |
| `EXCLUSION_1_DATE` | Exclusion date | `3/15/2026` | Date (optional) |
| `EXCLUSION_2_NAME` | Second exclusion | `Prostate Cancer` | Text (optional) |
| `EXCLUSION_2_VALUE` | Second exclusion value | `1` | Text/Number (optional) |
| ... | Up to 5 exclusions | ... | ... |

### **Optional Metadata Columns:**

| Column Name | Description | Example |
|-------------|-------------|---------|
| `SCENARIO_DESCRIPTION` | Human-readable description | `Member with PSA test in MY` |
| `EXPECTED_RESULT` | Expected compliance result | `Compliant`, `Not Compliant`, `Excluded` |
| `TEST_OBJECTIVE` | What this test case validates | `Verify PSA test detection` |

---

## 📝 Example: Standard Format

```
MEMBER_ID          | AGE | GENDER | PRODUCT_LINE | ENROLLMENT_1_START | ENROLLMENT_1_END | ENROLLMENT_2_START | ENROLLMENT_2_END | VISIT_1_DATE | VISIT_2_DATE | PSA_TEST | HOSPICE | EXPECTED_RESULT
-------------------|-----|--------|--------------|--------------------|--------------------|--------------------|--------------------|--------------|--------------|----------|---------|----------------
PSA_CE_01          | 70  | M      | Medicare     | 1/1/MY-1           | 12/31/MY           |                    |                    | 2/1/MY       |              | 1        | 0       | Compliant
PSA_CE_02          | 72  | M      | Medicare     | 1/1/MY-1           | 10/1/MY            | 11/14/MY           | 12/31/MY           | 2/1/MY       |              | 1        | 0       | Compliant
PSA_HOSPICE_01     | 68  | M      | Medicare     | 1/1/MY             | 12/31/MY           |                    |                    | 2/1/MY       |              | 1        | 1       | Excluded
PSA_MULTI_VISIT_01 | 75  | M      | Commercial   | 1/1/MY             | 12/31/MY           |                    |                    | 2/1/MY       | 6/15/MY      | 1        | 0       | Compliant
```

---

## 🔄 Converting Existing Test Cases

### **Common Messy Formats:**

1. **Concatenated data in single cell:**
   - `"1/1/MY-1 TO 10/1/MY, 11/14/MY TO 12/31/MY"` 
   - Should become: `ENROLLMENT_1_START=1/1/MY-1`, `ENROLLMENT_1_END=10/1/MY`, `ENROLLMENT_2_START=11/14/MY`, `ENROLLMENT_2_END=12/31/MY`

2. **Embedded logic:**
   - `"Product_ID=1, CE=1, AD=1; Product_ID=2, CE=1, AD=0"`
   - Should become: `VISIT_1_DATE=...`, `PSA_TEST=1`, `VISIT_2_DATE=...`

3. **Inconsistent headers:**
   - `"MEM_NBR"`, `"Member ID"`, `"#TC"`, `"Test Case ID"`
   - Should all become: `MEMBER_ID`

4. **Multiple sheets:**
   - Different aspects in different sheets
   - Should be consolidated into single sheet with all columns

### **Reformatter Tool:**

Use the `TestCaseReformatter` to convert messy test cases:

```python
from src.reformatter import TestCaseReformatter

reformatter = TestCaseReformatter()
reformatter.reformat_to_standard(
    input_file='messy_testcase.xlsx',
    output_file='standard_testcase.xlsx',
    measure='PSA'
)
```

---

## 🎯 Benefits of Standard Format

### **For Users:**
- ✅ **Easy to create** - Clear column structure
- ✅ **Easy to edit** - No complex formulas
- ✅ **Easy to validate** - Can spot errors quickly
- ✅ **Portable** - Works across different measures

### **For System:**
- ✅ **Simple parsing** - No regex gymnastics
- ✅ **Reliable** - Predictable data structure
- ✅ **Fast** - No AI fallback needed
- ✅ **Maintainable** - Easy to add new fields

### **For Quality:**
- ✅ **Accurate** - Less room for interpretation
- ✅ **Complete** - All data explicitly defined
- ✅ **Traceable** - Clear mapping to output
- ✅ **Testable** - Easy to verify correctness

---

## 📐 Measure-Specific Extensions

### **PSA Measure:**
```
Required: MEMBER_ID, AGE, GENDER, PRODUCT_LINE, ENROLLMENT_1_START, ENROLLMENT_1_END, VISIT_1_DATE, PSA_TEST
Optional: HOSPICE, PROSTATE_CANCER, DECEASED
```

### **WCC Measure:**
```
Required: MEMBER_ID, AGE, GENDER, PRODUCT_LINE, ENROLLMENT_1_START, ENROLLMENT_1_END, VISIT_1_DATE, BMI_PERCENTILE
Optional: NUTRITION_COUNSELING, PHYSICAL_ACTIVITY_COUNSELING
```

### **IMA Measure:**
```
Required: MEMBER_ID, AGE, GENDER, PRODUCT_LINE, ENROLLMENT_1_START, ENROLLMENT_1_END, IMMUNIZATION_1, IMMUNIZATION_2
Optional: IMMUNIZATION_3, IMMUNIZATION_4
```

---

## 🛠️ Implementation Plan

### **Phase 1: Define Standard (DONE)**
- ✅ Document standard format
- ✅ Create example templates

### **Phase 2: Enhance Reformatter**
- 🔄 Update `TestCaseReformatter` to output standard format
- 🔄 Add validation for standard format
- 🔄 Support multiple input formats

### **Phase 3: Update Parser**
- 🔄 Simplify parser to only handle standard format
- 🔄 Add strict validation
- 🔄 Remove complex regex patterns

### **Phase 4: User Tools**
- 🔄 Create Excel template files
- 🔄 Add format validator
- 🔄 Provide conversion examples

---

## 📚 Next Steps

1. **Create standard template** - Excel file with proper headers
2. **Enhance reformatter** - Convert any format to standard
3. **Update parser** - Simplify to only read standard format
4. **Document workflow** - User guide for creating test cases

---

## 💡 Example Workflow

```
User's Messy Test Case
        ↓
TestCaseReformatter (AI-powered)
        ↓
Standard Format Test Case
        ↓
Simple Parser (regex-only, fast)
        ↓
Mockup Engine
        ↓
Output Data
```

**Key Insight:** Move complexity to the **reformatter** (one-time conversion) instead of the **parser** (runs every time).

---

**Status:** 🎯 Ready to implement!
