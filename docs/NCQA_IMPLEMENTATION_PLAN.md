# 🏗️ NCQA Integration - Detailed Implementation Plan

## 📋 Overview

NCQA integration will add **validation and compliance** at multiple points in the workflow.

---

## 🔄 Current Flow (No NCQA Validation)

```
User uploads test case
    ↓
Parser reads test case
    ↓
Engine generates data (using manual config/PSA.yaml)
    ↓
Output Excel file
```

**Problem:** No guarantee config matches NCQA spec!

---

## 🎯 New Flow (With NCQA Integration)

```
User uploads test case
    ↓
[NEW] NCQA Validator checks config
    ↓
Parser reads test case
    ↓
Engine generates data
    ↓
[NEW] NCQA Compliance Checker validates output
    ↓
Output Excel file + Compliance Report
```

---

## 📁 File Structure & Logic Placement

### **1. New Files to Create:**

```
src/
├── ncqa_parser.py          ✅ EXISTS (needs enhancement)
├── ncqa_validator.py       ❌ NEW - Config validation
└── ncqa_compliance.py      ❌ NEW - Output compliance checking

docs/
└── ncqa_specs/             ❌ NEW - NCQA PDF storage
    ├── README.md
    ├── PSA_MY2026_Spec.pdf
    ├── WCC_MY2026_Spec.pdf
    └── IMA_MY2026_Spec.pdf

scripts/
└── validate_config.py      ❌ NEW - Standalone validator
```

---

## 🔧 Implementation Details

### **Component 1: NCQA Validator** (`src/ncqa_validator.py`)

**Purpose:** Validate config YAML against NCQA PDF spec

**Location:** `src/ncqa_validator.py` (NEW FILE)

**Logic:**
```python
class NCQAValidator:
    def __init__(self, ncqa_pdf_path):
        self.pdf_path = ncqa_pdf_path
        self.spec_parser = NCQASpecParser(ncqa_pdf_path)
        
    def validate_config(self, config_path):
        """
        Compare config/PSA.yaml against NCQA spec
        
        Checks:
        1. Age range matches
        2. Enrollment requirements match
        3. Value sets exist
        4. Exclusions match
        
        Returns:
        - is_valid: bool
        - errors: list of critical issues
        - warnings: list of non-critical issues
        """
        # Extract spec from PDF
        spec = self.spec_parser.generate_config()
        
        # Load config
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        errors = []
        warnings = []
        
        # Check age range
        if config['rules']['age_range'] != spec['rules']['age_range']:
            errors.append(f"Age range mismatch: {config} vs {spec}")
        
        # Check enrollment
        if config['rules']['continuous_enrollment']['period_months'] != spec['rules']['continuous_enrollment']['period_months']:
            errors.append("Enrollment period mismatch")
        
        # Check value sets exist
        for component in config['rules']['clinical_events']['numerator_components']:
            for vs_name in component.get('value_set_names', []):
                if not self._value_set_exists(vs_name):
                    warnings.append(f"Value set not found: {vs_name}")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
```

**Integration Points:**
1. **main.py** - Before generation
2. **app.py** - When user uploads config
3. **scripts/validate_config.py** - Standalone tool

---

### **Component 2: NCQA Compliance Checker** (`src/ncqa_compliance.py`)

**Purpose:** Validate generated output against NCQA requirements

**Location:** `src/ncqa_compliance.py` (NEW FILE)

**Logic:**
```python
class NCQAComplianceChecker:
    def __init__(self, measure_config, ncqa_pdf_path=None):
        self.config = measure_config
        self.ncqa_pdf = ncqa_pdf_path
        
    def check_compliance(self, output_data):
        """
        Validate generated mockup data
        
        Checks:
        1. Age distribution matches denominator
        2. Enrollment periods meet requirements
        3. Clinical events match numerator
        4. Exclusions properly applied
        5. Data types correct
        
        Returns:
        - compliance_score: 0-100
        - issues: list of compliance issues
        - report: detailed compliance report
        """
        issues = []
        
        # Check age distribution
        member_df = output_data['MEMBER_IN']
        ages = member_df['AGE'].values
        
        min_age, max_age = self.config['rules']['age_range']
        if ages.min() < min_age or ages.max() > max_age:
            issues.append(f"Age out of range: {ages.min()}-{ages.max()} vs {min_age}-{max_age}")
        
        # Check enrollment
        enrollment_df = output_data['ENROLLMENT_IN']
        # Validate continuous enrollment logic
        
        # Check clinical events
        # Validate numerator components
        
        # Calculate compliance score
        compliance_score = 100 - (len(issues) * 5)  # -5 points per issue
        
        return {
            'score': max(0, compliance_score),
            'issues': issues,
            'passed': compliance_score >= 80
        }
```

