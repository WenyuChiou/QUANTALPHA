#!/usr/bin/env python3
"""Quick verification that all pipeline components work."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

def verify_imports():
    """Verify all critical imports work."""
    print("Verifying imports...")
    try:
        from src.factors.recipes import get_tsmom_factor
        from src.factors.dsl import DSLParser
        from src.memory.store import ExperimentStore
        from src.backtest.metrics import sharpe, max_drawdown
        from src.agents.feature_agent import FeatureAgent
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def verify_factor_generation():
    """Verify factor generation works."""
    print("\nVerifying factor generation...")
    try:
        from src.factors.recipes import get_tsmom_factor
        from src.factors.dsl import DSLParser
        
        factor = get_tsmom_factor()
        parser = DSLParser()
        
        # Validate
        is_valid, warnings = parser.validate_no_lookahead(factor)
        
        # Convert to YAML
        yaml_str = factor.to_yaml()
        
        print(f"✓ Factor generated: {factor.name}")
        print(f"  Validation: {'PASSED' if is_valid else 'FAILED'}")
        print(f"  YAML length: {len(yaml_str)} characters")
        return True
    except Exception as e:
        print(f"✗ Factor generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_database():
    """Verify database operations work."""
    print("\nVerifying database...")
    try:
        from src.memory.store import ExperimentStore
        import time
        
        db_path = f"verify_test_{int(time.time())}.db"
        store = ExperimentStore(db_path)
        
        factor = store.create_factor(
            name="VerifyTest",
            yaml="name: VerifyTest\nuniverse: sp500",
            tags=["test"]
        )
        
        # Close connection before deleting
        store.engine.dispose()
        Path(db_path).unlink(missing_ok=True)
        print(f"✓ Database operations work")
        return True
    except Exception as e:
        print(f"✗ Database failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_metrics():
    """Verify metrics calculation works."""
    print("\nVerifying metrics...")
    try:
        import pandas as pd
        import numpy as np
        from src.backtest.metrics import sharpe, max_drawdown
        
        returns = pd.Series(np.random.normal(0.001, 0.02, 252))
        equity = (1 + returns).cumprod()
        
        sharpe_val = sharpe(returns)
        dd = max_drawdown(equity)
        
        print(f"✓ Metrics calculation works")
        print(f"  Sharpe: {sharpe_val:.4f}, MaxDD: {dd:.4f}")
        return True
    except Exception as e:
        print(f"✗ Metrics failed: {e}")
        return False

def main():
    """Run all verifications."""
    print("="*70)
    print("Pipeline Verification")
    print("="*70)
    
    results = []
    results.append(("Imports", verify_imports()))
    results.append(("Factor Generation", verify_factor_generation()))
    results.append(("Database", verify_database()))
    results.append(("Metrics", verify_metrics()))
    
    print("\n" + "="*70)
    print("Verification Summary")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:12s}: {name}")
    
    print(f"\nTotal: {passed}/{total} passed")
    
    if passed == total:
        print("\n✅ All components verified! Pipeline is ready.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} components failed verification.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

