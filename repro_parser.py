import traceback
import yaml
import sys
import os

# Add current dir to path just in case
sys.path.append(os.getcwd())

from src.parser import TestCaseParser

try:
    print("Loading config...")
    if not os.path.exists('config/PSA.yaml'):
        print("Config not found, creating dummy config")
        config = {'measure_name': 'PSA', 'rules': {'clinical_events': {'numerator_components': []}}}
    else:
        with open('config/PSA.yaml') as f:
            config = yaml.safe_load(f)

    print("Initializing parser...")
    parser = TestCaseParser('data/PSA_MY2026_TestCase.xlsx')
    
    print("Parsing scenarios...")
    scenarios = parser.parse_scenarios(config)
    print(f"Found {len(scenarios)} scenarios.")
    
except Exception:
    print("\nCRASH CAUGHT:")
    traceback.print_exc()