**Integration Points:**
1. **main.py** - After generation, before saving
2. **app.py** - Show compliance report in UI

---

### **Component 3: Enhanced NCQA Parser** (`src/ncqa_parser.py`)

**Purpose:** Better PDF extraction and rule detection

**Location:** `src/ncqa_parser.py` (ENHANCE EXISTING)

**Enhancements:**
```python
class NCQASpecParser:
    # EXISTING CODE...
    
    # NEW: Better value set extraction
    def extract_value_sets_detailed(self):
        """
        Extract value sets with more context
        - Value set name
        - Purpose (numerator/denominator/exclusion)
        - Required vs optional
        """
        pass
    
    # NEW: Extract stratifications
    def extract_stratifications(self):
        """
        Extract age groups, product lines, etc.
        """
        pass
    
    # NEW: Extract rate calculations
    def extract_rate_calculation(self):
        """
        Extract how rate is calculated
        """
        pass
```

---

## 🔗 Integration Points

### **1. main.py Integration**

**Where:** After loading config, before generation

```python
# main.py - Line ~50 (after loading config)

def run_measure_gen_custom(measure_name, testcase_path, vsd_path, 
                           skip_quality_check=False, disable_ai=None,
                           validate_ncqa=True):  # NEW PARAMETER
    
    # ... existing code ...
    
    # NEW: NCQA Validation
    if validate_ncqa:
        ncqa_pdf = f'docs/ncqa_specs/{measure_name}_MY2026_Spec.pdf'
        if os.path.exists(ncqa_pdf):
            print("🔍 Validating config against NCQA spec...")
            from src.ncqa_validator import NCQAValidator
            
            validator = NCQAValidator(ncqa_pdf)
            validation = validator.validate_config(config_path)
            
            if not validation['is_valid']:
                print("❌ Config validation failed:")
                for error in validation['errors']:
                    print(f"   - {error}")
                
                if not skip_quality_check:
                    raise ValueError("Config does not match NCQA spec")
            
            if validation['warnings']:
                print("⚠️  Warnings:")
                for warning in validation['warnings']:
                    print(f"   - {warning}")
        else:
            print(f"⚠️  NCQA spec not found: {ncqa_pdf}")
            print("   Skipping NCQA validation")
    
    # ... existing generation code ...
    
    # NEW: Compliance Check (after generation)
    if validate_ncqa and not skip_quality_check:
        print("🔍 Checking NCQA compliance...")
        from src.ncqa_compliance import NCQAComplianceChecker
        
        checker = NCQAComplianceChecker(measure_config, ncqa_pdf)
        compliance = checker.check_compliance(output_data)
        
        print(f"   Compliance Score: {compliance['score']}/100")
        if compliance['issues']:
            print("   Issues found:")
            for issue in compliance['issues']:
                print(f"   - {issue}")
        
        # Save compliance report
        report_path = output_file.replace('.xlsx', '_Compliance_Report.txt')
        with open(report_path, 'w') as f:
            f.write(f"NCQA Compliance Report\n")
            f.write(f"Score: {compliance['score']}/100\n")
            f.write(f"Status: {'PASSED' if compliance['passed'] else 'FAILED'}\n")
            f.write(f"\nIssues:\n")
            for issue in compliance['issues']:
                f.write(f"- {issue}\n")
```

---

### **2. app.py Integration**

**Where:** In the generate action handler

```python
# app.py - Line ~93 (in generate action)

elif action == 'generate':
    # ... existing code ...
    
    # NEW: Check if NCQA validation is requested
    validate_ncqa = request.form.get('validate_ncqa') == 'on'
    
    # Run generation with NCQA validation
    output_file = run_measure_gen_custom(
        measure, 
        tc_path, 
        vsd_path,
        skip_quality_check=skip_quality_check,
        disable_ai=disable_ai,
        validate_ncqa=validate_ncqa  # NEW
    )
    
    # NEW: Show compliance score if validated
    if validate_ncqa:
        compliance_report = output_file.replace('.xlsx', '_Compliance_Report.txt')
        if os.path.exists(compliance_report):
            with open(compliance_report) as f:
                report_content = f.read()
            flash(f"📊 NCQA Compliance: {report_content.split('Score: ')[1].split('/')[0]}/100", "info")
```

---

### **3. Web UI Enhancement**

**Where:** `templates/index.html`

