"""Test script for 3-panel equity curve visualization."""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.viz.plots import plot_equity_curve_3panel

def test_3panel_chart():
    """Test 3-panel chart generation."""
    print("Testing 3-panel equity curve chart...")
    
    # Generate synthetic data
    np.random.seed(42)
    dates = pd.date_range('2020-01-01', '2023-12-31', freq='D')
    
    # Create equity curve with some realistic behavior
    returns = np.random.normal(0.0005, 0.01, len(dates))
    equity = pd.Series((1 + returns).cumprod(), index=dates)
    
    # Create benchmark
    benchmark_returns = np.random.normal(0.0003, 0.008, len(dates))
    benchmark = pd.Series((1 + benchmark_returns).cumprod(), index=dates)
    
    # Create turnover
    turnover = pd.Series(np.random.uniform(0.05, 0.15, len(dates)), index=dates)
    
    # Create metadata
    meta = {
        'strategy_name': 'Test Momentum Strategy',
        'period': '2020-01-01 to 2023-12-31',
        'total_return': '+45.2%',
        'annual_return': '+12.3%',
        'sharpe': '1.85',
        'psr': '0.92',
        'sortino': '2.15',
        'calmar': '1.42',
        'linearity': '0.88',
        'maxdd': '-18.5%',
        'var95': '-2.1%',
        'cvar': '-3.2%',
        'avg_turnover': '85.3%'
    }
    
    # Set OOS start date
    oos_start = pd.Timestamp('2022-01-01')
    
    # Create output directory
    output_dir = Path('test_results/charts')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate chart
    out_path = output_dir / 'test_equity_curve_3panel.png'
    result_path = plot_equity_curve_3panel(
        equity=equity,
        benchmark=benchmark,
        turnover=turnover,
        meta=meta,
        out_path=out_path,
        oos_start=oos_start
    )
    
    # Verify
    if result_path and result_path.exists():
        file_size = result_path.stat().st_size
        print(f"✓ Chart created successfully: {result_path}")
        print(f"  File size: {file_size:,} bytes")
        
        # Check file size is reasonable (should be > 50KB for a good quality chart)
        if file_size > 50000:
            print("✓ File size looks good (> 50KB)")
        else:
            print("⚠ Warning: File size seems small, chart quality may be low")
        
        return True
    else:
        print("✗ Failed to create chart")
        return False

if __name__ == '__main__':
    success = test_3panel_chart()
    sys.exit(0 if success else 1)
