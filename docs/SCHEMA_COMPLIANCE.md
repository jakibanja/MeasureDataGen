# Schema Compliance & Data Generation

## 🎯 Critical Principle

**ALL generated data MUST strictly conform to the column schema defined in `data_columns_info.json`.**

This ensures:
- ✅ Output files match database table structures
- ✅ No missing required columns
- ✅ No unexpected extra columns
- ✅ Correct column order

---

## 📋 Schema Definition

### File: `data_columns_info.json`

This file defines the **exact column list** for each table.

**Example:**
```json
{
  "PSA_MEMBER_IN": [
    "MEM_NBR",
    "DOB",
    "GENDER",
    "BEN_HOSPICE",
    "DEATH_DT"
  ],
  "PSA_ENROLLMENT_IN": [
    "MEM_NBR",
    "ENR_START",
    "ENR_END",
    "PRODUCT_ID",
    "FLD00",
    "FLD01",
    ...
    "FLD23"
  ]
}
```

---

## 🔧 How Schema Compliance Works

### Step 1: Data Generation
The `MockupEngine` generates data as **Python dictionaries**:

```python
member_row = {
    "MEM_NBR": "PSA_001",
    "DOB": "1950-01-01",
    "GENDER": "M"
}
```

**Note:** The engine may not populate ALL columns (e.g., `BEN_HOSPICE` might be missing).

---

### Step 2: DataFrame Creation
Convert rows to pandas DataFrame:

```python
df = pd.DataFrame(rows)
```

**Current columns:** `['MEM_NBR', 'DOB', 'GENDER']`  
**Missing:** `BEN_HOSPICE`, `DEATH_DT`

---

### Step 3: Schema Reindexing ✅
**This is the critical step!**

```python
df = df.reindex(columns=full_schema[sheet_name])
```

**What this does:**
1. **Reorders columns** to match schema
2. **Adds missing columns** with `NaN` (null)
3. **Removes extra columns** not in schema

**Result:**
```
MEM_NBR    | DOB        | GENDER | BEN_HOSPICE | DEATH_DT
PSA_001    | 1950-01-01 | M      | NaN         | NaN
```

---

### Step 4: Excel Export
```python
df.to_excel(writer, sheet_name=sheet_name, index=False)
```

**Output:** Perfectly aligned with schema!

---

## 🛡️ Schema Validation

### Current Implementation (in `main.py`)

```python
# Load schema
with open('data_columns_info.json', 'r') as f:
    full_schema = json.load(f)

# For each table
for sheet_name in full_schema.keys():
    if not sheet_name.startswith(f"{measure_name}_"):
        continue
    
    rows = data_store.get(sheet_name, [])
    df = pd.DataFrame(rows)
    
    # ✅ CRITICAL: Reindex to match schema
    df = df.reindex(columns=full_schema[sheet_name])
    
    df.to_excel(writer, sheet_name=sheet_name, index=False)
```

---

## 📊 Example: PSA_ENROLLMENT_IN

### Schema (from `data_columns_info.json`)
```json
"PSA_ENROLLMENT_IN": [
  "MEM_NBR",
  "ENR_START",
  "ENR_END",
  "PRODUCT_ID",
  "FLD00",
  "FLD01",
  "FLD02",
  ...
  "FLD23"
]
```

### Generated Data (from engine)
```python
{
  "MEM_NBR": "PSA_001",
  "ENR_START": "2026-01-01",
  "ENR_END": "2026-12-31",
  "PRODUCT_ID": 2
}
```

### After Reindexing
```
MEM_NBR | ENR_START  | ENR_END    | PRODUCT_ID | FLD00 | FLD01 | ... | FLD23
PSA_001 | 2026-01-01 | 2026-12-31 | 2          | NaN   | NaN   | ... | NaN
```

**All 27 columns present, in correct order!**

---

## 🚨 Common Issues & Solutions

### Issue 1: Column Name Mismatch
**Problem:** Engine generates `MemberID` but schema expects `MEM_NBR`.

**Solution:** Update engine to use exact schema column names:
```python
# ❌ Wrong
row = {"MemberID": mem_id}

# ✅ Correct
row = {target_table['pk']: mem_id}  # Uses schema-defined primary key
```

---

