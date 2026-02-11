import pandas as pd
import json
import os
import time
import yaml
from dotenv import load_dotenv
from src.engine import MockupEngine
from src.parser import TestCaseParser
from src.standard_parser import StandardFormatParser
from src.vsd import VSDManager

# Load environment variables from .env file
load_dotenv()

# ⚡ Performance Optimization: Global caches to avoid reloading heavy resources
_vsd_cache = {}
_ai_extractor_cache = None

def run_measure_gen_custom(measure_name, testcase_path, vsd_path, skip_quality_check=False, disable_ai=None, validate_ncqa=False, model_name="qwen2:0.5b", mocking_depth='population', column_scope='all', baseline_path=None, delta_run=False):
    """
    Core function for running measure generation with explicit paths.
    Returns the path to the generated output file.
    
    Args:
        measure_name: Name of the measure (e.g., 'PSA')
        testcase_path: Path to test case Excel file
        vsd_path: Path to VSD Excel file
        skip_quality_check: If True, skips quality checks for faster generation
        disable_ai: If True, skips AI Extractor (faster). If None, checks DISABLE_AI_EXTRACTOR env var
        model_name: Name of the Ollama model to use
        mocking_depth: 'population' (default) or 'scenario'
        column_scope: 'all' (default) or 'mandatory'
    """
    start_time = time.time()
    measure_name = measure_name.upper()
    config_dir = os.getenv('CONFIG_DIR', 'config')
    schema_path = os.getenv('SCHEMA_MAP_PATH', 'config/schema_map.yaml')
    config_path = os.path.join(config_dir, f'{measure_name}.yaml')
    
    # ⚡ Automated Schema Expansion: Ensure physical tables exist for this measure
    from src.schema_manager import SchemaManager
    sm = SchemaManager()
    sm.expand_schema(measure_name)
    
    # ⚡ Universal Fallback: If no specific config exists, use the Universal template
    if not os.path.exists(config_path):
        print(f"⚠️  No config found for {measure_name}, using Universal template...")
        config_path = os.path.join(config_dir, 'Universal.yaml')
    
    if not os.path.exists(testcase_path):
        print(f"Skipping {measure_name}: Test case file not found at {testcase_path}")
        return None

    # ⚡ Use cached VSD Manager (saves 10-30 seconds on subsequent runs)
    if vsd_path not in _vsd_cache:
        print("📚 Loading VSD (first time only, this may take 10-30 seconds)...")
        vsd_load_start = time.time()
        _vsd_cache[vsd_path] = VSDManager(vsd_path, measurement_year=2026)
        print(f"   ✓ VSD loaded in {time.time() - vsd_load_start:.2f}s")
    else:
        print("⚡ Using cached VSD (instant!)")
    vsd_manager = _vsd_cache[vsd_path]
    
    # ⚡ Use cached AI Extractor (saves 5-15 seconds on subsequent runs)
    if disable_ai is None:
        disable_ai = os.getenv('DISABLE_AI_EXTRACTOR', 'false').lower() == 'true'
    
    global _ai_extractor_cache
    extractor = None
    
    if disable_ai:
        print("⚡ AI Extractor disabled (using regex-only mode for maximum speed)")
    else:
        try:
            from src.ai_extractor import AIScenarioExtractor
            needs_init = _ai_extractor_cache is None or _ai_extractor_cache == "FAILED"
            if not needs_init and hasattr(_ai_extractor_cache, 'model_name') and _ai_extractor_cache.model_name != model_name:
                print(f"🔄 Switching AI model from {_ai_extractor_cache.model_name} to {model_name}...")
                needs_init = True

            if needs_init:
                print(f"🤖 Initializing AI Extractor with model '{model_name}' (this may take 5-15 seconds)...")
                ai_load_start = time.time()
                try:
                    _ai_extractor_cache = AIScenarioExtractor(model_name=model_name)
                    print(f"   ✓ AI Extractor loaded in {time.time() - ai_load_start:.2f}s")
                except Exception as init_error:
                    print(f"   ❌ AI Extractor failed to initialize: {init_error}")
                    _ai_extractor_cache = "FAILED"
            elif _ai_extractor_cache == "FAILED":
                print("⚡ AI Extractor previously failed, using regex-only mode")
            else:
                print(f"⚡ Using cached AI Extractor with model '{model_name}'")
                extractor = _ai_extractor_cache
        except Exception as e:
            print(f"⚠️  AI Extractor initialization failed: {e}")
            _ai_extractor_cache = "FAILED"

    # ⚡ Auto-detect format and use appropriate parser
    use_standard_parser = _is_standard_format(testcase_path)
    
    if use_standard_parser:
        print("📋 Detected standard format - using StandardFormatParser")
        parser = StandardFormatParser(testcase_path)
    else:
        print("📋 Detected legacy format - using TestCaseParser")
        parser = TestCaseParser(testcase_path, extractor=extractor)

    # ⚡ Handle Baseline Parser (for Delta Run)
    baseline_parser = None
    if delta_run and baseline_path:
        if not os.path.exists(baseline_path):
            print(f"⚠️ Baseline file not found: {baseline_path}")
        else:
            print("📋 Initializing Baseline Parser...")
            if _is_standard_format(baseline_path):
                baseline_parser = StandardFormatParser(baseline_path)
            else:
                baseline_parser = TestCaseParser(baseline_path, extractor=extractor)
    
    engine = MockupEngine(config_path, schema_path, vsd_manager=vsd_manager, measure_name_override=measure_name, mocking_depth=mocking_depth, column_scope=column_scope)
    
    # Load config for parser
    with open(config_path) as f:
        measure_config = yaml.safe_load(f)

    result = _process_measure(measure_config, measure_name, parser, engine, skip_quality_check=skip_quality_check, validate_ncqa=validate_ncqa, baseline_parser=baseline_parser)
    
    total_time = time.time() - start_time
    print(f"\n⏱️  Total generation time: {total_time:.2f} seconds")
    
    return result

