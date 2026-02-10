import pandas as pd
mock_path = 'output/SMD_MY2026_Mockup_v20.xlsx'
xl = pd.ExcelFile(mock_path)
print('=== FINAL GENERATED SHEETS ===')
print(xl.sheet_names)
print('\n--- ROW COUNTS ---')
for s in xl.sheet_names:
    df = pd.read_excel(xl, sheet_name=s)
    print(f'{s:25}: {len(df)} rows')
