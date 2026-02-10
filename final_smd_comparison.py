import pandas as pd
import os

def final_comparison():
    tc_path = 'data/SMD_MY2026_TestCase.xlsx'
    mock_path = 'output/SMD_MY2026_Mockup_v20.xlsx'
    
    xl_tc = pd.ExcelFile(tc_path)
    xl_mock = pd.ExcelFile(mock_path)
    
    print("-" * 50)
    print("HOW TESTERS ARE DOING IT (Manual Sheets)")
    print("-" * 50)
    for s in xl_tc.sheet_names:
        if s.startswith('SMD_'):
            df = pd.read_excel(xl_tc, sheet_name=s)
            print(f"Sheet: {s:30} | Rows: {len(df):4} | Primary Column: {df.columns[0]}")
            
    print("\n" + "-" * 50)
    print("HOW THE TOOL IS DOING IT (Generated Tables)")
    print("-" * 50)
    for s in xl_mock.sheet_names:
        df = pd.read_excel(xl_mock, sheet_name=s)
        print(f"Table: {s:30} | Rows: {len(df):4} | Primary Column: {df.columns[0]}")
        
    print("\n" + "-" * 50)
    print("DEEP DIVE: Scenario vs Execution (Sample: SMD_CE_01)")
    print("-" * 50)
    
    # 1. Look up Scenario in Tester's Sheet
    df_measure = pd.read_excel(xl_tc, sheet_name='SMD_Measure')
    scenario = df_measure[df_measure['mem_nbr'] == 'SMD_CE_01']
    print("Scenario Description:")
    print(scenario[['mem_nbr', 'Scenario', 'Expected Result']].to_string(index=False))
    
    # 2. Look up Manual Data in Tester's Clinical Sheet
    df_manual = pd.read_excel(xl_tc, sheet_name='SMD_Clinical_CE_Excl_DST_TEMPLATE')
    # Match by ID in the first column
    manual_data = df_manual[df_manual.iloc[:, 0].astype(str).str.contains('SMD_CE_01', na=False)]
    print("\nTester's MANUALLY entered data (Row from SMD_Clinical_CE_Excl_DST_TEMPLATE):")
    if not manual_data.empty:
        print(manual_data.iloc[:, :7].to_string(index=False))
    else:
        print("No manual data found for this ID in that sheet.")
        
    # 3. Look up Tool's Generated Data
    df_tool = pd.read_excel(xl_mock, sheet_name='SMD_VISIT_IN')
    tool_data = df_tool[df_tool['MEM_NBR'] == 'SMD_CE_01']
    print("\nTool's AUTOMATICALLY generated data (Row from SMD_VISIT_IN):")
    if not tool_data.empty:
        print(tool_data.iloc[:, :7].to_string(index=False))
    else:
        print("No tool data found for this ID.")

if __name__ == "__main__":
    final_comparison()
