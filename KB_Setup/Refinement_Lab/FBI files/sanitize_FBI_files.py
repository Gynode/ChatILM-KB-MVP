import json
import re
import os

def clean_text(text):
    if not isinstance(text, str): return text
    # Strip all HTML tags
    clean = re.compile('<.*?>')
    text = re.sub(clean, '', text)
    # Normalize whitespace and HTML entities
    text = text.replace('&nbsp;', ' ')
    text = " ".join(text.split()).strip()
    return text

def process_node(node):
    if isinstance(node, dict):
        # Normalize keys (strip spaces) and recurse values
        return {k.strip(): process_node(v) for k, v in node.items()}
    elif isinstance(node, list):
        return [process_node(i) for i in node]
    else:
        return clean_text(node)

def execute_stage_1_clean(root_path):
    print(f"--- INITIATING STAGE 1: RECURSIVE CLEAN ---")
    for root, dirs, files in os.walk(root_path):
        for file in files:
            if file.endswith(".json") and not file.endswith("-clean.json"):
                source_file = os.path.join(root, file)
                # Create the [filename]-clean.json name
                name_part, ext = os.path.splitext(file)
                target_file = os.path.join(root, f"{name_part}-clean{ext}")
                
                try:
                    with open(source_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    cleaned_data = process_node(data)
                    
                    with open(target_file, 'w', encoding='utf-8') as f:
                        json.dump(cleaned_data, f, indent=4)
                    
                    print(f"CLEANED: {target_file}")
                except Exception as e:
                    print(f"FAILED: {source_file} | Error: {str(e)}")

# Target path set to the master repository
execute_stage_1_clean(r'C:\Alim\factbook.json-master')