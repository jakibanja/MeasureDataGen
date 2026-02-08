# Universal Test Case Format - Quick Start Guide

## 🎯 Overview

We now have a **universal standard format** that works for ALL HEDIS measures (PSA, WCC, IMA, etc.). No more measure-specific formats!

---

## ✅ What's Ready

### 1. **Standard Format Specification**
- **File:** `docs/STANDARD_TESTCASE_FORMAT.md`
- **Purpose:** Defines the universal column structure
- **Key Features:**
  - Works for ALL measures
  - Generic `EVENT_X_NAME` columns (not PSA_TEST, BMI_PERCENTILE, etc.)
  - Generic `VISIT_X_DATE` columns for multiple visits
  - Generic `ENROLLMENT_X_START/END` for multiple enrollments

### 2. **Standard Reformatter**
- **File:** `src/standard_reformatter.py`
- **Purpose:** Converts messy test cases → standard format
- **Usage:**
  ```bash
  python src/standard_reformatter.py input.xlsx output.xlsx
  ```

---

## 📊 Universal Column Structure

### **Core Columns (Same for ALL measures):**
```
MEMBER_ID, AGE, GENDER, PRODUCT_LINE
```

### **Enrollment Columns (Up to 10):**
```
ENROLLMENT_1_START, ENROLLMENT_1_END, ENROLLMENT_1_PRODUCT_ID
ENROLLMENT_2_START, ENROLLMENT_2_END, ENROLLMENT_2_PRODUCT_ID
...
```

### **Visit Columns (Up to 10):**
```
VISIT_1_DATE, VISIT_1_TYPE, VISIT_1_CPT, VISIT_1_DIAG
VISIT_2_DATE, VISIT_2_TYPE, VISIT_2_CPT, VISIT_2_DIAG
...
```

### **Clinical Event Columns (Up to 10):**
```
EVENT_1_NAME, EVENT_1_VALUE, EVENT_1_DATE, EVENT_1_CODE
EVENT_2_NAME, EVENT_2_VALUE, EVENT_2_DATE, EVENT_2_CODE
...
```

### **Exclusion Columns (Up to 5):**
```
EXCLUSION_1_NAME, EXCLUSION_1_VALUE, EXCLUSION_1_DATE
EXCLUSION_2_NAME, EXCLUSION_2_VALUE, EXCLUSION_2_DATE
...
```

### **Metadata:**
```
EXPECTED_RESULT, SCENARIO_DESCRIPTION
```

---

## 📝 Example: PSA Test Case

```
MEMBER_ID     | AGE | GENDER | PRODUCT_LINE | ENROLLMENT_1_START | ENROLLMENT_1_END | ENROLLMENT_2_START | ENROLLMENT_2_END | VISIT_1_DATE | VISIT_2_DATE | EVENT_1_NAME | EVENT_1_VALUE | EVENT_2_NAME | EVENT_2_VALUE | EXPECTED_RESULT
--------------|-----|--------|--------------|--------------------|--------------------|--------------------|--------------------|--------------|--------------|--------------|---------------|--------------|---------------|----------------
PSA_CE_01     | 70  | M      | Medicare     | 1/1/MY-1           | 12/31/MY           |                    |                    | 2/1/MY       |              | PSA Test     | 1             | Hospice      | 0             | Compliant
PSA_CE_02     | 72  | M      | Medicare     | 1/1/MY-1           | 10/1/MY            | 11/14/MY           | 12/31/MY           | 2/1/MY       |              | PSA Test     | 1             | Hospice      | 0             | Compliant
PSA_MULTI_VIS | 75  | M      | Commercial   | 1/1/MY             | 12/31/MY           |                    |                    | 2/1/MY       | 6/15/MY      | PSA Test     | 1             | Hospice      | 0             | Compliant
```

---

## 📝 Example: WCC Test Case

**Same columns, different events!**

```
MEMBER_ID     | AGE | GENDER | PRODUCT_LINE | ENROLLMENT_1_START | ENROLLMENT_1_END | VISIT_1_DATE | EVENT_1_NAME      | EVENT_1_VALUE | EVENT_2_NAME            | EVENT_2_VALUE | EXPECTED_RESULT
--------------|-----|--------|--------------|--------------------|--------------------|--------------|-------------------|---------------|-------------------------|---------------|----------------
WCC_BMI_01    | 5   | F      | Commercial   | 1/1/MY             | 12/31/MY           | 3/1/MY       | BMI Percentile    | 85            | Nutrition Counseling    | 1             | Compliant
WCC_BMI_02    | 7   | M      | Medicaid     | 1/1/MY             | 12/31/MY           | 4/15/MY      | BMI Percentile    | 92            | Physical Activity       | 1             | Compliant
```

---

## 🔄 Workflow

### **Option 1: Use Reformatter (Recommended)**

If you have a messy test case:

```bash
# Convert messy → standard
python src/standard_reformatter.py data/messy_testcase.xlsx data/standard_testcase.xlsx

# Then use standard file for generation
python main.py --testcase data/standard_testcase.xlsx
```

### **Option 2: Create Standard Format Directly**

1. Open Excel
2. Create columns: `MEMBER_ID`, `AGE`, `GENDER`, `PRODUCT_LINE`, `ENROLLMENT_1_START`, `ENROLLMENT_1_END`, `VISIT_1_DATE`, `EVENT_1_NAME`, `EVENT_1_VALUE`, etc.
3. Fill in data
4. Save as `.xlsx`
5. Use for generation

---

## 🎯 Benefits

### **For Users:**
- ✅ **One format for all measures** - No need to learn different formats
- ✅ **Easy to create** - Clear column structure
- ✅ **Easy to edit** - Just add/remove rows
- ✅ **Portable** - Works across PSA, WCC, IMA, etc.

### **For System:**
- ✅ **Simple parsing** - No regex gymnastics
- ✅ **Fast** - No AI fallback needed
- ✅ **Reliable** - Predictable structure
- ✅ **Maintainable** - Easy to extend

---

## 🚀 Next Steps

### **Immediate:**
1. ✅ Standard format defined
2. ✅ Reformatter created
3. 🔄 **TODO:** Update parser to read standard format
4. 🔄 **TODO:** Test with PSA, WCC, IMA

### **Future:**
1. Create Excel template with headers
2. Add format validator
3. Integrate into web UI
4. Add auto-reformatting option

---

## 💡 Key Insight

**Before:** Each measure had different column names → Complex parser → Slow, error-prone

**After:** Universal columns → Simple parser → Fast, reliable

**Example:**
- PSA: `PSA_TEST` column → Now: `EVENT_1_NAME="PSA Test"`, `EVENT_1_VALUE=1`
- WCC: `BMI_PERCENTILE` column → Now: `EVENT_1_NAME="BMI Percentile"`, `EVENT_1_VALUE=85`
- IMA: `IMMUNIZATION_1` column → Now: `EVENT_1_NAME="DTaP"`, `EVENT_1_VALUE=1`

**Same columns, different values!** 🎉

---

**Status:** ✅ Format and Reformatter ready! Next: Update parser to read standard format.
