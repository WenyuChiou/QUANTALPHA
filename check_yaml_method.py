with open('src/memory/factor_registry.py', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

# 找 to_yaml 和 to_dict 方法
for i, line in enumerate(lines[90:110], 91):
    print(f"{i:3}: {line.rstrip()}")
