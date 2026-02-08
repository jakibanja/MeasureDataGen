"""
Enhanced Test Case Reformatter - Converts any messy test case to standard format

This reformatter takes messy, unstructured test case files and converts them
to the standard format defined in docs/STANDARD_TESTCASE_FORMAT.md
"""

import os
import pandas as pd
import re
from typing import Dict, List, Any, Optional
import yaml


class StandardTestCaseReformatter:
    """
    Converts messy test case files to standard format.
    
    Standard format has clear columns:
    - MEMBER_ID, AGE, GENDER, PRODUCT_LINE
    - ENROLLMENT_1_START, ENROLLMENT_1_END, ENROLLMENT_2_START, etc.
    - VISIT_1_DATE, VISIT_2_DATE, etc.
    - PSA_TEST, HOSPICE, etc. (measure-specific)
    """
    
    def __init__(self, measure: str = 'PSA', use_ai: bool = False):
        """
        Initialize reformatter.
        
        Args:
            measure: Measure name (PSA, WCC, IMA)
            use_ai: Whether to use AI for complex parsing (slower but more accurate)
        """
        self.measure = measure
        self.use_ai = use_ai
        self.ai_extractor = None
        
        if use_ai:
            try:
                from src.ai_extractor import AIScenarioExtractor
                print("🤖 Initializing AI Extractor for reformatting...")
                self.ai_extractor = AIScenarioExtractor(model_name="tinyllama")
            except Exception as e:
                print(f"⚠️  AI Extractor failed to initialize: {e}")
                print("   Continuing with regex-only mode")
    
    def reformat_file(self, input_path: str, output_path: Optional[str] = None) -> str:
        """
        Convert messy test case file to standard format.
        
        Args:
            input_path: Path to messy test case Excel file
            output_path: Path for output file (default: data/ folder with same filename)
        
        Returns:
            Path to standardized output file
        """
        if not output_path:
            # Extract filename and add _STANDARD suffix
            base_name = os.path.basename(input_path)
            name_without_ext = os.path.splitext(base_name)[0]
            # Save to data/ folder with _STANDARD suffix
            output_path = os.path.join('data', f'{name_without_ext}_STANDARD.xlsx')
        
        print(f"\n📋 Reformatting test case: {input_path}")
        print(f"   Output: {output_path}")
        
        # Read all sheets
        excel_file = pd.ExcelFile(input_path)
        print(f"   Found {len(excel_file.sheet_names)} sheets: {excel_file.sheet_names}")
        
        # Process each sheet and consolidate
        all_scenarios = []
        
        for sheet_name in excel_file.sheet_names:
            print(f"\n   Processing sheet: {sheet_name}")
            df = pd.read_excel(input_path, sheet_name=sheet_name, header=None)
            
            # Find header row
            header_row = self._find_header_row(df)
            if header_row is None:
                print(f"      ⚠️  No header found, skipping sheet")
                continue
            
            # Set headers
            df.columns = df.iloc[header_row]
            df = df.iloc[header_row + 1:].reset_index(drop=True)
            
            # Process each row
            for idx, row in df.iterrows():
                scenario = self._parse_row_to_standard(row, sheet_name)
                if scenario and scenario.get('MEMBER_ID'):
                    all_scenarios.append(scenario)
            
            print(f"      ✓ Extracted {len(all_scenarios)} scenarios from this sheet")
        
        # Convert to DataFrame with standard columns
        standard_df = pd.DataFrame(all_scenarios)
        
        # Ensure all standard columns exist
        standard_columns = self._get_standard_columns()
        for col in standard_columns:
            if col not in standard_df.columns:
                standard_df[col] = None
        
        # Reorder columns
        standard_df = standard_df[standard_columns]
        
        # Write to Excel
        standard_df.to_excel(output_path, index=False, sheet_name=f'{self.measure}_Standard')
        
        print(f"\n✅ Reformatting complete!")
        print(f"   Total scenarios: {len(all_scenarios)}")
        print(f"   Output file: {output_path}")
        
        return output_path
    
    def _find_header_row(self, df: pd.DataFrame) -> Optional[int]:
        """Find the row containing column headers."""
        for idx, row in df.iterrows():
            row_str = ' '.join([str(v).upper() for v in row.values if pd.notna(v)])
            # Look for common header indicators
            if any(indicator in row_str for indicator in ['MEMBER', 'MEM_NBR', '#TC', 'TEST CASE', 'SCENARIO']):
                return idx
        return None
    
    def _parse_row_to_standard(self, row: pd.Series, sheet_name: str) -> Dict[str, Any]:
        """
        Parse a messy row into standard format.
        
        Returns dict with standard column names.
        """
        scenario = {}
        
        # Combine all row data for pattern matching
        row_text = ' '.join([str(v) for v in row.values if pd.notna(v)])
        row_text_lower = row_text.lower()
        
        # Use AI if enabled and available
        if self.use_ai and self.ai_extractor:
            try:
                ai_data = self.ai_extractor.extract_scenario_info({
                    'id': str(row.get('MEMBER_ID', row.get('MEM_NBR', ''))),
                    'scenario': row_text,
                    'expected': str(row.get('EXPECTED_RESULT', ''))
                })
                # Overlay AI data onto scenario early
                if ai_data.get('age'): scenario['AGE'] = ai_data['age']
                if ai_data.get('gender'): scenario['GENDER'] = ai_data['gender']
                if ai_data.get('product_line'): scenario['PRODUCT_LINE'] = ai_data['product_line']
            except:
                pass

        # 1. Extract MEMBER_ID
        scenario['MEMBER_ID'] = self._extract_member_id(row)
        if not scenario.get('MEMBER_ID'):
            return {}  # Skip rows without member ID
        
        # 2. Extract AGE
        scenario['AGE'] = self._extract_age(row, row_text)
        
        # 3. Extract GENDER
        scenario['GENDER'] = self._extract_gender(row, row_text)
        
        # 4. Extract PRODUCT_LINE
        scenario['PRODUCT_LINE'] = self._extract_product_line(row, row_text)
        
        # 5. Extract ENROLLMENT periods
        enrollments = []
        if self.use_ai and self.ai_extractor and ai_data.get('enrollment_spans'):
            enrollments = ai_data['enrollment_spans']
        else:
            enrollments = self._extract_enrollments(row, row_text)
            
        for i, enr in enumerate(enrollments[:5], 1):
            scenario[f'ENROLLMENT_{i}_START'] = enr.get('start')
            scenario[f'ENROLLMENT_{i}_END'] = enr.get('end')
            if enr.get('product_id'):
                scenario[f'ENROLLMENT_{i}_PRODUCT_ID'] = enr.get('product_id')
        
        # 6. Extract VISITS
        visits = []
        if self.use_ai and self.ai_extractor and ai_data.get('clinical_events'):
            # Filter for generic visits or use all clinical events as visits if they have dates
            for evt in ai_data['clinical_events']:
                if isinstance(evt, dict) and evt.get('date'):
                    visits.append(evt)
        
        if not visits:
            visits = self._extract_visits(row, row_text)
            
        for i, visit in enumerate(visits[:5], 1):
            scenario[f'VISIT_{i}_DATE'] = visit.get('date')
            if visit.get('type'):
                scenario[f'VISIT_{i}_TYPE'] = visit.get('type')
        
        # 7. Extract CLINICAL EVENTS & EXCLUSIONS (Universal Layout)
        events = []
        exclusions = []
        
        if self.measure == 'PSA':
            if self._extract_psa_test(row, row_text) == 1:
                events.append({'name': 'PSA Test', 'value': 1})
            if self._extract_hospice(row, row_text) == 1:
                exclusions.append({'name': 'Hospice', 'value': 1})
            if self._extract_prostate_cancer(row, row_text) == 1:
                exclusions.append({'name': 'Prostate Cancer', 'value': 1})
            if self._extract_deceased(row, row_text) == 1:
                exclusions.append({'name': 'Deceased', 'value': 1})
        elif self.measure == 'WCC':
            # Add WCC specific logic if needed
            pass
            
        # Distribute into EVENT_i columns
        for i, evt in enumerate(events[:5], 1):
            scenario[f'EVENT_{i}_NAME'] = evt['name']
            scenario[f'EVENT_{i}_VALUE'] = evt['value']
            scenario[f'EVENT_{i}_DATE'] = evt.get('date', '6/1/2026')
            
        # Distribute into EXCLUSION_i columns
        for i, exc in enumerate(exclusions[:3], 1):
            scenario[f'EXCLUSION_{i}_NAME'] = exc['name']
            scenario[f'EXCLUSION_{i}_VALUE'] = exc['value']
            scenario[f'EXCLUSION_{i}_DATE'] = exc.get('date', '3/15/2026')
        
        # 8. Extract EXPECTED_RESULT
        scenario['EXPECTED_RESULT'] = self._extract_expected_result(row, row_text)
        
        # 9. Extract SCENARIO_DESCRIPTION
        scenario['SCENARIO_DESCRIPTION'] = self._extract_description(row, row_text, sheet_name)
        
        return scenario
    
    def _extract_member_id(self, row: pd.Series) -> Optional[str]:
        """Extract member ID from row."""
        # Check first few columns for ID-like values
        for val in row.iloc[:5]:
            if pd.notna(val):
                val_str = str(val).strip()
                # Look for patterns like PSA_CE_01, WCC_01, etc.
                if re.match(r'^[A-Z_0-9]+$', val_str) and len(val_str) > 3:
                    return val_str
        return None
    
    def _extract_age(self, row: pd.Series, row_text: str) -> Optional[int]:
        """Extract age from row."""
        # Look for age patterns
        age_match = re.search(r'\b(6[6-9]|7[0-9]|8[0-9]|9[0-9]|1[0-9]{2})\b', row_text)
        if age_match:
            return int(age_match.group(1))
        return 70  # Default age
    
    def _extract_gender(self, row: pd.Series, row_text: str) -> str:
        """Extract gender from row."""
        if re.search(r'\b(male|m)\b', row_text.lower()):
            return 'M'
        elif re.search(r'\b(female|f)\b', row_text.lower()):
            return 'F'
        return 'M'  # Default
    
    def _extract_product_line(self, row: pd.Series, row_text: str) -> str:
        """Extract product line from row."""
        text_lower = row_text.lower()
        if 'medicare' in text_lower:
            return 'Medicare'
        elif 'commercial' in text_lower:
            return 'Commercial'
        elif 'medicaid' in text_lower:
            return 'Medicaid'
        elif 'exchange' in text_lower:
            return 'Exchange'
        return 'Medicare'  # Default
    
    def _extract_enrollments(self, row: pd.Series, row_text: str) -> List[Dict[str, str]]:
        """
        Extract enrollment periods from row.
        
        Handles formats like:
        - "1/1/MY-1 TO 10/1/MY"
        - "1/1/MY-1 TO 10/1/MY, 11/14/MY TO 12/31/MY"
        - "Product_ID=1, 1/1/MY TO 12/31/MY"
        """
        enrollments = []
        
        # Pattern: date TO date
        pattern = r'(\d{1,2}/\d{1,2}/[A-Z0-9\-+]+)\s*(?:TO|to|-|–)\s*(\d{1,2}/\d{1,2}/[A-Z0-9\-+]+)'
        matches = re.findall(pattern, row_text)
        
        for start, end in matches:
            enr = {'start': start.strip(), 'end': end.strip()}
            
            # Try to find associated product_id
            # Look for "Product_ID=X" near this enrollment
            pid_match = re.search(r'Product_ID\s*=\s*(\d+)', row_text)
            if pid_match:
                enr['product_id'] = int(pid_match.group(1))
            
            enrollments.append(enr)
        
        # If no enrollments found, create default
        if not enrollments:
            enrollments.append({'start': '1/1/MY', 'end': '12/31/MY'})
        
        return enrollments
    
    def _extract_visits(self, row: pd.Series, row_text: str) -> List[Dict[str, str]]:
        """
        Extract visit dates from row.
        
        Handles formats like:
        - "2/1/MY"
        - "Visit: 2/1/MY, 6/15/MY"
        - "Product_ID=1, CE=1, AD=1" (multiple events)
        """
        visits = []
        
        # Look for standalone dates (not in enrollment patterns)
        # Pattern: date not followed by TO
        pattern = r'(\d{1,2}/\d{1,2}/[A-Z0-9\-+]+)(?!\s*(?:TO|to))'
        potential_dates = re.findall(pattern, row_text)
        
        # Filter out dates that are in enrollment patterns
        enrollment_pattern = r'(\d{1,2}/\d{1,2}/[A-Z0-9\-+]+)\s*(?:TO|to|-|–)\s*(\d{1,2}/\d{1,2}/[A-Z0-9\-+]+)'
        enrollment_dates = set()
        for start, end in re.findall(enrollment_pattern, row_text):
            enrollment_dates.add(start.strip())
            enrollment_dates.add(end.strip())
        
        for date in potential_dates:
            if date.strip() not in enrollment_dates:
                visits.append({'date': date.strip()})
        
        # Also look for multiple events pattern: "Product_ID=X, CE=1, AD=1"
        # Each such pattern represents a visit
        event_pattern = r'Product_ID\s*=\s*\d+\s*,\s*CE\s*=\s*1'
        event_matches = re.findall(event_pattern, row_text)
        
        # If we found multiple event patterns but no explicit dates, create visits
        if len(event_matches) > len(visits):
            # Create additional visits for each event
            for i in range(len(event_matches) - len(visits)):
                visits.append({'date': '2/1/MY'})  # Default visit date
        
        return visits
    
    def _extract_psa_test(self, row: pd.Series, row_text: str) -> int:
        """Extract PSA test indicator (1 or 0)."""
        text_lower = row_text.lower()
        # Look for CE=1, PSA, Lab Test, etc.
        if re.search(r'\bce\s*[:=]\s*1\b', text_lower):
            return 1
        if 'psa' in text_lower and 'no psa' not in text_lower:
            return 1
        if 'lab test' in text_lower:
            return 1
        return 0
    
    def _extract_hospice(self, row: pd.Series, row_text: str) -> int:
        """Extract hospice indicator."""
        text_lower = row_text.lower()
        if 'hospice' in text_lower:
            return 1
        return 0
    
    def _extract_prostate_cancer(self, row: pd.Series, row_text: str) -> int:
        """Extract prostate cancer indicator."""
        text_lower = row_text.lower()
        if 'prostate cancer' in text_lower or 'prostate ca' in text_lower:
            return 1
        return 0
    
    def _extract_deceased(self, row: pd.Series, row_text: str) -> int:
        """Extract deceased indicator."""
        text_lower = row_text.lower()
        if 'deceased' in text_lower or 'death' in text_lower:
            return 1
        return 0
    
    def _extract_expected_result(self, row: pd.Series, row_text: str) -> Optional[str]:
        """Extract expected result."""
        text_lower = row_text.lower()
        if 'compliant' in text_lower and 'not compliant' not in text_lower:
            return 'Compliant'
        elif 'not compliant' in text_lower or 'non-compliant' in text_lower:
            return 'Not Compliant'
        elif 'excluded' in text_lower or 'exclusion' in text_lower:
            return 'Excluded'
        elif 'not tested' in text_lower:
            return 'Not Tested'
        return None
    
    def _extract_description(self, row: pd.Series, row_text: str, sheet_name: str) -> str:
        """Extract or generate scenario description."""
        # Look for description-like columns
        for val in row.values:
            if pd.notna(val):
                val_str = str(val).strip()
                # If it's a long text (>20 chars) and contains spaces, likely a description
                if len(val_str) > 20 and ' ' in val_str:
                    return val_str
        
        # Generate description from sheet name and member ID
        return f"{sheet_name} scenario"
    
    def _get_standard_columns(self) -> List[str]:
        """Get list of standard column names in order."""
        columns = [
            # Core identifiers
            'MEMBER_ID',
            'AGE',
            'GENDER',
            'PRODUCT_LINE',
            
            # Enrollments (up to 5)
            'ENROLLMENT_1_START',
            'ENROLLMENT_1_END',
            'ENROLLMENT_1_PRODUCT_ID',
            'ENROLLMENT_2_START',
            'ENROLLMENT_2_END',
            'ENROLLMENT_2_PRODUCT_ID',
            'ENROLLMENT_3_START',
            'ENROLLMENT_3_END',
            'ENROLLMENT_3_PRODUCT_ID',
            'ENROLLMENT_4_START',
            'ENROLLMENT_4_END',
            'ENROLLMENT_4_PRODUCT_ID',
            'ENROLLMENT_5_START',
            'ENROLLMENT_5_END',
            'ENROLLMENT_5_PRODUCT_ID',
            
            # Visits (up to 5)
            'VISIT_1_DATE', 'VISIT_1_TYPE', 'VISIT_1_CPT', 'VISIT_1_DIAG',
            'VISIT_2_DATE', 'VISIT_2_TYPE', 'VISIT_2_CPT', 'VISIT_2_DIAG',
            'VISIT_3_DATE', 'VISIT_3_TYPE', 'VISIT_3_CPT', 'VISIT_3_DIAG',
            'VISIT_4_DATE', 'VISIT_4_TYPE', 'VISIT_4_CPT', 'VISIT_4_DIAG',
            'VISIT_5_DATE', 'VISIT_5_TYPE', 'VISIT_5_CPT', 'VISIT_5_DIAG',

            # Events (Universal Layout - up to 5)
            'EVENT_1_NAME', 'EVENT_1_VALUE', 'EVENT_1_DATE', 'EVENT_1_CODE',
            'EVENT_2_NAME', 'EVENT_2_VALUE', 'EVENT_2_DATE', 'EVENT_2_CODE',
            'EVENT_3_NAME', 'EVENT_3_VALUE', 'EVENT_3_DATE', 'EVENT_3_CODE',
            'EVENT_4_NAME', 'EVENT_4_VALUE', 'EVENT_4_DATE', 'EVENT_4_CODE',
            'EVENT_5_NAME', 'EVENT_5_VALUE', 'EVENT_5_DATE', 'EVENT_5_CODE',

            # Exclusions (Universal Layout - up to 3)
            'EXCLUSION_1_NAME', 'EXCLUSION_1_VALUE', 'EXCLUSION_1_DATE',
            'EXCLUSION_2_NAME', 'EXCLUSION_2_VALUE', 'EXCLUSION_2_DATE',
            'EXCLUSION_3_NAME', 'EXCLUSION_3_VALUE', 'EXCLUSION_3_DATE',
            
            # Metadata
            'EXPECTED_RESULT',
            'SCENARIO_DESCRIPTION',
        ]
        
        return columns


# CLI usage
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python standard_reformatter.py <INPUT_FILE> [OUTPUT_FILE] [--measure PSA] [--use-ai]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else None
    
    measure = 'PSA'
    use_ai = False
    
    for arg in sys.argv:
        if arg.startswith('--measure='):
            measure = arg.split('=')[1]
        elif arg == '--use-ai':
            use_ai = True
    
    reformatter = StandardTestCaseReformatter(measure=measure, use_ai=use_ai)
    reformatter.reformat_file(input_file, output_file)
