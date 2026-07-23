import os
import json
import re

# --- CEO REFINEMENT CONFIG ---
SOURCE_DIR = r"C:\Alim\Gutenberg_Raw"
REFINED_DIR = r"C:\ChatILM-KB\KB_Setup\Refinement_Lab\Gutenberg_Refined"

def run_universal_refinement():
    print("--- INITIATING UNIVERSAL REFINEMENT: THE SCIENTIFIC GIANTS ---")
    
    refined_count = 0
    for root, dirs, files in os.walk(SOURCE_DIR):
        for file in files:
            if not file.endswith(".txt"): continue
            
            # 1. Determine the Axiomatic Path
            parts = root.split(os.sep)
            domain = "Euro" if "euro_gk" in root.lower() else "Islamic"
            sub_shelf = parts[-1].split('_')[-1].capitalize()
            path_string = f"/GK/{domain}/{sub_shelf}"

            source_path = os.path.join(root, file)
            asset_id = file.replace(".txt", "")

            with open(source_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # 2. The Surgical Strip (Gutenberg Markers)
            start = re.search(r"\*\*\* START OF (THE|THIS) PROJECT GUTENBERG EBOOK.*?\*\*\*", content)
            end = re.search(r"\*\*\* END OF (THE|THIS) PROJECT GUTENBERG EBOOK", content)
            
            if start and end:
                clean_text = content[start.end():end.start()].strip()
            else:
                # Fallback to 10% trim if markers are missing
                clean_text = content[int(len(content)*0.05):int(len(content)*0.95)].strip()

            # 3. Semantic Chunking (800 step for ~200-300 overlap)
            chunks = []
            for i in range(0, len(clean_text), 800): 
                chunk_text = clean_text[i:i + 1000].strip()
                if len(chunk_text) < 100: continue
                chunks.append({
                    "id": f"{asset_id}_{len(chunks)}",
                    "text": chunk_text,
                    "path": path_string
                })

            # 4. Mirrored Storage
            rel_path = os.path.relpath(root, SOURCE_DIR)
            target_dir = os.path.join(REFINED_DIR, rel_path)
            os.makedirs(target_dir, exist_ok=True)

            output_file = os.path.join(target_dir, f"{asset_id}.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(chunks, f, indent=4)

            print(f"💎 REFINED: {asset_id} -> {path_string} ({len(chunks)} blocks)")
            refined_count += 1

    print(f"\n--- REFINEMENT COMPLETE: {refined_count} GIANTS PROCESSED ---")

if __name__ == "__main__":
    run_universal_refinement()