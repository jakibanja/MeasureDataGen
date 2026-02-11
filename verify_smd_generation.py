
from src.engine import MockupEngine
from datetime import datetime
import pandas as pd

def run_verification():
    print("--- Starting SMD Verification Run ---")
    
    # Init Engine
    engine = MockupEngine('config/SMD.yaml', 'config/schema_map.yaml', year=2026, mocking_depth='scenario')
    
    # Create reverse mapping: Physical Name -> Logical Key
    phys_to_logical = {cfg['name']: key for key, cfg in engine.schema['tables'].items()}

    # Mock Data Store
    data_store = {}
    for t in engine.schema['tables']:
        data_store[t] = []
        
    # Define Complex Component to Test
    components_to_test = [
        "Schizophrenia Diagnosis",
        "Diabetes Diagnosis",
        "Diabetes Medication"
    ]
    
    mem_id = "VERIFY_MEMBER_01"
    
    # ⚡ Simulate Main Loop Logic
    for comp_name in components_to_test:
        print(f"\nGeneratng: {comp_name}")
        
        # Call Engine
        result = engine.generate_clinical_event(
            mem_id, comp_name, is_compliant=True, offset_days=0, 
            overrides={'force_vs_names': [comp_name]} # Ensure VS name for logging
        )
        
        # Handle List vs Single (Crucial fix in main.py logic)
        events_to_process = []
        if isinstance(result, list):
            print(f"  -> Returned LIST of {len(result)} events (Composite Logic Working!)")
            events_to_process = result
        else:
            print(f"  -> Returned SINGLE event")
            events_to_process = [result]
            
        # Process Results
        for table_phys, row in events_to_process:
            # Resolve physical table name to logical key
            table = phys_to_logical.get(table_phys)
            
            if not table or table not in data_store:
                print(f"  Warning: Table {table_phys} (logical: {table}) not in schema!")
                continue
            data_store[table].append(row)
            # Log key fields
            date_val = row.get('SERV_DT') or row.get('RX_SERV_DT')
            code_val = row.get('DIAG_I_1') or row.get('RX_NDC')
            print(f"    + {table}: Date={date_val}, Code={code_val}")

    print("\n--- Verification Summary ---")
    total_events = sum(len(rows) for rows in data_store.values())
    print(f"Total Generated Events: {total_events}")
    
    # Assertion Checks
    visit_count = len(data_store.get('visit', []))
    rx_count = len(data_store.get('rx', []))
    
    print(f"Visit Count: {visit_count} (Expected: 1 Inpat + 2 Outpat + 1 Diab = 4)")
    print(f"Rx Count:    {rx_count}    (Expected: 1 Diab Rx = 1)")
    
    if visit_count == 4 and rx_count == 1:
        print("\n SUCCESS: All complex logic verified!")
    else:
        print("\n FAILURE: Counts do not match expectations.")

if __name__ == "__main__":
    run_verification()
