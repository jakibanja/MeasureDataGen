import pandas as pd
import os

file_path = 'data/PSA_MY2026_TestCase.xlsx'

with open('tc_scan_utf8.txt', 'w', encoding='utf-8') as f:
    xl = pd.ExcelFile(file_path)
    f.write(f"File: {file_path}\n")
    f.write(f"Sheets: {xl.sheet_names}\n")

    for sheet in xl.sheet_names:
        f.write(f"\n--- Sheet: {sheet} ---\n")
        df = pd.read_excel(file_path, sheet_name=sheet, nrows=15, header=None)
        f.write(f"Shape: {df.shape}\n")
        
        for i, row in df.iterrows():
            vals = [str(val).strip() for val in row if pd.notna(val)]
            row_str = " | ".join(vals)
            f.write(f"Row {i}: {row_str}\n")
            
            lower_row = row_str.lower()
            if any(x in lower_row for x in ['#tc', 'mem_nbr', 'member number', 'testcase id']):
                f.write(f"  [MATCH] parser would use this row as header!\n")
            else:
                f.write(f"  [NO MATCH] checked: '#tc', 'mem_nbr', 'member number', 'testcase id'\n")
