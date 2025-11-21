with open('tests/conftest.py', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}\n")
for i, line in enumerate(lines, 1):
    print(f"{i:3}: {line.rstrip()}")
