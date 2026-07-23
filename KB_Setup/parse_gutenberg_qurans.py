import re
import json
import os

# Define the local vault paths
KB_FOLDER = r"C:\ChatILM-KB"
RAW_FILE = os.path.join(KB_FOLDER, "pg16955.txt") # Ensure this is where you saved it
OUTPUT_JSON = os.path.join(KB_FOLDER, "quran_parallel_trio.json")

def parse_parallel_quran():
    if not os.path.exists(RAW_FILE):
        print(f"❌ Error: {RAW_FILE} not found. Please save the text file there first.")
        return

    print("Reading the 2.8M character Master File...")
    with open(RAW_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex to find the verse marker (e.g. 001.001) and the three lines following it
    # Pattern: Digit.Digit -> Line 1 (Yusuf Ali) -> Line 2 (Pickthall) -> Line 3 (Shakir)
    pattern = r"(\d{3})\.(\d{3})\n(.*?)\n(.*?)\n(.*?)(?=\n\d{3}\.\d{3}|\n\s*\n|$)"
    
    matches = re.findall(pattern, content, re.DOTALL)
    
    structured_kb = []
    
    print(f"Parsing verses...")
    for m in matches:
        surah, ayah, y_ali, pickthall, shakir = m
        
        # Creating the 'Pluggable' entry
        entry = {
            "id": f"quran_{int(surah)}_{int(ayah)}",
            "path_string": "/Islamic/Quran/Parallel",
            "metadata": {
                "surah": int(surah),
                "ayah": int(ayah),
                "source_id": "Gutenberg_16955"
            },
            "content": f"Yusuf Ali: {y_ali.strip()}\nPickthall: {pickthall.strip()}\nShakir: {shakir.strip()}"
        }
        structured_kb.append(entry)

    # Save the Structured JSON
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(structured_kb, f, indent=4)
    
    print(f"✅ Success! Created {OUTPUT_JSON}")
    print(f"Total Verses Structured: {len(structured_kb)}")

if __name__ == "__main__":
    parse_parallel_quran()