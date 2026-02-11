import json
import os
import shutil

class SchemaManager:
    """
    Manages the data_columns_info.json schema file.
    Handles 'Universalization' (creating TEMPLATE_ tables) and 
    'Expansion' (cloning templates for new measures).
    """
    
    def __init__(self, schema_path='data_columns_info.json'):
        self.schema_path = schema_path
        self.schema = {}
        self.load_schema()

    def load_schema(self):
        """Load the current schema from JSON."""
        if os.path.exists(self.schema_path):
            with open(self.schema_path, 'r') as f:
                self.schema = json.load(f)
        else:
            print(f"Warning: Schema file {self.schema_path} not found. Starting fresh.")
            self.schema = {}

    def save_schema(self):
        """Save the current schema to JSON."""
        with open(self.schema_path, 'w') as f:
            json.dump(self.schema, f, indent=4)
        print(f"Schema saved to {self.schema_path}")

    def universalize_schema(self, source_measure='PSA'):
        """
        Create TEMPLATE_* tables based on a robust source measure (default: PSA).
        This decouples future measures from legacy naming.
        """
        print(f"Universalizing schema using {source_measure} as base...")
        
        # Check if templates already exist
        if any(k.startswith('TEMPLATE_') for k in self.schema.keys()):
            print("  TEMPLATE_* tables already exist. Skipping creation.")
            return

        new_templates = {}
        for table_key, columns in self.schema.items():
            if table_key.startswith(f"{source_measure}_"):
                # Define the logical suffix (e.g. MEMBER_IN, VISIT_IN)
                suffix = table_key.replace(f"{source_measure}_", "")
                template_key = f"TEMPLATE_{suffix}"
                
                new_templates[template_key] = columns
                print(f"  + Created {template_key} from {table_key}")

        if new_templates:
            self.schema.update(new_templates)
            self.save_schema()
        else:
            print(f"Warning: Could not find any tables starting with {source_measure}_ to use as templates.")

    def expand_schema(self, new_measure_name):
        """
        Ensure schema exists for a new measure by cloning TEMPLATE_* tables.
        """
        new_measure_name = new_measure_name.upper()
        print(f"Expanding schema for {new_measure_name}...")

        # 1. Ensure we have templates
        if not any(k.startswith('TEMPLATE_') for k in self.schema.keys()):
            self.universalize_schema()

        # 2. Clone templates for new measure
        new_tables = {}
        for table_key, columns in self.schema.items():
            if table_key.startswith('TEMPLATE_'):
                suffix = table_key.replace('TEMPLATE_', "")
                new_key = f"{new_measure_name}_{suffix}"
                
                if new_key not in self.schema:
                    new_tables[new_key] = columns
                    print(f"  + Created {new_key}")
        
        if new_tables:
            self.schema.update(new_tables)
            self.save_schema()
        else:
            print(f"  Schema for {new_measure_name} already complete.")

if __name__ == "__main__":
    # Test Run
    sm = SchemaManager()
    sm.universalize_schema()
    sm.expand_schema("DEMO_MEASURE")
