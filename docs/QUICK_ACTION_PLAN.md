# 🎯 Quick Action Plan - Top Priority Improvements

## 🔥 CRITICAL (Do First)

### **1. Enhance Visit Code Population** ⏱️ 2-3 hours
**Current Issue:** Visits only have CPT=99213, POS=11. Missing diagnosis codes, HCPCS, varied CPT codes.

**Solution:**
```python
# In src/engine.py - generate_visits()
def generate_visits(self, mem_id, spans=None):
    # For each visit:
    # 1. Get CPT codes from VSD (Outpatient value set)
    # 2. Add diagnosis codes (DIAG_I_1, DIAG_I_2, etc.)
    # 3. Add HCPCS codes if applicable
    # 4. Vary POS based on visit type
```

**Files to modify:**
- `src/engine.py` - `generate_visits()` method

**Testing:**
- Check PSA_VISIT_IN sheet
- Verify CPT, DIAG, HCPCS columns populated

---

### **2. Make Reformatter Truly Universal** ⏱️ 2-3 hours
**Current Issue:** Reformatter uses measure-specific columns (PSA_TEST, HOSPICE) instead of generic EVENT columns.

**Solution:**
```python
# In src/standard_reformatter.py
# Instead of:
scenario['PSA_TEST'] = 1
scenario['HOSPICE'] = 1

# Use:
scenario['EVENT_1_NAME'] = 'PSA Test'
scenario['EVENT_1_VALUE'] = 1
scenario['EVENT_2_NAME'] = 'Hospice'
scenario['EVENT_2_VALUE'] = 1
```

**Files to modify:**
- `src/standard_reformatter.py` - `_parse_row_to_standard()` method
- `src/standard_reformatter.py` - `_get_standard_columns()` method

**Testing:**
- Reformat PSA test case
- Check output has EVENT columns, not PSA_TEST
- Verify standard parser can read it

---

## ⚡ HIGH PRIORITY (Do Next)

### **3. Create Excel Template** ⏱️ 1 hour
**Goal:** Make it easy for users to create standard format test cases.

**Solution:**
1. Create `templates/Standard_TestCase_Template.xlsx`
2. Add sheets:
   - Instructions
   - Template (with headers and example rows)
   - Column Definitions
3. Add data validation where applicable

**Structure:**
```
Sheet 1: Instructions
- How to use this template
- Column descriptions
- Examples

Sheet 2: Test Cases
- Pre-filled headers
- 2-3 example rows
- Empty rows for user data

Sheet 3: Reference
- Column definitions
- Valid values
- Examples
```

---

### **4. Add Format Validator** ⏱️ 1-2 hours
**Goal:** Validate test case files before generation.

**Solution:**
```python
# Create src/format_validator.py
class FormatValidator:
    def validate(self, file_path):
        # Check:
        # 1. Required columns present
        # 2. Data types correct
        # 3. Required fields not empty
        # 4. Dates in valid format
        # 5. Values in valid ranges
        
        # Return:
        # - is_valid: bool
        # - errors: list of error messages
        # - warnings: list of warning messages
```

**Usage:**
```bash
python src/format_validator.py data/testcase.xlsx
```

---

### **5. Add Progress Indicators** ⏱️ 1 hour
**Goal:** Show progress during generation.

**Solution:**
```python
# In main.py - _process_measure()
from tqdm import tqdm

for idx, sc in tqdm(enumerate(scenarios, 1), total=len(scenarios), desc="Processing scenarios"):
    # Generate data
    pass
```

**Install:**
```bash
pip install tqdm
```

---

## 🎯 QUICK WINS (< 1 hour each)

### **6. Add Output Versioning** ⏱️ 30 min
```python
# In main.py
from datetime import datetime
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_file = f'output/{measure}_MY{year}_Mockup_{timestamp}.xlsx'
```

### **7. Add Multi-Measure Support** ⏱️ 1 hour
```python
# In main.py
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--measures', default='PSA', help='Comma-separated measures')
    args = parser.parse_args()
    
    measures = args.measures.split(',')
    for measure in measures:
        run_measure_gen(measure.strip())
```

**Usage:**
```bash
python main.py --measures PSA,WCC,IMA
```

---

## 📋 Implementation Checklist

### **Week 1: Critical Fixes**
- [ ] Enhance visit code population
- [ ] Make reformatter truly universal
- [ ] Test with PSA measure
- [ ] Test with WCC measure
- [ ] Commit and push

### **Week 2: Usability**
- [ ] Create Excel template
- [ ] Add format validator
- [ ] Add progress indicators
- [ ] Add output versioning
- [ ] Add multi-measure support
- [ ] Commit and push

### **Week 3: Polish**
- [ ] Add error recovery
- [ ] Add performance profiling
- [ ] Update documentation
- [ ] Create video tutorial
- [ ] Final testing

---

## 🚀 Getting Started

### **Option 1: Start with Visit Codes** (Recommended)
This has the highest impact on data quality.

```bash
# 1. Open src/engine.py
# 2. Find generate_visits() method (line ~190)
# 3. Enhance to add:
#    - Multiple CPT codes from VSD
#    - Diagnosis codes
#    - HCPCS codes
# 4. Test with PSA measure
```

### **Option 2: Start with Template**
This has the highest impact on usability.

```bash
# 1. Create templates/ folder
# 2. Create Standard_TestCase_Template.xlsx
# 3. Add instructions, headers, examples
# 4. Test by creating a new test case
```

### **Option 3: Start with Quick Wins**
Get multiple small improvements done quickly.

```bash
# 1. Add output versioning (30 min)
# 2. Add multi-measure support (1 hour)
# 3. Add progress indicators (1 hour)
# Total: 2.5 hours, 3 improvements!
```

---

## 💡 Recommended Order

1. **Visit Code Population** (2-3 hours) - Highest impact on quality
2. **Excel Template** (1 hour) - Highest impact on usability
3. **Quick Wins** (2.5 hours) - Multiple small improvements
4. **Format Validator** (1-2 hours) - Prevents errors
5. **Universal Reformatter** (2-3 hours) - Completes the vision

**Total Time:** 8.5-11.5 hours
**Impact:** Transforms system from good to excellent!

---

## ✅ Success Metrics

After these improvements:
- ✅ Visit data is complete and realistic
- ✅ Users can easily create test cases
- ✅ System provides feedback during generation
- ✅ Multiple measures can be generated at once
- ✅ Output files are versioned
- ✅ Format is validated before generation
- ✅ System is truly universal

**Result:** 10/10 production-ready system! 🎉

---

**Status:** Ready to implement! Pick your starting point and go! 🚀
