import os
import json
import re

# --- CEO PROBE CONFIG ---
SOURCE_FILE = r"C:\Alim\Gutenberg_Raw\euro_gk\euro_physics\30155.txt"
OUTPUT_DIR = r"C:\ChatILM-KB\KB_Setup\Refinement_Lab\Gutenberg_Refined\euro_gk\euro_physics"
TARGET_PATH = "/GK/Euro/Physics"

def probe_einstein():
    print(f"--- INITIATING SINGLE-ASSET PROBE: EINSTEIN (30155) ---")
    
    if not os.path.exists(SOURCE_FILE):
        print(f"❌ Error: Source file not found at {SOURCE_FILE}")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(SOURCE_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # The Surgical Strip (Gutenberg Cleaning)
    start = re.search(r"\*\*\* START OF (THE|THIS) PROJECT GUTENBERG EBOOK.*?\*\*\*", content)
    end = re.search(r"\*\*\* END OF (THE|THIS) PROJECT GUTENBERG EBOOK", content)
    
    if start and end:
        clean_text = content[start.end():end.start()].strip()
        print("✅ Gutenberg Markers Found and Stripped.")
    else:
        clean_text = content[int(len(content)*0.1):int(len(content)*0.9)].strip()
        print("⚠️ Markers not found. Using fallback trim.")

    # Semantic Chunking (1000 size, 200 overlap)
    chunks = []
    # Using 800 step for 1000 size creates the 200 overlap
    for i in range(0, len(clean_text), 800): 
        chunk_text = clean_text[i:i + 1000].strip()
        if len(chunk_text) < 100: continue
        
        chunks.append({
            "id": f"30155_{len(chunks)}",
            "text": chunk_text,
            "path": TARGET_PATH
        })

    # Generate JSON Output
    output_file = os.path.join(OUTPUT_DIR, "30155.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(chunks, f, indent=4)

    print(f"\n--- PROBE COMPLETE ---")
    print(f"Refined JSON: {output_file}")
    print(f"Total Knowledge Blocks: {len(chunks)}")

if __name__ == "__main__":
    probe_einstein()