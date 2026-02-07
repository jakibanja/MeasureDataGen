import pandas as pd
import json
import os
from src.engine import MockupEngine
from src.parser import TestCaseParser
from src.vsd import VSDManager

def run_measure_gen_custom(measure_name, testcase_path, vsd_path):
    """
    Core function for running measure generation with explicit paths.
    Returns the path to the generated output file.
    """
    config_path = f'config/{measure_name}.yaml'
    schema_path = 'config/schema_map.yaml'
    
    if not os.path.exists(testcase_path):
        print(f"Skipping {measure_name}: Test case file not found at {testcase_path}")
        return None

    # Initialize VSD Manager with measurement year validation
    vsd_manager = VSDManager(vsd_path, measurement_year=2026)
    
    # Initialize AI Extractor (Optional)
    extractor = None
    try:
        from src.ai_extractor import AIScenarioExtractor
        print("Initializing AI Extractor (tinyllama)...")
        extractor = AIScenarioExtractor(model_name="tinyllama")
    except Exception as e:
        print(f"⚠️  AI Extractor initialization failed (running in regex-only mode): {e}")

    parser = TestCaseParser(testcase_path, extractor=extractor)
    engine = MockupEngine(config_path, schema_path, vsd_manager=vsd_manager)
    
    return _process_measure(measure_name, parser, engine)

def run_measure_gen(measure_name):
    """ Legacy wrapper for default paths """
    testcase_path = f'data/{measure_name}_MY2026_TestCase.xlsx'
    if measure_name == 'WCC':
         if not os.path.exists(testcase_path):
             testcase_path = 'data/WCC_Test_Scenarios.xlsx'
             
    vsd_path = r"C:\Users\sushi\Downloads\RAG-Tutorials-main\data\HEDIS MY 2026 Volume 2 Value Set Directory_2025-08-01.xlsx"
    
    return run_measure_gen_custom(measure_name, testcase_path, vsd_path)

def _process_measure(measure_name, parser, engine, output_path=None, audit_logger=None):
    """
    Core processing logic: parse scenarios, generate data, write output.
    
    Args:
        measure_name: Name of the measure (e.g., 'PSA')
        parser: TestCaseParser instance
        engine: MockupEngine instance
        output_path: Optional custom output path
        audit_logger: Optional AuditLogger instance for tracking
    
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

    # 3. Process each scenario
    for sc in scenarios:
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

    # 4. Run Data Quality Checks
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

    # 5. Write to Output
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
