import pandas as pd
import yaml

# Parse the test case to see what visits are defined
from src.parser import TestCaseParser

parser = TestCaseParser('data/PSA_MY2026_TestCase.xlsx')
config = yaml.safe_load(open('config/PSA.yaml'))
scenarios = parser.parse_scenarios(config)

# Find GG_PROD_SWTICH scenarios
gg_scenarios = [s for s in scenarios if 'GG_PROD_SWTICH' in s['id']]

print("=" * 80)
print("GG_PROD_SWTICH SCENARIOS - PARSED DATA")
print("=" * 80)

for sc in gg_scenarios[:6]:  # First 6
    print(f"\n{sc['id']}:")
    print(f"  Enrollment spans: {len(sc.get('enrollment_spans', []))}")
    for i, span in enumerate(sc.get('enrollment_spans', []), 1):
        print(f"    {i}. {span.get('start')} to {span.get('end')}")
    
    print(f"  Visit spans: {len(sc.get('visit_spans', []))}")
    for i, visit in enumerate(sc.get('visit_spans', []), 1):
        print(f"    {i}. {visit.get('date')}")
    
    print(f"  Compliant: {sc.get('compliant', [])}")
    print(f"  Excluded: {sc.get('excluded', [])}")
