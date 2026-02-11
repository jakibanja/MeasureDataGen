import yaml
import re
import os
import json
import pandas as pd
from datetime import datetime, timedelta
from faker import Faker

class MockupEngine:
    def __init__(self, measure_config_path, schema_path, vsd_manager=None, year=2026, measure_name_override=None, mocking_depth='population', column_scope='all'):
        with open(measure_config_path, 'r') as f:
            self.measure = yaml.safe_load(f)
        
        with open(schema_path, 'r') as f:
            self.schema = yaml.safe_load(f)
            
        # ⚡ Dynamic Schema Prefixing: Replace {MEASURE} with actual measure name
        measure_name = measure_name_override if measure_name_override else self.measure.get('measure_name', 'PSA')
        for table_key in self.schema['tables']:
            table_name = self.schema['tables'][table_key]['name']
            if '{MEASURE}' in table_name:
                self.schema['tables'][table_key]['name'] = table_name.format(MEASURE=measure_name)
                
        self.year = year
        self.fake = Faker()
        self.vsd_manager = vsd_manager
        self.mocking_depth = mocking_depth
        self.column_scope = column_scope
        
        print(f"MockupEngine initialized for {measure_name} (MY {year}) | Depth={mocking_depth}, Scope={column_scope}")
        
        # ⚡ Professional Config: Load Product Line IDs from file
        product_config_path = os.path.join(os.path.dirname(measure_config_path), 'products.yaml')
        if os.path.exists(product_config_path):
            with open(product_config_path, 'r') as f:
                self.product_config = yaml.safe_load(f)
        else:
            self.product_config = {}

        # Product Line Mapping (Unified) - Keep for backward compatibility
        self.pl_map = {
            "Medicare": 1,
            "Commercial": 2,
            "Medicaid": 3,
            "Exchange": 4
        }
        
        # ⚡ Phase 3: Load External Medication Code Overrides (NDC/RxNorm)
        self.medication_codes = {}
        med_codes_path = os.path.join(os.getcwd(), 'data', 'HEDIS_Medication_Codes.json')
        if os.path.exists(med_codes_path):
            with open(med_codes_path, 'r') as f:
                self.medication_codes = json.load(f)
            print(f"  🎯 Loaded {len(self.medication_codes)} HEDIS Medication Value Sets for code overrides.")

    def calculate_birth_date(self, age):
        # Age as of Dec 31
        return datetime(self.year - age, 6, 15) # Middle of year birth

    def validate_demographics(self, age, gender):
        """
        Validates age/gender against config-defined stratification rules (e.g. SPCE).
        Smart Fallback logic: 
        1. If explicit age/gender provided -> Priority (Fidelity)
        2. If missing -> HEDIS rule enforcement (Safety Net)
        """
        # --- FIDELITY FIRST: Respect explicit test scenario data ---
        # If age is valid (>0) and gender is provided, return them as is.
        # This allows for negative/exclusion testing (e.g. testing an 80yo for a 21-75 range).
        explicit_age = age if (age and age > 0) else None
        explicit_gender = gender if (gender and gender in ['M', 'F']) else None
        
        # If both are explicit, we are done
        if explicit_age and explicit_gender:
            return True, explicit_age, explicit_gender

        # --- SMART FALLBACK: If missing, look for HEDIS rules ---
        strat = self.measure['rules'].get('age_stratification', [])
        
        # Find matching rule or default
        rule = None
        if explicit_gender:
            rule = next((s for s in strat if s.get('gender', '').upper() == explicit_gender.upper()), None)
        
        if not rule:
            rule = strat[0] if strat else {'age_range': self.measure['rules'].get('age_range', [18, 100])}
            if not explicit_gender:
                explicit_gender = rule.get('gender', 'M')

        rng = rule.get('age_range', [18, 100])
        
        # If age was missing, suggest midpoint
        if not explicit_age:
            explicit_age = (rng[0] + rng[1]) // 2
            return False, explicit_age, explicit_gender
        
        # If age was provided but gender was missing, we still return the explicit age
        return True, explicit_age, explicit_gender

    def generate_member_base(self, mem_id, age, gender='F', overrides=None):
        # ⚡ Smart Fallback: Prioritize fidelity, auto-heal missing data
        is_valid, age, gender = self.validate_demographics(age, gender)
        if not is_valid:
            print(f"  ✨ [Smart Fallback] Auto-populated missing demographics for {mem_id}: Age {age}, Gender {gender}")

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
        
        # ⚡ Robustness: specific handle for non-string types (already dates)
        if hasattr(date_str, 'strftime'):
            return date_str
            
        date_str = str(date_str).lower().strip()
        str_year = str(self.year)
        
        # Replace MY+/-offset
        if 'my' in date_str:
            # Check for offsets like MY-1 or MY+1
            offset = 0
            if 'my-' in date_str:
                parts = date_str.split('my-')
                if len(parts) > 1 and len(parts[1]) > 0 and parts[1][0].isdigit():
                    offset = -int(parts[1][0])
                    date_str = date_str.replace(f"my{offset}", str(self.year + offset))
            elif 'my+' in date_str:
                 parts = date_str.split('my+')
                 if len(parts) > 1 and len(parts[1]) > 0 and parts[1][0].isdigit():
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

    def generate_visits(self, mem_id, spans=None, overrides=None, product_line='COMMERCIAL'):
        target_table = self.schema['tables']['visit']
        rows = []
        
        # If no explicit spans
        if not spans:
            if self.mocking_depth == 'scenario':
                # Skip default/random visit for cleaner "scenario-only" output
                return target_table['name'], []
            else:
                # Default "population" behavior: always has one visit
                spans = [{'date': datetime(self.year, 2, 1), 'type': 'Outpatient'}]
            
        for i, v in enumerate(spans):
            d = self.parse_date_str(v['date'])
            v_type = str(v.get('type', 'Outpatient')).strip()
            
            # ⚡ Dynamic Code Selection based on Visit Type (Code vs Description)
            cpt_code = "99213"  # Default Outpatient
            diag_code = "Z00.00"
            pos_code = "11"     # Office
            rev_code = ""

            resolved_code = None
            resolved_system = "Unknown"
            
            is_explicit_code = False
            
            # 1. explicit code check
            # Heuristic: Uppercase alphanumeric, 3-7 chars, no spaces = Code
            if re.match(r'^[A-Z0-9]{3,7}$', v_type, re.IGNORECASE):
                 if v_type.upper() not in ["OFFICE", "HOME", "VISIT", "LTC", "SNF", "ED", "ER", "URGENT", "CLINIC"]:
                     resolved_code = v_type.upper()
                     is_explicit_code = True
                     # Lookup system in VSD
                     if self.vsd_manager:
                         sys = self.vsd_manager.get_code_system(resolved_code)
                         if sys != 'Unknown':
                             resolved_system = sys
                         else:
                             # Inference fallback
                             if len(resolved_code) == 3 and resolved_code.isdigit(): resolved_system = 'UBREV'
                             elif '.' in resolved_code: resolved_system = 'ICD-10-CM'
                             else: resolved_system = 'CPT'
            
            # 2. Value Set Lookup (if not explicit code)
            if not is_explicit_code:
                # Text-based Logic for Pos/Defaults
                if "Inpatient" in v_type:
                    cpt_code = "99221"; pos_code = "21"
                elif "ED" in v_type or "Emergency" in v_type:
                    cpt_code = "99281"; pos_code = "23"
                elif "Telehealth" in v_type:
                    pos_code = "02"

                if self.vsd_manager:
                    # Find code from pattern
                    candidates = self.vsd_manager.find_value_sets(v_type)
                    if not candidates and "Outpatient" not in v_type and "Inpatient" not in v_type:
                         candidates = self.vsd_manager.find_value_sets("Outpatient")
                    
                    if candidates:
                        # Pick random value set, then random code
                        vs_name = candidates[0] 
                        code = self.vsd_manager.get_random_code(vs_name)
                        if code:
                            resolved_code = code
                            resolved_system = self.vsd_manager.get_code_system(code)
            
            # 3. ⚡ Smart Routing
            if resolved_code:
                sys_upper = str(resolved_system).upper()
                if any(x in sys_upper for x in ['CPT', 'HCPCS', 'PROCEDURE']):
                    cpt_code = resolved_code
                elif any(x in sys_upper for x in ['ICD', 'DIAGNOSIS', 'CM']):
                    diag_code = resolved_code
                elif any(x in sys_upper for x in ['REV', 'UBREV', 'REVENUE']):
                    rev_code = resolved_code

            # Always try to get a relevant diagnosis code if we don't have one yet
            # (Or if the resolved code was a Procedure, we still need a Diag)
            if diag_code == "Z00.00" and self.vsd_manager:
                 vsd_diag = self.vsd_manager.get_random_code_from_pattern("Diagnosis")
                 if vsd_diag: diag_code = vsd_diag

            row_data = {
                target_table['fk']: mem_id,
                target_table['pk']: f"C_{mem_id}_{i+1:02d}",
                target_table['fields']['date']: d,
                target_table['fields']['pos']: pos_code,
                "CPT_1": cpt_code,
                "DIAG_I_1": diag_code
            }
            if rev_code:
                row_data["REVENUE_CODE"] = rev_code
                
            # 4. ⚡ Apply Pinned Overrides (V1: DIAG=...)
            if overrides and 'pinned_visits' in overrides:
                # 1-based index support (V1 matches i=0)
                visit_idx = i + 1
                if visit_idx in overrides['pinned_visits']:
                    specific_meta = overrides['pinned_visits'][visit_idx]
                    for k, v in specific_meta.items():
                        # robust mapping
                        # 1. Check if key is a direct physical column (e.g. CPT_1)
                        if k in row_data:
                            row_data[k] = v
                        # 2. Check if key matches a logical field name (e.g. 'pos' -> 'POS')
                        elif k.lower() in target_table['fields']:
                            phy_col = target_table['fields'][k.lower()]
                            row_data[phy_col] = v
                        # 3. Fallback: Upper case key matches physical column?
                        elif k.upper() in row_data:
                             row_data[k.upper()] = v
                        else:
                             # 4. Insert as-is (might be a new column not in standard schema)
                             row_data[k] = v

            # Populate extra fields if scope is 'all'
            if self.column_scope == 'all':
                # Determine product line from overrides or default? Use generic default for now as standard visits don't carry PL info yet
                self._populate_visit_fields(row_data, target_table, mem_id, product_line=product_line)

            rows.append(row_data)
        
        return target_table['name'], rows

    def generate_composite_event(self, mem_id, component_config, base_date, overrides=None, product_line='COMMERCIAL'):
        """
        Generates multiple events based on a complex component definition.
        """
        events = []
        count = component_config.get('count', 1)
        sub_events = component_config.get('events', [])
        
        # If no explicit sub-events, treat config itself as one
        if not sub_events:
            sub = component_config.copy()
            # Ensure it has basic fields
            if 'table' not in sub: sub['table'] = 'visit'
            if 'value_set_names' not in sub: sub['value_set_names'] = []
            sub_events = [sub]

        for i in range(count):
            # Stagger dates: Each iteration moves forward
            # Base date + (Iteration * Separation)
            sep = component_config.get('min_separation_days', 7)
            date_offset = i * sep
            
            for sub in sub_events:
                 # Override logic for the sub-event
                 sub_overrides = overrides.copy() if overrides else {}
                 sub_overrides['force_table'] = sub.get('table', 'visit')
                 if sub.get('value_set_names'):
                    sub_overrides['force_vs_names'] = sub['value_set_names']
                 if sub.get('diagnosis_pattern'):
                    sub_overrides['force_diag_pattern'] = sub['diagnosis_pattern']
                 
                 # Call standard generator
                 # We calculate offset_days relative to Jan 1 to keep API consistent
                 dt_target = base_date + timedelta(days=date_offset)
                 dt_jan1 = datetime(self.year, 1, 1)
                 offset = (dt_target - dt_jan1).days

                 t_name, row = self.generate_clinical_event(
                    mem_id, 
                    component_name=component_config.get('name', 'Composite'), # Use real name if composite
                    is_compliant=True, 
                    offset_days=offset, 
                    overrides=sub_overrides, 
                    product_line=product_line
                 )
                 events.append((t_name, row))
        return events

    def _get_code_override(self, value_set_name, table_key):
        """
        Phase 3: External Code Reference Integration.
        Checks for high-fidelity medication codes preprocessed from HEDIS Excel.
        """
        if value_set_name in self.medication_codes:
            import random
            codes_config = self.medication_codes[value_set_name]
            
            # Decide which code system to use based on target table
            # RX table -> NDC
            # Visit/Lab table -> RxNorm (Clinical metadata)
            if 'rx' in table_key.lower():
                codes = codes_config.get('NDC', [])
            else:
                codes = codes_config.get('RxNorm', [])
            
            if codes:
                return random.choice(codes)
        
        return None

    def generate_clinical_event(self, mem_id, component_name, is_compliant=True, offset_days=0, overrides=None, product_line='COMMERCIAL'):
        # Locate component in measure config
        vs_name = None
        
        # ⚡ Composite Override Support (Priority 1)
        if overrides and 'force_table' in overrides:
             table_key = overrides['force_table']
             # Create dummy component config
             component = {
                 'name': component_name,
                 'table': table_key,
                 'value_set_names': overrides.get('force_vs_names', []),
                 'diagnosis_pattern': overrides.get('force_diag_pattern')
             }
             if overrides.get('force_vs_names'):
                 vs_name = overrides['force_vs_names'][0] # Use first VS name for logging
        else:
            # Check Numerator Components (Standard)
            component = next((c for c in self.measure['rules']['clinical_events']['numerator_components'] if c['name'] == component_name), None)
            
            # Check Denominator Components (New for Complex Measures)
            if not component and 'denominator_components' in self.measure['rules']['clinical_events']:
                 component = next((c for c in self.measure['rules']['clinical_events']['denominator_components'] if c['name'] == component_name), None)
                 if component:
                     # If found in denominator list, check if it's complex
                     if component.get('count', 1) > 1 or component.get('events'):
                         return self.generate_composite_event(mem_id, component, datetime(self.year, 1, 1), overrides, product_line)

            if component:
                table_key = component['table'] # e.g. "lab", "visit"
            else:
                # ⚡ Universal Support: Smart-default table based on name
                table_key = 'visit'
                if "BMI" in component_name or "Weight" in component_name:
                    table_key = 'emr'
                elif "PSA" in component_name or "Lab" in component_name:
                    table_key = 'lab'
                elif "Medication" in component_name or "Drug" in component_name or "Rx" in component_name:
                    table_key = 'rx'
                    
                # Create a dummy component for logic below
                component = {
                    'name': component_name,
                    'table': table_key,
                    'value_set_names': [component_name] # Fallback
                }

        if table_key not in self.schema['tables']:
            # Fallback for old configs that might still use [MEASURE]_...
            measure_prefix = f"{self.measure.get('measure_name', 'PSA')}_"
            table_raw = table_key.replace(measure_prefix, '').replace('_IN', '').lower()
            if 'VISIT' in table_raw.upper(): table_key = 'visit'
            elif 'EMR' in table_raw.upper(): table_key = 'emr'
            elif 'LAB' in table_raw.upper(): table_key = 'lab'
            elif 'RX' in table_raw.upper() or 'PHARM' in table_raw.upper(): table_key = 'rx'
            else: table_key = 'visit'

        target_table = self.schema['tables'][table_key]
        event_date = datetime(self.year, 6, 1) + timedelta(days=offset_days)
        
        # ⚡ Apply Overrides from Scenario (Universal Format support)
        specific_code = None
        specific_value = None
        specific_days = 30
        specific_qty = 30
        
        # Priority 1: Specific metadata passed directly (for multi-event scenarios)
        meta = overrides.get('specific_metadata') if overrides else None
        
        # Priority 2: Global overrides by name (legacy/single-event support)
        if not meta and overrides and 'events' in overrides and component_name in overrides['events']:
            meta = overrides['events'][component_name]
            # Handle list-based metadata (take first if list) - fallback
            if isinstance(meta, list) and meta:
                meta = meta[0]

        # Priority 3: Component level defaults from YAML
        if component:
            # ⚡ Smart Adherence: detect maintenance meds
            is_maintenance = any(kw in component_name.lower() or kw in str(vs_name).lower() for kw in ['statin', 'maintenance', 'adherence'])
            default_days = 90 if is_maintenance else 30
            
            specific_days = component.get('days_supply', default_days)
            specific_qty = component.get('quantity', specific_days)

        if meta:
            if 'date' in meta:
                try:
                    event_date = self.parse_date_str(meta['date'])
                except:
                    pass
            if 'code' in meta:
                specific_code = meta['code']
            if 'value' in meta:
                specific_value = meta['value']
            if 'days_supply' in meta:
                specific_days = meta['days_supply']
            if 'quantity' in meta:
                specific_qty = meta['quantity']

        # ⚡ Randomized Lab Values Support
        if is_compliant and component.get('table') == 'lab' and 'value_range' in component:
             import random
             low, high = component['value_range']
             # Format as float string if range contains floats
             if isinstance(low, float) or isinstance(high, float):
                 specific_value = f"{random.uniform(low, high):.1f}"
             else:
                 specific_value = str(random.randint(low, high))

        row = {
            target_table['fk'] if 'fk' in target_table else target_table['pk']: mem_id,
            target_table['fields']['date']: event_date
        }
        
        if specific_code:
            row['_CODE'] = specific_code # Mark it for later use

        # Add specific values for compliance
        if is_compliant:
            # Try to get code from VSD if possible
            vsd_code = None
            if self.vsd_manager and component.get('value_set_names'):
                vs_name = component['value_set_names'][0]
                
                # ⚡ Phase 3: Check for External Master List (NDC/CPT) override
                override_code = self._get_code_override(vs_name, table_key)
                if override_code:
                    vsd_code = override_code
                    print(f"   🎯 Using external master code override for {vs_name}: {vsd_code}")
                else:
                    vsd_code = self.vsd_manager.get_random_code(vs_name)
                
                row['_VALUE_SET_NAME'] = vs_name
            
            # ⚡ Priority: 1. Manual override from Excel 2. VSD code 3. Placeholder
            final_code = specific_code if specific_code else vsd_code
            if final_code:
                row['_CODE'] = final_code
                
                # Use as main code if column exists
                if table_key == 'lab':
                    row[target_table['fields']['cpt']] = final_code
                elif table_key == 'visit':
                    # ⚡ Smart Code Routing: Diagnosis (ICD) vs Procedure (CPT/RxNorm)
                    code_system = self.vsd_manager.get_code_system(final_code) if self.vsd_manager else "Unknown"
                    if "ICD" in code_system.upper() or "DIAGNOSIS" in code_system.upper():
                        row["DIAG_I_1"] = final_code
                    else:
                        row["CPT_1"] = final_code
                elif table_key == 'rx':
                    row[target_table['fields']['ndc']] = final_code
                    row[target_table['fields']['days_supply']] = specific_days
                    row[target_table['fields']['quantity']] = specific_qty
            else:
                row['_CODE'] = 'MANUAL'
            
            # ⚡ Populate detailed fields only if requested scope is 'all'
            if self.column_scope == 'all':
                if table_key == 'rx':
                    self._populate_rx_fields(row, target_table, mem_id, product_line=product_line)
                elif table_key == 'visit':
                    self._populate_visit_fields(row, target_table, mem_id, product_line=product_line)

            # Add a realistic diagnosis if it's a visit (Force it even if code wasn't found)
            if table_key == 'visit' and self.vsd_manager and not row.get("DIAG_I_1"):
                diag = self.vsd_manager.get_random_code_from_pattern("Diagnosis")
                if diag: row["DIAG_I_1"] = diag
            
            row['_VALUE_SET_NAME'] = vs_name if vs_name else 'MANUAL'

            # --- Measure-Specific Post-Processing ---
            if component_name == "BMI Percentile":
                row[target_table['fields']['bmi_percentile']] = specific_value if specific_value is not None else 85
            elif "Counseling" in component_name:
                code = final_code if final_code else ('Z71.3' if "Nutrition" in component_name else 'Z71.89')
                target_field = target_table['fields'].get('procedure_codes', ['CPT_1'])[0]
                row[target_field] = code
                if not row.get('_CODE'): row['_CODE'] = code # Fallback
            elif component_name == "PSA Test" or table_key == 'lab':
                # Use value_range if provided, else default
                val = specific_value if specific_value is not None else ('1.0' if component_name == "PSA Test" else '0.1')
                row[target_table['fields'].get('value', 'LAB_VALUE')] = val
                row[target_table['fields'].get('cpt', 'LAB_CPT')] = final_code if final_code else '80000'
            elif final_code:
                # Catch-all for other components if we found a code
                code_field = target_table['fields'].get('procedure_codes', [target_table['fields'].get('cpt', 'CPT_1')])[0]
                row[code_field] = final_code
        
            if overrides:
                for f, v in overrides.items():
                    if f in row: row[f] = v

        return target_table['name'], row

    def _populate_rx_fields(self, row, target_table, mem_id, product_line='COMMERCIAL'):
        """Populates rich metadata for pharmacy claims using schema mapping."""
        fields = target_table.get('fields', {})
        import time
        
        # Claim Identity
        if 'claim_id' in fields:
            row[fields['claim_id']] = f"RX_{mem_id}_{int(time.time())}"
        
        # Claim Indicators
        if 'claim_den' in fields: row[fields['claim_den']] = 'N'
        if 'claim_type' in fields: row[fields['claim_type']] = 'P' # P = Pharmacy
        
        # Provider Context
        if 'prov_nbr' in fields: row[fields['prov_nbr']] = 'PROV123'
        if 'prov_npi' in fields: row[fields['prov_npi']] = '1234567890'
        if 'pharm_npi' in fields: row[fields['pharm_npi']] = '0987654321'
        
        # Product Context
        if 'product_id' in fields: 
            prod_info = self.product_config.get(product_line.upper(), {})
            # Ensure it is the numeric ID e.g. "150"
            row[fields['product_id']] = prod_info.get('id', self.pl_map.get(product_line, product_line))

    def _populate_visit_fields(self, row, target_table, mem_id, product_line='COMMERCIAL'):
        """Populates rich metadata for medical visits (Claims, POS, NPIs)."""
        fields = target_table.get('fields', {})
        import time
        
        # Claim Identity
        if 'claim_id' in fields:
            row[fields['claim_id']] = f"CL_{mem_id}_{int(time.time())}"
        
        # Claim Status
        if 'claim_status' in fields: row[fields['claim_status']] = 'P' # Paid
        
        # Place of Service (Default to Office=11)
        if 'pos' in fields: row[fields['pos']] = '11'
        
        # Provider Context
        if 'prov_nbr' in fields: row[fields['prov_nbr']] = 'PROV789'
        # Match schema_map.yaml key 'provider_npi'
        if 'provider_npi' in fields: row[fields['provider_npi']] = '1122334455'
        elif 'prov_npi' in fields: row[fields['prov_npi']] = '1122334455' # Fallback
        
        if 'tin' in fields: row[fields['tin']] = '99-8887776'
        
        # Product Context
        if 'product_id' in fields:
            prod_info = self.product_config.get(product_line.upper(), {})
            row[fields['product_id']] = prod_info.get('id', product_line.upper())

    def generate_exclusion(self, mem_id, exclusion_name, overrides=None):
        # Find exclusion in config
        exclusion = next((e for e in self.measure['rules']['exclusions'] if e['name'] == exclusion_name), None)
        
        if not exclusion:
            # ⚡ Universal Support: Default to 'visit' for unknown exclusions
            exclusion = {
                'name': exclusion_name,
                'value_set_names': [exclusion_name]
            }
            
        event_date = datetime(self.year, 3, 15) # Early year exclusion
        
        # ⚡ Apply Overrides from Scenario (Universal Format support)
        if overrides and 'exclusions' in overrides and exclusion_name in overrides['exclusions']:
            meta = overrides['exclusions'][exclusion_name]
            if 'date' in meta:
                try:
                    event_date = self.parse_date_str(meta['date'])
                except:
                    pass

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
            
        # Default Catch-all for exclusions (Universal support)
        target_table = self.schema['tables']['visit']
        code = vsd_code if vsd_code else 'Z00.00'
        row = {
            target_table['fk']: mem_id,
            target_table['fields']['date']: event_date,
            target_table['fields']['diagnosis_codes'][0]: code
        }
        return target_table['name'], row

    def generate_monthly_membership(self, mem_id, monthly_overrides):
        """
        Generates records for the monthly membership table (HOSPICE, LIS, etc.)
        based on structured overrides with run dates.
        """
        if not monthly_overrides:
            return None, []
            
        target_table = self.schema['tables']['monthly_membership']
        rows = []
        
        # Group by run_date to create one record per month if needed
        by_date = {}
        for entry in monthly_overrides:
            rd = self.parse_date_str(entry['run_date'])
            if rd not in by_date:
                by_date[rd] = {
                    target_table['fk']: mem_id,
                    target_table['fields']['run_date']: rd
                }
            
            # Map logical field to physical column if possible
            field = entry['field']
            mapped_col = target_table['fields'].get(field.lower(), field)
            by_date[rd][mapped_col] = entry['value']
            
        return target_table['name'], list(by_date.values())
