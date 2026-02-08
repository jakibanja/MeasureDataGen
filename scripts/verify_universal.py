import os
import sys
# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import run_measure_gen_custom

def verify():
    measure = "Universal"
    tc_path = "data/Universal_STANDARD.xlsx"
    vsd_path = r"C:\Users\sushi\Downloads\RAG-Tutorials-main\data\HEDIS MY 2026 Volume 2 Value Set Directory_2025-08-01.xlsx"
    
    print(f"Running Universal Test Case...")
    output = run_measure_gen_custom(measure, tc_path, vsd_path, skip_quality_check=True)
    
    if output and os.path.exists(output):
        print(f"✅ Success! Universal output generated at: {output}")
        
        # Verify contents
        import pandas as pd
        xl = pd.ExcelFile(output)
        print(f"Sheets: {xl.sheet_names}")
        
        # Check visit table for Flu Shot
        visit_df = pd.read_excel(output, sheet_name="Universal_VISIT_IN")
        print(f"\nUniversal_VISIT_IN Sample (Flu Shot):")
        print(visit_df[['MEM_NBR', 'SERV_DT', 'CPT_1']])
        
        # Check EMR table for BMI
        emr_df = pd.read_excel(output, sheet_name="Universal_EMR_IN")
        print(f"\nUniversal_EMR_IN Sample (BMI):")
        print(emr_df[['MEM_NBR', 'SERV_DT', 'BMI_PERCENTILE']])
        
    else:
        print(f"❌ Failed to generate output.")

if __name__ == "__main__":
    verify()
