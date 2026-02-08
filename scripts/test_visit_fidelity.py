
import pandas as pd
import os
from src.engine import MockupEngine
from src.vsd import VSDManager

def test_visit_fidelity():
    vsd_path = 'data/VSD_MY2026.xlsx'
    if not os.path.exists(vsd_path):
        print("VSD not found, using basic test.")
        vsd = None
    else:
        vsd = VSDManager(vsd_path)
        
    engine = MockupEngine('config/PSA.yaml', 'config/schema_map.yaml', vsd_manager=vsd)
    
    # Test different visit types
    spans = [
        {'date': '2026-03-15', 'type': 'Outpatient'},
        {'date': '2026-05-20', 'type': 'Inpatient'},
        {'date': '2026-08-10', 'type': 'Emergency Department'},
        {'date': '2026-10-05', 'type': 'Telehealth'}
    ]
    
    table_name, rows = engine.generate_visits('TST_01', spans=spans)
    df = pd.DataFrame(rows)
    
    print(f"\nGenerated {len(df)} visits for TST_01:")
    print(df[['SERV_DT', 'POS', 'CPT_1', 'DIAG_I_1']])
    
    # Verify POS codes
    pos_map = {
        'Outpatient': '11',
        'Inpatient': '21',
        'Emergency': '23',
        'Telehealth': '02'
    }
    
    # Simple check (heuristic)
    for i, span in enumerate(spans):
        expected_pos = None
        for k, v in pos_map.items():
            if k in span['type']: 
                expected_pos = v
                break
        
        actual_pos = str(df.iloc[i]['POS'])
        if expected_pos and actual_pos == expected_pos:
            print(f"✅ Visit {i+1} ({span['type']}): POS {actual_pos} matches expected {expected_pos}")
        else:
            print(f"❌ Visit {i+1} ({span['type']}): POS {actual_pos} (Expected {expected_pos})")

if __name__ == "__main__":
    test_visit_fidelity()
