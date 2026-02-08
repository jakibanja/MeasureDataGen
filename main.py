import pandas as pd
import json
import os
import time
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

def run_measure_gen_custom(measure_name, testcase_path, vsd_path, skip_quality_check=False, disable_ai=None, validate_ncqa=False):
    """
    Core function for running measure generation with explicit paths.
    Returns the path to the generated output file.
    
    Args:
        measure_name: Name of the measure (e.g., 'PSA')
        testcase_path: Path to test case Excel file
        vsd_path: Path to VSD Excel file
        skip_quality_check: If True, skips quality checks for faster generation
        disable_ai: If True, skips AI Extractor (faster). If None, checks DISABLE_AI_EXTRACTOR env var
    """
    start_time = time.time()
    measure_name = measure_name.upper()
    config_path = f'config/{measure_name}.yaml'
    schema_path = 'config/schema_map.yaml'
    
    # ⚡ Universal Fallback: If no specific config exists, use the Universal template
    if not os.path.exists(config_path):
        print(f"⚠️  No config found for {measure_name}, using Universal template...")
        config_path = 'config/Universal.yaml'
    
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
    # Can be disabled via parameter or environment variable
    if disable_ai is None:
        disable_ai = os.getenv('DISABLE_AI_EXTRACTOR', 'false').lower() == 'true'
    
    global _ai_extractor_cache
    extractor = None
    
    if disable_ai:
        print("⚡ AI Extractor disabled (using regex-only mode for maximum speed)")
    else:
        try:
            from src.ai_extractor import AIScenarioExtractor
            if _ai_extractor_cache is None:
                print("🤖 Initializing AI Extractor (first time only, this may take 5-15 seconds)...")
                print("   💡 Tip: Set DISABLE_AI_EXTRACTOR=true to skip this and use regex-only mode")
                ai_load_start = time.time()
                
                # Add timeout to prevent hanging
                import signal
                def timeout_handler(signum, frame):
                    raise TimeoutError("AI Extractor initialization timed out")
                
                # Set 30 second timeout (Windows doesn't support signal.alarm, so we'll use a different approach)
                try:
                    _ai_extractor_cache = AIScenarioExtractor(model_name="tinyllama")
                    print(f"   ✓ AI Extractor loaded in {time.time() - ai_load_start:.2f}s")
                except Exception as init_error:
                    print(f"   ❌ AI Extractor failed to initialize: {init_error}")
                    print(f"   ⚡ Continuing in regex-only mode (faster anyway!)")
                    _ai_extractor_cache = "FAILED"  # Mark as failed to avoid retrying
            elif _ai_extractor_cache == "FAILED":
                print("⚡ AI Extractor previously failed, using regex-only mode")
            else:
                print("⚡ Using cached AI Extractor (instant!)")
                extractor = _ai_extractor_cache
        except Exception as e:
            print(f"⚠️  AI Extractor initialization failed (running in regex-only mode): {e}")
            _ai_extractor_cache = "FAILED"

    # ⚡ Auto-detect format and use appropriate parser
    use_standard_parser = _is_standard_format(testcase_path)
    
    if use_standard_parser:
        print("📋 Detected standard format - using StandardFormatParser")
        parser = StandardFormatParser(testcase_path)
    else:
        print("📋 Detected legacy format - using TestCaseParser")
        parser = TestCaseParser(testcase_path, extractor=extractor)
    
    engine = MockupEngine(config_path, schema_path, vsd_manager=vsd_manager, measure_name_override=measure_name)
    
    result = _process_measure(measure_name, parser, engine, skip_quality_check=skip_quality_check, validate_ncqa=validate_ncqa)
    
    total_time = time.time() - start_time
    print(f"\n⏱️  Total generation time: {total_time:.2f} seconds")
    
    return result

def _is_standard_format(file_path):
    """
    Detect if test case file is in standard format.
    
    Returns True if:
    - Filename contains '_STANDARD'
    - File has single sheet with standard columns (MEMBER_ID, ENROLLMENT_1_START, etc.)
    """
    # Check filename
    if '_STANDARD' in file_path.upper():
        return True
    
    # Check file structure
    try:
        xl = pd.ExcelFile(file_path)
        # Standard format has single sheet
        if len(xl.sheet_names) == 1:
            df = pd.read_excel(file_path, nrows=0)  # Just read headers
            columns = set(df.columns)
            # Check for standard format columns
            standard_indicators = {'MEMBER_ID', 'ENROLLMENT_1_START', 'VISIT_1_DATE', 'EVENT_1_NAME'}
            if standard_indicators.issubset(columns):
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
             
    # Use VSD path from environment variable
    vsd_path = os.getenv('VSD_PATH', 'data/VSD_MY2026.xlsx')
    
    return run_measure_gen_custom(measure_name, testcase_path, vsd_path)

