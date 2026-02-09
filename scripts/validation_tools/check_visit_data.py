import pandas as pd

# Read first visit record
vis = pd.read_excel('output/PSA_MY2026_Mockup_v15.xlsx', sheet_name='PSA_VISIT_IN', nrows=1)

print("=" * 80)
print("VISIT TABLE - First Record")
print("=" * 80)

print("\n📋 Columns with NON-NULL values:")
for col in vis.columns:
    val = vis[col].iloc[0]
    if pd.notna(val):
        print(f"  ✓ {col:25s} = {val}")

print("\n📋 Columns with NULL values:")
null_cols = []
for col in vis.columns:
    val = vis[col].iloc[0]
    if pd.isna(val):
        null_cols.append(col)

print(f"  Total NULL columns: {len(null_cols)}")
print(f"  Examples: {', '.join(null_cols[:10])}")

# Check for CPT, DIAG, HCPCS, POS columns
print("\n📋 Key Clinical Code Columns:")
for col in vis.columns:
    if any(x in col.upper() for x in ['CPT', 'DIAG', 'HCPC', 'POS', 'ICD', 'DX']):
        val = vis[col].iloc[0]
        status = "✓" if pd.notna(val) else "✗"
        print(f"  {status} {col:25s} = {val if pd.notna(val) else 'NULL'}")
