
import pandas as pd
import os
from main import run_measure_gen_custom

def create_test_file(filename, scenarios):
    df = pd.DataFrame(scenarios)
    # Ensure correct columns for Standard parser or simple parser
    # Let's use simple columns that look like a test case file
    # Required: ID, SCENARIO, EXPECTED
    df.to_excel(filename, index=False)
    print(f"Created {filename} with {len(scenarios)} scenarios.")

def run_test():
    print("--- Setting up Delta Run Test ---")
    os.makedirs('tests/delta', exist_ok=True)
    baseline_path = 'tests/delta/Baseline.xlsx'
    target_path = 'tests/delta/Target.xlsx'
    
    # helper to make rows - STANDARD FORMAT
    def make_rows(ids, content):
        data = []
        for i, c in zip(ids, content):
            data.append({
                'MEMBER_ID': i, 
                'SCENARIO_DESCRIPTION': c, 
                'EXPECTED_RESULT': 'Compliant',
                'AGE': 65,
                'GENDER': 'M',
                'PRODUCT_LINE': 'Medicare',
                'ENROLLMENT_1_START': '1/1/2026', # Mandatory for standard parser
                'ENROLLMENT_1_END': '12/31/2026',
                'VISIT_1_DATE': '1/1/2026',       # Mandatory for standard parser detection
                'EVENT_1_NAME': 'Test Event'      # Mandatory for standard parser detection
            })
        return data

    # 1. Baseline: SC1, SC2
    create_test_file(baseline_path, make_rows(
        ['SC1', 'SC2'], 
        ['Member visit', 'Member checkup']
    ))
    
    # 2. Target: SC1 (Same), SC2 (Changed), SC3 (New)
    create_test_file(target_path, make_rows(
        ['SC1', 'SC2', 'SC3'], 
        ['Member visit', 'Member checkup AND MORE', 'Member new']
    ))
    
    # 3. Dummy VSD
    vsd_path = 'tests/delta/dummy_vsd.xlsx'
    df_vsd = pd.DataFrame([
        {'Value Set Name': 'Test VS', 'Code System': 'ICD-10', 'Code': 'A00'}
    ])
    df_vsd.to_excel(vsd_path, index=False)
    print(f"Created dummy VSD at {vsd_path}")

    print("\n--- Running Generation (Delta Mode) ---")
    # Using 'Universal' or 'PSA' config
    # We need a valid measure config. Let's use 'PSA' or create a dummy one.
    # main.py defaults to 'Universal.yaml' if config not found.
    # Let's use a dummy measure name 'DELTA_TEST'
    
    output_file = run_measure_gen_custom(
        measure_name='DELTA_TEST',
        testcase_path=target_path,
        vsd_path=vsd_path,
        baseline_path=baseline_path,
        delta_run=True,
        disable_ai=True,
        skip_quality_check=True,
        mocking_depth='scenario'
    )
    
    print(f"\nGeneration complete: {output_file}")
    
    # 3. Verify Output
    # The output is a ZIP file, but data_store generates CSVs in data/ or output/.
    # The function returns the ZIP path.
    # However, the engine writes CSVs to `output/DELTA_TEST_MEMBER_IN.csv` before zipping?
    # No, Engine writes to `self.output_dir` which is `output/DELTA_TEST_v...`.
    
    import zipfile
    
    if not output_file:
         print("❌ No output file generated!")
         return

    df_out = None
    if output_file.endswith('.xlsx'):
        print(f"Reading Excel output: {output_file}")
        try:
            xl = pd.ExcelFile(output_file)
            print(f"Sheets found: {xl.sheet_names}")
            # Find Member sheet
            member_sheet = next((s for s in xl.sheet_names if 'MEMBER' in s), None)
            if member_sheet:
                df_out = pd.read_excel(output_file, sheet_name=member_sheet)
            else:
                print("❌ No MEMBER sheet found in Excel output!")
                return
        except Exception as e:
            print(f"❌ Failed to read Excel output: {e}")
            return
    elif output_file.endswith('.zip'):
        with zipfile.ZipFile(output_file, 'r') as zip_ref:
            # Check MEMBER table
            # Filename inside zip likely 'DELTA_TEST_MEMBER_IN.csv'
            # Or just check for ANY member file
            member_csv_name = next((f for f in zip_ref.namelist() if 'MEMBER' in f), None)
            if not member_csv_name:
                print(f"❌ No MEMBER table found in zip!")
                print(zip_ref.namelist())
                return
                
            with zip_ref.open(member_csv_name) as f:
                df_out = pd.read_csv(f)
    else:
        print(f"❌ Unknown output format: {output_file}")
        return
            
    print("\n--- Output Verification ---")
    print(df_out)
    
    # Check generated IDs
    # MEMBER_ID column usually named 'MEM_ID' or 'MEMBER_ID'
    id_col = next((c for c in df_out.columns if 'MEM' in c or 'ID' in c), 'MEM_ID')
    member_ids = df_out[id_col].astype(str).tolist()
    print(f"Generated IDs: {member_ids}")
    
    # SC1 (Unchanged), SC2 (Modified), SC3 (New)
    # Expect: SC2, SC3. (SC1 skipped)
    
    passed = True
    if 'SC1' in member_ids:
        print("❌ FAILURE: SC1 (Unchanged) was included.")
        passed = False
    
    if 'SC2' not in member_ids:
        print("❌ FAILURE: SC2 (Modified) was skipped.")
        passed = False
        
    if 'SC3' not in member_ids:
        print("❌ FAILURE: SC3 (New) was skipped.")
        passed = False
        
    if passed:
        print("✅ SUCCESS: Delta Logic verified correctly!")

if __name__ == "__main__":
    run_test()