**Add checkbox:**
```html
<!-- In the form, near other checkboxes -->
<div class="form-check">
    <input type="checkbox" class="form-check-input" id="validate_ncqa" name="validate_ncqa" checked>
    <label class="form-check-label" for="validate_ncqa">
        🔍 Validate against NCQA Specification
        <small class="text-muted">(Ensures compliance with official NCQA requirements)</small>
    </label>
</div>
```

---

## 📊 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    NCQA Integration Flow                     │
└─────────────────────────────────────────────────────────────┘

1. STARTUP
   ├─ Load config/PSA.yaml
   ├─ Check docs/ncqa_specs/PSA_MY2026_Spec.pdf exists
   └─ [NEW] NCQAValidator.validate_config()
       ├─ Extract rules from PDF
       ├─ Compare with config
       └─ Report errors/warnings

2. GENERATION
   ├─ TestCaseParser reads test case
   ├─ MockupEngine generates data
   └─ (existing flow continues)

3. POST-GENERATION
   └─ [NEW] NCQAComplianceChecker.check_compliance()
       ├─ Validate age distribution
       ├─ Validate enrollment periods
       ├─ Validate clinical events
       ├─ Calculate compliance score
       └─ Generate compliance report

4. OUTPUT
   ├─ PSA_MY2026_Mockup.xlsx (existing)
   └─ PSA_MY2026_Mockup_Compliance_Report.txt (NEW)
```

---

## 🎯 Implementation Phases

### **Phase 1: Foundation** (2-3 hours)

**Files to create:**
1. `src/ncqa_validator.py` - Config validation
2. `docs/ncqa_specs/README.md` - Instructions to get PDFs
3. `scripts/validate_config.py` - Standalone validator

**Tasks:**
- [ ] Create NCQAValidator class
- [ ] Implement validate_config() method
- [ ] Test with PSA config
- [ ] Add to main.py (optional flag)

---

### **Phase 2: Compliance Checking** (2-3 hours)

**Files to create:**
1. `src/ncqa_compliance.py` - Output validation

**Tasks:**
- [ ] Create NCQAComplianceChecker class
- [ ] Implement check_compliance() method
- [ ] Generate compliance reports
- [ ] Integrate into main.py

---

### **Phase 3: UI Integration** (1-2 hours)

**Files to modify:**
1. `app.py` - Add NCQA validation option
2. `templates/index.html` - Add checkbox

**Tasks:**
- [ ] Add validate_ncqa parameter
- [ ] Show compliance score in UI
- [ ] Display compliance report

---

### **Phase 4: Enhancement** (1-2 hours)

**Files to modify:**
1. `src/ncqa_parser.py` - Better extraction

**Tasks:**
- [ ] Improve value set extraction
- [ ] Add stratification extraction
- [ ] Better error handling

---

## 🧪 Testing Plan

### **Test 1: Config Validation**
```bash
python scripts/validate_config.py config/PSA.yaml docs/ncqa_specs/PSA_MY2026_Spec.pdf
# Should show: ✅ Config valid or ❌ Errors found
```

### **Test 2: Generation with Validation**
```bash
python main.py --measure PSA --validate-ncqa
# Should generate mockup + compliance report
```

### **Test 3: Web UI**
```
1. Upload test case
2. Check "Validate against NCQA" checkbox
3. Generate
4. See compliance score in flash message
```

---

## 📝 Success Criteria

After implementation:
- ✅ Config validated against NCQA spec before generation
- ✅ Output validated for compliance after generation
- ✅ Compliance reports generated
- ✅ Web UI shows compliance score
- ✅ Standalone validator available
- ✅ System score: 9.5/10

---

## 💡 Key Design Decisions

### **1. Optional vs Required**
**Decision:** Make NCQA validation **optional but recommended**
**Reason:** Users might not have NCQA PDFs, but should still be able to generate

### **2. Fail vs Warn**
**Decision:** **Warn** on validation errors, don't fail generation
**Reason:** Config might be intentionally different for testing

### **3. PDF Storage**
**Decision:** **Don't commit PDFs** to git, provide download instructions
**Reason:** Large files, potential copyright issues

### **4. Integration Points**
**Decision:** Integrate at **config load** and **post-generation**
**Reason:** Catch issues early, validate output quality

---

## 🚀 Ready to Implement?

**Estimated Time:** 6-8 hours total
**Complexity:** Medium-High
**Impact:** High - Ensures NCQA compliance

**Start with:** Phase 1 (Foundation) - Config validation
**Then:** Phase 2 (Compliance checking)
**Finally:** Phase 3 & 4 (UI and enhancements)

---

**Should I proceed with Phase 1?** 🎯
