# HEDIS Mockup Generator - Complete Documentation

## 📋 Table of Contents
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Components](#components)
4. [Usage Guide](#usage-guide)
5. [Future Enhancements](#future-enhancements)
6. [Technical Specifications](#technical-specifications)

---

## 🎯 System Overview

The **HEDIS Mockup Generator** is an AI-powered data generation system that creates NCQA-compliant test data for HEDIS measures. It combines regex-based parsing with AI fallback to handle both structured and messy test case formats.

### Key Features
- ✅ **Hybrid Parsing**: Fast regex + AI fallback for edge cases
- ✅ **Multi-Measure Support**: PSA, WCC, IMA (extensible)
- ✅ **Auto-Reformatting**: AI-powered test case cleanup
- ✅ **Web UI**: Beautiful, user-friendly interface
- ✅ **VSD Integration**: Dynamic code pulling from Value Set Directory
- ✅ **Schema Automation**: Auto-generate configs for new measures

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Web UI (Flask)                         │
│  - File Upload (Test Cases, VSD)                           │
│  - Auto-Reformat Checkbox                                  │
│  - Progress Tracking                                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Main Processing Engine                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ TestCase     │  │   Mockup     │  │     VSD      │     │
│  │   Parser     │→ │   Engine     │← │   Manager    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         ↓                  ↓                                │
│  ┌──────────────┐  ┌──────────────┐                       │
│  │ AI Extractor │  │   Schema     │                       │
│  │ (tinyllama)  │  │   Mapper     │                       │
│  └──────────────┘  └──────────────┘                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Output Generation                        │
│  - Excel Files (Multi-sheet)                               │
│  - Schema-compliant tables                                 │
│  - MEMBER_IN, ENROLLMENT_IN, VISIT_IN, LAB_IN, etc.       │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧩 Components

### 1. **Core Modules**

#### `src/parser.py` - TestCaseParser
**Purpose:** Extracts scenarios from Excel test case files.

**Key Features:**
- Regex-based parsing for structured data
- AI fallback for complex/messy scenarios
- Handles enrollment spans, product lines, clinical events
- Supports overrides and exclusions

**Example Usage:**
```python
from src.parser import TestCaseParser
from src.ai_extractor import AIScenarioExtractor

extractor = AIScenarioExtractor(model_name="tinyllama")
parser = TestCaseParser("data/PSA_MY2026_TestCase.xlsx", extractor=extractor)
scenarios = parser.parse_scenarios(measure_config)
```

---

#### `src/engine.py` - MockupEngine
**Purpose:** Generates HEDIS-compliant data records.

**Key Methods:**
- `generate_member_base()` - Creates member demographics
- `generate_enrollments()` - Creates enrollment spans
- `generate_clinical_event()` - Creates visits, labs, procedures
- `generate_exclusion()` - Creates exclusion events

**Example:**
```python
from src.engine import MockupEngine

engine = MockupEngine("config/PSA.yaml", "config/schema_map.yaml", vsd_manager)
member_row = engine.generate_member_base("PSA_001", age=70, gender="M")
enrollment_rows = engine.generate_enrollments("PSA_001", "Medicare")
```

---

#### `src/vsd.py` - VSDManager
**Purpose:** Manages Value Set Directory for clinical codes.

**Key Features:**
- Loads VSD Excel file
- Retrieves random codes by value set name
- Caches codes for performance

**Example:**
```python
from src.vsd import VSDManager

vsd = VSDManager("data/HEDIS_MY2026_VSD.xlsx")
psa_code = vsd.get_random_code("PSA Lab Test")  # Returns: "84152"
```

---

#### `src/ai_extractor.py` - AIScenarioExtractor
**Purpose:** AI-powered fallback for complex test case parsing.

**Model:** tinyllama (local LLM via Ollama)

**Extracts:**
- Enrollment spans
- Product lines
- Clinical events
- Expected results
- Exclusions

**Example:**
```python
from src.ai_extractor import AIScenarioExtractor

extractor = AIScenarioExtractor(model_name="tinyllama")
result = extractor.extract_scenario_info({
    'id': 'PSA_001',
    'scenario': 'Member enrolled in Medicare from Jan 1 to Dec 31, 2026...',
    'expected': 'Compliant'
})
# Returns: {'enrollment_spans': [...], 'product_line': 'Medicare', ...}
```

---

### 2. **Automation Tools**

#### `src/measure_automator.py`
**Purpose:** Auto-generates schema and config for new measures.

**Usage:**
```bash
python src/measure_automator.py IMA
```

**Output:**
- Updates `data_columns_info.json` with IMA tables
- Creates `config/IMA.yaml` (draft config)

---

#### `src/reformatter.py`
**Purpose:** Cleans and standardizes messy test case files.

**Usage:**
```bash
python src/reformatter.py data/Messy_TestCase.xlsx
```

**Output:**
- `data/Messy_TestCase_Cleaned.xlsx`
- Structured columns: ID, Scenario, Structured_Enrollment, Product_Line, etc.

---

### 3. **Web Application**

#### `app.py` - Flask Server
**Endpoints:**
- `GET /` - Main UI
- `POST /` - Handle uploads and generation

**Features:**
- File upload (test cases, VSD)
- Auto-reformat checkbox
- Flash messages for user feedback
- File download

**Run:**
```bash
python app.py
# Navigate to: http://localhost:5000
```

---

#### `templates/index.html` - UI Template
**Features:**
- Modern gradient design
- File upload forms
- Auto-reformat checkbox
- Loading overlay with progress tracking
- Real-time status updates (simulated)

---

## 📖 Usage Guide

### Quick Start

1. **Start the Web UI:**
```bash
python app.py
```

2. **Open Browser:**
Navigate to `http://localhost:5000`

3. **Generate Mockup:**
   - Select measure (PSA/WCC/IMA)
   - Upload test case Excel file
   - ✅ Check "Auto-reformat" if data is messy
   - Click "Generate Mockup"
   - Download the result

---

### Command-Line Usage

#### Generate PSA Mockup
```bash
python main.py
```

#### Add New Measure (IMA)
```bash
# 1. Auto-generate schema
python src/measure_automator.py IMA

# 2. Edit config/IMA.yaml (update rules)

# 3. Add to main.py
# Change: for m in ['PSA']:
# To:     for m in ['PSA', 'IMA']:

# 4. Run
python main.py
```

#### Reformat Messy Test Case
```bash
python src/reformatter.py data/Messy_TestCase.xlsx
# Output: data/Messy_TestCase_Cleaned.xlsx
```

---

## 🚀 Future Enhancements

### Priority 0 (Critical)

#### 1. **NCQA PDF Parser**
**Goal:** Auto-extract measure rules from NCQA specification PDFs.

**Implementation:**
- Use PyPDF2 or pdfplumber to extract text
- AI (tinyllama) to identify:
  - Denominator criteria
  - Numerator components
  - Exclusions
  - Value set names
- Auto-generate `config/{MEASURE}.yaml`

**Benefit:** No manual config writing!

**Example Workflow:**
```
Upload: PSA_HEDIS_MY2026_Spec.pdf
↓
AI reads: "Denominator: Men age 66-100..."
↓
Generates: config/PSA.yaml with age_range: [66, 100]
```

---

#### 2. **Expected Results Validator**
**Goal:** Verify generated data matches test case expectations.

**Implementation:**
- After generation, run HEDIS logic
- Compare: "Test case says compliant" vs "Data is compliant"
- Generate validation report

**Example Output:**
```
✅ PSA_001: Expected Compliant → Generated data IS compliant
❌ PSA_002: Expected Non-Compliant → Generated data IS compliant (MISMATCH!)
```

---

### Priority 1 (Important)

#### 3. **VSD Date Validation**
- Filter codes by effective/expiration dates
- Warn if using deprecated codes

#### 4. **Data Quality Checks**
- Validate no duplicate member IDs
- Check date logic (enrollment end > start)
- Ensure required fields are populated

---

### Priority 2 (Nice to Have)

#### 5. **Download Format Options**
- CSV export
- SQL INSERT statements
- Schema DDL generation

#### 6. **Batch Processing**
- Upload multiple test cases
- Generate all measures at once
- Zip outputs

#### 7. **Audit Trail**
- Log generation metadata
- Export summary reports

---

## 🔧 Technical Specifications

### System Requirements
- **Python:** 3.11+
- **OS:** Windows (tested), Linux/Mac (should work)
- **RAM:** 4GB minimum (8GB recommended for AI)
- **Disk:** 2GB for Ollama models

### Dependencies
```
pandas>=2.0.0
openpyxl>=3.1.0
pyyaml>=6.0
ollama>=0.1.0
flask>=3.0.0
```

### File Structure
```
MeasMockD/
├── app.py                    # Flask web server
├── main.py                   # CLI entry point
├── src/
│   ├── parser.py            # Test case parser
│   ├── engine.py            # Mockup generator
│   ├── vsd.py               # VSD manager
│   ├── ai_extractor.py      # AI fallback
│   ├── measure_automator.py # Measure automation
│   └── reformatter.py       # Test case cleaner
├── config/
│   ├── PSA.yaml             # PSA measure config
│   ├── IMA.yaml             # IMA measure config
│   └── schema_map.yaml      # Table mappings
├── data/
│   ├── PSA_MY2026_TestCase.xlsx
│   └── data_columns_info.json
├── templates/
│   └── index.html           # Web UI
├── output/                  # Generated mockups
└── data_uploads/            # User uploads
```

### Configuration Files

#### `config/{MEASURE}.yaml`
Defines measure-specific rules:
```yaml
measure_name: PSA
rules:
  age_range: [66, 100]
  continuous_enrollment:
    period_months: 12
    allowable_gap_days: 45
  clinical_events:
    numerator_components:
      - name: PSA Test
        value_set_names:
          - PSA Lab Test
        table: PSA_LAB_IN
  exclusions:
    - name: Hospice
      value_set_names:
        - Hospice Encounter
```

#### `data_columns_info.json`
Defines table schemas:
```json
{
  "PSA_MEMBER_IN": ["MEM_NBR", "DOB", "GENDER", ...],
  "PSA_ENROLLMENT_IN": ["MEM_NBR", "ENR_START", "ENR_END", ...]
}
```

---

## 📊 Performance Benchmarks

### Parsing Speed
- **Regex Mode:** ~0.05s per test case
- **AI Fallback:** ~15s per test case (CPU)

### Expected Runtime (500 Test Cases)
- **All Regex:** ~30 seconds
- **50% AI Fallback:** ~6 minutes
- **100% AI Fallback:** ~2 hours

### Optimization Tips
1. Use auto-reformat to clean data upfront
2. Ensure test cases follow structured format
3. Run on GPU for faster AI inference (future)

---

## 🐛 Troubleshooting

### Issue: "AI Extractor initialization failed"
**Cause:** Ollama not running or model not installed.

**Fix:**
```bash
ollama pull tinyllama
ollama serve
```

---

### Issue: "VSD file not found"
**Cause:** Hardcoded path in `main.py` or `app.py`.

**Fix:** Update `DEFAULT_VSD` path or upload via UI.

---

### Issue: "Config file not found"
**Cause:** Measure config doesn't exist.

**Fix:**
```bash
python src/measure_automator.py <MEASURE_NAME>
# Then edit config/<MEASURE_NAME>.yaml
```

---

## 📝 License & Credits

**Author:** AI-Assisted Development  
**Version:** 1.0  
**Last Updated:** 2026-02-07

---

## 🤝 Contributing

To add a new measure:
1. Run `measure_automator.py`
2. Edit generated config
3. Add test case file
4. Update `main.py`
5. Test and validate

---

**End of Documentation**
