"""
NCQA Config Validator - Compares user config vs NCQA YAML
"""

import os
import yaml

class NCQAValidator:
    def __init__(self, measure_name):
        self.measure = measure_name
        # Path to official NCQA converted YAML
        self.ncqa_config_path = f'config/ncqa/{measure_name}_NCQA.yaml'
        
    def validate_config(self, user_config_path):
        """
        Compare user's config vs NCQA official config YAML.
        
        Args:
            user_config_path: Path to user's config (e.g., config/PSA.yaml)
        
        Returns:
            {
                'is_valid': bool,
                'errors': list,
                'warnings': list,
                'differences': dict
            }
        """
        # Load NCQA official config
        if not os.path.exists(self.ncqa_config_path):
            return {
                'is_valid': False,
                'errors': [f'NCQA config not found for measure {self.measure}: {self.ncqa_config_path}'],
                'warnings': [f'Please convert the NCQA PDF first using: python scripts/convert_ncqa_pdfs.py --measure {self.measure}'],
                'differences': {}
            }
        
        try:
            with open(self.ncqa_config_path, 'r') as f:
                ncqa_config = yaml.safe_load(f)
        except Exception as e:
            return {
                'is_valid': False,
                'errors': [f'Error loading NCQA config: {str(e)}'],
                'warnings': [],
                'differences': {}
            }
        
        # Load user config
        try:
            with open(user_config_path, 'r') as f:
                user_config = yaml.safe_load(f)
        except Exception as e:
            return {
                'is_valid': False,
                'errors': [f'Error loading User config: {str(e)}'],
                'warnings': [],
                'differences': {}
            }
        
        errors = []
        warnings = []
        differences = {}
        
        # Compare critical rules
        ncqa_rules = ncqa_config.get('rules', {})
        user_rules = user_config.get('rules', {})
        
        # 1. Compare Age Range
        ncqa_age = ncqa_rules.get('age_range')
        user_age = user_rules.get('age_range')
        
        if ncqa_age and user_age:
            if ncqa_age != user_age:
                errors.append(f"Age range mismatch: User={user_age}, NCQA={ncqa_age}")
                differences['age_range'] = {'user': user_age, 'ncqa': ncqa_age}
        elif ncqa_age and not user_age:
            errors.append(f"Missing age_range rule in user config. NCQA requires: {ncqa_age}")
            
        # 2. Compare Enrollment
        ncqa_enroll = ncqa_rules.get('continuous_enrollment', {}).get('period_months')
        user_enroll = user_rules.get('continuous_enrollment', {}).get('period_months')
        
        if ncqa_enroll and user_enroll:
            if ncqa_enroll != user_enroll:
                errors.append(f"Enrollment period mismatch: User={user_enroll} months, NCQA={ncqa_enroll} months")
                differences['enrollment'] = {'user': user_enroll, 'ncqa': ncqa_enroll}
        elif ncqa_enroll and not user_enroll:
             errors.append(f"Missing continuous_enrollment period in user config. NCQA requires: {ncqa_enroll}")

        # 3. Check value sets exist (basic check)
        # This iterates through user's defined clinical events and checks if they exist in NCQA map (if available)
        # For now, we compare the structure of 'numerator_components'
        
        ncqa_num = ncqa_rules.get('clinical_events', {}).get('numerator_components', [])
        user_num = user_rules.get('clinical_events', {}).get('numerator_components', [])
        
        if len(ncqa_num) != len(user_num):
            warnings.append(f"Numerator component count mismatch: User has {len(user_num)}, NCQA has {len(ncqa_num)}")
            differences['numerator_count'] = {'user': len(user_num), 'ncqa': len(ncqa_num)}

        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'differences': differences
        }
