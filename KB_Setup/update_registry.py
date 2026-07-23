import sqlite3
import datetime

# CEO Path Configuration
DB_PATH = r'C:\CHATILM-KB\staging_vault.db'

def update_kb_registry(table_name, asset_display_name, domain_id, sub_domain_id, note=""):
    """
    SOP Step 5: Final Registry Seal.
    Dynamically maps Asset 15 to the existing Audit Ledger schema.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 1. Verification: Get the count from the worker table
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        record_count = cursor.fetchone()[0]
        
        # 2. Schema Discovery: What are the ACTUAL columns in kb_audit_table?
        cursor.execute("PRAGMA table_info(kb_audit_table)")
        columns = [info[1].lower() for info in cursor.fetchall()]
        
        if not columns:
            print("❌ ERROR: kb_audit_table does not exist or is empty.")
            return

        # 3. Dynamic Mapping Logic
        # We find which column is the 'Primary' (usually first column or 'asset_name')
        primary_key_col = columns[0] 
        
        # Prepare the data mapping
        data_map = {
            'domain': domain_id,
            'sub_domain': sub_domain_id,
            'record_count': record_count,
            'status': "✅ SECURE",
            'last_updated': datetime.date.today().isoformat(),
            'ceo_note': note
        }
        
        # Filter only the columns that actually exist in your table
        insert_cols = [primary_key_col]
        insert_vals = [asset_display_name]
        
        for col in columns:
            if col in data_map:
                insert_cols.append(col)
                insert_vals.append(data_map[col])

        # 4. Final Injection
        placeholders = ", ".join(["?"] * len(insert_vals))
        col_names = ", ".join(insert_cols)
        
        sql = f"INSERT OR REPLACE INTO kb_audit_table ({col_names}) VALUES ({placeholders})"
        
        cursor.execute(sql, insert_vals)
        conn.commit()
        
        print(f"🛡️ [Registry Seal] '{asset_display_name}' officially registered.")
        print(f"📊 Verified Atoms: {record_count}")
        print(f"🔗 Mapped to columns: {insert_cols}")

    except Exception as e:
        print(f"❌ REGISTRY SYNC FAILED: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    update_kb_registry(
        table_name='facts_gk_table',
        asset_display_name='CIA World Factbook',
        domain_id='facts_gk',
        sub_domain_id='geopolitical_data',
        note='69,234 atoms vectorized via MiniLM-L6-v2.'
    )