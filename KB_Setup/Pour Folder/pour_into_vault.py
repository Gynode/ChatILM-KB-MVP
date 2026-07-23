# ===============================================================================================
# ChatILM KNOWLEDGE BASE INGESTION - BUKHARI EXPANSION
# ===============================================================================================
# CRITICAL CONFIGURATION INSTRUCTIONS:
# 1. INPUT CONFIGURATION: 
#    - Uses r'C:\ChatILM-HRE' to fix escape sequence warnings.
# 2. OUTPUT CONTROL PANEL:
#    - Configured to loop through all Bukhari JSON segments.
#    - KB_path_string: /Islam/Sunni/sunnah
# ===============================================================================================

import json
import sqlite3
import os
import sys
import glob
import numpy as np
from sentence_transformers import SentenceTransformer

# 1. PATH CONFIGURATION
sys.path.insert(0, r"C:\ChatILM-HRE")

# Define fallback path if import fails
DB_PATH = r"C:\CHATILM-KB\staging_vault.db"

# 2. Load Embedding Model
print("LOADING EMBEDDING ENGINE...")
model = SentenceTransformer('all-MiniLM-L6-v2')

def pour_into_vault(json_file_path, book_label, KB_path_string, table_name, language_code="en"):
    """Ingests Catholic Catechism atoms into the specified Vault Table."""
    
    print(f"\n--- INITIATING CATHOLIC POUR: {os.path.basename(json_file_path)} ---")
    
    if not os.path.exists(json_file_path):
        print(f"❌ ERROR: File not found: {json_file_path}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Ensure Catholic Table Structure
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_book TEXT,
            kb_path TEXT,
            content_text TEXT,
            content_arabic TEXT,
            vector BLOB,
            grade TEXT,
            language TEXT
        )
    """)

    with open(json_file_path, 'r', encoding='utf-8-sig') as f:
        data = json.load(f)

    atoms_count = 0
    
    for entry in data:
        # Hybrid logic: handles if the JSON is a list of strings or list of dicts
        if isinstance(entry, dict):
            english_text = entry.get('english', '')
        else:
            english_text = str(entry)

        if not english_text.strip():
            continue

        # Duplicate Check
        cursor.execute(f"SELECT id FROM {table_name} WHERE content_text = ? AND source_book = ?", (english_text, book_label))
        if cursor.fetchone():
            continue

        # Generate Vector Embedding
        vector = model.encode(english_text).astype(np.float32).tobytes()

        # Insert into Vault - Corrected 7-tuple alignment
        cursor.execute(f"""
            INSERT INTO {table_name} 
            (source_book, kb_path, content_text, content_arabic, vector, grade, language)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            book_label,      # 1. source_book
            KB_path_string,  # 2. kb_path
            english_text,    # 3. content_text
            "",              # 4. content_arabic (Empty but required)
            vector,          # 5. vector
            "",              # 6. grade
            language_code    # 7. language
        ))
        
        atoms_count += 1

    conn.commit()
    conn.close()
    print(f"VAULTED: {os.path.basename(json_file_path)} | NEW CATHOLIC ATOMS: {atoms_count}")

# --- OUTPUT CONTROL PANEL (CATHOLICISM ONLY) ---
if __name__ == "__main__":
    print("\n" + "="*60)
    print("      ChatILM KNOWLEDGE BASE: CATHOLIC DOMAIN EXPANSION")
    print("="*60)

    source_dir = r'C:\Alim\Christianity\Catholic' 
    
    json_files = glob.glob(os.path.join(source_dir, "*.json"))
    
    if not json_files:
        print(f"❌ FATAL: No Catholic JSON files found in {source_dir}")
        sys.exit(1)

    for file_path in json_files:
        pour_into_vault(
            json_file_path=file_path, 
            book_label="Catechism", 
            KB_path_string='/Christianity/Catholicism/Catechism', 
            table_name='catholic', 
            language_code='en'
        )

    print("\n" + "="*60)
    print("--- CATHOLIC POUR COMPLETE ---")
    print("Next: Run your Audit to check the final 50k count.")
    print("="*60 + "\n")