import sys
import os
import pandas as pd
import yaml
sys.path.append(os.getcwd())

from src.standard_parser import StandardFormatParser
from src.engine import MockupEngine
from src.vsd import VSDManager

measure = 'SMD'
config_path = f'config/ncqa/{measure}_NCQA.yaml'
schema_path = 'config/schema_map.yaml'

# 1. Verify Config
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

print(f"--- Verifying {measure} Config ---")
for comp in config['rules']['clinical_events']['numerator_components']:
    print(f"  Component: {comp['name']} -> Target Table: {comp['table']}")

# 2. Verify Parser with 'Compliant' text
print(f"\n--- Verifying Parser (Handling 'Compliant' text) ---")
# Mock a row from the smart template
mock_row = pd.Series({
    'MEMBER_ID': 'TEST_MEMBER',
    'EVENT_1_NAME': 'HbA1c Test',
    'EVENT_1_VALUE': 'Compliant',
    'EVENT_1_DATE': '2026-05-20',
    'SCENARIO_DESCRIPTION': 'Test case'
})

parser = StandardFormatParser('dummy.xlsx')
scenario = parser._parse_row(mock_row, config)

print(f"  Parsed Compliant Events: {scenario['compliant']}")
if 'HbA1c Test' in scenario['compliant']:
    print("  [OK] SUCCESS: Parser recognized 'Compliant' string!")
else:
    print("  [FAIL] FAILURE: Parser missed 'Compliant' string.")

# 3. Verify Engine Table Selection
print(f"\n--- Verifying Engine Table Resolution ---")
vsd_path = os.getenv('VSD_PATH', 'data/VSD_MY2026.xlsx')
vsd = VSDManager(vsd_path) if os.path.exists(vsd_path) else None
engine = MockupEngine(config_path, schema_path, vsd_manager=vsd, measure_name_override=measure)

t_name, row = engine.generate_clinical_event('TEST_MEMBER', 'HbA1c Test', is_compliant=True, overrides={})
print(f"  Event 'HbA1c Test' generated in table: {t_name}")
if 'LAB' in t_name.upper():
    print("  [OK] SUCCESS: Event correctly mapped to LAB table!")
else:
    print(f"  [FAIL] FAILURE: Event mapped to {t_name}")
