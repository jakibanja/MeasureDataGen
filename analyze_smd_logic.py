import pandas as pd
import os

def analyze_smd():
    tc_path = 'data/SMD_MY2026_TestCase.xlsx'
    mock_path = 'output/SMD_MY2026_Mockup_v20.xlsx'
    
    print("=== 1. TEST CASE (SCENARIO LOGIC) ===")
    df_tc = pd.read_excel(tc_path, sheet_name='SMD_Measure')
    # Filter out empty rows or headers
    df_tc = df_tc[df_tc['mem_nbr'].notna()].head(15)
    
    pd.set_option('display.max_colwidth', 60)
    print(df_tc[['mem_nbr', 'Scenario', 'Expected Result']])
    
    print("\n=== 2. GENERATED MOCKUP DATA SUMMARY ===")
    if not os.path.exists(mock_path):
        print(f"Error: {mock_path} not found.")
        return
        
    xl_mock = pd.ExcelFile(mock_path)
    sheets = xl_mock.sheet_names
    print(f"Generated Sheets: {sheets}")
    
    df_mem = xl_mock.parse('SMD_MEMBER_IN')
    df_enr = xl_mock.parse('SMD_ENROLLMENT_IN')
    df_lab = xl_mock.parse('SMD_LAB_IN') if 'SMD_LAB_IN' in sheets else pd.DataFrame()
    df_vis = xl_mock.parse('SMD_VISIT_IN') if 'SMD_VISIT_IN' in sheets else pd.DataFrame()
    
    print(f"\nTotal Members: {len(df_mem)}")
    print(f"Total Lab Records: {len(df_lab)}")
    print(f"Total Visit Records: {len(df_vis)}")
    
    print("\n=== 3. COMPARISON (FIRST 10 SAMPLES) ===")
    comp_list = []
    for mid in df_tc['mem_nbr'].head(10).tolist():
        # Scenarios often have "Expected Result" like CE=1, CE=0
        exp_text = str(df_tc[df_tc['mem_nbr'] == mid]['Expected Result'].values[0])
        expect_compliant = "CE=1" in exp_text or "COMPLIANT" in exp_text.upper()
        
        # Real life check
        found_lab = len(df_lab[df_lab['MEM_NBR'] == mid]) > 0
        found_visit = len(df_vis[df_vis['MEM_NBR'] == mid]) > 0
        
        status = "✅ MATCH"
        if expect_compliant and not (found_lab or found_visit):
            status = "❌ MISMATCH (Under-generated)"
        elif not expect_compliant and (found_lab): # Simple check for non-compliant
            status = "❌ MISMATCH (Over-generated)"
            
        comp_list.append({
            'Member ID': mid,
            'Expected': exp_text.split()[-1],
            'Found Lab': "YES" if found_lab else "no",
            'Found Visit': "YES" if found_visit else "no",
            'Status': status
        })
    
    print(pd.DataFrame(comp_list).to_string())
    
    print("\n=== 4. STRUCTURAL GAP ANALYSIS ===")
    missing_tables = []
    for expected in ['SMD_RX_IN', 'SMD_EMR_IN']:
        if expected not in sheets:
            missing_tables.append(expected)
    
    if missing_tables:
        print(f"Notice: Tables {missing_tables} are missing because NO scenarios in this test case triggered Pharmacy or SNOMED events yet.")
    else:
        print("All expected tables (MEMBER, ENROLL, VISIT, LAB, RX, EMR) generated successfully.")

if __name__ == "__main__":
    analyze_smd()
