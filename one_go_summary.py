import pandas as pd

def one_go_analysis():
    tc_path = 'data/SMD_MY2026_TestCase.xlsx'
    mock_path = 'output/SMD_MY2026_Mockup_v20.xlsx'
    
    xl_tc = pd.ExcelFile(tc_path)
    print(f"Tester Sheets: {xl_tc.sheet_names}")
    
    # Let's find the scenario sheet
    sc_sheet = [s for s in xl_tc.sheet_names if 'Measure' in s][0]
    # Let's find a data sheet (likely the last one with many columns)
    data_sheet = xl_tc.sheet_names[-1] 
    
    df_rules = pd.read_excel(xl_tc, sheet_name=sc_sheet)
    df_manual = pd.read_excel(xl_tc, sheet_name=data_sheet)
    
    print("-" * 60)
    print(f"1. THE TESTER'S MANUAL PROCESS (Sheet: {data_sheet})")
    print("-" * 60)
    
    sample_id = 'SMD_CE_01'
    # Find row that contains the ID
    manual_rows = df_manual[df_manual.apply(lambda row: row.astype(str).str.contains(sample_id).any(), axis=1)]
    
    if not manual_rows.empty:
        manual = manual_rows.iloc[0]
        print(f"For ID {sample_id}, the tester manually typed:")
        print(manual.iloc[:5].to_dict())
    else:
        print(f"Could not find manual data for {sample_id} in {data_sheet}.")

    print("\n" + "-" * 60)
    print("2. THE TOOL'S AUTOMATED PROCESS")
    print("-" * 60)
    try:
        df_tool = pd.read_excel(mock_path, sheet_name='SMD_VISIT_IN')
        tool_row = df_tool[df_tool['MEM_NBR'] == sample_id].iloc[0]
        print(f"The tool automatically generated this for {sample_id}:")
        print(tool_row.iloc[:5].to_dict())
    except Exception as e:
        print(f"Tool check: {e}")

if __name__ == "__main__":
    one_go_analysis()
