import os
import re

files_with_field_validator = []

for root, dirs, files in os.walk("src"):
    dirs[:] = [d for d in dirs if d != '__pycache__']
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                    if 'field_validator' in content:
                        lines = content.split('\n')
                        for i, line in enumerate(lines):
                            if 'field_validator' in line:
                                files_with_field_validator.append({
                                    'file': filepath,
                                    'line': i+1,
                                    'content': line.strip()
                                })
            except:
                pass

print("Files using field_validator:\n")
for item in files_with_field_validator:
    print(f"{item['file']}:{item['line']}")
    print(f"  {item['content'][:100]}")
