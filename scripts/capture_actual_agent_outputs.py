"""
Capture actual agent outputs (not just test pass/fail).
This script runs agents and saves their actual responses/outputs.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.backtester import BacktesterAgent
from src.agents.feature_agent import FeatureAgent
import pandas as pd
import numpy as np


def create_sample_data():
    """Create sample price and return data."""
    dates = pd.date_range('2020-01-01', periods=100, freq='D')
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META']
    
    # Random walk prices
    np.random.seed(42)
    prices = pd.DataFrame(
        np.cumsum(np.random.randn(100, 5) * 0.02, axis=0) + 100,
        index=dates,
        columns=tickers
    )
    
    # Calculate returns
    returns = prices.pct_change()
    
    return prices, returns


def create_sample_factor_yaml():
    """Create a sample factor YAML."""
    return """name: "TestFactor_Momentum"
universe: "sp500"
frequency: "D"
signals:
  - id: "momentum"
    expr: "RET_LAG(1,21)"
    normalize: "zscore_252"
portfolio:
  scheme: "long_short_deciles"
  weight: "equal"
  notional: 1.0
validation:
  min_history_days: 252
  purge_gap_days: 21
  max_turnover_monthly: 250.0
targets:
  min_sharpe: 1.8
  max_maxdd: 0.25
  min_avg_ic: 0.05
"""


def capture_backtester_outputs():
    """Capture BacktesterAgent actual outputs."""
    print("\n" + "="*80)
    print("CAPTURING: BacktesterAgent Outputs")
    print("="*80)
    
    agent = BacktesterAgent(output_base_dir="experiments/test_outputs")
    prices, returns = create_sample_data()
    factor_yaml = create_sample_factor_yaml()
    
    # Run backtest
    result = agent.run_backtest(
        factor_yaml=factor_yaml,
        prices_df=prices,
        returns_df=returns,
        run_id="capture_test_001"
    )
    
    output = {
        "agent": "BacktesterAgent",
        "timestamp": datetime.now().isoformat(),
        "input": {
            "factor_yaml": factor_yaml,
            "data_shape": {
                "prices": str(prices.shape),
                "returns": str(returns.shape)
            },
            "run_id": "capture_test_001"
        },
        "output": {
            "output_dir": result.get('output_dir'),
            "metrics": result.get('metrics'),
            "artifacts": result.get('artifacts'),
            "issues": result.get('issues', []),
            "is_valid": result.get('is_valid')
        }
    }
    
    print(f"\n✅ Captured BacktesterAgent output")
    print(f"   Output directory: {result.get('output_dir')}")
    print(f"   Metrics: {result.get('metrics')}")
    
    return output


def capture_feature_agent_outputs():
    """Capture FeatureAgent actual outputs."""
    print("\n" + "="*80)
    print("CAPTURING: FeatureAgent Outputs")
    print("="*80)
    
    agent = FeatureAgent()
    prices, returns = create_sample_data()
    factor_yaml = create_sample_factor_yaml()
    
    # Test 1: Valid YAML
    print("\n--- Test 1: Valid YAML ---")
    result_valid = agent.compute_features(factor_yaml, prices, returns)
    
    # Test 2: Invalid YAML
    print("\n--- Test 2: Invalid YAML ---")
    invalid_yaml = "invalid: yaml: ["
    result_invalid = agent.compute_features(invalid_yaml, prices, returns)
    
    # Test 3: Lookahead detection
    print("\n--- Test 3: Lookahead Detection ---")
    lookahead_yaml = """name: "BadFactor"
universe: "sp500"
signals:
  - id: "bad"
    expr: "RET_LAG(0,21)"
"""
    result_lookahead = agent.compute_features(lookahead_yaml, prices, returns)
    
    output = {
        "agent": "FeatureAgent",
        "timestamp": datetime.now().isoformat(),
        "tests": [
            {
                "test": "valid_yaml",
                "input": {
                    "factor_yaml": factor_yaml,
                    "data_shape": {
                        "prices": str(prices.shape),
                        "returns": str(returns.shape)
                    }
                },
                "output": {
                    "success": result_valid.get('success'),
                    "signals_shape": str(result_valid.get('signals').shape) if result_valid.get('signals') is not None else None,
                    "warnings": result_valid.get('warnings', []),
                    "error": result_valid.get('error')
                }
            },
            {
                "test": "invalid_yaml",
                "input": {
                    "factor_yaml": invalid_yaml
                },
                "output": {
                    "success": result_invalid.get('success'),
                    "error": result_invalid.get('error'),
                    "warnings": result_invalid.get('warnings', [])
                }
            },
            {
                "test": "lookahead_detection",
                "input": {
                    "factor_yaml": lookahead_yaml
                },
                "output": {
                    "success": result_lookahead.get('success'),
                    "error": result_lookahead.get('error'),
                    "warnings": result_lookahead.get('warnings', [])
                }
            }
        ]
    }
    
    print(f"\n✅ Captured FeatureAgent outputs")
    print(f"   Valid YAML: success={result_valid.get('success')}")
    print(f"   Invalid YAML: success={result_invalid.get('success')}, error={result_invalid.get('error')}")
    print(f"   Lookahead: success={result_lookahead.get('success')}, warnings={result_lookahead.get('warnings')}")
    
    return output


def main():
    """Main function to capture all agent outputs."""
    print("="*80)
    print("AGENT OUTPUT CAPTURE SCRIPT")
    print("="*80)
    
    outputs = []
    
    # Capture BacktesterAgent
    try:
        backtester_output = capture_backtester_outputs()
        outputs.append(backtester_output)
    except Exception as e:
        print(f"❌ Error capturing BacktesterAgent: {e}")
        import traceback
        traceback.print_exc()
    
    # Capture FeatureAgent
    try:
        feature_output = capture_feature_agent_outputs()
        outputs.append(feature_output)
    except Exception as e:
        print(f"❌ Error capturing FeatureAgent: {e}")
        import traceback
        traceback.print_exc()
    
    # Save outputs
    output_dir = Path("test_results/agent_outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save JSON
    json_path = output_dir / "agent_actual_outputs.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "agents": outputs
        }, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*80)
    print(f"✅ All outputs saved to: {json_path}")
    print("="*80)
    
    # Create organized output by agent
    for output in outputs:
        agent_name = output['agent']
        agent_file = output_dir / f"{agent_name}_outputs.json"
        with open(agent_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"   - {agent_file}")


if __name__ == "__main__":
    main()
