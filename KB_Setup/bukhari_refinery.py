import json
import sqlite3
import os
import glob
from sentence_transformers import SentenceTransformer

# CEO-Grade Configuration
# We use .. to point to the root folder from the KB_Setup subfolder
DB_PATH = os.path.join("..", "chatilm_data.db")
SOURCE_DIR = r"C:\Alim\Sunnah\bukhari"

print("Loading local 'Brain' for Sunnah Embeddings...")
model = SentenceTransformer('all-MiniLM-L6-v2')

def initialize_sunnah_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Create the Sunnah Table (This is the first time it will exist)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sunnah_kb (
            id TEXT PRIMARY KEY,
            source_book TEXT,
            hadith_number TEXT,
            matn_english TEXT,
            grade TEXT,
            path_string TEXT,
            embedding BLOB
        )
    ''')
    conn.commit()
    return conn

def pour_bukhari():
    # Absolute path check for safety
    abs_db_path = os.path.abspath(DB_PATH)
    if not os.path.exists(abs_db_path):
        print(f"❌ ERROR: Database not found at {abs_db_path}")
        return

    conn = initialize_sunnah_table()
    cursor = conn.cursor()
    
    json_files = glob.glob(os.path.join(SOURCE_DIR, "*.json"))
    print(f"Found {len(json_files)} Bukhari chapters. Starting the Pour...")

    total_inserted = 0
    for file_path in json_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            hadiths = data.get('hadiths', [])
            
            for h in hadiths:
                h_num = h.get('hadithNumber')
                h_id = f"bukhari_{h_num}"
                english_text = h.get('english', {}).get('text', '').strip()
                
                if not english_text: continue

                # Generate the semantic vector
                vector = model.encode(english_text)
                vector_blob = vector.astype('float32').tobytes()

                cursor.execute('''
                    INSERT OR REPLACE INTO sunnah_kb 
                    (id, source_book, hadith_number, matn_english, grade, path_string, embedding)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (h_id, "Sahih al-Bukhari", h_num, 
                      english_text, "Sahih", "/Islamic/Sunnah/Bukhari", vector_blob))
                total_inserted += 1

        conn.commit()
        print(f"✅ Vaulted: {os.path.basename(file_path)}")

    print(f"\n--- BUKHARI POUR COMPLETE ---")
    print(f"Total Hadiths Vaulted: {total_inserted}")
    conn.close()

if __name__ == "__main__":
    pour_bukhari()