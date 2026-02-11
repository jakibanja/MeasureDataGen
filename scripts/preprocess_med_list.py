import pandas as pd
import json
import os

def preprocess():
    file_path = 'HEDIS MY 2026 Medication List Directory_2025-08-01.xlsx'
    output_path = 'data/HEDIS_Medication_Codes.json'
    
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return

    print(f"Reading {file_path}...")
    # Read the core mapping sheet
    df = pd.read_excel(file_path, sheet_name='Medication Lists to Codes', engine='openpyxl')
    
    # Select relevant columns - using the actual names found in the MY2026 file
    cols = ['Medication List Name', 'Code', 'Code System']
    try:
        df = df[cols]
    except KeyError as e:
        print(f"KeyError: {e}")
        print("Available columns:", df.columns.tolist())
        return
    
    # Group by Value Set Name
    mapping = {}
    
    print("Processing mappings...")
    for vs_name, group in df.groupby('Medication List Name'):
        mapping[vs_name] = {
            'NDC': group[group['Code System'] == 'NDC']['Code'].astype(str).unique().tolist(),
            'RxNorm': group[group['Code System'] == 'RxNorm']['Code'].astype(str).unique().tolist()
        }
        
    # Remove empty lists
    clean_mapping = {k: v for k, v in mapping.items() if v['NDC'] or v['RxNorm']}
    
    print(f"Saving {len(clean_mapping)} value sets to {output_path}...")
    with open(output_path, 'w') as f:
        json.dump(clean_mapping, f, indent=2)
    
    print("Done!")

if __name__ == "__main__":
    preprocess()
