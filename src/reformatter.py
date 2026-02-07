import pandas as pd
import os
import json
import re

class TestCaseReformatter:
    def __init__(self, extractor=None):
        """
        Initialize with an optional AI Extractor instance.
        If no extractor is provided, it will attempt to initialize one.
        """
        self.extractor = extractor
        if not self.extractor:
            try:
                from src.ai_extractor import AIScenarioExtractor
                print("Initializing AI Extractor (tinyllama) for reformatting...")
                self.extractor = AIScenarioExtractor(model_name="tinyllama")
            except Exception as e:
                print(f"⚠️  AI Extractor initialization failed: {e}")
                
    def reformat_file(self, input_path, output_path=None):
        """
        Reads a raw Excel file, uses AI to extract structured data from scenarios,
        and saves a clean, standardized Excel file ready for the main engine.
        """
        if not os.path.exists(input_path):
            print(f"Error: Input file {input_path} not found.")
            return

        print(f"Reformatting {input_path}...")
        df = pd.read_excel(input_path)
        
        # Identify columns
        # Heuristic: Look for 'Scenario', 'Objective', 'Expected'
        # Or just operate on all text columns combined
        
        cleaned_data = []
        
        total_rows = len(df)
        print(f"Processing {total_rows} rows...")
        
        for i, row in df.iterrows():
            # Basic info
            row_id = row.get('ID', f"TC_{i+1}")
            scenario_text = str(row.get('Scenario', '')) + " " + str(row.get('Objective', ''))
            
            # Use AI to extract structure
            if self.extractor:
                print(f"  [{i+1}/{total_rows}] Extracting info for {row_id}...")
                ai_result = self.extractor.extract_scenario_info({
                    'id': row_id,
                    'scenario': scenario_text,
                    'objective': '',
                    'expected': str(row.get('Expected', ''))
                })
                
                # Convert AI result to flat structure for Excel
                # We format spans as string: "Start-End:Product"
                spans_str = ""
                for span in ai_result.get('enrollment_spans', []):
                    s = span.get('start', '')
                    e = span.get('end', '')
                    p = span.get('product_id', '')
                    spans_str += f"{s} - {e}"
                    if p: spans_str += f" Product={p}"
                    spans_str += "\n"
                
                clean_row = {
                    'ID': row_id,
                    'Scenario': scenario_text, # Keep original for reference
                    'Structured_Enrollment': spans_str.strip(),
                    'Product_Line': ai_result.get('product_line', 'Medicare'),
                    'DOB': f"Age {ai_result.get('age', 70)}", # Engine parses "Age X"
                    'Gender': ai_result.get('gender', 'M'),
                    'Expected_Compliance': json.dumps(ai_result.get('expected_results', {})),
                    'Extracted_Events': json.dumps(ai_result.get('clinical_events', [])),
                    'Overrides': json.dumps(ai_result.get('overrides', {}))
                }
                cleaned_data.append(clean_row)
            else:
                 # Fallback: Just copy mostly as is ensuring headers exist
                 cleaned_data.append(row.to_dict())

        # Save to new Excel
        if not output_path:
            base, ext = os.path.splitext(input_path)
            output_path = f"{base}_Cleaned{ext}"
            
        df_clean = pd.DataFrame(cleaned_data)
        df_clean.to_excel(output_path, index=False)
        print(f"✅ Reformatting complete! Saved to {output_path}")
        return output_path

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        reformatter = TestCaseReformatter()
        reformatter.reformat_file(sys.argv[1])
    else:
        print("Usage: python src/reformatter.py <INPUT_EXCEL_FILE>")
