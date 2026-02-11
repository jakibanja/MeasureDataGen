import json
import os

def verify_ndc():
    json_path = 'data/HEDIS_Medication_Codes.json'
    
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found.")
        return

    # Load mapping
    with open(json_path, 'r') as f:
        mapping = json.load(f)
    
    # Test specific Value Sets from SPCE (Aligned with HEDIS MY 2026)
    targets = [
        'High and Moderate Intensity Statin Medications',
        'High, Moderate and Low Intensity Statin Medications'
    ]
    
    print(f"Verifying {len(mapping)} value sets in {json_path}...")
    
    for vs in targets:
        if vs in mapping:
            ndcs = mapping[vs].get('NDC', [])
            rxnorms = mapping[vs].get('RxNorm', [])
            print(f"\n✅ Value Set Found: {vs}")
            print(f"   - NDCs: {len(ndcs)} (Sample: {ndcs[0] if ndcs else 'None'})")
            print(f"   - RxNorms: {len(rxnorms)} (Sample: {rxnorms[0] if rxnorms else 'None'})")
        else:
            print(f"\n❌ Value Set NOT found: {vs}")

if __name__ == "__main__":
    verify_ndc()
