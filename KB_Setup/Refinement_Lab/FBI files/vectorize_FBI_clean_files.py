import json
import os

def flatten_to_atoms(data, prefix_list):
    """Recursively flattens JSON into Atomic Strings."""
    atoms = []
    if isinstance(data, dict):
        for key, value in data.items():
            # Skip the 'text' key as a label, use it as the trigger for the value
            if key == "text":
                atoms.append(" :: ".join(prefix_list) + " :: " + str(value))
            else:
                atoms.extend(flatten_to_atoms(value, prefix_list + [key]))
    elif isinstance(data, list):
        for index, item in enumerate(data):
            atoms.extend(flatten_to_atoms(item, prefix_list + [str(index)]))
    return atoms

def generate_atomic_manifest(root_path):
    all_atoms = []
    for root, _, files in os.walk(root_path):
        for file in files:
            if file.endswith("-clean.json"):
                # Extract Country Name from the file or metadata
                country_code = file.replace("-clean.json", "").upper()
                
                with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Use the 'conventional short form' if available for better context
                try:
                    country_name = data['Government']['Country name']['conventional short form']['text']
                except KeyError:
                    country_name = country_code

                # Generate atoms for this country
                country_atoms = flatten_to_atoms(data, ["[CIA-world-factbook]", country_name])
                all_atoms.extend(country_atoms)
                
    return all_atoms

# Execute and save to a Master Atomic Manifest
manifest = generate_atomic_manifest(r'C:\Alim\factbook.json-master')

with open(r'C:\Alim\atomic_factbook_manifest.txt', 'w', encoding='utf-8') as f:
    for line in manifest:
        f.write(line + "\n")