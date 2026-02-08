import pandas as pd

# Read the test case
df = pd.read_excel('data/PSA_MY2026_TestCase.xlsx', sheet_name='PSA_Measure', header=None)

# Find PSA_CE_02 rows
psa_ce_02_rows = df[df.apply(lambda row: 'PSA_CE_02' in str(row.values), axis=1)]

print("=" * 80)
print("PSA_CE_02 Test Case Data:")
print("=" * 80)

for idx, row in psa_ce_02_rows.iterrows():
    print(f"\nRow {idx}:")
    for col_idx, val in enumerate(row.values):
        if str(val) != 'nan' and str(val).strip():
            print(f"  Col {col_idx}: {val}")
