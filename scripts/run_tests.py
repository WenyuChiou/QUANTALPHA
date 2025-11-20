#!/usr/bin/env python3
"""Run all tests and generate report."""

import sys
import subprocess
from pathlib import Path
from datetime import datetime

def run_command(cmd, description):
    """Run a command and return result."""
    print(f"\n{'='*70}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*70)
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        print(f"Timeout: {description}")
        return False, "", "Timeout"
    except Exception as e:
        print(f"Error: {e}")
        return False, "", str(e)


def main():
    """Run all tests."""
    print("="*70)
    print("QuantAlpha Test Suite")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    results = []
    
    # Test 1: Pipeline test
    success, stdout, stderr = run_command(
        [sys.executable, "test_pipeline.py"],
        "Pipeline Integration Test"
    )
    results.append(("Pipeline Test", success, stdout, stderr))
    
    # Test 2: Unit tests (if pytest available)
    try:
        success, stdout, stderr = run_command(
            [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
            "Unit Tests"
        )
        results.append(("Unit Tests", success, stdout, stderr))
    except Exception as e:
        print(f"Skipping pytest: {e}")
        results.append(("Unit Tests", None, "", ""))
    
    # Summary
    print("\n" + "="*70)
    print("Test Summary")
    print("="*70)
    
    passed = 0
    failed = 0
    skipped = 0
    
    for name, success, stdout, stderr in results:
        if success is None:
            status = "SKIPPED"
            skipped += 1
        elif success:
            status = "PASSED"
            passed += 1
        else:
            status = "FAILED"
            failed += 1
        
        print(f"{status:8s}: {name}")
        if not success and success is not None and stderr:
            print(f"  Error: {stderr[:200]}")
    
    print(f"\nTotal: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Skipped: {skipped}")
    print("="*70)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

