import pandas as pd
import os
import sys

file_path = 'output/PSA_MY2026_Mockup_v15.xlsx'
if not os.path.exists(file_path):
    print(f"File not found: {file_path}")
    sys.exit(1)

xl = pd.ExcelFile(file_path)
print(f"Output File: {file_path}")
print(f"Sheets: {xl.sheet_names}")

target_id = "PSA_CE_02"
found = False

for sheet in xl.sheet_names:
    df = pd.read_excel(file_path, sheet_name=sheet)
    # Check if target_id in any column (usually first one 'MEMBER_ID')
    matching_rows = df[df.apply(lambda row: row.astype(str).str.contains(target_id).any(), axis=1)]
    
    if not matching_rows.empty:
        found = True
        print(f"\n--- Sheet: {sheet} ---")
        print(f"Found {len(matching_rows)} matching rows for '{target_id}':")
        for idx, row in matching_rows.iterrows():
            # Print row as dict but filter out NaNs
            d = {k: v for k, v in row.to_dict().items() if pd.notna(v)}
            print(f"  Row {idx}: {d}")

if not found:
    print(f"\n❌ Member ID '{target_id}' not found in any sheet!")
