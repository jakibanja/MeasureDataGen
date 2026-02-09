import pandas as pd

# Read the test case Excel file
df = pd.read_excel('data/PSA_MY2026_TestCase.xlsx', sheet_name='PSA_GG Dual Enroll', header=None)

# Find rows with GG_PROD_SWTICH
gg_rows = df[df.apply(lambda row: any('GG_PROD_SWTICH' in str(val) for val in row.values), axis=1)]

print("=" * 80)
print("GG_PROD_SWTICH TEST CASE DATA (Raw)")
print("=" * 80)

for idx, row in gg_rows.head(6).iterrows():
    # Find the ID
    row_id = None
    for val in row.values:
        if 'GG_PROD_SWTICH' in str(val):
            row_id = val
            break
    
    print(f"\nRow {idx}: {row_id}")
    print("  Non-empty cells:")
    for col_idx, val in enumerate(row.values):
        if pd.notna(val) and str(val).strip():
            print(f"    Col {col_idx}: {val}")