def _process_measure(measure_name, parser, engine, output_path=None, audit_logger=None, skip_quality_check=False, validate_ncqa=False):
    """
    Core processing logic: parse scenarios, generate data, write output.
    
    Args:
        measure_name: Name of the measure (e.g., 'PSA')
        parser: TestCaseParser instance
        engine: MockupEngine instance
        output_path: Optional custom output path
        audit_logger: Optional AuditLogger instance for tracking
        skip_quality_check: If True, skips quality checks for faster generation
    
    Returns:
        Path to generated output file
    """
    print(f"\n--- Processing {measure_name} ---")
    
    # Load measure config
    import yaml
    config_path = f'config/{measure_name}.yaml'
    with open(config_path) as f:
        measure_config = yaml.safe_load(f)
    
    # 1. Parse Scenarios
    print("Reading scenarios from {}...".format(parser.file_path))
    scenarios = parser.parse_scenarios(measure_config)
    print(f"Found {len(scenarios)} scenarios.")
    
    # Log parsing
    if audit_logger:
        ai_fallback_count = sum(1 for sc in scenarios if sc.get('_ai_extracted', False))
        audit_logger.log_parsing(len(scenarios), ai_fallback_count)

    # 2. Containers for data (dynamically build based on measure)
    data_store = {}
    # Get all table names from schema
    for table_key, table_info in engine.schema['tables'].items():
        table_name = table_info['name']
        data_store[table_name] = []

    # 3. Process each scenario with progress indicators
    from src.progress import progress_tracker
    progress_tracker.update(f"🔄 Processing {len(scenarios)} scenarios for {measure_name}...", member_count=0)
    
    print(f"📊 Processing {len(scenarios)} scenarios...")
    for idx, sc in enumerate(scenarios, 1):
        mem_id = sc['id']
        progress_tracker.update(
            f"🔄 Generating records: {mem_id}", 
            member_count=idx,
            details=f"Processing member {idx} of {len(scenarios)}"
        )
        
        # Progress indicator every 10 scenarios
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
        v_table, v_rows = engine.generate_visits(mem_id, spans=sc.get('visit_spans'))
        data_store[v_table].extend(v_rows)

        # 4. Compliance Events
        # Track which components we've processed to avoid duplicates
        processed_components = set()
        
        # First, process components defined in the measure config
        for i, comp in enumerate(engine.measure['rules']['clinical_events']['numerator_components']):
            if comp['name'] in sc['compliant']:
                table_name, row = engine.generate_clinical_event(
                    mem_id, comp['name'], is_compliant=True, offset_days=i*30, 
                    overrides=overrides
                )
                if table_name and table_name in data_store:
                    data_store[table_name].append(row)
                processed_components.add(comp['name'])
        
        # Then, process any extra events in sc['compliant'] not in config (Universal support)
        for i, event_name in enumerate(sc['compliant']):
            if event_name not in processed_components:
                # Default to 'visit' table for unknown events
                table_name, row = engine.generate_clinical_event(
                    mem_id, event_name, is_compliant=True, offset_days=(len(processed_components)+i)*30, 
                    overrides=overrides
                )
                if table_name and table_name in data_store:
                    data_store[table_name].append(row)

        # 5. Exclusion Events
        for excl_name in sc['excluded']:
            table_name, row = engine.generate_exclusion(mem_id, excl_name, overrides=overrides)
            if table_name and table_name in data_store:
                data_store[table_name].append(row)

    # Load full schema for both quality checks and writing
    with open('data_columns_info.json', 'r') as f:
        full_schema = json.load(f)

    # 4. Run Data Quality Checks (optional for faster generation)
    if not skip_quality_check:
        progress_tracker.update("🔍 Running data quality checks...", details="Verifying data integrity and schema compliance")
        print("\n🔍 Running data quality checks...")
        from src.quality_checker import DataQualityChecker
        
        quality_checker = DataQualityChecker(data_store, full_schema)
        quality_report = quality_checker.check_all()
        
        # Export quality report
        quality_report_path = f'output/{measure_name}_Quality_Report.xlsx'
        quality_checker.export_report(quality_report_path)
        
        # Warn if critical issues found
        if not quality_report['passed']:
            print(f"⚠️  Quality check failed! See report: {quality_report_path}")
    else:
        print("\n⚡ Skipping quality checks for faster generation")

    # 5. Run NCQA Compliance Checks (if enabled)
    if validate_ncqa and not skip_quality_check:
        progress_tracker.update("🔍 Checking NCQA compliance...", details="Validating against official NCQA rules")
        print("\n🔍 Checking NCQA compliance...")
        try:
            from src.ncqa_compliance import NCQAComplianceChecker
            
            # Look for NCQA spec
            ncqa_spec_path = f'config/ncqa/{measure_name}_NCQA.yaml'
            
            # Use VSD manager from engine if available
            vsd_manager = engine.vsd_manager if hasattr(engine, 'vsd_manager') else None
            
            checker = NCQAComplianceChecker(measure_config, ncqa_spec_path, vsd_manager)
            compliance = checker.check_compliance(data_store, scenarios)
            
            print(f"   Compliance Score: {compliance['score']}/100")
            
            if compliance['issues']:
                print("   ⚠️ Compliance Issues:")
                for issue in compliance['issues']:
                    print(f"   - {issue}")
            else:
                print("   ✅ Data appears compliant with available rules.")
            
            # Save simple report
            report_path = f'output/{measure_name}_Compliance_Report.txt'
            with open(report_path, 'w') as f:
                f.write(f"NCQA Compliance Report for {measure_name}\n")
                f.write(f"Score: {compliance['score']}/100\n")
                f.write(f"Status: {'PASSED' if compliance['passed'] else 'FAILED'}\n\n")
                f.write("Issues found:\n" if compliance['issues'] else "No issues found.\n")
                for issue in compliance['issues']:
                    f.write(f"- {issue}\n")
                    
        except ImportError:
            print("⚠️ NCQAComplianceChecker not found. Skipping.")
        except Exception as e:
            print(f"⚠️ Compliance check error: {e}")

    # 6. Write to Output
    print("\n📝 Writing output file...")
    if not output_path:
        output_path = f'output/{measure_name}_MY2026_Mockup_v15.xlsx'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # Get all mapped table names for this measure from engine
        measure_tables = [table['name'] for table in engine.schema['tables'].values()]
        
        has_written = False
        for sheet_name in measure_tables:
            rows = data_store.get(sheet_name, [])
            if not rows:
                continue
                
            df = pd.DataFrame(rows)
            # Use full_schema for column ordering if available, else use df columns
            # Map sheet_name back to logical name or PSA counterpart to get columns
            logical_key = next((k for k, v in engine.schema['tables'].items() if v['name'] == sheet_name), None)
            psa_sheet = f"PSA_{logical_key.upper()}_IN" if logical_key else None
            
            cols = full_schema.get(sheet_name)
            if not cols and psa_sheet:
                cols = full_schema.get(psa_sheet)
                
            if cols:
                df = df.reindex(columns=[c for c in cols if c in df.columns or True]) # Mantain order, allow new
            
            df.to_excel(writer, sheet_name=sheet_name[:31], index=False) # Excel sheet name limit
            print(f"  Written {len(df)} rows to {sheet_name}")
            has_written = True
            
        if not has_written:
            # Fallback to avoid "At least one sheet must be visible"
            pd.DataFrame([{"Info": "No data generated"}]).to_excel(writer, sheet_name="Empty_Report")
    
    progress_tracker.update("✅ Generation complete!", details=f"Mockup saved to {os.path.basename(output_path)}")
    print(f"\n✅ Success! {measure_name} Mockup generated at {output_path}")
    return output_path

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='HEDIS Mockup Generator v2.0')
    parser.add_argument('measures', nargs='?', default='PSA', help='Comma-separated measure names (e.g. PSA,WCC)')
    parser.add_argument('--testcase', help='Path to test case file')
    parser.add_argument('--vsd', help='Path to VSD file')
    parser.add_argument('--no-ai', action='store_true', help='Disable AI extractor')
    
    args = parser.parse_args()
    
    measures = [m.strip() for m in args.measures.split(',')]
    vsd_path = args.vsd if args.vsd else os.getenv('VSD_PATH', 'data/VSD_MY2026.xlsx')
    
    print(f"🚀 Starting HEDIS Mockup Generation for: {', '.join(measures)}")
    
    for measure in measures:
        tc_path = args.testcase if args.testcase else f'data/{measure}_MY2026_TestCase.xlsx'
        # Try STANDARD format if default missing
        if not os.path.exists(tc_path) and not args.testcase:
            standard_path = f'data/{measure}_STANDARD.xlsx'
            if os.path.exists(standard_path): tc_path = standard_path

        run_measure_gen_custom(
            measure, 
            tc_path, 
            vsd_path, 
            disable_ai=args.no_ai
        )
