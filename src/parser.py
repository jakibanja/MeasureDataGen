import pandas as pd
import re
import yaml
import os

class TestCaseParser:
    def __init__(self, file_path, extractor=None):
        self.file_path = file_path
        self.extractor = extractor
        self.benefit_profiles = {}
        # Load Benefit Profiles
        try:
            # Priority 1: Dedicated benefits.yaml
            ben_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'benefits.yaml')
            if os.path.exists(ben_path):
                with open(ben_path, 'r') as f:
                    self.benefit_profiles = yaml.safe_load(f)
            else:
                # Fallback: schema_map.yaml (Legacy)
                config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'schema_map.yaml')
                if os.path.exists(config_path):
                    with open(config_path, 'r') as f:
                        cfg = yaml.safe_load(f)
                        self.benefit_profiles = cfg.get('benefit_profiles', {})
        except Exception as e:
            print(f"Warning: Could not load benefit profiles: {e}")
        
    def parse_scenarios(self, measure_config):
        xl = pd.ExcelFile(self.file_path)
        all_scenarios = []
        measure_abbr = measure_config.get('measure_name', '').lower()
        
        # Sheets to exclude
        exclude_sheets = ['Revision_History', 'DST', 'Fileid_Summary', 'Fileid_Detail']

        for sheet_name in xl.sheet_names:
            if sheet_name in exclude_sheets:
                continue
            
            print(f"  Parsing sheet: {sheet_name}")
            df_raw = xl.parse(sheet_name, header=None)
            header_row_idx = -1
            
            for i, row in df_raw.iterrows():
                row_str = " ".join([str(cell).lower() for cell in row])
                if any(x in row_str for x in ['#tc', 'mem_nbr', 'member number', 'testcase id', 'member_id', 'member id']):
                    header_row_idx = i
                    break
            
            if header_row_idx == -1:
                continue

            df = xl.parse(sheet_name, skiprows=header_row_idx)
            df.columns = [str(c).strip() for c in df.columns]
            
            id_cols = [c for c in df.columns if any(x in c.lower() for x in ['#tc', 'id', 'mem_nbr', 'member number'])]
            if not id_cols:
                id_cols = [c for c in df.columns if '#' in c or 's.n' in c.lower()]
            
            col_map = {
                'id': id_cols[0] if id_cols else df.columns[0],
                'scenario': next((c for c in df.columns if 'scenario' in c.lower() or 'test objective' in c.lower()), None),
                'objective': next((c for c in df.columns if 'objective' in c.lower()), None),
                'expected': next((c for c in df.columns if 'expected' in c.lower()), None),
                'period': next((c for c in df.columns if 'period' in c.lower() or 'enr_period' in c.lower()), None),
                # ⚡ Capture all VISIT date columns
                'visit_cols': sorted([c for c in df.columns if re.search(r'VISIT_\d+_DATE', c, re.IGNORECASE)]),
                # ⚡ Capture all BEN_ columns
                'benefit_cols': [c for c in df.columns if str(c).upper().startswith('BEN_')]
            }

            current_sc = None
            for idx, row in df.iterrows():
                try:
                    tc_id_raw = str(row.get(col_map['id'], '')).strip()
                    
                    is_continuation = False
                    if tc_id_raw.lower() in ["nan", "none", "", "#", "#tc", "mem_nbr", "s.n"]:
                        if current_sc:
                            is_continuation = True
                        else:
                            continue
                    
                    if not is_continuation:
                        if len(tc_id_raw) > 60: continue
                        if any(x in tc_id_raw.lower() for x in ["verify if", "member has", "objective:"]): continue
                        
                        scenario_text = str(row.get(col_map['scenario'], '')) if col_map['scenario'] else ""
                        objective_text = str(row.get(col_map['objective'], '')) if col_map['objective'] else ""
                        search_blob = (tc_id_raw + " " + scenario_text + " " + objective_text).lower()
                        if measure_abbr not in search_blob and "all" not in search_blob and "psa" not in sheet_name.lower():
                            continue
                            
                        current_sc = {
                            "id": tc_id_raw,
                            "scenario": scenario_text,
                            "objective": objective_text,
                            "expected": str(row.get(col_map['expected'], '')) if col_map['expected'] else "",
                            "sheet": sheet_name,
                            "age": 70, 
                            "gender": 'M',
                            "compliant": [],
                            "excluded": [],
                            "product_line": "Medicare",
                            "enrollment_spans": [],
                            "visit_spans": [],
                            "overrides": {},
                            "monthly_overrides": []
                        }
                        all_scenarios.append(current_sc)
    
                    self._parse_row_details(current_sc, row, col_map, sheet_name, measure_config)
                except Exception as e:
                    print(f"❌ Error parsing row {idx} in {sheet_name}: {e}")
                    # print(f"Row content: {row.to_dict()}")
                    import traceback
                    traceback.print_exc()

        return all_scenarios

    def _parse_row_details(self, parsed_sc, row, col_map, sheet_name, measure_config):
        numerator_comps = measure_config['rules']['clinical_events']['numerator_components']
        exclusion_comps = measure_config['rules'].get('exclusions', [])
        
        # ⚡ Shared Regex Definitions for Dates & Ranges
        date_part = r'\d{1,4}[-/.\s]\d{1,2}[-/.\s](?:MY(?:[\-\+]\d+)?|\d{2,4})'
        date_part_full = rf'(?:{date_part}|MY(?:[\-\+]\d+)?)'
        range_regex = rf'({date_part_full})\s*(?:-|to|until|—)\s*({date_part_full})'

        # Combine all columns into lines to scan for data
        row_values = [str(val) for val in row.values if pd.notna(val)]
        blob_full = " ".join(row_values).lower()

        # 1. Product Line (PL:)
        pl_match = re.search(r'pl\s*:\s*(\w+)', blob_full)
        if pl_match:
            pl_query = pl_match.group(1).lower()
        else:
            pl_query = blob_full

        pl_aliases = {
            "Commercial": ["commercial", "comm"],
            "Medicaid": ["medicaid", "medi-cal", "mcd"],
            "Medicare": ["medicare", "mcr"],
            "Exchange": ["exchange", "marketplace", "qhp", "hix"]
        }
        for pl_name, aliases in pl_aliases.items():
            if any(alias in pl_query for alias in aliases):
                parsed_sc["product_line"] = pl_name
                break

        # 1.5 ⚡ BE: Benefit Profile Shortcut (e.g., BE: Medical)
        be_match = re.search(r'be\s*:\s*(\w+)', blob_full)
        if be_match:
            profile_name = be_match.group(1).upper()
            if profile_name in self.benefit_profiles:
                for mapped_col in self.benefit_profiles[profile_name]:
                    parsed_sc["overrides"][mapped_col] = 1
            else:
                parsed_sc["overrides"][f"BEN_{profile_name}"] = 1

        # 2. Age Detection (AG:)
        ag_match = re.search(r'ag\s*:\s*(\d+)', blob_full)
        if ag_match:
            parsed_sc["age"] = int(ag_match.group(1))
        elif parsed_sc.get("age") == 70:
            age_match = re.search(r'(\d+)\s*(?:-|to)\s*(\d+)', blob_full)
            if age_match:
                low, high = map(int, age_match.groups())
                temp_age = (low + high) // 2
                if 0 <= temp_age <= 110: parsed_sc["age"] = temp_age
            else:
                matches = re.findall(r'(\d+)', blob_full)
                for m in matches:
                    val = int(m)
                    if 18 <= val <= 100:
                        parsed_sc["age"] = val
                        break
        
        # 2.5 Anchor Date Detection (AD:)
        ad_match = re.search(r'ad\s*:\s*(' + date_part_full + r'|[\w\s]+?measurement year)', blob_full, re.IGNORECASE)
        if ad_match:
            parsed_sc["anchor_date"] = ad_match.group(1).strip()

        # 2.6 Event Date Override (ED:) - Support multiple formats
        # a) Global/Multi: ED: 1/1/MY, 2/1/MY
        ed_list_match = re.search(r'\bed\s*:\s*((?:' + date_part_full + r'(?:\s*,\s*)?)+)', blob_full, re.IGNORECASE)
        if ed_list_match:
            date_blob = ed_list_match.group(1).strip()
            # Split by comma or space if multiple dates
            dates = [d.strip() for d in re.split(r'[,\s]+', date_blob) if d.strip()]
            parsed_sc["event_dates"] = dates # Store as list
            if dates:
                parsed_sc["event_date_override"] = dates[0]
            
        # b) Numbered: ED1: 1/1/MY, ED2: 2/1/MY
        ed_numbers = re.findall(r'\bed(\d+)\s*:\s*(' + date_part_full + r')', blob_full, re.IGNORECASE)
        for num, dt in ed_numbers:
            parsed_sc["overrides"].setdefault("events_by_index", {})[int(num)] = dt.strip()

        # c) Named: ED: PSA Test=6/1/MY
        ed_named = re.findall(r'\bed\s*:\s*([^=\n]+?)\s*[:=]\s*(' + date_part_full + r')', blob_full, re.IGNORECASE)
        for name, dt in ed_named:
            clean_name = name.strip().lower()
            if clean_name not in ['ad', 'ce', 'ne', 'ag', 'pl']: # Skip other prefixes
                if 'events' not in parsed_sc["overrides"]: parsed_sc["overrides"]['events'] = {}
                matched_name = next((c['name'] for c in numerator_comps if clean_name in c['name'].lower()), name.strip())
                parsed_sc["overrides"]['events'][matched_name] = {'date': dt.strip()}

        # 2.7 ⚡ Professional Overrides: F1: Value, F2: Value, etc.
        field_overrides = re.findall(r'\bf(\d+)\s*[:=]\s*([\w\d\-\s]+)', blob_full, re.IGNORECASE)
        for num, val in field_overrides:
            parsed_sc["overrides"][f"FIELD{num}"] = val.strip()

        # 2.8 ⚡ Pinned Overrides: V1: DIAG=Z00.00, V2: CPT=99214
        # Matches V<number>: <KEY>=<VALUE>
        pinned_overrides = re.findall(r'\bv(\d+)\s*:\s*([\w\d]+)\s*[:=]\s*([\w\d\-\.]+)', blob_full, re.IGNORECASE)
        for num, key, val in pinned_overrides:
             idx = int(num)
             if 'pinned_visits' not in parsed_sc["overrides"]: parsed_sc["overrides"]['pinned_visits'] = {}
             if idx not in parsed_sc["overrides"]['pinned_visits']: parsed_sc["overrides"]['pinned_visits'][idx] = {}
             
             # Standardize keys
             clean_key = key.strip().upper()
             if clean_key in ['DIAG', 'DIAGNOSIS']: clean_key = 'DIAG_I_1'
             elif clean_key in ['CPT', 'PROC']: clean_key = 'CPT_1'
             elif clean_key in ['POS']: clean_key = 'POS'
             
             parsed_sc["overrides"]['pinned_visits'][idx][clean_key] = val.strip()

        # Specific Diagnosis Override (DIAG: Z71.3)
        diag_match = re.search(r'diag\s*[:=]\s*([\w\d.]+)', blob_full)
        if diag_match:
            parsed_sc["overrides"]["DIAG_I_1"] = diag_match.group(1).upper()
        
        # 3. Compliance & Exclusions (CE: and NE:)
        for comp in numerator_comps:
            kw = comp['name'].lower()
            found = False
            
            # ⚡ Explicit CE: prefix
            if re.search(rf'\bce\s*[:=]\s*{kw}', blob_full):
                found = True
            
            # Direct keyword match
            if kw in blob_full:
                found = True
            
            # PSA-specific patterns
            if 'psa' in kw and 'test' in kw:
                if re.search(r'\bce\s*[:=]\s*1\b', blob_full):
                    found = True
                if any(pattern in blob_full for pattern in ['psa', 'lab test', 'screening', 'clinical event']):
                    if not any(neg in blob_full for neg in ['no psa', 'not tested', 'ce=0', 'ce:0', 'ce =0', 'ce:  0']):
                        found = True
            
            if found:
                if comp['name'] not in parsed_sc["compliant"]:
                    parsed_sc["compliant"].append(comp['name'])
                
                # ⚡ Extract Pharmacy-specific metadata (Days Supply, Quantity, NDC)
                if comp.get('table') == 'rx' or "Medication" in comp['name'] or "Drug" in comp['name']:
                    if 'events' not in parsed_sc["overrides"]: parsed_sc["overrides"]['events'] = {}
                    if comp['name'] not in parsed_sc["overrides"]['events']:
                        parsed_sc["overrides"]['events'][comp['name']] = {}
                    
                    meta = parsed_sc["overrides"]['events'][comp['name']]
                    
                    # Days Supply: DS: 30, Days: 90
                    ds_match = re.search(r'(?:ds|days?|days?\s*supply)\s*[:=]\s*(\d+)', blob_full)
                    if ds_match: meta['days_supply'] = int(ds_match.group(1))
                    
                    # Quantity: QTY: 30
                    qty_match = re.search(r'(?:qty|quantity)\s*[:=]\s*(\d+)', blob_full)
                    if qty_match: meta['quantity'] = int(qty_match.group(1))
                    
                    # NDC: NDC: 12345678901
                    ndc_match = re.search(r'ndc\s*[:=]\s*([\d-]+)', blob_full)
                    if ndc_match: meta['code'] = ndc_match.group(1).strip()
        
        for excl in exclusion_comps:
            kw_excl = excl['name'].lower()
            found_excl = False
            
            # ⚡ Explicit NE: prefix
            if re.search(rf'\bne\s*[:=]\s*{kw_excl}', blob_full):
                found_excl = True
                
            if kw_excl in blob_full:
                found_excl = True
                
            if found_excl:
                if excl['name'] not in parsed_sc["excluded"]:
                    parsed_sc["excluded"].append(excl['name'])
        
        # 3.5 Specific Field Overrides (Field=1, Field=0, No Field)
        
        # ⚡ Process explicit Benefit Columns (BEN_MEDICAL, etc.) from col_map
        if col_map.get('benefit_cols'):
            for ben_col in col_map['benefit_cols']:
                val = row.get(ben_col)
                if pd.notna(val):
                    # Store as override (e.g. BEN_MEDICAL = val)
                    col_upper = ben_col.upper()
                    
                    # ⚡ Check if mapped to a profile (e.g. BEN_MEDICAL -> [List of 10 cols])
                    if col_upper in self.benefit_profiles:
                        for mapped_col in self.benefit_profiles[col_upper]:
                            parsed_sc["overrides"][mapped_col] = val
                    else:
                        # Direct assignment
                        parsed_sc["overrides"][col_upper] = val

        # Look for patterns like BEN_MH_INP=0 or HOSPICE=1
        field_matches = re.findall(r'(\b[a-zA-Z0-9_]+\b)\s*[:=]\s*([01])', blob_full)
        for field, val in field_matches:
            parsed_sc["overrides"][field.upper()] = int(val)
            
        # Look for "No [Benefit]" or "Doesn't have [Benefit]"
        no_patterns = [
            (r'no\s+(ben_[a-z_]+)', 0),
            (r'no\s+mental\s+health', 0, 'BEN_MH_INP'),
            (r'no\s+pharmacy', 0, 'BEN_RX'),
            (r'no\s+medical', 0, 'BEN_MEDICAL'),
            (r'hospice\s*[:=]\s*1', 1, 'HOSPICE'),
            (r'hospice\s*[:=]\s*0', 0, 'HOSPICE'),
        ]
        
        for entry in no_patterns:
            pattern = entry[0]
            val = entry[1]
            match = re.search(pattern, blob_full)
            if match:
                if len(entry) > 2:
                    parsed_sc["overrides"][entry[2]] = val
                else:
                    parsed_sc["overrides"][match.group(1).upper()] = val

        # 4. Dates & Ranges
        in_enr_section = False
        for cell_val in row_values:
            cell_str = str(cell_val).strip()
            if not cell_str: continue
            
            l_norm = cell_str.lower()
            if any(kw in l_norm for kw in ["enrollment", "enr", "member", "ce:"]):
                in_enr_section = True
            
            # Find Ranges (Enrollment)
            # ⚡ Enhanced for Tester Syntax (1st Enrollment, --prod id, etc.)
            for match in re.finditer(range_regex, cell_str, re.IGNORECASE):
                start_str, end_str = match.groups()
                start_pos = match.start()
                
                # Look backwards for "1st Enrollment", "2nd Enrollment", "Plan 1"
                prefix_context = cell_str[max(0, start_pos-40):start_pos].lower()
                
                # Look forwards for attributes
                search_end = cell_str.find("\n", match.end())
                if search_end == -1: search_end = len(cell_str)
                context_str = cell_str[start_pos:search_end]
                
                prod_regex = r'(?:product_?id|rollup_?id|prod_?id|pl_?id|product|rollup|prod|pl)\s*[:=]?\s*(\w+)'
                prod_match = re.search(prod_regex, context_str, re.IGNORECASE)
                
                if not prod_match:
                    # Try looking for --prod id 11
                    prod_match = re.search(r'--prod\s*id\s*(\d+)', context_str, re.IGNORECASE)

                prod_val = prod_match.group(1) if prod_match else None
                
                cov_regex = r'(?:coverage_indicator|coverage_ind|coverage|cover|cov)\s*[:=]\s*(\w+)'
                cov_match = re.search(cov_regex, context_str, re.IGNORECASE)
                cov_val = cov_match.group(1) if cov_match else None
                
                ben_hospice_match = re.search(r'ben[-_]hospice\s*[:=]\s*(\w+)', context_str, re.IGNORECASE)
                ben_hospice_val = ben_hospice_match.group(1) if ben_hospice_match else None

                span_data = {
                    'start': start_str, 
                    'end': end_str, 
                    'product_id': prod_val
                }
                if cov_val: span_data['coverage_indicator'] = cov_val
                if ben_hospice_val:
                    val = 1 if ben_hospice_val.upper() in ['Y', '1', 'YES', 'P'] else 0
                    span_data['BEN_HOSPICE'] = val

                parsed_sc["enrollment_spans"].append(span_data)

            # ⚡ 4.5 Flags with Run Dates (Hospice=Y in ... with Rundate=...)
            flag_date_matches = re.findall(r'(\b\w+\b)\s*([:=])\s*([yn01])\b.*?rundate\s*[:=]\s*(' + date_part_full + r')', cell_str, re.IGNORECASE)
            for flag, _, val, run_dt in flag_date_matches:
                col = flag.upper()
                v = 1 if val.upper() in ['Y', '1'] else 0
                parsed_sc["monthly_overrides"].append({
                    'field': col,
                    'value': v,
                    'run_date': run_dt.upper()
                })

            # Find Single Dates (Visits)
            if any(kw in l_norm for kw in ["visit", "encounter", "checkup"]):
                dates = re.findall(date_part_full, cell_str, re.IGNORECASE)
                for d in dates:
                    # Avoid duplicates with enrollment
                    if not any(d in [s['start'], s['end']] for s in parsed_sc["enrollment_spans"]):
                        parsed_sc["visit_spans"].append({
                            'date': d,
                            'type': 'Outpatient' 
                        })

        # 5. ⚡ Structured Visits (New logic)
        if col_map.get('visit_cols'):
            for date_col in col_map['visit_cols']:
                date_val = row.get(date_col)
                if pd.notna(date_val):
                    # Find corresponding TYPE column (VISIT_1_DATE -> VISIT_1_TYPE)
                    # Use index search to be robust against slight naming variations
                    prefix = str(date_col).replace('DATE', '').replace('date', '') 
                    type_col = next((c for c in row.index if str(c).startswith(prefix) and 'TYPE' in str(c).upper()), None)
                    
                    type_val = row.get(type_col) if type_col else "Outpatient"
                    if pd.isna(type_val) or str(type_val).strip() == "":
                        type_val = "Outpatient"
                    
                    parsed_sc["visit_spans"].append({
                        'date': date_val,
                        'type': str(type_val).strip()
                    })

        # --- AI Fallback Logic ---
        # If regex failed to find any enrollment spans, try the AI extractor
        if not parsed_sc["enrollment_spans"] and self.extractor:
            print(f"    ⚠️  No enrollment spans found for {parsed_sc['id']}. Triggering AI Extractor...")
            
            # Prepare row dict for AI
            ai_input = {
                'id': parsed_sc['id'],
                'scenario': parsed_sc['scenario'],
                'objective': parsed_sc['objective'],
                'expected': parsed_sc['expected'],
                'sheet': sheet_name
            }
            
            ai_result = self.extractor.extract_scenario_info(ai_input)
            
            if not ai_result.get('_ai_failed'):
                # Merge AI results
                if ai_result.get('enrollment_spans'):
                    print(f"      ✅ AI found {len(ai_result['enrollment_spans'])} spans.")
                    parsed_sc["enrollment_spans"].extend(ai_result['enrollment_spans'])
                
                if ai_result.get('product_line'):
                    parsed_sc["product_line"] = ai_result['product_line']
                    
                # Merge expected results into overrides if present
                if ai_result.get('expected_results'):
                    for k, v in ai_result['expected_results'].items():
                        parsed_sc["overrides"][k.upper()] = v
                        
                # Merge exclusions found by AI
                for excl in ai_result.get('exclusions', []):
                    if excl not in parsed_sc["excluded"]:
                        parsed_sc["excluded"].append(excl)
            else:
                print(f"      ❌ AI extraction also failed: {ai_result.get('_error')}")
