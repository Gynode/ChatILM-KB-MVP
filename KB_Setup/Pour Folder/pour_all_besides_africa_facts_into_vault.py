import json
import sqlite3
import os
import glob
import numpy as np
from sentence_transformers import SentenceTransformer

# 1. SETUP
DB_PATH = r"C:\CHATILM-KB\staging_vault.db"
model = SentenceTransformer('all-MiniLM-L6-v2')

def flatten_factbook(data, prefix=""):
    items = []
    if isinstance(data, dict):
        for key, value in data.items():
            new_prefix = f"{prefix} > {key}" if prefix else key
            items.extend(flatten_factbook(value, new_prefix))
    elif isinstance(data, list):
        for item in data:
            items.extend(flatten_factbook(item, prefix))
    else:
        if str(data).strip():
            items.append(f"{prefix}: {data}")
    return items

def pour_global_remaining(root_dir):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get all subdirectories (regions)
    regions = [d for d in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, d))]
    
    # Skip Africa as it's already vaulted
    regions_to_process = [r for r in regions if r.lower() != 'africa']

    print(f"--- REGIONS DETECTED: {', '.join(regions_to_process)} ---")

    total_global_atoms = 0

    for region in regions_to_process:
        region_path = os.path.join(root_dir, region)
        clean_pattern = os.path.join(region_path, "*-clean.json")
        clean_files = glob.glob(clean_pattern)

        print(f"\nProcessing Region: {region.upper()} ({len(clean_files)} countries)")

        for file_path in clean_files:
            country_code = os.path.basename(file_path).replace("-clean.json", "").upper()
            
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                try:
                    data = json.load(f)
                except:
                    continue

            fact_atoms = flatten_factbook(data)
            
            for fact in fact_atoms:
                # Duplicate Check
                cursor.execute("SELECT id FROM facts_gk WHERE content_text = ?", (fact,))
                if cursor.fetchone():
                    continue

                vector = model.encode(fact).astype(np.float32).tobytes()

                cursor.execute("""
                    INSERT INTO facts_gk 
                    (source_book, kb_path, content_text, content_arabic, vector, grade, language)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (f"Factbook_{country_code}", f"/GK/GlobalFacts/{region.capitalize()}", fact, "", vector, "Global Fact", "en"))
                
                total_global_atoms += 1
        
        conn.commit()
        print(f"Region {region.upper()} Complete.")

    conn.close()
    print(f"\n--- GLOBAL VAULTING COMPLETE: {total_global_atoms} NEW ATOMS ADDED ---")

if __name__ == "__main__":
    FACTBOOK_ROOT = r"C:\Alim\factbook.json-master"
    pour_global_remaining(FACTBOOK_ROOT)