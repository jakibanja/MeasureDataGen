
from src.engine import MockupEngine
from datetime import datetime
import pandas as pd
import yaml

# Load Configs
with open('config/SMD.yaml', 'r') as f:
    measure_config = yaml.safe_load(f)

with open('config/schema_map.yaml', 'r') as f:
    schema = yaml.safe_load(f)

# Initialize Engine - Pass file paths, engine loads them internally
engine = MockupEngine('config/SMD.yaml', 'config/schema_map.yaml', year=2026, mocking_depth='scenario')

# Test 1: Schizophrenia Outpatient History (Should create 2 visits)
print("\n--- Test 1: Schizophrenia Outpatient History (Count: 2) ---")
# Use the correct path based on YAML structure: rules -> clinical_events -> denominator_components
comp_config = next(c for c in measure_config['rules']['clinical_events']['denominator_components'] 
                  if c['name'] == 'Schizophrenia_Outpatient_History')

events = engine.generate_composite_event(
    mem_id="TEST_MEM_01",
    component_config=comp_config,
    base_date=datetime(2026, 1, 15)
)

print(f"Generated {len(events)} events.")
for i, (table, row) in enumerate(events):
    print(f"Event {i+1} ({table}): Date={row.get('SERV_DT')}, POS={row.get('POS')}, Diag={row.get('DIAG_I_1')}")

# Test 2: Diabetes Pharmacy History (Composite: Visit + Rx)
print("\n--- Test 2: Diabetes Pharmacy History (Visit + Rx) ---")
comp_config_rx = next(c for c in measure_config['rules']['clinical_events']['denominator_components'] 
                     if c['name'] == 'Diabetes_Pharmacy_History')

events_rx = engine.generate_composite_event(
    mem_id="TEST_MEM_02",
    component_config=comp_config_rx,
    base_date=datetime(2026, 2, 10)
)

print(f"Generated {len(events_rx)} events.")
for i, (table, row) in enumerate(events_rx):
    date_field = 'RX_SERV_DT' if table == 'rx' else 'SERV_DT'
    code_field = 'RX_NDC' if table == 'rx' else 'DIAG_I_1'
    print(f"Event {i+1} ({table}): Date={row.get(date_field)}, Code={row.get(code_field)}")
