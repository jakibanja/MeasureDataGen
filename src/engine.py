import yaml
import pandas as pd
from datetime import datetime, timedelta
from faker import Faker

class MockupEngine:
    def __init__(self, measure_config_path, schema_map_path, vsd_manager=None):
        with open(measure_config_path, 'r') as f:
            self.measure = yaml.safe_load(f)
        with open(schema_map_path, 'r') as f:
            self.schema = yaml.safe_load(f)
            
        self.vsd_manager = vsd_manager
        self.year = 2026 # Default for MY 2026
        self.anchor_date = datetime(self.year, 12, 31)
        self.fake = Faker()
        
        # Product Line Mapping (Unified)
        self.pl_map = {
            "Medicare": 1,
            "Commercial": 2,
            "Medicaid": 3,
            "Exchange": 4
        }

    def calculate_birth_date(self, age):
        # Age as of Dec 31
        return datetime(self.year - age, 6, 15) # Middle of year birth

    def generate_member_base(self, mem_id, age, gender='F', overrides=None):
        dob = self.calculate_birth_date(age)
        
        # Seed faker with member ID for deterministic output
        self.fake.seed_instance(sum(ord(c) for c in mem_id))
        
        if gender == 'F':
            fname = self.fake.first_name_female()
        else:
            fname = self.fake.first_name_male()
            
        lname = self.fake.last_name()
        
        return {
            self.schema['tables']['member']['pk']: mem_id,
            self.schema['tables']['member']['fields']['dob']: dob,
            self.schema['tables']['member']['fields']['gender']: gender,
            self.schema['tables']['member']['fields']['first_name']: fname,
            self.schema['tables']['member']['fields']['last_name']: lname,
            self.schema['tables']['member']['fields']['middle_name']: self.fake.first_name()[0],
            self.schema['tables']['member']['fields']['addr1']: self.fake.street_address(),
            self.schema['tables']['member']['fields']['city']: self.fake.city(),
            self.schema['tables']['member']['fields']['state']: self.fake.state_abbr(),
            self.schema['tables']['member']['fields']['zip']: self.fake.zipcode(),
            self.schema['tables']['member']['fields']['ssn']: self.fake.ssn(),
            self.schema['tables']['member']['fields']['hic']: f"{self.fake.random_number(digits=9)}A",
            self.schema['tables']['member']['fields']['mbi']: self.fake.bothify(text='?#??-?#?-?#??').upper()
        }
        
        if overrides:
            for field, val in overrides.items():
                if field in res: res[field] = val
        return res

    def parse_date_str(self, date_str):
        # Handle "1/1/MY", "12/31/MY-1", "1/1/2050"
        date_str = date_str.lower().strip()
        str_year = str(self.year)
        
        # Replace MY+/-offset
        if 'my' in date_str:
            # Check for offsets like MY-1 or MY+1
            offset = 0
            if 'my-' in date_str:
                parts = date_str.split('my-')
                if len(parts) > 1 and parts[1][0].isdigit():
                    offset = -int(parts[1][0])
                    date_str = date_str.replace(f"my{offset}", str(self.year + offset))
            elif 'my+' in date_str:
                 parts = date_str.split('my+')
                 if len(parts) > 1 and parts[1][0].isdigit():
                    offset = int(parts[1][0])
                    date_str = date_str.replace(f"my+{offset}", str(self.year + offset))
            
            # Simple replacement if logic above didn't fully catch it or plain MY
            date_str = date_str.replace('my', str(self.year))
            
            # Clean up potential double operators if logic was loose
            # (Keeping it simple for now)
        
        try:
            return pd.to_datetime(date_str)
        except:
            return datetime(self.year, 1, 1)

    def generate_enrollments(self, mem_id, product_line="Medicare", spans=None, overrides=None):
        target_table = self.schema['tables']['enrollment']
        rows = []
        
        product_id = self.pl_map.get(product_line, 1)
        
        # Comprehensive Default flags and Identifiers based on user image
        base_record = {
            'BEN_MEDICAL': 1,
            'BEN_DENT': 0,
            'BEN_RX': 1,
            'BEN_MH_INP': 1,
            'BEN_MH_INT': 1,
            'BEN_MH_AMB': 1,
            'BEN_CD_INP': 1,
            'BEN_CD_INT': 1,
            'BEN_CD_AMB': 1,
            'BEN_HOSPICE': 0,
            'BEN_ESRD': 0,
            'BEN_OS': 0,
            'EMLS_ESCL_FL': 0,
            'SCH_ID': "K10",
            'GRP_ID': "1",
            'IP_EMPLOYER': "X",
            'EMP_ID': "K10",
            'MED_ORG_EXT_ID': "51",
            'COVERAGE_INDICATOR': "C",
            'PBP_NBR': "001",
            'SUB_TYPE': "",
            'ASO_IND': "",
            'CMS_NUMBER': "H0123",
            'PRODUCT_ID': product_id,
            'PRODUCT_ID_2': product_id
        }

        # If no explicit spans, default to full measurement year
        if not spans:
            spans = [{'start': f"1/1/my", 'end': f"12/31/my"}]

        for span in spans:
            start_dt = self.parse_date_str(span['start'])
            end_dt = self.parse_date_str(span['end'])
            
            p_id = span.get('product_id')
            final_pid = int(p_id) if (p_id and str(p_id).isdigit()) else product_id

            row = {
                target_table['pk']: mem_id,
                target_table['fields']['start_date']: start_dt,
                target_table['fields']['end_date']: end_dt,
                **base_record,
                'PRODUCT_ID': final_pid,
                'PRODUCT_ID_2': final_pid
            }

            # 1. Apply Global Overrides (Generic matches)
            if overrides:
                for f, v in overrides.items():
                    # Handle both exact field name and logical mapping
                    if f in row: 
                        row[f] = v
                    else:
                        # Try to find if it matches a mapped column
                        mapped_col = next((col for logic, col in target_table['fields'].items() if f == logic or f == col), None)
                        if mapped_col: row[mapped_col] = v
            
            # 2. Apply Span-specific overrides (Specific takes precedence)
            if 'coverage_indicator' in span:
                row['COVERAGE_INDICATOR'] = span['coverage_indicator']
            
            if 'BEN_HOSPICE' in span:
                row['BEN_HOSPICE'] = span['BEN_HOSPICE']

            # Calculate FLD00 - FLD23 (24 months: MY-1 and MY)
            # FLD00 = Jan MY-1, FLD12 = Jan MY
            for i in range(24):
                year_off = (i // 12) - 1 # -1 for first 12, 0 for second 12
                month = (i % 12) + 1
                target_month_start = datetime(self.year + year_off, month, 1)
                
                # Check if enrolled this month (at least one day)
                # Enrolled if start_dt <= last_day_of_month and end_dt >= first_day_of_month
                # For simplicity, check if target_month_start is within range or same month
                is_enrolled = 0
                if start_dt <= target_month_start <= end_dt:
                    is_enrolled = 1
                elif start_dt.year == target_month_start.year and start_dt.month == target_month_start.month:
                    is_enrolled = 1
                
                row[f"FLD{i:02d}"] = is_enrolled

            rows.append(row)
        
        return rows

    def generate_visits(self, mem_id, spans=None):
        target_table = self.schema['tables']['visit']
        rows = []
        
        # If no explicit spans, default to single IP visit
        if not spans:
            rows.append({
                target_table['fk']: mem_id,
                target_table['pk']: f"C_{mem_id}_01",
                target_table['fields']['date']: datetime(self.year, 2, 1),
                target_table['fields']['pos']: '11', # Office Visit
                "CPT_1": "99213" 
            })
        else:
            for i, v in enumerate(spans):
                 d = self.parse_date_str(v['date'])
                 rows.append({
                    target_table['fk']: mem_id,
                    target_table['pk']: f"C_{mem_id}_{i+1:02d}",
                    target_table['fields']['date']: d,
                    target_table['fields']['pos']: '11',
                    "CPT_1": "99213" 
                })
        
        return target_table['name'], rows

    def generate_clinical_event(self, mem_id, component_name, is_compliant=True, offset_days=0, overrides=None):
        # Locate component in measure config
        component = next((c for c in self.measure['rules']['clinical_events']['numerator_components'] if c['name'] == component_name), None)
        if not component:
            return None, None
        
        table_raw = component['table'] # e.g. PSA_LAB_IN
        table_key = table_raw.replace('PSA_', '').replace('_IN', '').lower()
        if table_key not in self.schema['tables']:
            # Fallback if names don't match exactly
            if 'VISIT' in table_raw: table_key = 'visit'
            elif 'EMR' in table_raw: table_key = 'emr'
            elif 'LAB' in table_raw: table_key = 'lab'
            else: table_key = 'visit'

        target_table = self.schema['tables'][table_key]
        event_date = datetime(self.year, 6, 1) + timedelta(days=offset_days)
        
        row = {
            target_table['fk'] if 'fk' in target_table else target_table['pk']: mem_id,
            target_table['fields']['date']: event_date
        }

        # Add specific values for compliance
        if is_compliant:
            # Try to get code from VSD if possible
            vsd_code = None
            if self.vsd_manager and component.get('value_set_names'):
                vsd_code = self.vsd_manager.get_random_code(component['value_set_names'][0])

            if component_name == "BMI Percentile":
                row[target_table['fields']['bmi_percentile']] = 85
            elif "Counseling" in component_name:
                code = vsd_code if vsd_code else ('Z71.3' if "Nutrition" in component_name else '97802')
                row[target_table['fields'].get('procedure_codes', ['CPT_1'])[0]] = code
            elif component_name == "PSA Test":
                row[target_table['fields'].get('cpt', 'LAB_CPT')] = vsd_code if vsd_code else '84153'
                row[target_table['fields'].get('value', 'LAB_VALUE')] = '1.0'
            elif vsd_code:
                # Catch-all for other components if we found a VSD code
                code_field = target_table['fields'].get('procedure_codes', [target_table['fields'].get('cpt', 'CPT_1')])[0]
                row[code_field] = vsd_code
        
        if overrides:
            for f, v in overrides.items():
                if f in row: row[f] = v

        return table_raw, row

    def generate_exclusion(self, mem_id, exclusion_name, overrides=None):
        # Find exclusion in config
        exclusion = next((e for e in self.measure['rules']['exclusions'] if e['name'] == exclusion_name), None)
        if not exclusion:
            return None, None
            
        event_date = datetime(self.year, 3, 15) # Early year exclusion
        
        # Try to get code from VSD
        vsd_code = None
        if self.vsd_manager and exclusion.get('value_set_names'):
            vsd_code = self.vsd_manager.get_random_code(exclusion['value_set_names'][0])

        if exclusion_name == "Hospice":
            # Per schema_map: monthly_membership table
            target_table = self.schema['tables']['monthly_membership']
            row = {
                target_table['fk']: mem_id,
                target_table['fields']['run_date']: event_date,
                target_table['fields']['hospice_flag']: 1 # Use numeric 1 for hospice
            }
            if overrides:
                for f, v in overrides.items():
                    if f in row or f == 'HOSPICE': row[target_table['fields']['hospice_flag']] = v
            return target_table['name'], row
            
        elif exclusion_name == "Pregnancy" or exclusion_name == "Prostate Cancer":
            # Per spec: usually Visit table with diagnosis code
            target_table = self.schema['tables']['visit']
            code = vsd_code if vsd_code else ('O09.212' if exclusion_name == "Pregnancy" else 'C61')
            row = {
                target_table['fk']: mem_id,
                target_table['fields']['date']: event_date,
                target_table['fields']['diagnosis_codes'][0]: code
            }
            return target_table['name'], row
            
        return None, None
