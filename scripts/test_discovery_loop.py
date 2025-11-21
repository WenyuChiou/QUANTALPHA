"""Test Phase 11: Reflection Loop and Alpha Discovery

This script tests the iterative alpha discovery loop with:
- ReflectorAgent analyzing failures
- Policy rules application
- Alpha numbering (alpha_001, alpha_002, ...)
- Iteration until target metrics are met
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.orchestrator import Orchestrator
from datetime import datetime, timedelta


def test_discovery_loop():
    """Test the full discovery loop."""
    
    print("="*70)
    print(" PHASE 11: REFLECTION LOOP TEST")
    print("="*70)
    
    # Initialize orchestrator
    orchestrator = Orchestrator(
        universe='sp500',
        db_path='test_results/phase11_test.db'
    )
    
    # Initialize data (last 3 years)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=3*365)
    
    print("\nInitializing data...")
    orchestrator.initialize_data(start_date=start_date, end_date=end_date)
    
    # Run discovery loop
    print("\nStarting discovery loop...")
    print("Target: Sharpe >= 1.0, MaxDD >= -20%")
    print("Max iterations: 3 (for testing)")
    
    result_alpha_id = orchestrator.run_discovery_loop(
        universe='sp500',
        n_candidates=1,  # 1 candidate per iteration for faster testing
        max_iterations=3,
        target_sharpe=1.0
    )
    
    # Print results
    print("\n" + "="*70)
    print(" TEST RESULTS")
    print("="*70)
    
    if result_alpha_id:
        print(f"\n✅ SUCCESS!")
        print(f"   Found successful alpha: {result_alpha_id}")
        print(f"   Check success_factors/{result_alpha_id}_*/ for artifacts")
    else:
        print(f"\n⚠️ No alpha met targets within 3 iterations")
        print(f"   This is expected for testing - real runs would use more iterations")
    
    print("\n" + "="*70)
    print(" ARTIFACTS GENERATED")
    print("="*70)
    
    # List test results
    test_results_dir = Path('test_results')
    if test_results_dir.exists():
        for item in test_results_dir.glob('alpha_*'):
            if item.is_dir():
                print(f"\n{item.name}/")
                for artifact in item.rglob('*'):
                    if artifact.is_file():
                        rel_path = artifact.relative_to(item)
                        size = artifact.stat().st_size
                        print(f"  {rel_path} ({size:,} bytes)")
    
    return result_alpha_id is not None


if __name__ == '__main__':
    try:
        success = test_discovery_loop()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
