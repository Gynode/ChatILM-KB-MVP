import os
import json
import sqlite3

# --- CEO STAGING CONFIG ---
REFINED_DIR = r"C:\CHATILM-KB\KB_Setup\Refinement_Lab\Gutenberg_Refined"
# REDIRECTED TO STAGING VAULT
STAGING_DB = r"C:\CHATILM-KB\Staging_Vault.db"

def universal_pour_to_staging():
    print("--- INITIATING UNIVERSAL POUR: STAGING_VAULT.DB ---")
    
    # Ensure Staging DB exists and has the schema
    conn = sqlite3.connect(STAGING_DB)
    cursor = conn.cursor()
    
    # Quick Schema Check/Creation for Staging
    for table in ["euro_gk_table", "islamic_gk_table"]:
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {table} (
                block_id TEXT PRIMARY KEY,
                content TEXT,
                path_string TEXT
            )
        ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kb_audit_table (
            asset_id TEXT PRIMARY KEY,
            block_count INTEGER,
            last_updated DATETIME
        )
    ''')

    total_injected = 0
    for root, dirs, files in os.walk(REFINED_DIR):
        for file in files:
            if not file.endswith(".json"): continue
            
            table_name = "euro_gk_table" if "euro_gk" in root.lower() else "islamic_gk_table"
            file_path = os.path.join(root, file)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                chunks = json.load(f)

            for chunk in chunks:
                cursor.execute(f'''
                    INSERT OR REPLACE INTO {table_name} (block_id, content, path_string)
                    VALUES (?, ?, ?)
                ''', (chunk['id'], chunk['text'], chunk['path']))

            # Update Audit for the specific Asset
            asset_id = file.replace(".json", "")
            cursor.execute(f'''
                INSERT OR REPLACE INTO kb_audit_table (asset_id, block_count, last_updated)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (asset_id, len(chunks)))

            total_injected += len(chunks)
            print(f"📦 STAGED: {file} -> {table_name} ({len(chunks)} blocks)")

    conn.commit()
    conn.close()
    print(f"\n--- STAGING COMPLETE: {total_injected} BLOCKS READY FOR REVIEW ---")

if __name__ == "__main__":
    universal_pour_to_staging()