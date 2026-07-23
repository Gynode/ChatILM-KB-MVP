import json

source_path = r"C:\Alim\Anglicanism\anglican_catechism_clean.json"
output_path = r"C:\Alim\Anglicanism\anglican_ready.json"

with open(source_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Combine Question and Answer into a single logical asset
formatted_data = [f"ID: {item.get('id')} | Question: {item.get('question')} | Answer: {item.get('answer')}" for item in data]

with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(formatted_data, f)

print(f"Transformation Complete: {len(formatted_data)} assets ready.")