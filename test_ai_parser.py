
import sys
from unittest.mock import MagicMock
sys.modules['PyPDF2'] = MagicMock()
from src.ncqa_parser import NCQASpecParser
from src.ai_extractor import AIScenarioExtractor
import os
import json

class MockParser(NCQASpecParser):
    def extract_text(self, target_measure_title=None):
        # Override with our known SMD text snippet
        self.text = """
        MEASURE: Diabetes Monitoring for People With Diabetes and Schizophrenia (SMD)
        
        DESCRIPTION: The percentage of members 18–64 years of age with schizophrenia and diabetes who had an HbA1c test and an LDL-C test during the measurement year.
        
        DENOMINATOR / EVENT / DIAGNOSIS:
        Step 1: Identify members who met at least one of the following criteria during the measurement year.
          - At least one acute inpatient encounter with any diagnosis of schizophrenia.
          - At least two visits in an outpatient setting, observation visit, telephone visit, or online assessment with any diagnosis of schizophrenia on different dates of service.
          
        Step 2: Identify members who met at least one of the following criteria during the measurement year or the year prior to the measurement year.
          - At least two visits in an outpatient setting, observation visit, telephone visit, or online assessment with any diagnosis of diabetes on different dates of service.
          - At least one encounter in an outpatient setting with any diagnosis of diabetes AND at least one diabetes medication dispensing event.
          
        NUMERATOR:
        Identify members who had an HbA1c test and an LDL-C test during the measurement year.
        """
        print("Mocked PDF text loaded.")
        return self.text

# Initialize actual AI Extractor (requires Ollama running)
try:
    extractor = AIScenarioExtractor(model_name='qwen2:0.5b') # Or whatever model is available
    print("AI Extractor initialized.")
except Exception as e:
    print(f"Skipping test: AI Extractor init failed: {e}")
    exit(0)

# Run Parser
parser = MockParser("dummy.pdf", ai_extractor=extractor)
config = parser.generate_config(output_path="config/test_SMD_AI.yaml", target_measure_title="Diabetes Monitoring (SMD)")

# Verify Output
print("\n--- Verification Report ---")
if 'denominator_components' in config['rules']['clinical_events']:
    print("✅ Denominator Components Found:")
    for comp in config['rules']['clinical_events']['denominator_components']:
        print(f"  - Name: {comp['name']}")
        print(f"    Count: {comp.get('count', 1)}")
        if 'min_separation_days' in comp:
            print(f"    Separation: {comp['min_separation_days']} days")
        if comp.get('type') == 'composite':
             print(f"    Type: Composite ({len(comp.get('events', []))} sub-events)")
else:
    print("❌ NO Denominator Components Found! (Check extracted text or AI prompt)")
