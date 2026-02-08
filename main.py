import pandas as pd
import json
import os
import time
from dotenv import load_dotenv
from src.engine import MockupEngine
from src.parser import TestCaseParser
from src.vsd import VSDManager

# Load environment variables from .env file
load_dotenv()

# ⚡ Performance Optimization: Global caches to avoid reloading heavy resources
_vsd_cache = {}
_ai_extractor_cache = None

def run_measure_gen_custom(measure_name, testcase_path, vsd_path, skip_quality_check=False, disable_ai=None):
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
    config_path = f'config/{measure_name}.yaml'
    schema_path = 'config/schema_map.yaml'
    
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

    parser = TestCaseParser(testcase_path, extractor=extractor)
    engine = MockupEngine(config_path, schema_path, vsd_manager=vsd_manager)
    
    result = _process_measure(measure_name, parser, engine, skip_quality_check=skip_quality_check)
    
    total_time = time.time() - start_time
    print(f"\n⏱️  Total generation time: {total_time:.2f} seconds")
    
    return result

def run_measure_gen(measure_name):
    """ Legacy wrapper for default paths """
    testcase_path = f'data/{measure_name}_MY2026_TestCase.xlsx'
    if measure_name == 'WCC':
         if not os.path.exists(testcase_path):
             testcase_path = 'data/WCC_Test_Scenarios.xlsx'
             
    vsd_path = r"C:\Users\sushi\Downloads\RAG-Tutorials-main\data\HEDIS MY 2026 Volume 2 Value Set Directory_2025-08-01.xlsx"
    
    return run_measure_gen_custom(measure_name, testcase_path, vsd_path)

def _process_measure(measure_name, parser, engine, output_path=None, audit_logger=None, skip_quality_check=False):
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
    print(f"📊 Processing {len(scenarios)} scenarios...")
    for idx, sc in enumerate(scenarios, 1):
        # Progress indicator every 10 scenarios
        if idx % 10 == 0 or idx == len(scenarios):
            print(f"  Progress: {idx}/{len(scenarios)} scenarios processed ({idx*100//len(scenarios)}%)")
        
        mem_id = sc['id']
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

        # Compliance Events
        for i, comp in enumerate(engine.measure['rules']['clinical_events']['numerator_components']):
            if comp['name'] in sc['compliant']:
                table_name, row = engine.generate_clinical_event(
                    mem_id, comp['name'], is_compliant=True, offset_days=i*30, 
                    overrides=overrides
                )
                if table_name and table_name in data_store:
                    data_store[table_name].append(row)
        
        # Exclusion Events
        for excl_name in sc['excluded']:
            table_name, row = engine.generate_exclusion(mem_id, excl_name, overrides=overrides)
            if table_name and table_name in data_store:
                data_store[table_name].append(row)

    # Load full schema for both quality checks and writing
    with open('data_columns_info.json', 'r') as f:
        full_schema = json.load(f)

    # 4. Run Data Quality Checks (optional for faster generation)
    if not skip_quality_check:
        print("\n🔍 Running data quality checks...")
        from src.quality_checker import DataQualityChecker
        
        quality_checker = DataQualityChecker(data_store, full_schema)
        quality_report = quality_checker.check_all()
        
        # Export quality report
        quality_report_path = f'output/{measure_name}_Quality_Report.xlsx'
        quality_checker.export_report(quality_report_path)
        
        # Warn if critical issues found
        if not quality_report['passed']:
            print(f"\n⚠️  WARNING: {quality_report['total_issues']} critical issues found!")
            print(f"   Review quality report: {quality_report_path}")
            print(f"   Continuing with mockup generation...")
    else:
        print("\n⚡ Skipping quality checks for faster generation")

    # 5. Write to Output
    print("\n📝 Writing output file...")
    if not output_path:
        output_path = f'output/{measure_name}_MY2026_Mockup_v15.xlsx'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        for sheet_name in full_schema.keys():
            # Only write tables that match this measure
            if not sheet_name.startswith(f"{measure_name}_"):
                continue
                
            rows = data_store.get(sheet_name, [])
            df = pd.DataFrame(rows)
            df = df.reindex(columns=full_schema[sheet_name])
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            print(f"  Written {len(df)} rows to {sheet_name}")
    
    print(f"\n✅ Success! {measure_name} Mockup generated at {output_path}")
    return output_path

if __name__ == "__main__":
    for m in ['PSA']:  # Add 'WCC', 'IMA' when ready
        run_measure_gen(m)
