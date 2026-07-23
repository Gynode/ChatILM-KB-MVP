import sqlite3
import os

DB_PATH = r"C:\ChatILM-KB\staging_vault.db"

def run_total_knowledge_audit():
    if not os.path.exists(DB_PATH):
        print(f"❌ CRITICAL ERROR: Vault not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. Discover all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [t[0] for t in cursor.fetchall()]

        total_atoms = 0
        audit_data = [] # We collect everything here first

        for table in tables:
            # Count the atoms
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            total_atoms += count

            # 2. DYNAMIC IDENTITY DISCOVERY
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [c[1] for c in cursor.fetchall()]
            
            identities_list = []
            if 'source_book' in columns:
                cursor.execute(f"SELECT DISTINCT source_book FROM {table}")
                identities_list = [str(row[0]) for row in cursor.fetchall() if row[0]]
            
            identity_str = ", ".join(identities_list) if identities_list else "System Metadata / Other"
            
            # Save to our collection
            audit_data.append((table, identity_str, count))

        # --- PRINT SECTION (Run after collection is complete) ---
        print("\n" + "="*95)
        print("           ChatILM VAULT: DYNAMIC OMNI-AUDIT (ZERO-MAP DESIGN)")
        print("="*95)
        print(f"{'TABLE':<15} | {'CONTENTS / IDENTITIES'}")
        print("-" * 95)

        for table, identities, count in audit_data:
            print(f"{table:<15} | {identities}") # No truncation here
            print(f"{' ':<15} | -> ATOMS: {count:,}")
            print("-" * 95)

        print(f"SYSTEM STATUS: DYNAMIC SCAN COMPLETE | TOTAL ATOMS: {total_atoms:,}")
        print("="*95 + "\n")

    except Exception as e:
        print(f"❌ DYNAMIC AUDIT FAILED: {str(e)}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    run_total_knowledge_audit()