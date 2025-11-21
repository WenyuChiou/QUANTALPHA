"""
Capture detailed agent test outputs for user review.
This script runs each agent test individually and captures their outputs.
"""

import subprocess
import json
from datetime import datetime
from pathlib import Path

def run_test_and_capture(test_path, test_name):
    """Run a single test and capture its output."""
    cmd = f"python -m pytest {test_path} -v -s --tb=short"
    
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
        cwd=r"c:\Users\wenyu\Desktop\investment\QuantAlpha"
    )
    
    return {
        "test_name": test_name,
        "test_path": test_path,
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "passed": result.returncode == 0
    }

def main():
    """Run all agent tests and capture outputs."""
    
    tests = [
        ("tests/agents/test_backtester.py::TestBacktesterAgent::test_initialization", 
         "BacktesterAgent - Initialization"),
        ("tests/agents/test_backtester.py::TestBacktesterAgent::test_output_directory_creation",
         "BacktesterAgent - Output Directory Creation"),
        ("tests/agents/test_feature_agent.py::TestFeatureAgent::test_initialization",
         "FeatureAgent - Initialization"),
        ("tests/agents/test_feature_agent.py::TestFeatureAgent::test_compute_features_valid_yaml",
         "FeatureAgent - Compute Features (Valid YAML)"),
        ("tests/agents/test_feature_agent.py::TestFeatureAgent::test_compute_features_invalid_yaml",
         "FeatureAgent - Compute Features (Invalid YAML)"),
        ("tests/agents/test_feature_agent.py::TestFeatureAgent::test_compute_features_lookahead_detection",
         "FeatureAgent - Lookahead Detection"),
    ]
    
    results = []
    
    print("Running agent tests and capturing outputs...\n")
    
    for test_path, test_name in tests:
        print(f"Running: {test_name}")
        result = run_test_and_capture(test_path, test_name)
        results.append(result)
        
        status = "✅ PASSED" if result["passed"] else "❌ FAILED"
        print(f"  {status}\n")
    
    # Save results
    output_dir = Path("test_results/agent_outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save JSON
    json_path = output_dir / "detailed_test_outputs.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "tests": results
        }, f, indent=2)
    
    # Save text report
    txt_path = output_dir / "detailed_test_outputs.txt"
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("AGENT TEST DETAILED OUTPUTS\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write("=" * 80 + "\n\n")
        
        for result in results:
            f.write(f"\n{'=' * 80}\n")
            f.write(f"TEST: {result['test_name']}\n")
            f.write(f"PATH: {result['test_path']}\n")
            f.write(f"STATUS: {'PASSED' if result['passed'] else 'FAILED'}\n")
            f.write(f"EXIT CODE: {result['exit_code']}\n")
            f.write(f"{'=' * 80}\n\n")
            
            f.write("STDOUT:\n")
            f.write("-" * 80 + "\n")
            f.write(result['stdout'])
            f.write("\n" + "-" * 80 + "\n\n")
            
            if result['stderr']:
                f.write("STDERR:\n")
                f.write("-" * 80 + "\n")
                f.write(result['stderr'])
                f.write("\n" + "-" * 80 + "\n\n")
    
    print(f"\nResults saved to:")
    print(f"  - {json_path}")
    print(f"  - {txt_path}")
    
    # Summary
    passed = sum(1 for r in results if r['passed'])
    total = len(results)
    print(f"\nSummary: {passed}/{total} tests passed")

if __name__ == "__main__":
    main()
