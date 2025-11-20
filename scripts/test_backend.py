#!/usr/bin/env python3
"""Test backend components to ensure they work before frontend integration."""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_database():
    """Test database operations."""
    print("\n" + "="*70)
    print("Test 1: Database Operations")
    print("="*70)
    
    try:
        from src.memory.store import ExperimentStore
        
        # Create test database
        db_path = "test_backend.db"
        store = ExperimentStore(db_path)
        print("✓ Database created")
        
        # Test factor creation
        factor = store.create_factor(
            name="TestFactor_Backend",
            yaml="name: TestFactor_Backend\nuniverse: sp500",
            tags=["test", "backend"]
        )
        print(f"✓ Factor created: ID={factor.id}, Name={factor.name}")
        
        # Test run creation
        run = store.create_run(
            factor_id=factor.id,
            start_date=datetime(2020, 1, 1),
            end_date=datetime(2023, 12, 31)
        )
        print(f"✓ Run created: ID={run.id}")
        
        # Test metrics creation
        metrics = store.create_metrics(run.id, {
            'sharpe': 1.5,
            'maxdd': -0.2,
            'avg_ic': 0.08,
            'ann_ret': 0.15,
            'ann_vol': 0.12,
            'ir': 0.67,
            'turnover_monthly': 50.0,
            'hit_rate': 0.55
        })
        print(f"✓ Metrics created: Sharpe={metrics.sharpe:.2f}, IC={metrics.avg_ic:.4f}")
        
        # Test retrieval
        retrieved_factor = store.get_factor(factor.id)
        assert retrieved_factor.name == factor.name
        print("✓ Factor retrieval works")
        
        top_runs = store.get_top_runs(limit=5, order_by="sharpe")
        print(f"✓ Top runs retrieval works: {len(top_runs)} runs")
        
        # Cleanup
        Path(db_path).unlink(missing_ok=True)
        print("✓ Database test passed")
        return True
        
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_factor_dsl():
    """Test Factor DSL parsing."""
    print("\n" + "="*70)
    print("Test 2: Factor DSL Parsing")
    print("="*70)
    
    try:
        from src.factors.dsl import DSLParser
        
        parser = DSLParser()
        
        # Test YAML parsing
        test_yaml = """
name: "TestFactor_DSL"
universe: "sp500"
frequency: "D"
signals:
  - id: "momentum"
    expr: "RET_LAG(1,21)"
    normalize: "zscore_252"
portfolio:
  scheme: "long_short_deciles"
  weight: "equal"
validation:
  min_history_days: 252
targets:
  min_sharpe: 1.8  # Updated requirement: minimum Sharpe 1.8
  max_maxdd: 0.25  # Updated requirement: maximum drawdown -25%
  min_avg_ic: 0.05
"""
        
        spec = parser.parse(test_yaml)
        print(f"✓ YAML parsed: Name={spec.name}, Universe={spec.universe}")
        
        # Test validation
        is_valid, warnings = parser.validate_no_lookahead(spec)
        print(f"✓ Lookahead validation: {'Passed' if is_valid else 'Failed'}")
        if warnings:
            for w in warnings:
                print(f"  Warning: {w}")
        
        # Test parameter extraction
        params = parser.extract_parameters(spec)
        print(f"✓ Parameters extracted: {len(params)} parameters")
        
        print("✓ Factor DSL test passed")
        return True
        
    except Exception as e:
        print(f"✗ Factor DSL test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_primitives():
    """Test factor primitives."""
    print("\n" + "="*70)
    print("Test 3: Factor Primitives")
    print("="*70)
    
    try:
        from src.factors.primitives import PRIMITIVES
        
        # Generate test data
        dates = pd.date_range('2020-01-01', periods=100, freq='D')
        prices = pd.Series(100 + np.cumsum(np.random.randn(100) * 0.02), index=dates)
        returns = prices.pct_change(1).dropna()
        
        # Test RET_LAG (needs prices, not returns)
        if 'RET_LAG' in PRIMITIVES:
            ret_lag = PRIMITIVES['RET_LAG']
            result = ret_lag(lag=1, period=21, prices=prices)
            print(f"✓ RET_LAG works: {len(result.dropna())} valid values")
        
        # Test ROLL_STD
        if 'ROLL_STD' in PRIMITIVES:
            roll_std = PRIMITIVES['ROLL_STD']
            result = roll_std(returns, window=21)
            print(f"✓ ROLL_STD works: {len(result.dropna())} valid values")
        
        # Test ZSCORE
        if 'ZSCORE' in PRIMITIVES:
            zscore = PRIMITIVES['ZSCORE']
            result = zscore(returns, window=252)
            print(f"✓ ZSCORE works: {len(result.dropna())} valid values")
        
        print("✓ Primitives test passed")
        return True
        
    except Exception as e:
        print(f"✗ Primitives test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_metrics():
    """Test metrics calculation."""
    print("\n" + "="*70)
    print("Test 4: Metrics Calculation")
    print("="*70)
    
    try:
        from src.backtest.metrics import sharpe, max_drawdown, information_coefficient
        
        # Generate test returns
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0.001, 0.02, 252))
        equity = (1 + returns).cumprod()
        
        # Test Sharpe
        sharpe_ratio = sharpe(returns)
        print(f"✓ Sharpe calculation: {sharpe_ratio:.4f}")
        assert not np.isnan(sharpe_ratio)
        
        # Test MaxDD
        dd = max_drawdown(equity)
        print(f"✓ MaxDD calculation: {dd:.4f}")
        assert dd <= 0
        
        # Test IC
        signals = pd.Series(np.random.randn(252))
        ic = information_coefficient(signals, returns)
        print(f"✓ IC calculation: {ic:.4f}")
        assert not np.isnan(ic)
        
        print("✓ Metrics test passed")
        return True
        
    except Exception as e:
        print(f"✗ Metrics test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_fetching():
    """Test data fetching."""
    print("\n" + "="*70)
    print("Test 5: Data Fetching")
    print("="*70)
    
    try:
        from src.tools.fetch_data import fetch_data
        from datetime import datetime
        
        # Test with small sample
        tickers = ["AAPL", "MSFT"]
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)
        
        # Fetch prices (Close)
        prices_df = fetch_data(tickers, start=start_date, end=end_date, fields=['Close'])
        
        print(f"✓ Data fetched: {len(prices_df)} rows")
        print(f"  Data shape: {prices_df.shape}")
        
        # Calculate returns
        if len(prices_df) > 0:
            # Extract Close prices for each ticker
            if isinstance(prices_df.columns, pd.MultiIndex):
                close_prices = prices_df.xs('Close', level=1, axis=1)
            else:
                close_prices = prices_df
            
            returns = close_prices.pct_change(1).dropna()
            print(f"  Returns shape: {returns.shape}")
            
            assert len(prices_df) > 0
            assert len(returns) > 0
            
            print("✓ Data fetching test passed")
            return True
        else:
            print("⚠ No data fetched (may require internet connection)")
            return False
        
    except Exception as e:
        print(f"✗ Data fetching test failed: {e}")
        print("  Note: This requires internet connection and yfinance")
        import traceback
        traceback.print_exc()
        return False


