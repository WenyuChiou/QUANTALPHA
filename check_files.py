import os

files_to_check = [
    'src/memory/factor_registry.py',
    'src/memory/store.py',
    'requirements.txt',
]

for f in files_to_check:
    if os.path.exists(f):
        with open(f, 'r', encoding='utf-8', errors='replace') as file:
            lines = file.readlines()
            print(f"\n{'='*60}")
            print(f"FILE: {f}")
            print(f"{'='*60}")
            print(f"Lines: {len(lines)}")
            for i, line in enumerate(lines[:35], 1):
                print(f"{i:3}: {line.rstrip()}")
