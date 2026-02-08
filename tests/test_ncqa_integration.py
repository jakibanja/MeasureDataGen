"""
Integration Test for NCQA Validation & Compliance
"""

import os
import yaml
import sys
import pandas as pd

# Add project root to path
sys.path.append(os.getcwd())

from src.ncqa_validator import NCQAValidator
from src.ncqa_compliance import NCQAComplianceChecker

def run_test():
    print("🚀 Starting NCQA Integration Test...\n")
    
    # 1. Setup Dummy Data
    os.makedirs('config/ncqa', exist_ok=True)
    
    # Dummy NCQA Spec (YAML)
    ncqa_spec = {
        'measure_name': 'TEST_MEASURE',
        'rules': {
            'age_range': [50, 75],
            'continuous_enrollment': {'period_months': 12}
        }
    }
    with open('config/ncqa/TEST_NCQA.yaml', 'w') as f:
        yaml.dump(ncqa_spec, f)
        
    # Dummy User Config (Valid)
    user_config_valid = {
        'measure_name': 'TEST_MEASURE',
        'rules': {
            'age_range': [50, 75],  # Matches
            'continuous_enrollment': {'period_months': 12}
        }
    }
    with open('config/TEST_VALID.yaml', 'w') as f:
        yaml.dump(user_config_valid, f)

    # Dummy User Config (Invalid)
    user_config_invalid = {
        'measure_name': 'TEST_MEASURE',
        'rules': {
            'age_range': [18, 85],  # Mismatch!
            'continuous_enrollment': {'period_months': 6}
        }
    }
    with open('config/TEST_INVALID.yaml', 'w') as f:
        yaml.dump(user_config_invalid, f)

    # 2. Test Config Validator
    print("🔍 Testing Config Validator...")
    validator = NCQAValidator('TEST')
    
    # Test Valid Config
    res_valid = validator.validate_config('config/TEST_VALID.yaml')
    if res_valid['is_valid']:
        print("   ✅ Valid config passed validation.")
    else:
        print(f"   ❌ Valid config failed validation: {res_valid['errors']}")

    # Test Invalid Config
    res_invalid = validator.validate_config('config/TEST_INVALID.yaml')
    if not res_invalid['is_valid']:
        print("   ✅ Invalid config correctly failed validation.")
        print(f"      Errors detected: {res_invalid['errors']}")
    else:
        print("   ❌ Invalid config incorrectly passed validation.")

    print("-" * 30)

    # 3. Test Compliance Checker
    print("\n🔍 Testing Compliance Checker...")
    checker = NCQAComplianceChecker(user_config_valid, 'config/ncqa/TEST_NCQA.yaml')
    
    # Dummy Output Data (Valid)
    valid_data = {
        'MEMBER_IN': pd.DataFrame({'AGE': [50, 60, 75]}),  # Inside [50, 75]
        'ENROLLMENT_IN': pd.DataFrame({'START_DATE': ['2026-01-01'], 'END_DATE': ['2026-12-31']})
    }
    
    # Dummy Output Data (Invalid)
    invalid_data = {
        'MEMBER_IN': pd.DataFrame({'AGE': [45, 80]}),      # Outside [50, 75]
        'ENROLLMENT_IN': pd.DataFrame({'START_DATE': ['2026-12-31'], 'END_DATE': ['2026-01-01']}) # Start > End
    }

    # Test Valid Output
    # Scenario: Mem 50 is compliant
    scenarios = [{'id': '50', 'compliant': ['PSA_TEST'], 'age': 50}]
    
    # Valid: Mem 50 has data (AGE column is 50, so id is 50 implicit in dummy logic? No, need MEM_ID)
    valid_data['MEMBER_IN']['MEM_ID'] = ['50', '60', '75'] # Add IDs
    # Add dummy clinical table
    valid_data['PSA_TEST'] = pd.DataFrame({'MEM_ID': ['50']})
    
    res_compliance_valid = checker.check_compliance(valid_data, scenarios)
    if res_compliance_valid['passed']:
        print(f"   ✅ Valid data passed scenario compliance (Score: {res_compliance_valid['score']}).")
    else:
        print(f"   ❌ Valid data failed scenario compliance: {res_compliance_valid['issues']}")

    # Test Invalid Output (Missing Clinical Data)
    # Scenario: Mem 80 is compliant, but no data in tables
    scenarios_invalid = [{'id': '80', 'compliant': ['PSA_TEST'], 'age': 80}]
    invalid_data['MEMBER_IN']['MEM_ID'] = ['45', '80']
    
    res_compliance_invalid = checker.check_compliance(invalid_data, scenarios_invalid)
    if not res_compliance_invalid['passed'] and any("expected to be compliant" in i for i in res_compliance_invalid['issues']):
        print(f"   ✅ Invalid data correctly failed scenario compliance.")
        print(f"      Issues detected: {res_compliance_invalid['issues']}")
    else:
        print(f"   ❌ Invalid data incorrectly passed scenario compliance or missed scenario issue.")

    # Test VSD Validation failure
    # Mock VSD Manager
    class MockVSD:
        pass
    
    checker_vsd = NCQAComplianceChecker(user_config_valid, 'config/ncqa/TEST_NCQA.yaml', vsd_manager=MockVSD())
    
    # Valid data but with MISSING code for VSD validation
    vsd_test_data = {
        'PSA_TEST': pd.DataFrame({
            'MEM_ID': ['50'], 
            '_CODE': [None],             # Missing code!
            '_VALUE_SET_NAME': ['PSA']   # Has VS, needs code
        })
    }
    # We must also clear MEMBER_IN/ENROLLMENT errors by providing valid ones
    vsd_test_data['MEMBER_IN'] = valid_data['MEMBER_IN']
    vsd_test_data['ENROLLMENT_IN'] = valid_data['ENROLLMENT_IN']
    
    res_vsd = checker_vsd.check_compliance(vsd_test_data)
    
    if not res_vsd['passed'] and any("invalid/empty code" in i for i in res_vsd['issues']):
        print(f"   ✅ VSD Validation correctly identified missing code.")
    else:
        print(f"   ❌ VSD Validation failed to identify missing code: {res_vsd.get('issues')}")

    print("\n🚀 Integration Test Complete!")
    
    # Cleanup
    try:
        os.remove('config/ncqa/TEST_NCQA.yaml')
        os.remove('config/TEST_VALID.yaml')
        os.remove('config/TEST_INVALID.yaml')
    except:
        pass

if __name__ == '__main__':
    run_test()
