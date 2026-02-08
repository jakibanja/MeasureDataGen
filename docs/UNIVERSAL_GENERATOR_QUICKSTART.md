# 🚀 Universal HEDIS Mockup Generator - Quickstart

The system has been upgraded to a **Universal Paradigm**. You can now generate mockup data for ANY HEDIS measure without needing to write custom code or complex configurations for each one.

## 🌟 Key Features
1.  **Universal Parser**: Uses `StandardFormatParser` to read a single, consistent Excel format for all measures.
2.  **Dynamic Schema**: Automatically prefixes table names (e.g., `PSA_`, `WCC_`, `Universal_`) based on the measure name.
3.  **Manual Overrides**: Specify exact `EVENT_i_CODE` and `EVENT_i_DATE` in the Excel to bypass random VSD selection.
4.  **Pattern-Based VSD**: Automatically finds appropriate codes for generic needs like "Outpatient," "Office Visit," or "Diagnosis" if no specific code is provided.
5.  **Smart Defaults**: Unknown clinical events automatically default to a `visit` or `emr` record based on their name.

---

## 🛠️ How to Generate Data for a New Measure (e.g., "COL")

### 1. Create a Minimal Config
Create `config/COL.yaml`:
```yaml
measure_name: COL
description: Colorectal Cancer Screening
rules:
  age_range: [45, 75]
  age_as_of: "December 31"
  anchor_date_type: "calendar_end"
  
  continuous_enrollment:
    period_months: 12
    allowable_gap_days: 45
    no_gap_on_last_day: true

  initial_population:
    - event: "Outpatient Visit"
      table: "visit" # Logical key

  exclusions:
    - name: "Hospice" # Optional: add standard exclusions

  clinical_events:
    numerator_components:
      - name: "Fecal Occult Blood Test"
        table: "lab"
```

### 2. Prepare your Test Case
Use `data/Universal_STANDARD.xlsx` as a template. Add rows for your members. Specify names, dates, and codes as needed.

### 3. Run Generation
```bash
python main.py COL
```
Or use the Web UI!

---

## 📈 Technical Details
- **Schema Mapping**: `config/schema_map.yaml` uses `{MEASURE}` placeholders.
- **VSD Logic**: `src/vsd.py` supports `get_random_code_from_pattern(pattern)`.
- **System Parser**: `src/standard_parser.py` captures all generic columns.
- **Engine Logic**: `src/engine.py` prioritizes Excel overrides over VSD lookups.
