# Validation Scripts

This folder contains scripts used to verify the mock data generation process.

## Key Scripts:
- `verify_psa_v17.py`: Checks the latest mockup (v17) for `PSA_CE_02` visit data and correct column mapping (CPT_1, DIAG_I_1, REVENUE_CODE).
- `inspect_vsd_headers.py`: Inspects the Value Set Directory columns to ensure 'Code System' is found.
- `inspect_tc.py`: Useful for debugging input test case parsing.

## Older Checks:
- `check_*.py`: Various checks for earlier versions/issues (e.g., date parsing, multi-visit handling).
- `verify_psa_ce_02_01.py`: Original verification script for v15.

## Usage:
Run from the project root:
```bash
python scripts/validation_tools/verify_psa_v17.py
```
