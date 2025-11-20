"""MCP tool: Run backtest and return metrics."""

from typing import Dict, Any, Optional
from pathlib import Path
import json
from datetime import datetime

from ..backtest.pipeline import walkforward_backtest
from ..backtest.validator import validate_run
from ..memory.factor_registry import FactorSpec
from .compute_factor import compute_factor


def run_backtest(
    factor_yaml: str,
    prices_df,
    returns_df,
    split_cfg: Optional[Dict[str, Any]] = None,
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """Run backtest and return metrics.
    
    Args:
        factor_yaml: Factor DSL YAML string
        prices_df: Prices DataFrame
        returns_df: Returns DataFrame
        split_cfg: Walk-forward split configuration
        output_dir: Output directory for artifacts
    
    Returns:
        Dictionary with:
        - metrics: Calculated metrics
        - artifacts: Paths to saved artifacts
        - issues: Validation issues
        - is_valid: Whether run passed validation
    """
    from ..factors.dsl import DSLParser
    
    parser = DSLParser()
    spec = parser.parse(factor_yaml)
    
    # Compute factor signals
    factor_result = compute_factor(factor_yaml, prices_df, returns_df)
    
    if factor_result['signals'] is None:
        return {
            'metrics': None,
            'artifacts': {},
            'issues': factor_result.get('warnings', []),
            'is_valid': False,
            'error': factor_result.get('error', 'Unknown error')
        }
    
    signals_df = factor_result['signals']
    
    # Run walk-forward backtest
    try:
        backtest_result = walkforward_backtest(
            signals_df=signals_df,
            prices_df=prices_df,
            returns_df=returns_df,
            factor_spec=spec,
            config=split_cfg
        )
    except Exception as e:
        return {
            'metrics': None,
            'artifacts': {},
            'issues': [f"Backtest error: {e}"],
            'is_valid': False,
            'error': str(e)
        }
    
    metrics = backtest_result['overall_metrics']
    
    # Validate run
    is_valid, issues = validate_run(
        signals_df=signals_df,
        returns_df=returns_df,
        prices_df=prices_df,
        positions_df=backtest_result.get('positions', None),
        metrics=metrics
    )
    
    # Save artifacts
    artifacts = {}
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save metrics
        metrics_file = output_dir / "metrics.json"
        with open(metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2, default=str)
        artifacts['metrics'] = str(metrics_file)
        
        # Save signals
        signals_file = output_dir / "signals.parquet"
        signals_df.to_parquet(signals_file)
        artifacts['signals'] = str(signals_file)
        
        # Save equity curve
        equity_file = output_dir / "equity_curve.parquet"
        backtest_result['equity_curve'].to_frame('equity').to_parquet(equity_file)
        artifacts['equity_curve'] = str(equity_file)
    
    return {
        'metrics': metrics,
        'artifacts': artifacts,
        'issues': issues,
        'is_valid': is_valid,
        'backtest_result': backtest_result
    }

