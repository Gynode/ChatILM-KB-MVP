import os
import requests
import time

# --- CEO REPOSITORY CONFIG ---
BASE_DIR = r"C:\Alim\Gutenberg_Raw"

# --- THE GOLD STANDARD INDEX (Synchronized) ---
# euro_physics:
#   30155: Einstein (Relativity: The Special and General Theory)
#   28233: Newton (Principia - Biographical/Analytical context)
#   14455: Faraday (Experimental Researches in Electricity)
#   42095: Lord Kelvin (Mathematical and Physical Papers)
#   30310: Galileo Galilei (Dialogues Concerning Two New Sciences)
#
# euro_math:
#   21076: Euclid (The Thirteen Books of the Elements)
#   21330: Leonhard Euler (Elements of Algebra)
#   22629: Carl Friedrich Gauss (General Investigations of Curved Surfaces)
#   32159: René Descartes (The Geometry)
#
# islamic_science:
#   16568: Al-Khwarizmi (The Algebra - Latin translation/context)
#   47842: History of Arabic Science (Medicine/Alchemy context)
#   52332: Avicenna (Canon of Medicine - Historical analysis)
#   28555: Alhazen (Optics - Historical context)
#
# islamic_logic:
#   19958: Averroes (Philosophy and Theology)
#   20455: Al-Ghazali (The Renovation of Religious Sciences)

VERIFIED_MAP = {
    "euro_gk/euro_physics": [30155, 28233, 14455, 42095, 30310],
    "euro_gk/euro_math": [21076, 21330, 22629, 32159],
    "islamic_gk/islamic_science": [16568, 47842, 52332, 28555],
    "islamic_gk/islamic_logic": [19958, 20455]
}

def fetch_verified_assets():
    print("--- INITIATING VERIFIED FETCH: THE AXIOMATIC UPGRADE ---")
    
    for folder_path, ids in VERIFIED_MAP.items():
        target_dir = os.path.join(BASE_DIR, folder_path.replace("/", "\\"))
        os.makedirs(target_dir, exist_ok=True)
        
        for asset_id in ids:
            file_path = os.path.join(target_dir, f"{asset_id}.txt")
            
            # Skip if already exists
            if os.path.exists(file_path):
                print(f"✅ Asset {asset_id} already exists in {folder_path}. Skipping.")
                continue

            # Gutenberg Mirror URL (Plain Text)
            url = f"https://www.gutenberg.org/files/{asset_id}/{asset_id}-0.txt"
            
            try:
                response = requests.get(url, timeout=10)
                if response.status_code != 200:
                    # Fallback for older naming conventions
                    url = f"https://www.gutenberg.org/cache/epub/{asset_id}/pg{asset_id}.txt"
                    response = requests.get(url, timeout=10)

                if response.status_code == 200:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(response.text)
                    print(f"💎 SUCCESSFULLY INGESTED: Asset {asset_id} -> {folder_path}")
                else:
                    print(f"❌ FAILED to retrieve Asset {asset_id}. Status: {response.status_code}")
                
                # Polite delay for Gutenberg servers
                time.sleep(1)

            except Exception as e:
                print(f"⚠️ Error fetching {asset_id}: {e}")

    print("\n--- VERIFIED INGESTION COMPLETE ---")

if __name__ == "__main__":
    fetch_verified_assets()