def test_backtest_pipeline():
    """Test backtest pipeline."""
    print("\n" + "="*70)
    print("Test 6: Backtest Pipeline")
    print("="*70)
    
    try:
        from src.backtest.pipeline import WalkForwardBacktest
        from src.backtest.portfolio import long_short_deciles
        
        # Generate test data
        dates = pd.date_range('2020-01-01', periods=500, freq='D')
        tickers = ['TICKER1', 'TICKER2', 'TICKER3']
        
        np.random.seed(42)
        prices = pd.DataFrame(
            np.random.randn(len(dates), len(tickers)).cumsum(axis=0) + 100,
            index=dates,
            columns=tickers
        )
        returns = prices.pct_change(1).dropna()
        
        # Generate signals
        signals = pd.DataFrame(
            np.random.randn(len(returns), len(tickers)),
            index=returns.index,
            columns=tickers
        )
        
        # Test portfolio construction
        positions = long_short_deciles(signals.iloc[0])
        print(f"✓ Portfolio construction: {len(positions)} positions")
        assert len(positions) == len(tickers)
        
        # Test backtest initialization
        backtest = WalkForwardBacktest(n_splits=3, embargo_days=21)
        print(f"✓ Backtest initialized: {backtest.n_splits} splits")
        
        print("✓ Backtest pipeline test passed")
        return True
        
    except Exception as e:
        print(f"✗ Backtest pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rag_system():
    """Test RAG system."""
    print("\n" + "="*70)
    print("Test 7: RAG System")
    print("="*70)
    
    try:
        from src.rag.embedder import Embedder
        from src.rag.indexer import KnowledgeBaseIndexer
        
        # Test embedder
        embedder = Embedder()
        test_text = "This is a test document about momentum factors."
        embedding = embedder.embed(test_text)
        print(f"✓ Embedding created: shape={embedding.shape}")
        assert len(embedding) > 0
        
        # Test indexer (if KB exists)
        kb_dir = Path("kb")
        if kb_dir.exists():
            index_path = "./test_kb_index"
            indexer = KnowledgeBaseIndexer(kb_dir=kb_dir, index_path=index_path)
            counts = indexer.rebuild_index()
            print(f"✓ Index built: {sum(counts.values())} documents")
            
            # Cleanup
            import shutil
            shutil.rmtree(index_path, ignore_errors=True)
        else:
            print("⚠ Knowledge base not found, skipping indexer test")
        
        print("✓ RAG system test passed")
        return True
        
    except Exception as e:
        print(f"✗ RAG system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all backend tests."""
    print("="*70)
    print("Backend Component Testing")
    print("="*70)
    print("\nTesting backend components before frontend integration...")
    
    tests = [
        ("Database", test_database),
        ("Factor DSL", test_factor_dsl),
        ("Primitives", test_primitives),
        ("Metrics", test_metrics),
        ("Data Fetching", test_data_fetching),
        ("Backtest Pipeline", test_backtest_pipeline),
        ("RAG System", test_rag_system),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} test crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*70)
    print("Backend Test Summary")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status:12s}: {name}")
    
    print(f"\nTotal: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print("="*70)
    
    if passed == total:
        print("\n✅ All backend tests passed! Backend is ready for frontend integration.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} backend tests failed. Fix issues before frontend integration.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

