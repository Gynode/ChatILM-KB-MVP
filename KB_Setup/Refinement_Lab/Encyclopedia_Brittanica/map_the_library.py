import os

BRITANNICA_DIR = r"C:\Alim\Encyclopedia_Brittanica"
# Focus on the most certain historical anchors first
TARGETS = ["NEWTON", "ALGEBRA", "ARABIA", "ELECTRICITY"]

def deep_scan_foundry():
    print(f"--- INITIATING DEEP SCAN: C:\\Alim\\Encyclopedia_Brittanica ---")
    
    if not os.listdir(BRITANNICA_DIR):
        print("❌ The folder is empty. Check your extraction.")
        return

    for file_name in os.listdir(BRITANNICA_DIR):
        if not file_name.endswith(".txt"): continue
        
        file_path = os.path.join(BRITANNICA_DIR, file_name)
        
        # Try multiple encodings to bypass OCR corruption
        for enc in ['utf-8', 'latin-1', 'cp1252']:
            try:
                with open(file_path, 'r', encoding=enc, errors='ignore') as f:
                    # Read only the first 5000 chars to speed up the audit
                    chunk = f.read(5000).upper()
                    if not chunk: continue
                    
                    found = [t for t in TARGETS if t in chunk]
                    if found:
                        print(f"✅ [{file_name}] Contains: {found}")
                        break # Found it, move to next file
            except:
                continue

if __name__ == "__main__":
    deep_scan_foundry()