import pandas as pd
from datetime import datetime, timedelta
import yaml

class HEDISValidator:
    """
    Validates generated mockup data against test case expectations.
    Implements HEDIS logic to verify compliance/non-compliance.
    """
    
    def __init__(self, config_path, mockup_path, schema_path='config/schema_map.yaml', measure_name=None):
        self.config_path = config_path
        self.mockup_path = mockup_path
        self.schema_path = schema_path
        self.config = self._load_config()
        self.measure_name = measure_name if measure_name else self.config.get('measure_name', 'PSA').upper()
        self.schema = self._load_schema()
        self.data = self._load_mockup()
        self.results = []
        
    def _load_config(self):
        """Load measure configuration."""
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    def _load_schema(self):
        """Load and resolve schema with measure name."""
        with open(self.schema_path, 'r') as f:
            raw_schema = yaml.safe_load(f)
        
        # Resolve {MEASURE} placeholders
        resolved = {'tables': {}}
        for key, table in raw_schema['tables'].items():
            resolved['tables'][key] = table.copy()
            if isinstance(table.get('name'), str):
                resolved['tables'][key]['name'] = table['name'].replace('{MEASURE}', self.measure_name)
        return resolved
    
    def _load_mockup(self):
        """Load all sheets from mockup Excel."""
        return pd.read_excel(self.mockup_path, sheet_name=None)
    
    def _get_table_data(self, logical_name):
        """Helper to get data from a table by its logical name."""
        physical_name = self.schema['tables'].get(logical_name, {}).get('name')
        if not physical_name:
            return pd.DataFrame()
        
        # Exact match or case-insensitive match
        if physical_name in self.data:
            return self.data[physical_name]
        
        for sheet in self.data.keys():
            if sheet.lower() == physical_name.lower():
                return self.data[sheet]
        
        return pd.DataFrame()

    def validate_member(self, member_id, expected_result):
        """
        Validate a single member's data.
        """
        result = {
            'member_id': member_id,
            'expected': expected_result,
            'actual': None,
            'pass': False,
            'details': []
        }
        
        # 1. Check Age
        age_valid = self._validate_age(member_id, result)
        
        # 2. Check Enrollment
        enrollment_valid = self._validate_enrollment(member_id, result)
        
        # 3. Check Exclusions
        is_excluded = self._check_exclusions(member_id, result)
        
        if is_excluded:
            result['actual'] = 'Excluded'
            result['pass'] = (expected_result == 'Excluded')
            return result
        
        # 4. Check Numerator (Clinical Events)
        has_numerator = self._check_numerator(member_id, result)
        
        # 5. Determine Compliance
        if enrollment_valid and age_valid and has_numerator:
            result['actual'] = 'Compliant'
        else:
            result['actual'] = 'Non-Compliant'
        
        result['pass'] = (result['actual'] == expected_result)
        
        return result
    
    def _validate_enrollment(self, member_id, result):
        """Check continuous enrollment requirement using schema."""
        df = self._get_table_data('enrollment')
        
        if df.empty:
            result['details'].append("❌ Enrollment table not found")
            return False
        
        member_enrollments = df[df['MEM_NBR'] == member_id]
        
        if member_enrollments.empty:
            result['details'].append("❌ No enrollment records")
            return False
        
        # Check enrollment period
        rules = self.config.get('rules', {})
        enr_rules = rules.get('continuous_enrollment', {'period_months': 12, 'allowable_gap_days': 45})
        
        req_months = enr_rules.get('period_months', 12)
        
        # Sort by start date
        member_enrollments = member_enrollments.sort_values('ENR_START')
        
        # Calculate total enrollment days
        total_days = 0
        for _, row in member_enrollments.iterrows():
            start = pd.to_datetime(row['ENR_START'])
            end = pd.to_datetime(row['ENR_END'])
            total_days += (end - start).days + 1
        
        required_days = req_months * 30  # Approximate
        
        if total_days >= required_days:
            result['details'].append(f"✅ Enrollment: {total_days} days (>= {required_days})")
            return True
        else:
            result['details'].append(f"❌ Enrollment: {total_days} days (< {required_days})")
            return False
    
    def _validate_age(self, member_id, result):
        """Check age requirement using schema."""
        df = self._get_table_data('member')
        
        if df.empty:
            result['details'].append("❌ Member table not found")
            return False
        
        member_row = df[df['MEM_NBR'] == member_id]
        
        if member_row.empty:
            result['details'].append("❌ Member not found")
            return False
        
        dob_col = self.schema['tables']['member']['fields']['dob']
        dob = pd.to_datetime(member_row.iloc[0][dob_col])
        age_as_of = datetime(2026, 12, 31)  # MY 2026
        age = (age_as_of - dob).days // 365
        
        age_range = self.config.get('rules', {}).get('age_range', [0, 100])
        age_min, age_max = age_range
        
        if age_min <= age <= age_max:
            result['details'].append(f"✅ Age: {age} (in range {age_min}-{age_max})")
            return True
        else:
            result['details'].append(f"❌ Age: {age} (out of range {age_min}-{age_max})")
            return False
    
    def _check_exclusions(self, member_id, result):
        """Check if member has any exclusions from config."""
        exclusions = self.config.get('rules', {}).get('exclusions', [])
        
        for excl in exclusions:
            excl_name = excl['name']
            
            # 1. Check MEMBER table flags
            mbr_df = self._get_table_data('member')
            if not mbr_df.empty:
                mbr_row = mbr_df[mbr_df['MEM_NBR'] == member_id]
                if not mbr_row.empty:
                    # Generic hospice/death check
                    if excl_name.lower() == 'hospice' and 'BEN_HOSPICE' in mbr_row.columns:
                        if mbr_row.iloc[0]['BEN_HOSPICE'] == 1:
                            result['details'].append(f"🚫 Exclusion: {excl_name} (Member Flag)")
                            return True
                    if excl_name.lower() == 'deceased' and 'DEATH_DT' in mbr_row.columns:
                        if pd.notna(mbr_row.iloc[0]['DEATH_DT']):
                            result['details'].append(f"🚫 Exclusion: {excl_name} (Death DT)")
                            return True

            # 2. Check for exclusion in relevant tables
            # (In production, would use VSD codes from excl['value_set_names'])
            # For now, look for records in the logical tables associated withexclusions
            visit_df = self._get_table_data('visit')
            if not visit_df.empty:
                mbr_visits = visit_df[visit_df['MEM_NBR'] == member_id]
                # Heuristic: if a visit exists and config says exclusion can be in visit
                if not mbr_visits.empty and any('visit' in str(v).lower() for v in excl.get('value_set_names', [])):
                     # We assume if test case asked for exclusion and we generated a record, it's there
                     # Real HEDIS would check specific codes here
                     pass
        
        return False
    
    def _check_numerator(self, member_id, result):
        """Check if member has required clinical events from config."""
        numerator_components = self.config.get('rules', {}).get('clinical_events', {}).get('numerator_components', [])
        
        if not numerator_components:
            # Universal fallback: if no components, maybe it's purely dynamic
            result['details'].append("⚠️ No numerator components in config")
            return False

        for component in numerator_components:
            logical_table = component.get('table', 'visit')
            df = self._get_table_data(logical_table)
            
            if df.empty:
                continue
            
            member_events = df[df['MEM_NBR'] == member_id]
            
            if not member_events.empty:
                # Check for BMI Percentile specifically if requested
                if component['name'] == 'BMI Percentile' and 'BMI_PERCENTILE' in member_events.columns:
                    if pd.notna(member_events.iloc[0]['BMI_PERCENTILE']):
                        result['details'].append(f"✅ Numerator: {component['name']} ({member_events.iloc[0]['BMI_PERCENTILE']}%)")
                        return True
                
                result['details'].append(f"✅ Numerator: {component['name']} found")
                return True
        
        result['details'].append("❌ Numerator: No qualifying events found")
        return False
    
    def validate_all(self, test_cases):
        """
        Validate all members from test cases.
        
        Args:
            test_cases: List of dicts with 'id' and 'expected' keys
        
        Returns:
            Summary report
        """
        print(f"\n🔍 Validating {len(test_cases)} test cases...")
        
        for tc in test_cases:
            member_id = tc['id']
            expected = tc.get('expected', 'Unknown')
            
            result = self.validate_member(member_id, expected)
            self.results.append(result)
            
            # Print result
            status = "✅" if result['pass'] else "❌"
            print(f"{status} {member_id}: Expected {expected} → Got {result['actual']}")
            for detail in result['details']:
                print(f"    {detail}")
        
        return self._generate_summary()
    
    def _generate_summary(self):
        """Generate validation summary report."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r['pass'])
        failed = total - passed
        
        summary = {
            'total': total,
            'passed': passed,
            'failed': failed,
            'pass_rate': (passed / total * 100) if total > 0 else 0,
            'results': self.results
        }
        
        print(f"\n📊 Validation Summary:")
        print(f"   Total: {total}")
        print(f"   Passed: {passed} ({summary['pass_rate']:.1f}%)")
        print(f"   Failed: {failed}")
        
        if failed > 0:
            print(f"\n❌ Failed Cases:")
            for r in self.results:
                if not r['pass']:
                    print(f"   - {r['member_id']}: Expected {r['expected']}, Got {r['actual']}")
        
        return summary
    
    def export_report(self, output_path):
        """Export validation results to Excel."""
        df = pd.DataFrame(self.results)
        df.to_excel(output_path, index=False)
        print(f"\n📄 Validation report saved: {output_path}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python src/validator.py <CONFIG_PATH> <MOCKUP_PATH>")
        print("Example: python src/validator.py config/PSA.yaml output/PSA_MY2026_Mockup_v15.xlsx")
        sys.exit(1)
    
    config_path = sys.argv[1]
    mockup_path = sys.argv[2]
    
    validator = HEDISValidator(config_path, mockup_path)
    
    # Example test cases (in production, would load from test case file)
    test_cases = [
        {'id': 'PSA_PL_COMMERCIAL', 'expected': 'Compliant'},
        {'id': 'PSA_PL_MEDICAID', 'expected': 'Compliant'},
        {'id': 'PSA_RE_BH_ENROLL_05', 'expected': 'Non-Compliant'},
    ]
    
    summary = validator.validate_all(test_cases)
    validator.export_report('output/validation_report.xlsx')
