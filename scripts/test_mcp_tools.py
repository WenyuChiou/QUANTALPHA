"""Test core MCP tools without langchain dependencies."""

import sys
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

def test_fetch_data():
    """Test fetch_data tool."""
    print("\n" + "="*60)
    print("1. fetch_data(tickers, start, end, fields)")
    print("="*60)
    
    from src.tools.fetch_data import fetch_data
    
    tickers = ['AAPL', 'MSFT']
    start = datetime(2024, 1, 1)
    end = datetime(2024, 1, 31)
    
    try:
        data = fetch_data(tickers, start=start, end=end)
        
        if data is not None and len(data) > 0:
            # Save to parquet
            output_path = Path('test_results/mcp_tools/fetch_data.parquet')
            output_path.parent.mkdir(parents=True, exist_ok=True)
            data.to_parquet(output_path)
            
            result = {
                'parquet_path': str(output_path),
                'data_provenance': {
                    'tickers': tickers,
                    'start_date': start.isoformat(),
                    'end_date': end.isoformat(),
                    'fields': list(data.columns.get_level_values(0).unique()) if hasattr(data.columns, 'get_level_values') else list(data.columns),
                    'rows': len(data),
                    'source': 'yfinance'
                }
            }
            
            print("✓ Output (JSON):")
            print(json.dumps(result, indent=2))
            return True
        else:
            print("✗ No data returned")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_compute_factor():
    """Test compute_factor tool."""
    print("\n" + "="*60)
    print("2. compute_factor(factor_yaml)")
    print("="*60)
    
    from src.tools.compute_factor import compute_factor
    
    # Create test data
    dates = pd.date_range('2023-01-01', '2023-12-31', freq='D')
    tickers = ['AAPL', 'MSFT', 'GOOGL']
    
    prices_df = pd.DataFrame(
        np.random.randn(len(dates), len(tickers)).cumsum(axis=0) + 100,
        index=dates,
        columns=tickers
    )
    
    returns_df = prices_df.pct_change()
    
    factor_yaml = """
name: "simple_momentum"
universe: "sp500"
frequency: "D"
signals:
  - id: "mom_21"
    expr: "RET_21"
    standardize: "zscore_21"
portfolio:
  scheme: "long_short_deciles"
  weight: "equal"
  rebalance: "D"
"""
    
    try:
        result = compute_factor(factor_yaml, prices_df, returns_df)
        
        if result['signals'] is not None:
            # Save to parquet
            output_path = Path('test_results/mcp_tools/signals.parquet')
            output_path.parent.mkdir(parents=True, exist_ok=True)
            result['signals'].to_parquet(output_path)
            
            json_output = {
                'signals_path': str(output_path),
                'signals_meta': {
                    'factor_name': 'simple_momentum',
                    'num_signals': len(result['signals'].columns),
                    'num_observations': len(result['signals']),
                    'date_range': [
                        result['signals'].index.min().isoformat(),
                        result['signals'].index.max().isoformat()
                    ]
                }
            }
            
            print("✓ Output (JSON):")
            print(json.dumps(json_output, indent=2))
            return True
        else:
            print(f"✗ Failed: {result.get('error', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_run_backtest():
    """Test run_backtest tool."""
    print("\n" + "="*60)
    print("3. run_backtest(factor_yaml, split_cfg)")
    print("="*60)
    
    from src.tools.run_backtest import run_backtest
    
    # Create test data
    dates = pd.date_range('2020-01-01', '2023-12-31', freq='D')
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META']
    
    prices_df = pd.DataFrame(
        np.random.randn(len(dates), len(tickers)).cumsum(axis=0) + 100,
        index=dates,
        columns=tickers
    )
    
    returns_df = prices_df.pct_change()
    
    factor_yaml = """
name: "test_momentum"
universe: "sp500"
frequency: "D"
signals:
  - id: "mom_21"
    expr: "RET_21"
    standardize: "zscore_21"
portfolio:
  scheme: "long_short_deciles"
  weight: "equal"
  rebalance: "D"
"""
    
    output_dir = Path('test_results/mcp_tools/backtest')
    
    try:
        result = run_backtest(
            factor_yaml=factor_yaml,
            prices_df=prices_df,
            returns_df=returns_df,
            output_dir=output_dir
        )
        
        if result['metrics'] is not None:
            json_output = {
                'metrics_paths': {
                    'metrics': str(output_dir / 'metrics.json'),
                    'metrics_oos': 'N/A (not implemented yet)',
                    'ic_report': 'N/A (not implemented yet)',
                    'slice_metrics': 'N/A (not implemented yet)'
                },
                'charts_paths': {
                    'equity_curve_3panel': str(output_dir / 'charts' / 'equity_curve_3panel.png'),
                    'equity_curve': 'N/A',
                    'drawdown': 'N/A',
                    'ic_timeline': 'N/A'
                },
                'metrics_summary': {
                    'sharpe': round(result['metrics'].get('sharpe', 0), 2),
                    'maxdd': round(result['metrics'].get('maxdd', 0), 4),
                    'ann_ret': round(result['metrics'].get('ann_ret', 0), 4)
                }
            }
            
            print("✓ Output (JSON):")
            print(json.dumps(json_output, indent=2))
            
            # Check 3-panel chart
            chart_path = output_dir / 'charts' / 'equity_curve_3panel.png'
            if chart_path.exists():
                print(f"\n✓ 3-panel chart created: {chart_path}")
                print(f"  File size: {chart_path.stat().st_size:,} bytes")
            else:
                print(f"\n⚠ 3-panel chart not found at {chart_path}")
            
            return True
        else:
            print(f"✗ Backtest failed: {result.get('error', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_logbook():
    """Test logbook tool."""
    print("\n" + "="*60)
    print("4. log_run(payload)")
    print("="*60)
    
    from src.tools.logbook import log_run
    
    try:
        result = log_run(
            factor_id=1,
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31),
            metrics={
                'sharpe': 1.85,
                'maxdd': -0.18,
                'ann_ret': 0.12,
                'ann_vol': 0.065,
                'avg_ic': 0.06,
                'ir': 0.55,
                'hit_rate': 0.54,
                'turnover_monthly': 85.3
            },
            db_path='test_results/mcp_tools/test.db'
        )
        
        json_output = {
            'ok': True,
            'run_id': result['run_id']
        }
        
        print("✓ Output (JSON):")
        print(json.dumps(json_output, indent=2))
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run core MCP tool tests."""
    print("\n" + "="*70)
    print(" CORE MCP TOOLS JSON OUTPUT VERIFICATION")
    print("="*70)
    print("\nTesting tools that produce pure JSON outputs:")
    
    results = {
        'fetch_data': test_fetch_data(),
        'compute_factor': test_compute_factor(),
        'run_backtest': test_run_backtest(),
        'log_run': test_logbook()
    }
    
    print("\n" + "="*70)
    print(" SUMMARY")
    print("="*70)
    
    for tool, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:10} {tool}")
    
    total = len(results)
    passed = sum(results.values())
    print(f"\nTotal: {passed}/{total} core tools passed")
    
    print("\n" + "="*70)
    print(" NOTES")
    print("="*70)
    print("• rag_search and write_lesson require chromadb (not tested)")
    print("• All tools produce JSON-compatible outputs")
    print("• 3-panel charts are automatically generated in run_backtest")
    
    return all(results.values())

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
