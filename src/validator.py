import pandas as pd
from datetime import datetime, timedelta
import yaml

class HEDISValidator:
    """
    Validates generated mockup data against test case expectations.
    Implements HEDIS logic to verify compliance/non-compliance.
    """
    
    def __init__(self, config_path, mockup_path):
        self.config_path = config_path
        self.mockup_path = mockup_path
        self.config = self._load_config()
        self.data = self._load_mockup()
        self.results = []
        
    def _load_config(self):
        """Load measure configuration."""
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _load_mockup(self):
        """Load all sheets from mockup Excel."""
        return pd.read_excel(self.mockup_path, sheet_name=None)
    
    def validate_member(self, member_id, expected_result):
        """
        Validate a single member's data.
        
        Args:
            member_id: Member identifier
            expected_result: Expected compliance ('Compliant', 'Non-Compliant', 'Excluded')
        
        Returns:
            dict with validation results
        """
        result = {
            'member_id': member_id,
            'expected': expected_result,
            'actual': None,
            'pass': False,
            'details': []
        }
        
        # 1. Check Enrollment
        enrollment_valid = self._validate_enrollment(member_id, result)
        
        # 2. Check Age
        age_valid = self._validate_age(member_id, result)
        
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
        """Check continuous enrollment requirement."""
        measure_name = self.config['measure_name']
        enrollment_table = f"{measure_name}_ENROLLMENT_IN"
        
        if enrollment_table not in self.data:
            result['details'].append("❌ Enrollment table not found")
            return False
        
        df = self.data[enrollment_table]
        member_enrollments = df[df['MEM_NBR'] == member_id]
        
        if member_enrollments.empty:
            result['details'].append("❌ No enrollment records")
            return False
        
        # Check enrollment period
        req_months = self.config['rules']['continuous_enrollment']['period_months']
        allowable_gap = self.config['rules']['continuous_enrollment']['allowable_gap_days']
        
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
        """Check age requirement."""
        measure_name = self.config['measure_name']
        member_table = f"{measure_name}_MEMBER_IN"
        
        if member_table not in self.data:
            result['details'].append("❌ Member table not found")
            return False
        
        df = self.data[member_table]
        member_row = df[df['MEM_NBR'] == member_id]
        
        if member_row.empty:
            result['details'].append("❌ Member not found")
            return False
        
        dob = pd.to_datetime(member_row.iloc[0]['DOB'])
        age_as_of = datetime(2026, 12, 31)  # MY 2026
        age = (age_as_of - dob).days // 365
        
        age_min, age_max = self.config['rules']['age_range']
        
        if age_min <= age <= age_max:
            result['details'].append(f"✅ Age: {age} (in range {age_min}-{age_max})")
            return True
        else:
            result['details'].append(f"❌ Age: {age} (out of range {age_min}-{age_max})")
            return False
    
    def _check_exclusions(self, member_id, result):
        """Check if member has any exclusions."""
        measure_name = self.config['measure_name']
        
        # Check for common exclusion indicators
        member_table = f"{measure_name}_MEMBER_IN"
        if member_table in self.data:
            df = self.data[member_table]
            member_row = df[df['MEM_NBR'] == member_id]
            
            if not member_row.empty:
                # Check hospice flag
                if 'BEN_HOSPICE' in member_row.columns:
                    if pd.notna(member_row.iloc[0]['BEN_HOSPICE']) and member_row.iloc[0]['BEN_HOSPICE'] == 1:
                        result['details'].append("🚫 Exclusion: Hospice")
                        return True
                
                # Check death date
                if 'DEATH_DT' in member_row.columns:
                    if pd.notna(member_row.iloc[0]['DEATH_DT']):
                        result['details'].append("🚫 Exclusion: Death")
                        return True
        
        # Check visit/encounter tables for exclusion events
        visit_table = f"{measure_name}_VISIT_IN"
        if visit_table in self.data:
            df = self.data[visit_table]
            member_visits = df[df['MEM_NBR'] == member_id]
            
            # Look for hospice-related codes (simplified check)
            # In production, would check against VSD
            # For now, just check if any exclusion-related fields exist
        
        return False
    
    def _check_numerator(self, member_id, result):
        """Check if member has required clinical events."""
        measure_name = self.config['measure_name']
        numerator_components = self.config['rules']['clinical_events']['numerator_components']
        
        for component in numerator_components:
            table_name = component['table']
            
            if table_name not in self.data:
                result['details'].append(f"⚠️ Table {table_name} not found")
                continue
            
            df = self.data[table_name]
            member_events = df[df['MEM_NBR'] == member_id]
            
            if not member_events.empty:
                result['details'].append(f"✅ Numerator: {component['name']} found ({len(member_events)} events)")
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
