import json
import os
import glob

def audit_json_folder(json_source_path):
    print(f"\n--- COMPU-AID PRE-FLIGHT AUDIT: {json_source_path} ---")
    json_files = glob.glob(os.path.join(json_source_path, "*.json"))
    
    if not json_files:
        print("❌ ERROR: No JSON files found in the specified path.")
        return False

    report = {"READY": 0, "FAILED": 0, "SCHEMAS": {}}

    for file_path in json_files:
        filename = os.path.basename(file_path)
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
                
                # Proactive Schema Discovery
                if isinstance(data, list):
                    if len(data) > 0 and isinstance(data[0], str):
                        schema = "LIST_OF_STRINGS"
                    else:
                        schema = "LIST_OF_DICTS"
                elif isinstance(data, dict):
                    schema = "WRAPPED_DICT" if 'hadiths' in data else "UNKNOWN_DICT"
                else:
                    schema = "INVALID_ROOT"

                report["SCHEMAS"][schema] = report["SCHEMAS"].get(schema, 0) + 1
                
                if schema in ["LIST_OF_STRINGS", "LIST_OF_DICTS", "WRAPPED_DICT"]:
                    report["READY"] += 1
                else:
                    print(f"⚠️ WARNING: {filename} has problematic schema: {schema}")
                    report["FAILED"] += 1

        except Exception as e:
            print(f"❌ CRITICAL: {filename} is corrupted or unreadable - {e}")
            report["FAILED"] += 1

    print("\n--- AUDIT SUMMARY ---")
    print(f"Total Files Scanned: {len(json_files)}")
    print(f"Green Light (Ready): {report['READY']}")
    print(f"Red Light (Fix Required): {report['FAILED']}")
    print(f"Detected Shapes: {report['SCHEMAS']}")
    
    return report["FAILED"] == 0

if __name__ == "__main__":
    # Test the Bukhari folder
    audit_json_folder(r"C:\Alim\Al_Anwari_Physics")