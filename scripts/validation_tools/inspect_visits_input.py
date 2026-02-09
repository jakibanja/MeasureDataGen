import pandas as pd

file_path = 'data/PSA_MY2026_TestCase.xlsx'
df = pd.read_excel(file_path, sheet_name='PSA_Standard', header=0)

visit_cols = [c for c in df.columns if 'VISIT' in str(c).upper()]
print(f"Visit Columns: {visit_cols}")

if visit_cols:
    print(df[visit_cols].head(10).to_string())
else:
    print("No columns with 'VISIT' in name found!")
