
import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'src'))

from engine import MockupEngine
from vsd import VSDManager
import yaml

def test_column_mapping():
    print("🚀 Verifying Column Mapping & Code Routing...")
    
    # Setup dummy environment
    vsd_path = 'data/VSD_MY2026.xlsx'
    if not os.path.exists(vsd_path):
        vsd_path = 'data/VSD_Manual_Upload.xlsx'

    config_path = 'config/PSA.yaml'
    schema_path = 'config/schema_map.yaml'
    
    vsd = VSDManager(vsd_path)
    engine = MockupEngine(config_path, schema_path, vsd_manager=vsd, year=2026)
    
    # 1. Test RX NDC Mapping
    print("\n--- Testing RX Mapping ---")
    vs_name = "High and Moderate Intensity Statin Medications"
    code = engine._get_code_override(vs_name, 'rx')
    print(f"   Value Set: {vs_name}")
    print(f"   Picked Code (NDC): {code}")
    
    # Generate event
    t_name, row = engine.generate_clinical_event("MEM1", "Statin Therapy", overrides={'force_table': 'rx', 'force_vs_names': [vs_name]})
    print(f"   Target Table: {t_name}")
    print(f"   NDC Column (RX_NDC): {row.get('RX_NDC')}")
    
    if row.get('RX_NDC') == code:
        print("   ✅ SUCCESS: NDC correctly mapped to RX_NDC")
    else:
        print(f"   ❌ FAILURE: NDC mapped to {list(row.keys())}")

    # 2. Test Visit Diagnosis Mapping (ICD-10)
    print("\n--- Testing Visit Diagnosis Mapping ---")
    vs_diag = "Schizophrenia" # Usually contains ICD-10
    diag_code = engine.vsd_manager.get_random_code(vs_diag)
    diag_system = engine.vsd_manager.get_code_system(diag_code)
    print(f"   Value Set: {vs_diag}")
    print(f"   Picked Code: {diag_code} ({diag_system})")
    
    t_name, row = engine.generate_clinical_event("MEM1", "Schizophrenia Diagnosis", overrides={'force_table': 'visit', 'force_vs_names': [vs_diag]})
    print(f"   DIAG Column (DIAG_I_1): {row.get('DIAG_I_1')}")
    print(f"   CPT Column (CPT_1): {row.get('CPT_1')}")
    
    if row.get('DIAG_I_1') == diag_code:
        print("   ✅ SUCCESS: Diagnosis correctly mapped to DIAG_I_1")
    else:
        print("   ❌ FAILURE: Diagnosis not mapped to DIAG_I_1")

    # 3. Test Visit Procedure Mapping (CPT)
    print("\n--- Testing Visit Procedure Mapping ---")
    vs_proc = "Outpatient" # Usually contains CPT/HCPCS
    proc_code = engine.vsd_manager.get_random_code(vs_proc)
    proc_system = engine.vsd_manager.get_code_system(proc_code)
    print(f"   Value Set: {vs_proc}")
    print(f"   Picked Code: {proc_code} ({proc_system})")
    
    t_name, row = engine.generate_clinical_event("MEM1", "Outpatient Visit", overrides={'force_table': 'visit', 'force_vs_names': [vs_proc]})
    print(f"   CPT Column (CPT_1): {row.get('CPT_1')}")
    print(f"   DIAG Column (DIAG_I_1): {row.get('DIAG_I_1')}") # Should be a random diag, but not matching proc_code
    
    if row.get('CPT_1') == proc_code:
        print("   ✅ SUCCESS: Procedure correctly mapped to CPT_1")
    else:
        print("   ❌ FAILURE: Procedure not mapped to CPT_1")

if __name__ == "__main__":
    test_column_mapping()