def _is_standard_format(file_path):
    if '_STANDARD' in file_path.upper():
        return True
    try:
        xl = pd.ExcelFile(file_path)
        if len(xl.sheet_names) == 1:
            df = pd.read_excel(file_path, nrows=0)
            standard_indicators = {'MEMBER_ID', 'ENROLLMENT_1_START', 'VISIT_1_DATE', 'EVENT_1_NAME'}
            if standard_indicators.issubset(set(df.columns)):
                return True
    except:
        pass
    return False

def run_measure_gen(measure_name):
    """ Legacy wrapper for default paths """
    testcase_path = f'data/{measure_name}_MY2026_TestCase.xlsx'
    if measure_name == 'WCC':
         if not os.path.exists(testcase_path):
             testcase_path = 'data/WCC_Test_Scenarios.xlsx'
    vsd_path = os.getenv('VSD_PATH', 'data/VSD_MY2026.xlsx')
    return run_measure_gen_custom(measure_name, testcase_path, vsd_path)

def _process_measure(measure_config, measure_name, parser, engine, output_path=None, audit_logger=None, skip_quality_check=False, validate_ncqa=False, baseline_parser=None):
    print(f"\n--- Processing {measure_name} ---")
    
    # 1. Parse Scenarios
    print("Reading scenarios from {}...".format(parser.file_path))
    scenarios = parser.parse_scenarios(measure_config)
    print(f"Found {len(scenarios)} scenarios.")
    
    # --- Delta Logic ---
    if baseline_parser:
        print(f"Reading BASELINE scenarios from {baseline_parser.file_path}...")
        bl_scenarios = baseline_parser.parse_scenarios(measure_config)
        print(f"Found {len(bl_scenarios)} baseline scenarios.")
        
        # Build Baseline Hash Map
        # Key: Scenario ID (robust)
        # Value: Hash of (Header + Expected) to catch content changes
        bl_map = {}
        for sc in bl_scenarios:
            # ⚡ Robust Hash: Check Header (Legacy) + Scenario (Standard) + Expected
            content_hash = hash(str(sc.get('header', '')) + str(sc.get('scenario', '')) + str(sc.get('expected', '')))
            bl_map[sc['id']] = content_hash
            
        # Filter Target Scenarios
        filtered_scenarios = []
        for sc in scenarios:
             target_hash = hash(str(sc.get('header', '')) + str(sc.get('scenario', '')) + str(sc.get('expected', '')))
             sid = sc['id']
             
             if sid not in bl_map:
                 filtered_scenarios.append(sc) # New Scenario
                 print(f"  [NEW] {sid}")
             elif bl_map[sid] != target_hash:
                 filtered_scenarios.append(sc) # Changed Scenario
                 print(f"  [MODIFIED] {sid}")
             else:
                 pass # Unchanged - Skip
        
        print(f"📉 Delta Run: Filtered {len(scenarios)} -> {len(filtered_scenarios)} scenarios.")
        scenarios = filtered_scenarios
        
        if not scenarios:
            print("⚠️ No changes detected! Nothing to generate.")
            return None
    
    # 2. Containers for data
    data_store = {}
    for table_key, table_info in engine.schema['tables'].items():
        table_name = table_info['name']
        data_store[table_name] = []

    # 3. Process each scenario
    from src.progress import progress_tracker
    progress_tracker.update(f"🔄 Processing {len(scenarios)} scenarios for {measure_name}...", member_count=0)
    
    print(f"📊 Processing {len(scenarios)} scenarios...")
    for idx, sc in enumerate(scenarios, 1):
        mem_id = sc['id']
        if idx % 10 == 0 or idx == len(scenarios):
            print(f"  Progress: {idx}/{len(scenarios)} scenarios processed ({idx*100//len(scenarios)}%)")
        
        overrides = sc.get('overrides', {})
        
        # Member Base
        member_table = engine.schema['tables']['member']['name']
        data_store[member_table].append(engine.generate_member_base(
            mem_id, sc['age'], sc.get('gender', 'M'), 
            overrides=overrides
        ))
        
        # Enrollment
        enrollment_table = engine.schema['tables']['enrollment']['name']
        data_store[enrollment_table].extend(engine.generate_enrollments(
            mem_id, 
            sc.get('product_line', 'Medicare'),
            spans=sc.get('enrollment_spans'),
            overrides=overrides
        ))
        
        # Visits
        v_table, v_rows = engine.generate_visits(mem_id, spans=sc.get('visit_spans'), overrides=overrides, product_line=sc.get('product_line', 'Commercial'))
        data_store[v_table].extend(v_rows)

        # 4. Compliance Events
        # ⚡ Unified Event Loop (Supports Multiple Events per Scenario)
        
        # Helper: Ensure overrides are lists
        if 'events' in overrides:
             for k, v in overrides['events'].items():
                 if isinstance(v, dict):
                     overrides['events'][k] = [v]
        
        # Helper: Map component names to config index (for Legacy ED1/ED2 support)
        comp_map = {c['name']: i for i, c in enumerate(engine.measure['rules']['clinical_events']['numerator_components'])}
        
        # Track generated counts per type to match metadata
        gen_counts = {} 
        
        # ⚡ AUTO-INJECT DENOMINATOR COMPONENTS (For Multi-Step Measures)
        # For complex measures like SMD, SPC, SPD: automatically generate identification events
        # even if not explicitly in test case scenarios
        auto_events = []
        if 'denominator_components' in engine.measure['rules']['clinical_events']:
            for denom_comp in engine.measure['rules']['clinical_events']['denominator_components']:
                comp_name = denom_comp['name']
                # Only auto-add if not already in compliant list
                if comp_name not in sc['compliant']:
                    auto_events.append(comp_name)
        
        # Iterate through ALL compliant events + Auto-Injected Denominator Components
        all_events = auto_events + sc['compliant']  # Denominator first, then numerator
        for event_name in all_events:
            # Get Component Config Index
            comp_idx = comp_map.get(event_name, -1)
            
            # Metadata Retrieval
            specific_meta = {}
            if 'events' in overrides and event_name in overrides['events']:
                 meta_list = overrides['events'][event_name]
                 current_count = gen_counts.get(event_name, 0)
                 if current_count < len(meta_list):
                     specific_meta = meta_list[current_count]
            
            # Legacy ED1/ED2 Support (Apply to first instance only)
            if 'date' not in specific_meta and comp_idx != -1 and gen_counts.get(event_name, 0) == 0:
                 legacy_date = overrides.get('events_by_index', {}).get(comp_idx + 1)
                 if legacy_date:
                     specific_meta['date'] = legacy_date
            
            # Global ED override (if still no date)
            if 'date' not in specific_meta and sc.get("event_date_override"):
                 specific_meta['date'] = sc.get("event_date_override")

            # Generate (injecting specific_metadata for the new engine logic)
            # We copy overrides to avoid polluting global state, but it's shallow copy of dict
            call_overrides = overrides.copy()
            call_overrides['specific_metadata'] = specific_meta
            
            result = engine.generate_clinical_event(
                mem_id, event_name, is_compliant=True, 
                offset_days=len(data_store.get('visit', []))*5, # Stagger slightly
                overrides=call_overrides,
                product_line=sc.get('product_line', 'Commercial')
            )
            
            # Smart Handler: Support both Single (Table, Row) and List [(Table, Row), ...]
            events_to_process = []
            if isinstance(result, list):
                events_to_process = result
            else:
                events_to_process = [result]
                
            for table_name, row in events_to_process:
                if table_name and table_name in data_store:
                    data_store[table_name].append(row)
            
            gen_counts[event_name] = gen_counts.get(event_name, 0) + 1

        # 5. Exclusion Events
        for excl_name in sc['excluded']:
            table_name, row = engine.generate_exclusion(mem_id, excl_name, overrides=overrides)
            if table_name and table_name in data_store:
                data_store[table_name].append(row)
        
        # 6. Monthly Flags (Structured Overrides)
        m_table, m_rows = engine.generate_monthly_membership(mem_id, sc.get('monthly_overrides', []))
        if m_table and m_rows:
            data_store[m_table].extend(m_rows)

    # 4. Quality Checks
    with open('data_columns_info.json', 'r') as f:
        full_schema = json.load(f)

    if not skip_quality_check:
        print("\n🔍 Running data quality checks...")
        from src.quality_checker import DataQualityChecker
        quality_checker = DataQualityChecker(data_store, full_schema)
        quality_report = quality_checker.check_all()
        quality_report_path = os.path.join(os.getenv('OUTPUT_DIR', 'output'), f'{measure_name}_Quality_Report.xlsx')
        quality_checker.export_report(quality_report_path)
        if not quality_report['passed']:
            print(f"⚠️  Quality check failed! See report: {quality_report_path}")

    # 5. NCQA Compliance
    if validate_ncqa and not skip_quality_check:
        print("\n🔍 Checking NCQA compliance...")
        try:
            from src.ncqa_compliance import NCQAComplianceChecker
            ncqa_spec_path = f'config/ncqa/{measure_name}_NCQA.yaml'
            vsd_manager = engine.vsd_manager if hasattr(engine, 'vsd_manager') else None
            checker = NCQAComplianceChecker(measure_config, ncqa_spec_path, vsd_manager)
            compliance = checker.check_compliance(data_store, scenarios)
            print(f"   Compliance Score: {compliance['score']}/100")
        except:
            pass

    output_dir = os.getenv('OUTPUT_DIR', 'output')
    print("\n📝 Writing output file...")
    if not output_path:
        output_path = os.path.join(output_dir, f'{measure_name}_MY2026_Mockup_v20.xlsx')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # Use a set to track all tables that have data
        all_target_tables = set(engine.schema['tables'][t]['name'] for t in engine.schema['tables'])
        all_target_tables.update(data_store.keys())
        
        has_written = False
        # Sort to keep stable order (Member, Enrollment first usually)
        for sheet_name in sorted(list(all_target_tables)):
            rows = data_store.get(sheet_name, [])
            if not rows: continue
            
            df = pd.DataFrame(rows)
            
            # ⚡ ROBUSTNESS: Dynamic Column Selection (Prefix-Independent)
            cols = full_schema.get(sheet_name)
            if not cols:
                # Extract the logical part of the table name (e.g. SMD_VISIT_IN -> VISIT)
                parts = sheet_name.split('_')
                logical_type = parts[1] if len(parts) > 1 else 'VISIT'
                
                # Try to find ANY matching table type in the master schema
                # e.g. If looking for SMD_VISIT_IN, use the columns from PSA_VISIT_IN
                for existing_sheet in full_schema.keys():
                    if f'_{logical_type}_' in existing_sheet:
                        cols = full_schema[existing_sheet]
                        print(f"    ✨ Auto-mapped {sheet_name} to {existing_sheet} column structure")
                        break
            
            if cols:
                # Reindex to match requested schema columns
                # We use union of existing and requested to avoid losing data
                df = df.reindex(columns=cols)
            
            # Excel sheet names max 31 chars
            df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
            print(f"  Written {len(df)} rows to {sheet_name}")
            has_written = True
            
        if not has_written:
            pd.DataFrame([{"Info": "No data generated"}]).to_excel(writer, sheet_name="Empty_Report")
    
    print(f"\n✅ Success! {measure_name} Mockup generated at {output_path}")
    return output_path

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='HEDIS Mockup Generator v2.0')
    parser.add_argument('measures', nargs='?', default='PSA', help='Comma-separated measure names (e.g. PSA,WCC)')
    parser.add_argument('--testcase', help='Path to test case file')
    parser.add_argument('--vsd', help='Path to VSD file')
    parser.add_argument('--no-ai', action='store_true', help='Disable AI extractor')
    parser.add_argument('--model', default='qwen2:0.5b', help='Ollama model name')
    parser.add_argument('--skip-quality-check', action='store_true', help='Skip quality checks')
    parser.add_argument('--validate-ncqa', action='store_true', help='Validate NCQA compliance')
    parser.add_argument('--depth', choices=['population', 'scenario'], default='population', help='Mocking depth: full population data or only explicit scenario events')
    parser.add_argument('--scope', choices=['all', 'mandatory'], default='all', help='Column scope: all fields (including rich metadata) or only mandatory/compliance fields')
    
    args = parser.parse_args()
    measures = [m.strip() for m in args.measures.split(',')]
    vsd_path = args.vsd if args.vsd else os.getenv('VSD_PATH', 'data/VSD_MY2026.xlsx')
    data_dir = os.getenv('DATA_DIR', 'data')
    
    print(f"🚀 Starting HEDIS Mockup Generation for: {', '.join(measures)}")
    testcase_dir = os.getenv('TESTCASE_DIR', data_dir)
    
    for measure in measures:
        tc_default = os.path.join(testcase_dir, f'{measure}_MY2026_TestCase.xlsx')
        tc_path = args.testcase if args.testcase else tc_default
        
        if not os.path.exists(tc_path) and not args.testcase:
            if os.path.exists(measure):
                tc_path = measure
                measure = os.path.basename(measure).split('_')[0].upper()
            else:
                try:
                    candidates = [f for f in os.listdir(testcase_dir) if f.upper().startswith(measure.upper()) and f.endswith(('.xlsx', '.csv'))]
                    if candidates:
                        tc_path = os.path.join(testcase_dir, candidates[0])
                        print(f"🔍 Auto-detected test case: {tc_path}")
                except:
                    pass

        if not os.path.exists(tc_path) and not args.testcase:
            standard_path = os.path.join(data_dir, f'{measure}_STANDARD.xlsx')
            if os.path.exists(standard_path): tc_path = standard_path

        run_measure_gen_custom(
            measure, tc_path, vsd_path, 
            disable_ai=args.no_ai, 
            model_name=args.model,
            skip_quality_check=args.skip_quality_check,
            validate_ncqa=args.validate_ncqa,
            mocking_depth=args.depth,
            column_scope=args.scope
        )
