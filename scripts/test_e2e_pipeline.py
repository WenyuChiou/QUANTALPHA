"""End-to-end integration test for complete QuantAlpha pipeline."""

import sys
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

sys.path.append(str(Path(__file__).parent.parent))

from src.tools.fetch_data import fetch_data
from src.tools.compute_factor import compute_factor
from src.tools.run_backtest import run_backtest
from src.factors.alpha_spec_generator import dsl_to_alpha_spec


def test_full_pipeline():
    """Test complete pipeline: DSL → Signals → Backtest → Charts → alpha_spec.json"""
    
    print("\n" + "="*80)
    print(" END-TO-END INTEGRATION TEST")
    print("="*80)
    
    output_dir = Path('test_results/e2e_test')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Define Factor DSL
    print("\n[1/5] Defining Factor DSL...")
    factor_yaml = """
name: "momentum_21_63_volscaled"
universe: "sp500"
frequency: "D"
signals:
  - id: "mom_21"
    expr: "RET_21"
    standardize: "zscore_63"
  - id: "mom_63"
    expr: "RET_63"
    standardize: "zscore_63"
  - id: "rv_21"
    expr: "ROLL_STD(RET_D, 21)"
portfolio:
  scheme: "long_short_deciles"
  weight: "equal"
  rebalance: "W-FRI"
  costs:
    bps_per_trade: 5
    borrow_bps: 50
validation:
  purge_days: 5
  embargo_days: 2
  min_history_days: 252
"""
    
    print("✓ Factor DSL defined")
    print(f"  Name: momentum_21_63_volscaled")
    print(f"  Signals: 3")
    print(f"  Rebalance: W-FRI")
    
    # Step 2: Generate resolved alpha_spec.json
    print("\n[2/5] Generating resolved alpha_spec.json...")
    alpha_spec_path = output_dir / 'alpha_spec.json'
    alpha_spec = dsl_to_alpha_spec(factor_yaml, alpha_spec_path)
    print(f"✓ alpha_spec.json generated")
    print(f"  Path: {alpha_spec_path}")
    print(f"  Signal definitions: {len(alpha_spec['signal']['definitions'])}")
    
    # Step 3: Fetch data (or use synthetic)
    print("\n[3/5] Preparing market data...")
    dates = pd.date_range('2020-01-01', '2023-12-31', freq='D')
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'JPM', 'V', 'WMT']
    
    # Generate realistic synthetic data
    np.random.seed(42)
    prices_df = pd.DataFrame(
        np.random.randn(len(dates), len(tickers)).cumsum(axis=0) * 2 + 100,
        index=dates,
        columns=tickers
    )
    prices_df = prices_df.clip(lower=10)  # Prevent negative prices
    
    returns_df = prices_df.pct_change()
    
    print(f"✓ Data prepared")
    print(f"  Period: {dates[0].date()} to {dates[-1].date()}")
    print(f"  Tickers: {len(tickers)}")
    print(f"  Observations: {len(dates):,}")
    
    # Step 4: Compute factor signals
    print("\n[4/5] Computing factor signals...")
    factor_result = compute_factor(factor_yaml, prices_df, returns_df)
    
    if factor_result['signals'] is None:
        print(f"✗ Signal computation failed: {factor_result.get('error', 'Unknown error')}")
        return False
    
    signals_df = factor_result['signals']
    signals_path = output_dir / 'signals.parquet'
    signals_df.to_parquet(signals_path)
    
    print(f"✓ Signals computed")
    print(f"  Shape: {signals_df.shape}")
    print(f"  Columns: {list(signals_df.columns)}")
    print(f"  Saved to: {signals_path}")
    
    # Step 5: Run backtest with 3-panel chart generation
    print("\n[5/5] Running backtest...")
    backtest_dir = output_dir / 'backtest'
    
    backtest_result = run_backtest(
        factor_yaml=factor_yaml,
        prices_df=prices_df,
        returns_df=returns_df,
        output_dir=backtest_dir
    )
    
    if backtest_result['metrics'] is None:
        print(f"✗ Backtest failed: {backtest_result.get('error', 'Unknown error')}")
        return False
    
    metrics = backtest_result['metrics']
    
    print(f"✓ Backtest completed")
    print(f"\n  Performance Metrics:")
    print(f"    Sharpe Ratio:    {metrics.get('sharpe', 0):>8.2f}")
    print(f"    Annual Return:   {metrics.get('ann_ret', 0):>8.2%}")
    print(f"    Annual Vol:      {metrics.get('ann_vol', 0):>8.2%}")
    print(f"    Max Drawdown:    {metrics.get('maxdd', 0):>8.2%}")
    print(f"    Avg IC:          {metrics.get('avg_ic', 0):>8.4f}")
    print(f"    IR:              {metrics.get('ir', 0):>8.2f}")
    
    # Check artifacts
    print(f"\n  Artifacts Generated:")
    artifacts = backtest_result.get('artifacts', {})
    
    for name, path in artifacts.items():
        path_obj = Path(path)
        if path_obj.exists():
            size = path_obj.stat().st_size
            print(f"    ✓ {name:25} {size:>10,} bytes")
        else:
            print(f"    ✗ {name:25} NOT FOUND")
    
    # Verify 3-panel chart
    chart_path = backtest_dir / 'charts' / 'equity_curve_3panel.png'
    if chart_path.exists():
        print(f"\n  ✓ 3-Panel Chart Generated:")
        print(f"    Path: {chart_path}")
        print(f"    Size: {chart_path.stat().st_size:,} bytes")
    else:
        print(f"\n  ✗ 3-Panel chart not found")
    
    # Summary
    print("\n" + "="*80)
    print(" PIPELINE SUMMARY")
    print("="*80)
    print(f"✓ DSL → alpha_spec.json conversion: SUCCESS")
    print(f"✓ Signal computation: SUCCESS ({signals_df.shape[0]} obs, {signals_df.shape[1]} signals)")
    print(f"✓ Backtest execution: SUCCESS (Sharpe={metrics.get('sharpe', 0):.2f})")
    print(f"✓ 3-Panel chart generation: {'SUCCESS' if chart_path.exists() else 'FAILED'}")
    print(f"✓ Artifacts saved to: {output_dir}")
    
    # Generate manifest
    manifest = {
        'run_id': 'e2e_test_' + datetime.now().strftime('%Y%m%d_%H%M%S'),
        'factor_name': 'momentum_21_63_volscaled',
        'created_at': datetime.now().isoformat(),
        'artifacts': {
            'alpha_spec': str(alpha_spec_path),
            'signals': str(signals_path),
            'metrics': str(backtest_dir / 'metrics.json'),
            'equity_curve': str(backtest_dir / 'equity_curve.parquet'),
            'chart_3panel': str(chart_path) if chart_path.exists() else None
        },
        'metrics': {
            'sharpe': round(metrics.get('sharpe', 0), 2),
            'ann_ret': round(metrics.get('ann_ret', 0), 4),
            'maxdd': round(metrics.get('maxdd', 0), 4),
            'avg_ic': round(metrics.get('avg_ic', 0), 4)
        }
    }
    
    manifest_path = output_dir / 'manifest.json'
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"\n✓ Manifest saved: {manifest_path}")
    
    return True


if __name__ == '__main__':
    try:
        success = test_full_pipeline()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Pipeline failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
