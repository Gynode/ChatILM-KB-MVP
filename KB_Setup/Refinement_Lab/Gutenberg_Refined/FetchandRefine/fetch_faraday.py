import requests
import os

def manual_placement_faraday():
    asset_id = "14455"
    # Project Gutenberg Plain Text Mirror
    url = f"https://www.gutenberg.org/cache/epub/{asset_id}/pg{asset_id}.txt"
    
    # YOUR SPECIFIED PATH
    target_path = r"C:\Alim\Gutenberg_Raw\euro_gk\euro_physics\14455.txt"
    
    print(f"--- ATTEMPTING FETCH: MICHAEL FARADAY (ID: {asset_id}) ---")
    
    try:
        response = requests.get(url, timeout=20)
        
        if response.status_code == 200:
            # Check if the folder actually exists before writing
            if os.path.exists(os.path.dirname(target_path)):
                with open(target_path, "w", encoding="utf-8") as f:
                    f.write(response.text)
                
                print(f"💎 SUCCESS: Asset 14455 is now in its bucket.")
                print(f"📊 Verification: {len(response.text) / 1024:.2f} KB written.")
            else:
                print(f"❌ FAILED: The folder {os.path.dirname(target_path)} does not exist.")
        else:
            print(f"❌ FAILED: HTTP Status {response.status_code}")
            
    except Exception as e:
        print(f"⚠️ SYSTEM ERROR: {e}")

if __name__ == "__main__":
    manual_placement_faraday()