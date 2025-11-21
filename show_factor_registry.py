import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('src/memory/factor_registry.py', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

print("LINE-BY-LINE CONTENT:")
print("=" * 80)
for i, line in enumerate(lines, 1):
    print(f"{i:3}: {line.rstrip()}")
