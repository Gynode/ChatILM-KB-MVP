import sqlite3
import numpy as np
import os

DB_PATH = r"C:\CHATILM-KB\staging_vault.db"

def verify_vector_alignment():
    if not os.path.exists(DB_PATH):
        print(f"❌ ERROR: Vault not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("           ChatILM VECTOR ALIGNMENT AUDIT (384 DIMENSION CHECK)")
    print("="*80)
    print(f"{'ROOM (TABLE)':<25} | {'DIMENSION':<15} | {'STATUS'}")
    print("-" * 80)

    try:
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]

        for table in tables:
            # We specifically look for tables with an 'embedding' column
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [c[1] for c in cursor.fetchall()]
            
            if 'embedding' in columns:
                # Fetch one sample vector to check dimension
                cursor.execute(f"SELECT embedding FROM {table} LIMIT 1")
                sample = cursor.fetchone()
                
                if sample and sample[0]:
                    # Convert BLOB back to numpy to check length
                    vector = np.frombuffer(sample[0], dtype='float32')
                    dim = len(vector)
                    
                    # MiniLM Standard is 384
                    status = "✅ SYNCED" if dim == 384 else "❌ MISMATCH (RE-POUR REQ)"
                    print(f"{table:<25} | {str(dim):<15} | {status}")
                else:
                    print(f"{table:<25} | {'EMPTY':<15} | ⚠️ STAGED")
            else:
                print(f"{table:<25} | {'N/A (Metadata)':<15} | ✅ SKIP")

    except Exception as e:
        print(f"❌ AUDIT FAILED: {str(e)}")
    
    print("="*80 + "\n")
    conn.close()

if __name__ == "__main__":
    verify_vector_alignment()