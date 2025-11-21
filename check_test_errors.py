import sys
sys.path.insert(0, '.')

error_files = [
    'tests/agents/test_critic.py',
    'tests/e2e/test_pdrr_cycle.py',
    'tests/integration/test_agent_workflows.py'
]

for f in error_files:
    print(f"\n{'='*70}")
    print(f"FILE: {f}")
    print(f"{'='*70}")
    try:
        with open(f, 'r', encoding='utf-8', errors='replace') as file:
            lines = file.readlines()
            print(f"Total lines: {len(lines)}")
            print("\nFirst 40 lines:")
            for i, line in enumerate(lines[:40], 1):
                print(f"{i:3}: {line.rstrip()}")
    except Exception as e:
        print(f"Error reading file: {e}")
