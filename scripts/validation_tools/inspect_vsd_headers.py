import pandas as pd

vsd_path = r'C:\Users\sushi\Downloads\RAG-Tutorials-main\data\HEDIS MY 2026 Volume 2 Value Set Directory_2025-08-01.xlsx'

print(f"Reading Value Sets to Codes from {vsd_path}")
try:
    df = pd.read_excel(vsd_path, sheet_name='Value Set to Codes', nrows=5)
    print(df.columns.tolist())
except Exception as e:
    print(f"Error reading 'Value Set to Codes': {e}")
    # Try searching for similar name
    xl = pd.ExcelFile(vsd_path)
    for s in xl.sheet_names:
        if 'code' in s.lower() and 'value' in s.lower():
             print(f"Checking sheet: {s}")
             df = pd.read_excel(vsd_path, sheet_name=s, nrows=5)
             print(df.columns.tolist())
