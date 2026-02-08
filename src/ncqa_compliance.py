"""
NCQA Compliance Checker - Validates generated mockup data against NCQA rules
"""

import pandas as pd
import os
import yaml

class NCQAComplianceChecker:
    def __init__(self, measure_config, ncqa_spec_path=None, vsd_manager=None):
        self.config = measure_config
        self.ncqa_spec = None
        self.vsd_manager = vsd_manager  # Optional VSD Manager for code validation
        
        # Load NCQA spec if path provided
        if ncqa_spec_path and os.path.exists(ncqa_spec_path):
            with open(ncqa_spec_path, 'r') as f:
                self.ncqa_spec = yaml.safe_load(f)
        
    def check_compliance(self, output_data, scenarios=None):
        """
        Validate data against NCQA rules, Scenario expectations, AND VSD Codes.
        """
        issues = []
        
        # ... (Age/Enrollment checks remain the same) ...
        
        # 1. Check Age Distribution
        if 'MEMBER_IN' in output_data:
            member_df = output_data['MEMBER_IN']
            if 'AGE' in member_df.columns:
                ages = member_df['AGE'].dropna().astype(int)
                rules = self.ncqa_spec.get('rules', {}) if self.ncqa_spec else self.config.get('rules', {})
                min_age, max_age = rules.get('age_range', [0, 100])
                out_of_range = ages[(ages < min_age) | (ages > max_age)]
                if not out_of_range.empty:
                    issues.append(f"Found {len(out_of_range)} members with age outside allowed range {min_age}-{max_age}")
        
        # 2. Check Enrollment Logic
        if 'ENROLLMENT_IN' in output_data:
            enroll_df = output_data['ENROLLMENT_IN']
            if 'START_DATE' in enroll_df.columns and 'END_DATE' in enroll_df.columns:
                invalid_dates = enroll_df[enroll_df['START_DATE'] > enroll_df['END_DATE']]
                if not invalid_dates.empty:
                    issues.append(f"Found {len(invalid_dates)} enrollment records with Start Date > End Date")

        
        # 3. Identify Clinical Tables (Common for Scenario & VSD checks)
        clinical_tables = [t for t in output_data.keys() if t not in ['MEMBER_IN', 'ENROLLMENT_IN']]

        # 4. Check Scenario Compliance
        if scenarios:
            compliant_members = set()
            for sc in scenarios:
                if sc.get('compliant'):
                    compliant_members.add(str(sc['id']))
            
            found_members = set()
            for table in clinical_tables:
                df = output_data[table]
                if 'MEM_ID' in df.columns:
                    found_members.update(df['MEM_ID'].astype(str).unique())
            
            missing_compliance = compliant_members - found_members
            if missing_compliance:
                issues.append(f"❌ {len(missing_compliance)} members expected to be compliant but have NO clinical events: {list(missing_compliance)[:5]}...")

        # 5. VSD Code Validation
        if self.vsd_manager:
            for table in clinical_tables:
                df = output_data[table]
                if '_CODE' in df.columns and '_VALUE_SET_NAME' in df.columns:
                    unique_codes = df[['_CODE', '_VALUE_SET_NAME']].drop_duplicates()
                    for _, row in unique_codes.iterrows():
                        code = row['_CODE']
                        vs_name = row['_VALUE_SET_NAME']
                        if not code or str(code).lower() in ['none', 'nan', '']:
                             issues.append(f"❌ Found invalid/empty code in table {table} for Value Set {vs_name}")


        
        # Calculate score
        # Start with 100, deduct 5 points per issue
        compliance_score = max(0, 100 - (len(issues) * 5))
        
        return {
            'score': compliance_score,
            'issues': issues,
            'passed': len(issues) == 0  # Strict compliance: passed only if NO issues
        }
