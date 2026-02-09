import pandas as pd
import os
import sys

# Updated to v16
file_path = 'output/PSA_MY2026_Mockup_v16.xlsx'
if not os.path.exists(file_path):
    print(f"File not found: {file_path}")
    sys.exit(1)

xl = pd.ExcelFile(file_path)
print(f"Output File: {file_path}")
print(f"Sheets: {xl.sheet_names}")

target_id = "PSA_CE_02"
found = False

# Specifically check PSA_VISIT sheet if it exists
visit_sheet = next((s for s in xl.sheet_names if 'VISIT' in s), None)

if visit_sheet:
    print(f"\n--- Checking Visits for {target_id} in {visit_sheet} ---")
    df_v = pd.read_excel(file_path, sheet_name=visit_sheet)
    matches = df_v[df_v.apply(lambda row: row.astype(str).str.contains(target_id).any(), axis=1)]
    if not matches.empty:
        print(f"✅ Found {len(matches)} visit records:")
        for idx, row in matches.iterrows():
            d = {k: v for k, v in row.to_dict().items() if pd.notna(v)}
            print(f"  Row {idx}: {d}")
    else:
        print(f"❌ No visit records found for {target_id}!")
else:
    print("❌ No VISIT sheet found in output!")

# Also check other sheets briefly
for sheet in xl.sheet_names:
    if sheet == visit_sheet: continue
    df = pd.read_excel(file_path, sheet_name=sheet)
    matching_rows = df[df.apply(lambda row: row.astype(str).str.contains(target_id).any(), axis=1)]
    if not matching_rows.empty:
        found = True
        print(f"\n--- {sheet}: Found {len(matching_rows)} matches ---")
