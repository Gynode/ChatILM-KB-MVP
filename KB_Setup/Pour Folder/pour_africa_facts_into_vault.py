import json
import sqlite3
import os
import glob
import numpy as np
from sentence_transformers import SentenceTransformer

# 1. SETUP
DB_PATH = r"C:\CHATILM-KB\staging_vault.db"

print("LOADING EMBEDDING ENGINE...")
model = SentenceTransformer('all-MiniLM-L6-v2')

def flatten_factbook(data, prefix=""):
    """Recursively crawls the Factbook JSON to extract individual fact strings."""
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

def pour_africa_facts(source_dir):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Table: facts_gk
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS facts_gk (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_book TEXT, kb_path TEXT, content_text TEXT,
            content_arabic TEXT, vector BLOB, grade TEXT, language TEXT
        )
    """)

    # Target strictly the *-clean.json files in the Africa folder
    clean_pattern = os.path.join(source_dir, "*-clean.json")
    clean_files = glob.glob(clean_pattern)

    if not clean_files:
        print(f"❌ FATAL: No *-clean.json files found in {source_dir}")
        return

    print(f"--- FOUND {len(clean_files)} CLEAN AFRICAN COUNTRY FILES ---")

    total_atoms = 0

    for file_path in clean_files:
        country_code = os.path.basename(file_path).replace("-clean.json", "").upper()
        
        # FIX: Using 'utf-8-sig' to handle BOM and encoding issues
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            try:
                data = json.load(f)
            except Exception as e:
                print(f"Skipping {country_code} due to JSON error: {e}")
                continue

        fact_atoms = flatten_factbook(data)
        print(f"Pouring {country_code}: {len(fact_atoms)} atoms.")

        for fact in fact_atoms:
            # Duplicate Check within facts_gk
            cursor.execute("SELECT id FROM facts_gk WHERE content_text = ?", (fact,))
            if cursor.fetchone():
                continue

            vector = model.encode(fact).astype(np.float32).tobytes()

            cursor.execute("""
                INSERT INTO facts_gk 
                (source_book, kb_path, content_text, content_arabic, vector, grade, language)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (f"Factbook_{country_code}", "/GK/GlobalFacts/Africa", fact, "", vector, "Global Fact", "en"))
            
            total_atoms += 1
        
        conn.commit()

    conn.close()
    print(f"\n--- SUCCESS: {total_atoms} AFRICAN ATOMS LOADED ---")

if __name__ == "__main__":
    # Specific Africa source path
    AFRICA_SOURCE = r"C:\Alim\factbook.json-master\africa"
    pour_africa_facts(AFRICA_SOURCE)