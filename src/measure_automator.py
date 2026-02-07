import json
import os
import shutil
import yaml

def automate_new_measure(new_measure_name, source_measure='PSA'):
    """
    Automates the creation of schema and config for a new HEDIS measure.
    Values are cloned from a source measure (default: PSA) and renamed.
    """
    print(f"🚀 Initializing automation for NEW MEASURE: {new_measure_name}")
    
    # 1. Update data_columns_info.json (Schema Definitions)
    json_path = 'data_columns_info.json'
    try:
        with open(json_path, 'r') as f:
            schema = json.load(f)
        
        new_tables = {}
        for table, cols in schema.items():
            if table.startswith(f"{source_measure}_"):
                # Create corresponding table name for new measure
                new_table_name = table.replace(f"{source_measure}_", f"{new_measure_name}_")
                new_tables[new_table_name] = cols
                print(f"  - Generated schema for: {new_table_name}")
        
        # Merge and save
        schema.update(new_tables)
        with open(json_path, 'w') as f:
            json.dump(schema, f, indent=4)
        print("✅ Schema (data_columns_info.json) updated.")
        
    except Exception as e:
        print(f"❌ Failed to update schema: {e}")
        return

    # 2. Clone Configuration (Drafting config/IMA.yaml)
    source_config = f'config/{source_measure}.yaml'
    target_config = f'config/{new_measure_name}.yaml'
    
    if not os.path.exists(target_config):
        try:
            with open(source_config, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Simple text replacement for measure name
            config_data['measure_name'] = new_measure_name
            # Clear out specific clinical events to force user review (safety)
            # config_data['rules']['clinical_events']['numerator_components'] = [] 
            
            with open(target_config, 'w') as f:
                yaml.dump(config_data, f, sort_keys=False)
            print(f"✅ Configuration drafted at {target_config}")
            print("   👉 PLEASE EDIT THIS FILE to define specific numerators/exclusions!")
            
        except Exception as e:
            print(f"❌ Failed to create config: {e}")
    else:
        print(f"ℹ️  Config file {target_config} already exists. Skipping.")

    print(f"\n✨ Automation Complete! You can now run main.py for {new_measure_name}.")
    print(f"   (Don't forget to add '{new_measure_name}' to the list in main.py)")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        automate_new_measure(sys.argv[1])
    else:
        print("Usage: python src/measure_automator.py <MEASURE_NAME>")