### Issue 2: Missing Required Columns
**Problem:** Schema has 50 columns, engine only populates 10.

**Current Behavior:** ✅ Remaining 40 columns auto-filled with `NaN`.

**Future Enhancement:** Add validation to warn if critical columns are null.

---

### Issue 3: Extra Columns
**Problem:** Engine generates a column not in schema.

**Current Behavior:** ✅ Extra column is automatically removed during reindexing.

**Example:**
```python
# Engine generates
row = {"MEM_NBR": "001", "EXTRA_COL": "value"}

# After reindex (if EXTRA_COL not in schema)
# Result: {"MEM_NBR": "001"}  # EXTRA_COL removed
```

---

## 🔍 Verification

### How to Verify Schema Compliance

1. **Check Column Count:**
```python
expected_cols = len(full_schema["PSA_MEMBER_IN"])
actual_cols = len(df.columns)
assert expected_cols == actual_cols
```

2. **Check Column Names:**
```python
expected = full_schema["PSA_MEMBER_IN"]
actual = df.columns.tolist()
assert expected == actual
```

3. **Check Column Order:**
```python
for i, col in enumerate(full_schema["PSA_MEMBER_IN"]):
    assert df.columns[i] == col
```

---

## 📝 Adding New Columns

### When Schema Changes

If you need to add a new column to a table:

1. **Update `data_columns_info.json`:**
```json
"PSA_MEMBER_IN": [
  "MEM_NBR",
  "DOB",
  "GENDER",
  "NEW_COLUMN",  // ← Add here
  "BEN_HOSPICE",
  "DEATH_DT"
]
```

2. **Update Engine (if needed):**
```python
def generate_member_base(self, mem_id, age, gender, overrides=None):
    row = {
        "MEM_NBR": mem_id,
        "DOB": ...,
        "GENDER": gender,
        "NEW_COLUMN": "default_value",  // ← Add here
        ...
    }
```

3. **Reindex handles the rest automatically!**

---

## 🎯 Best Practices

### 1. Always Use Schema Keys
```python
# ✅ Good
pk_col = target_table['pk']
row[pk_col] = mem_id

# ❌ Bad
row['MEM_NBR'] = mem_id  # Hardcoded
```

### 2. Validate Schema on Startup
```python
def validate_schema(schema_path):
    with open(schema_path) as f:
        schema = json.load(f)
    
    for table, cols in schema.items():
        assert isinstance(cols, list), f"{table} columns must be a list"
        assert len(cols) > 0, f"{table} has no columns"
        assert len(cols) == len(set(cols)), f"{table} has duplicate columns"
```

### 3. Log Schema Mismatches
```python
if set(df.columns) != set(full_schema[sheet_name]):
    print(f"⚠️ Warning: {sheet_name} columns don't match schema")
    print(f"  Missing: {set(full_schema[sheet_name]) - set(df.columns)}")
    print(f"  Extra: {set(df.columns) - set(full_schema[sheet_name])}")
```

---

## 🚀 Future Enhancements

### 1. Schema Validation Tool
Create `src/schema_validator.py`:
```python
def validate_output(excel_path, schema_path):
    """Verify generated Excel matches schema exactly."""
    schema = load_schema(schema_path)
    
    for sheet_name in schema.keys():
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        
        # Check columns
        assert df.columns.tolist() == schema[sheet_name]
        
        # Check data types (future)
        # Check required fields (future)
```

### 2. Required Field Validation
Mark columns as required in schema:
```json
"PSA_MEMBER_IN": {
  "columns": ["MEM_NBR", "DOB", "GENDER"],
  "required": ["MEM_NBR", "DOB"]
}
```

### 3. Data Type Enforcement
```json
"PSA_MEMBER_IN": {
  "MEM_NBR": "string",
  "DOB": "date",
  "GENDER": "string"
}
```

---

## ✅ Summary

**Current Implementation:**
- ✅ Schema compliance is **enforced** via `df.reindex()`
- ✅ Column order is **guaranteed** to match schema
- ✅ Missing columns are **auto-filled** with null
- ✅ Extra columns are **automatically removed**

**Key Code:**
```python
df = df.reindex(columns=full_schema[sheet_name])
```

**This single line ensures 100% schema compliance!**

---

**Last Updated:** 2026-02-07  
**Status:** Implemented and Verified
