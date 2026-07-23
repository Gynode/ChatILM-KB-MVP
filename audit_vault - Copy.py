import sqlite3
import os

DB_PATH = r"C:\ChatILM-KB\staging_vault.db"

def run_total_knowledge_audit():
    if not os.path.exists(DB_PATH):
        print(f"❌ CRITICAL ERROR: Vault not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("\n" + "="*95)
    print("           ChatILM VAULT: DYNAMIC OMNI-AUDIT (ZERO-MAP DESIGN)")
    print("="*95)
    print(f"{'TABLE':<25} | {'CONTENTS / IDENTITIES':<45} | {'ATOMS':<10}")
    print("-" * 95)

    try:
        # 1. Discover all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [t[0] for t in cursor.fetchall()]

        total_atoms = 0
        
        for table in tables:
            # Count the atoms
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            total_atoms += count

            # 2. DYNAMIC IDENTITY DISCOVERY
            # We check if 'source_book' column exists to extract identities
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [c[1] for c in cursor.fetchall()]
            
            identities = []
            if 'source_book' in columns:
                cursor.execute(f"SELECT DISTINCT source_book FROM {table}")
                identities = [str(row[0]) for row in cursor.fetchall() if row[0]]
            
            # Formatting the identity string
            if identities:
                identity_str = ", ".join(identities)
            else:
                identity_str = "System Metadata / Other"

            # Truncate long identity strings for the display
            display_identity = (identity_str[:42] + '..') if len(identity_str) > 42 else identity_str

            print(f"{table:<25} | {display_identity:<45} | {count:<10}")

    except Exception as e:
        print(f"❌ DYNAMIC AUDIT FAILED: {str(e)}")
    
    print("-" * 95)
    print(f"SYSTEM STATUS: DYNAMIC SCAN COMPLETE | TOTAL ATOMS: {total_atoms:,}")
    print("="*95 + "\n")
    conn.close()

if __name__ == "__main__":
    run_total_knowledge_audit()