import pandas as pd
import os

def create_standard_template(output_path='templates/Standard_TestCase_Template.xlsx'):
    """
    Creates a blank Excel template following the Universal Standard Test Case Format.
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Define columns based on docs/STANDARD_TESTCASE_FORMAT.md
    core_cols = ['MEMBER_ID', 'AGE', 'GENDER', 'PRODUCT_LINE']
    
    enrollment_cols = []
    for i in range(1, 6):
        enrollment_cols.extend([f'ENROLLMENT_{i}_START', f'ENROLLMENT_{i}_END', f'ENROLLMENT_{i}_PRODUCT_ID'])
        
    visit_cols = []
    for i in range(1, 6):
        visit_cols.extend([f'VISIT_{i}_DATE', f'VISIT_{i}_TYPE', f'VISIT_{i}_CPT', f'VISIT_{i}_DIAG'])
        
    event_cols = []
    for i in range(1, 6):
        event_cols.extend([f'EVENT_{i}_NAME', f'EVENT_{i}_VALUE', f'EVENT_{i}_DATE', f'EVENT_{i}_CODE'])
        
    exclusion_cols = []
    for i in range(1, 3):
        exclusion_cols.extend([f'EXCLUSION_{i}_NAME', f'EXCLUSION_{i}_VALUE', f'EXCLUSION_{i}_DATE'])
        
    meta_cols = ['EXPECTED_RESULT', 'TEST_OBJECTIVE', 'SCENARIO_DESCRIPTION']
    
    all_columns = core_cols + enrollment_cols + visit_cols + event_cols + exclusion_cols + meta_cols
    
    # Create empty DataFrame
    df = pd.DataFrame(columns=all_columns)
    
    # Add an example row
    example_row = {
        'MEMBER_ID': 'EXAMPLE_01',
        'AGE': 70,
        'GENDER': 'M',
        'PRODUCT_LINE': 'Medicare',
        'ENROLLMENT_1_START': '1/1/2026',
        'ENROLLMENT_1_END': '12/31/2026',
        'VISIT_1_DATE': '2/1/2026',
        'VISIT_1_TYPE': 'Outpatient',
        'VISIT_1_CPT': '99213',
        'EVENT_1_NAME': 'PSA Test',
        'EVENT_1_VALUE': '1',
        'EVENT_1_DATE': '6/15/2026',
        'EXPECTED_RESULT': 'Compliant',
        'SCENARIO_DESCRIPTION': 'Member with valid enrollment and a PSA lab test.'
    }
    df = pd.concat([df, pd.DataFrame([example_row])], ignore_index=True)
    
    # Create instructions sheet
    instructions = [
        ['Sheet Name', 'Purpose'],
        ['Test Cases', 'Enter your mockup scenarios here, one per row.'],
        ['Core Columns', 'MEMBER_ID, AGE, GENDER, PRODUCT_LINE are mandatory.'],
        ['Dates', 'Use MM/DD/YYYY format or "Relative" formats like 1/1/MY (Current Year).'],
        ['Events', 'Use EVENT columns for any clinical data (Tests, Labs, IMC).'],
        ['Exclusions', 'Use EXCLUSION columns specifically for HEDIS exclusions like Hospice.'],
    ]
    df_instr = pd.DataFrame(instructions[1:], columns=instructions[0])
    
    # Save to Excel with multiple sheets
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df_instr.to_excel(writer, sheet_name='Instructions', index=False)
        df.to_excel(writer, sheet_name='Template', index=False)
        
    print(f"✅ Template created at: {output_path}")

if __name__ == "__main__":
    create_standard_template()
