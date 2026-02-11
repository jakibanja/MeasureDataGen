import sys
import os
sys.path.append(os.getcwd())

from src.ncqa_parser import NCQASpecParser

pdf_path = 'uploads/SMD_Spec.pdf'
measures = ['SMD', 'PSA', 'WCC']

for measure in measures:
    print(f"\nTesting extraction for {measure} from {pdf_path}...")
    parser = NCQASpecParser(pdf_path)
    config = parser.generate_config(target_measure_title=measure)
    print(f"Resulting Config for {measure}:")
    print(f"  Name: {config['measure_name']}")
    print(f"  Age: {config['rules']['age_range']}")
    for comp in config['rules']['clinical_events']['numerator_components']:
        print(f"  Numerator: {comp['name']} -> Table: {comp.get('table')}")
