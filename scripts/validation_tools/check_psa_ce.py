from src.parser import TestCaseParser
import yaml

# Parse scenarios
parser = TestCaseParser('data/PSA_MY2026_TestCase.xlsx')
config = yaml.safe_load(open('config/PSA.yaml'))
scenarios = parser.parse_scenarios(config)

# Find PSA CE scenarios
psa_ce = [s for s in scenarios if 'CE' in s['id'].upper()]

print(f"\n📊 Total scenarios found: {len(scenarios)}")
print(f"📊 PSA CE scenarios found: {len(psa_ce)}")
print(f"\n🔍 First 20 PSA CE scenarios:")
for i, s in enumerate(psa_ce[:20], 1):
    compliant = s.get('compliant', [])
    excluded = s.get('excluded', [])
    print(f"  {i}. {s['id']}")
    print(f"      Compliant: {compliant}")
    print(f"      Excluded: {excluded}")
    print()
