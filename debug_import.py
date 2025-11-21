import sys
import traceback

test_files = [
    'tests.agents.test_critic',
    'tests.e2e.test_pdrr_cycle',
    'tests.integration.test_agent_workflows'
]

for test_module in test_files:
    print(f"\n{'='*70}")
    print(f"Attempting to import: {test_module}")
    print(f"{'='*70}")
    try:
        __import__(test_module)
        print(f"✓ Successfully imported {test_module}")
    except Exception as e:
        print("X Error importing " + test_module + ":")
        print("  Type: " + type(e).__name__)
        print("  Message: " + str(e)[:200])
        traceback.print_exc()
