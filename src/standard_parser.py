"""
Standard Format Parser - Simple parser for standardized test case files

This parser reads test cases in the universal standard format defined in
docs/STANDARD_TESTCASE_FORMAT.md

Much simpler and faster than the legacy parser since it doesn't need complex
regex patterns or AI fallback.
"""

import pandas as pd
import yaml
from typing import Dict, List, Any, Optional


class StandardFormatParser:
    """
    Parser for standardized test case files.
    
    Reads test cases with clear column structure:
    - MEMBER_ID, AGE, GENDER, PRODUCT_LINE
    - ENROLLMENT_X_START, ENROLLMENT_X_END
    - VISIT_X_DATE
    - EVENT_X_NAME, EVENT_X_VALUE
    - EXCLUSION_X_NAME, EXCLUSION_X_VALUE
    """
    
    def __init__(self, file_path: str):
        """
        Initialize parser with test case file.
        
        Args:
            file_path: Path to standard format Excel file
        """
        self.file_path = file_path
        self.df = None
    
    def parse_scenarios(self, measure_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse all scenarios from standard format file.
        
        Args:
            measure_config: Measure configuration (from config/MEASURE.yaml)
        
        Returns:
            List of scenario dictionaries with parsed data
        """
        # Read Excel file
        self.df = pd.read_excel(self.file_path)
        
        print(f"  Loaded {len(self.df)} scenarios from standard format file")
        
        scenarios = []
        
        for idx, row in self.df.iterrows():
            scenario = self._parse_row(row, measure_config)
            if scenario:
                scenarios.append(scenario)
        
        return scenarios
    
    def _parse_row(self, row: pd.Series, measure_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse a single row into scenario dictionary.
        
        Args:
            row: DataFrame row
            measure_config: Measure configuration
        
        Returns:
            Scenario dictionary or None if invalid
        """
        # Skip rows without MEMBER_ID
        if pd.isna(row.get('MEMBER_ID')):
            return None
        
        scenario = {
            'id': str(row['MEMBER_ID']).strip(),
            'age': int(row.get('AGE', 70)),
            'gender': str(row.get('GENDER', 'M')).strip().upper(),
            'product_line': str(row.get('PRODUCT_LINE', 'Medicare')).strip(),
            'enrollment_spans': [],
            'visit_spans': [],
            'compliant': [],
            'excluded': [],
            'overrides': {},
            'scenario': row.get('SCENARIO_DESCRIPTION', ''),
            'expected': row.get('EXPECTED_RESULT', ''),
        }
        
        # Parse enrollment periods
        scenario['enrollment_spans'] = self._parse_enrollments(row)
        
        # Parse visits
        scenario['visit_spans'] = self._parse_visits(row)
        
        # Parse clinical events (compliant components)
        scenario['compliant'] = self._parse_events(row, measure_config)
        
        # Parse exclusions
        scenario['excluded'] = self._parse_exclusions(row, measure_config)
        
        return scenario
    
    def _parse_enrollments(self, row: pd.Series) -> List[Dict[str, Any]]:
        """
        Parse enrollment periods from ENROLLMENT_X_START/END columns.
        
        Returns:
            List of enrollment span dictionaries
        """
        enrollments = []
        
        # Check up to 10 enrollment periods
        for i in range(1, 11):
            start_col = f'ENROLLMENT_{i}_START'
            end_col = f'ENROLLMENT_{i}_END'
            pid_col = f'ENROLLMENT_{i}_PRODUCT_ID'
            
            if start_col not in row or pd.isna(row[start_col]):
                break  # No more enrollments
            
            enrollment = {
                'start': str(row[start_col]).strip(),
                'end': str(row[end_col]).strip() if pd.notna(row.get(end_col)) else '12/31/MY',
            }
            
            # Add product_id if specified
            if pid_col in row and pd.notna(row[pid_col]):
                enrollment['product_id'] = int(row[pid_col])
            
            enrollments.append(enrollment)
        
        # If no enrollments found, create default
        if not enrollments:
            enrollments.append({'start': '1/1/MY', 'end': '12/31/MY'})
        
        return enrollments
    
    def _parse_visits(self, row: pd.Series) -> List[Dict[str, str]]:
        """
        Parse visits from VISIT_X_DATE columns.
        
        Returns:
            List of visit dictionaries
        """
        visits = []
        
        # Check up to 10 visits
        for i in range(1, 11):
            date_col = f'VISIT_{i}_DATE'
            type_col = f'VISIT_{i}_TYPE'
            cpt_col = f'VISIT_{i}_CPT'
            diag_col = f'VISIT_{i}_DIAG'
            
            if date_col not in row or pd.isna(row[date_col]):
                break  # No more visits
            
            visit = {
                'date': str(row[date_col]).strip(),
            }
            
            # Add optional fields
            if type_col in row and pd.notna(row[type_col]):
                visit['type'] = str(row[type_col]).strip()
            if cpt_col in row and pd.notna(row[cpt_col]):
                visit['cpt'] = str(row[cpt_col]).strip()
            if diag_col in row and pd.notna(row[diag_col]):
                visit['diag'] = str(row[diag_col]).strip()
            
            visits.append(visit)
        
        return visits
    
    def _parse_events(self, row: pd.Series, measure_config: Dict[str, Any]) -> List[str]:
        """
        Parse clinical events from EVENT_X_NAME/VALUE columns.
        
        Returns:
            List of compliant component names
        """
        compliant = []
        
        # Get numerator components from measure config
        numerator_components = measure_config.get('rules', {}).get('clinical_events', {}).get('numerator_components', [])
        component_names = {comp['name'].lower(): comp['name'] for comp in numerator_components}
        
        # Check up to 10 events
        for i in range(1, 11):
            name_col = f'EVENT_{i}_NAME'
            value_col = f'EVENT_{i}_VALUE'
            
            if name_col not in row or pd.isna(row[name_col]):
                continue  # No event at this position
            
            event_name = str(row[name_col]).strip()
            event_value = row.get(value_col, 0)
            
            # Check if event is present (value = 1, Y, yes, etc.)
            is_present = False
            if pd.notna(event_value):
                val_str = str(event_value).strip().upper()
                if val_str in ['1', 'Y', 'YES', 'TRUE']:
                    is_present = True
                elif val_str.replace('.', '').isdigit():
                    # Numeric value (e.g., BMI percentile)
                    is_present = float(val_str) > 0
            
            if is_present:
                # Match event name to component name (case-insensitive)
                event_name_lower = event_name.lower()
                if event_name_lower in component_names:
                    compliant.append(component_names[event_name_lower])
                else:
                    # Add as-is if not found in config (might be valid)
                    compliant.append(event_name)
        
        return compliant
    
    def _parse_exclusions(self, row: pd.Series, measure_config: Dict[str, Any]) -> List[str]:
        """
        Parse exclusions from EXCLUSION_X_NAME/VALUE columns.
        
        Returns:
            List of exclusion names
        """
        excluded = []
        
        # Get exclusions from measure config
        exclusion_list = measure_config.get('rules', {}).get('exclusions', [])
        exclusion_names = {excl['name'].lower(): excl['name'] for excl in exclusion_list}
        
        # Check up to 5 exclusions
        for i in range(1, 6):
            name_col = f'EXCLUSION_{i}_NAME'
            value_col = f'EXCLUSION_{i}_VALUE'
            
            if name_col not in row or pd.isna(row[name_col]):
                continue  # No exclusion at this position
            
            exclusion_name = str(row[name_col]).strip()
            exclusion_value = row.get(value_col, 0)
            
            # Check if exclusion is present
            is_present = False
            if pd.notna(exclusion_value):
                val_str = str(exclusion_value).strip().upper()
                if val_str in ['1', 'Y', 'YES', 'TRUE']:
                    is_present = True
            
            if is_present:
                # Match exclusion name (case-insensitive)
                exclusion_name_lower = exclusion_name.lower()
                if exclusion_name_lower in exclusion_names:
                    excluded.append(exclusion_names[exclusion_name_lower])
                else:
                    # Add as-is if not found in config
                    excluded.append(exclusion_name)
        
        return excluded


# Example usage
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python standard_parser.py <STANDARD_FORMAT_FILE> [MEASURE]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    measure = sys.argv[2] if len(sys.argv) > 2 else 'PSA'
    
    # Load measure config
    config_path = f'config/{measure}.yaml'
    with open(config_path) as f:
        measure_config = yaml.safe_load(f)
    
    # Parse scenarios
    parser = StandardFormatParser(file_path)
    scenarios = parser.parse_scenarios(measure_config)
    
    print(f"\n✅ Parsed {len(scenarios)} scenarios")
    print(f"\nFirst scenario:")
    print(f"  ID: {scenarios[0]['id']}")
    print(f"  Age: {scenarios[0]['age']}")
    print(f"  Enrollments: {len(scenarios[0]['enrollment_spans'])}")
    print(f"  Visits: {len(scenarios[0]['visit_spans'])}")
    print(f"  Compliant: {scenarios[0]['compliant']}")
    print(f"  Excluded: {scenarios[0]['excluded']}")
