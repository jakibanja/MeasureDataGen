"""
Standard Format Parser - Simple parser for standardized test case files

This parser reads test cases in the universal standard format defined in
docs/STANDARD_TESTCASE_FORMAT.md

Much simpler and faster than the legacy parser since it doesn't need complex
regex patterns or AI fallback.
"""

import pandas as pd
import yaml
import re
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

        # ⚡ Apply Tester Syntax to SCENARIO_DESCRIPTION for flexibility
        desc = str(scenario['scenario']).lower()
        
        # PL: (Product Line)
        pl_match = re.search(r'pl\s*:\s*(\w+)', desc)
        if pl_match:
            pl_query = pl_match.group(1).lower()
            if 'comm' in pl_query: scenario['product_line'] = 'Commercial'
            elif 'medi-cal' in pl_query or 'mcd' in pl_query or 'medicaid' in pl_query: scenario['product_line'] = 'Medicaid'
            elif 'mcr' in pl_query or 'medicare' in pl_query: scenario['product_line'] = 'Medicare'
            elif 'exch' in pl_query or 'market' in pl_query: scenario['product_line'] = 'Exchange'

        # AG: (Age)
        ag_match = re.search(r'ag\s*:\s*(\d+)', desc)
        if ag_match: scenario['age'] = int(ag_match.group(1))

        # AD: (Anchor Date)
        ad_match = re.search(r'ad\s*:\s*([\d/MY\-\+]+)', desc, re.IGNORECASE)
        if ad_match: scenario['anchor_date'] = ad_match.group(1).strip()

        # ED: (Event Date)
        ed_match = re.search(r'ed\s*:\s*([\d/MY\-\+]+)', desc, re.IGNORECASE)
        if ed_match: scenario['event_date_override'] = ed_match.group(1).strip()

        # Parse enrollment periods
        scenario['enrollment_spans'] = self._parse_enrollments(row)
        
        # Parse visits
        scenario['visit_spans'] = self._parse_visits(row)
        
        # Parse clinical events
        scenario['compliant'] = self._parse_events(row, measure_config, scenario['overrides'])
        
        # CE: (Compliance Event Shorthand)
        for comp in measure_config.get('rules', {}).get('clinical_events', {}).get('numerator_components', []):
            kw = comp['name']
            if re.search(rf'\bce\s*[:=]\s*{kw.lower()}', desc) and kw not in scenario['compliant']:
                scenario['compliant'].append(kw)

        # Parse exclusions
        scenario['excluded'] = self._parse_exclusions(row, measure_config, scenario['overrides'])
        
        # NE: (Numerator Exclusion Shorthand)
        for excl in measure_config.get('rules', {}).get('exclusions', []):
            kw = excl['name']
            if re.search(rf'\bne\s*[:=]\s*{kw.lower()}', desc) and kw not in scenario['excluded']:
                scenario['excluded'].append(kw)

        # ⚡ Dynamic Passthrough: Catch-All for unknown columns
        # Any column NOT in this reserved list is treated as a direct override
        reserved_prefixes = ['MEMBER_ID', 'AGE', 'GENDER', 'PRODUCT_LINE', 'SCENARIO', 'EXPECTED', 'ENROLLMENT_', 'VISIT_', 'EVENT_', 'EXCLUSION_', 'NOTES']
        
        for col in row.index:
            col_str = str(col).strip().upper()
            if not any(col_str.startswith(prefix) for prefix in reserved_prefixes):
                # It's a custom column! (e.g. MEM_CITY, PROV_NPI)
                val = row[col]
                if pd.notna(val):
                    # Add to overrides['member'] or just 'overrides' depending on your engine logic
                    # For now, we put it in overrides['custom_columns'] and let Engine handle it, 
                    # OR we can just put it in the main specific override dict if we know the table.
                    # A safer bet is to assume it maps to MEMBER table or a specific table key if prefixed (e.g. MEMBER_IN.MEM_CITY)
                    
                    # Simple strategy: Direct key-value override
                    scenario['overrides'][col_str] = str(val).strip()

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
    
    def _parse_events(self, row: pd.Series, measure_config: Dict[str, Any], overrides: Dict[str, Any]) -> List[str]:
        """
        Parse clinical events from EVENT_X_NAME/VALUE columns.
        
        Returns:
            List of compliant component names
        """
        compliant = []
        
        # Get numerator components from measure config
        numerator_components = measure_config.get('rules', {}).get('clinical_events', {}).get('numerator_components', [])
        component_names = {comp['name'].lower(): comp['name'] for comp in numerator_components}
        
        # ⚡ Robust Column Matching (Direct columns like PSA_TEST)
        for col in row.index:
            col_str = str(col).strip().lower()
            # Skip reserved prefixes
            if any(col_str.startswith(p.lower()) for p in ['member_id', 'age', 'gender', 'product_line', 'enrollment', 'visit', 'notes']):
                continue
                
            # Match against component names
            matched_comp = None
            for comp_name_lower, real_name in component_names.items():
                # Exact match or component_name_test or component_name_val
                if col_str == comp_name_lower or col_str.replace('_', ' ') == comp_name_lower or col_str.startswith(comp_name_lower):
                    matched_comp = real_name
                    break
            
            if matched_comp:
                val = row[col]
                if self._is_truthy(val) and matched_comp not in compliant:
                    compliant.append(matched_comp)
                    # Look for date in sibling column
                    date_val = None
                    date_col = f"{col}_DATE"
                    if date_col in row:
                        date_val = row[date_col]
                    elif f"{col}_DT" in row:
                        date_val = row[f"{col}_DT"]
                        
                    meta = {'value': val}
                    if pd.notna(date_val): meta['date'] = str(date_val).strip()
                    
                    if 'events' not in overrides: overrides['events'] = {}
                    if matched_comp not in overrides['events']: overrides['events'][matched_comp] = []
                    overrides['events'][matched_comp].append(meta)

        # ⚡ Standard EVENT_X Matching
        for i in range(1, 11):
            name_col = f'EVENT_{i}_NAME'
            value_col = f'EVENT_{i}_VALUE'
            # ... (rest of old code structure)
            if name_col not in row or pd.isna(row[name_col]):
                continue
            
            event_name = str(row[name_col]).strip()
            event_value = row.get(value_col, 0)
            
            if self._is_truthy(event_value):
                event_name_matched = component_names.get(event_name.lower(), event_name)
                if event_name_matched not in compliant:
                    compliant.append(event_name_matched)
                
                # ... metadata handling ...
                code_col = f'EVENT_{i}_CODE'
                date_col = f'EVENT_{i}_DATE'
                event_meta = {'value': event_value}
                if code_col in row and pd.notna(row[code_col]): event_meta['code'] = str(row[code_col]).strip()
                if date_col in row and pd.notna(row[date_col]): event_meta['date'] = str(row[date_col]).strip()
                
                if 'events' not in overrides: overrides['events'] = {}
                if event_name_matched not in overrides['events']: overrides['events'][event_name_matched] = []
                overrides['events'][event_name_matched].append(event_meta)
        
        return compliant

    def _is_truthy(self, val) -> bool:
        """Helper to determine if a value indicates compliance."""
        if pd.isna(val): return False
        v_str = str(val).strip().upper()
        if v_str in ['1', 'Y', 'YES', 'TRUE', 'COMPLIANT', 'C']: return True
        try:
            return float(v_str) > 0
        except:
            return False

    def _parse_exclusions(self, row: pd.Series, measure_config: Dict[str, Any], overrides: Dict[str, Any]) -> List[str]:
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
                if val_str in ['1', 'Y', 'YES', 'TRUE', 'EXCLUDED']:
                    is_present = True
            
            if is_present:
                # Match exclusion name (case-insensitive)
                exclusion_name_matched = exclusion_name
                exclusion_name_lower = exclusion_name.lower()
                if exclusion_name_lower in exclusion_names:
                    exclusion_name_matched = exclusion_names[exclusion_name_lower]
                
                excluded.append(exclusion_name_matched)
                
                # Check for metadata (DATE)
                date_col = f'EXCLUSION_{i}_DATE'
                
                excl_meta = {}
                if date_col in row and pd.notna(row[date_col]):
                    excl_meta['date'] = str(row[date_col]).strip()
                    
                if excl_meta:
                    if 'exclusions' not in overrides: overrides['exclusions'] = {}
                    overrides['exclusions'][exclusion_name_matched] = excl_meta
        
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
