import pandas as pd
import os

def generate_chl_test_case():
    data = {
        'MEMBER_ID': ['CHL_MBR_01', 'CHL_MBR_02'],
        'AGE': [21, 23],
        'GENDER': ['F', 'F'],
        'PRODUCT_LINE': ['COMMERCIAL', 'MEDICAID'],
        'ENROLLMENT_1_START': ['2026-01-01', '2026-01-01'],
        'ENROLLMENT_1_END': ['2026-12-31', '2026-12-31'],
        'VISIT_1_DATE': ['2026-06-15', '2026-08-20'],
        'VISIT_1_TYPE': ['Outpatient', 'Outpatient'],
        'EVENT_1_NAME': ['ChlamydiaScreening', 'ChlamydiaScreening'],
        'EVENT_1_VALUE': [1, 0],
        'EVENT_1_DATE': ['2026-06-16', ''],
        'EXPECTED_RESULT': [1, 0],
        'NOTES': ['Compliant Member', 'Non-Compliant Member (Missing Screening)']
    }
    
    df = pd.DataFrame(data)
    
    # Ensure all standard columns exist for the parser
    standard_cols = [
        'MEMBER_ID', 'AGE', 'GENDER', 'PRODUCT_LINE',
        'ENROLLMENT_1_START', 'ENROLLMENT_1_END',
        'VISIT_1_DATE', 'VISIT_1_TYPE',
        'EVENT_1_NAME', 'EVENT_1_VALUE', 'EVENT_1_DATE',
        'EVENT_2_NAME', 'EVENT_2_VALUE', 'EVENT_2_DATE',
        'EXCLUSION_1_NAME', 'EXCLUSION_1_VALUE', 'EXCLUSION_1_DATE',
        'EXPECTED_RESULT', 'NOTES'
    ]
    
    for col in standard_cols:
        if col not in df.columns:
            df[col] = ''
            
    df = df[standard_cols] # Reorder
    
    output_path = 'data/CHL_TEST_READY.xlsx'
    df.to_excel(output_path, index=False)
    print(f"✅ Generated pre-filled test case: {output_path}")

if __name__ == "__main__":
    generate_chl_test_case()
