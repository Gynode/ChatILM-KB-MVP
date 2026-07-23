import json
import os

def convert_text_to_json():
    input_file = "pg16955.txt"
    output_file = "quran_parallel_duo.json"
    
    if not os.path.exists(input_file):
        print(f"❌ ERROR: Source file '{input_file}' not found.")
        return

    print(f"READING: {input_file}...")
    
    json_entries = []
    current_v_id = None
    y_buffer = []
    p_buffer = []
    
    # State tracking
    collecting_y = False
    collecting_p = False

    with open(input_file, 'r', encoding='utf-8-sig') as f:
        for line in f:
            clean_line = line.strip()
            
            # 1. Detect Verse ID (e.g., 001.001)
            # We look for a line that is exactly 7 chars long with a dot in the middle
            if len(clean_line) == 7 and clean_line[3] == '.':
                # Save previous verse before starting new one
                if current_v_id and (y_buffer or p_buffer):
                    add_entries(json_entries, current_v_id, y_buffer, p_buffer)
                
                current_v_id = clean_line
                y_buffer = []
                p_buffer = []
                collecting_y = False
                collecting_p = False
                continue

            # 2. Detect Start of Yusuf Ali
            if clean_line.startswith("Y:"):
                collecting_y = True
                collecting_p = False
                y_buffer.append(clean_line[2:].strip())
                continue
            
            # 3. Detect Start of Pickthall
            if clean_line.startswith("P:"):
                collecting_y = False
                collecting_p = True
                p_buffer.append(clean_line[2:].strip())
                continue
            
            # 4. Detect Start of Shakir (Stop collecting)
            if clean_line.startswith("S:"):
                collecting_y = False
                collecting_p = False
                continue

            # 5. Collect multi-line text
            if collecting_y and clean_line:
                y_buffer.append(clean_line)
            elif collecting_p and clean_line:
                p_buffer.append(clean_line)

    # Add the final verse in the file
    if current_v_id:
        add_entries(json_entries, current_v_id, y_buffer, p_buffer)

    # FINAL MASTER JSON
    master_json = {
        "metadata": {
            "domain": "Islam",
            "sub_domain": "Quran",
            "table_name": "quran"
        },
        "entries": json_entries
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(master_json, f, indent=4)

    print(f"✅ CONVERSION COMPLETE: {len(json_entries)} atoms written to {output_file}")

def add_entries(json_list, v_id, y_buf, p_buf):
    # Join multi-line text into a single string
    y_text = " ".join(y_buf).strip()
    p_text = " ".join(p_buf).strip()
    
    if y_text:
        json_list.append({
            "id": f"{v_id}_Y",
            "source_identity": "Quran (Yusuf Ali)",
            "verse": v_id,
            "text": y_text
        })
    if p_text:
        json_list.append({
            "id": f"{v_id}_P",
            "source_identity": "Quran (Pickthall)",
            "verse": v_id,
            "text": p_text
        })

if __name__ == "__main__":
    convert_text_to_json()