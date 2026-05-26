#!/usr/bin/env python3
"""
Exports the Pydantic VTRSidecar schema to a standard JSON Schema file.
Used in the CI pipeline to ensure the Python code and formal spec are synchronized.
"""

import os
import json
import sys

# Ensure the script can import from vtr_standard
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from vtr_standard.poc.schemas import VTRSidecar
except ImportError as e:
    print(f"Error importing VTRSidecar: {e}")
    sys.exit(1)

def export_schema():
    specs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'specs'))
    os.makedirs(specs_dir, exist_ok=True)

    schema_path = os.path.join(specs_dir, 'vtr-sidecar.schema.json')

    # Generate JSON schema from Pydantic model
    schema_dict = VTRSidecar.model_json_schema()

    with open(schema_path, 'w') as f:
        json.dump(schema_dict, f, indent=2)

    print(f"Successfully exported schema to {schema_path}")

if __name__ == '__main__':
    export_schema()
