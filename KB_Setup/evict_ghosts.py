import sqlite3
import os

# CEO Configuration
DB_PATH = r"C:\ChatILM-KB\chatilm_data.db"

def purge_legacy_ids():
    if not os.path.exists(DB_PATH):
        print(f"❌ ERROR: Vault not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("--- INITIATING GHOST EVICTION PROTOCOL ---")
    
    # We target records that DON'T have the chapter prefix pattern (e.g., _001_)
    # Valid IDs: sahih_al_bukhari_001_1
    # Ghost IDs: sahih_al_bukhari_1
    
    query = "DELETE FROM sunnah_kb WHERE id NOT LIKE '%_0%_'"
    
    cursor.execute(query)
    evicted_count = cursor.rowcount
    
    conn.commit()
    conn.close()

    print(f"✅ Successfully evicted {evicted_count} ghost records.")
    print(f"--- VAULT PURITY RESTORED ---")

if __name__ == "__main__":
    purge_legacy_ids()