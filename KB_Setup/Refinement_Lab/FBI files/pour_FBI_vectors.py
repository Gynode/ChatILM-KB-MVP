import sqlite3
import os
import datetime
from sentence_transformers import SentenceTransformer

# --- CEO CONFIGURATION ---
MANIFEST_PATH = r'C:\Alim\factbook.json-master\atomic_factbook_manifest.txt'
DB_PATH = r'C:\CHATILM-KB\staging_vault.db' 

# HRE Metadata
ROOT_DOMAIN = 'facts_gk' 
SUB_DOMAIN = 'geopolitical_data'
ASSET_NAME = 'CIA World Factbook'
KB_PATH_STRING = "/GK/Geopolitical/CIA_Factbook"

def execute_vector_pour():
    if not os.path.exists(MANIFEST_PATH):
        print(f"ERROR: Manifest not found at {MANIFEST_PATH}")
        return

    # Load the same model used in your successful Physics pours
    print("Loading local Embedding Model (MiniLM-L6-v2)...")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print(f"🚀 Initiating 1024-Dimension Vector Pour into {ROOT_DOMAIN}_table...")

    try:
        # Create the table using the "Proven" Physics/Sunnah schema
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {ROOT_DOMAIN}_table (
                id TEXT PRIMARY KEY, 
                source_book TEXT, 
                content TEXT, 
                path_string TEXT,
                embedding BLOB,
                timestamp TEXT
            )
        ''')

        with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        pour_count = 0
        current_ts = datetime.datetime.now().isoformat()

        for index, line in enumerate(lines):
            axiom = line.strip()
            if not axiom:
                continue
            
            # 1. Unique ID Generation (Matching your Physics fingerprint logic)
            unique_id = f"factbook_2026_{index + 1}"
            
            # 2. Vectorization (Same as Physics script)
            vector = model.encode(axiom)
            vector_blob = vector.astype('float32').tobytes()
            
            # 3. Vault Injection (Worker-only, no Audit interference)
            cursor.execute(f'''
                INSERT OR REPLACE INTO {ROOT_DOMAIN}_table 
                (id, source_book, content, path_string, embedding, timestamp) 
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (unique_id, ASSET_NAME, axiom, KB_PATH_STRING, vector_blob, current_ts))
            
            pour_count += 1

        conn.commit()
        print(f"✅ Pour Complete. {pour_count} atoms added to {ROOT_DOMAIN}_table.")

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ POUR FAILED: {str(e)}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    execute_vector_pour()