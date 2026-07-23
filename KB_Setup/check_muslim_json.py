import json
import os
import glob

def check_muslim_integrity(source_path):
    print("\n" + "="*80)
    print(f"           SAHIH MUSLIM PRE-FLIGHT INTEGRITY CHECK")
    print("="*80)
    
    json_files = glob.glob(os.path.join(source_path, "*.json"))
    
    if not json_files:
        print(f"❌ ERROR: No JSON files found in {source_path}")
        return

    total_files = len(json_files)
    passed_files = 0
    total_hadith_count = 0

    print(f"{'FILE NAME':<30} | {'COUNT':<8} | {'STRUCTURE STATUS'}")
    print("-" * 80)

    for file_path in json_files:
        filename = os.path.basename(file_path)
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
            
            # Identify the list of hadiths
            if isinstance(data, list):
                hadiths = data
            elif isinstance(data, dict):
                hadiths = data.get('hadiths', [])
            else:
                hadiths = []

            if not hadiths:
                print(f"{filename:<30} | {'0':<8} | ❌ EMPTY OR INVALID ROOT")
                continue

            # Validate the first entry as a sample
            sample = hadiths[0]
            total_hadith_count += len(hadiths)
            
            # Check for necessary keys used in Branch B
            has_english = 'english' in sample or 'text' in sample
            has_id = 'id' in sample or isinstance(sample, str)
            
            if has_english:
                print(f"{filename:<30} | {len(hadiths):<8} | ✅ READY")
                passed_files += 1
            else:
                print(f"{filename:<30} | {len(hadiths):<8} | ⚠️ MISSING CONTENT KEYS")

        except Exception as e:
            print(f"{filename:<30} | {'N/A':<8} | ❌ CORRUPT: {str(e)}")

    print("-" * 80)
    print(f"SUMMARY: {passed_files}/{total_files} Files Passed.")
    print(f"TOTAL POTENTIAL ATOMS: {total_hadith_count}")
    print("="*80 + "\n")

if __name__ == "__main__":
    # Point this to your Muslim source
    check_muslim_integrity(r"C:\Alim\Sunnah\muslim")