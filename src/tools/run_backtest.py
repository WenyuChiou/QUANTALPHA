"""MCP tool: Run backtest and return metrics."""

from typing import Dict, Any, Optional
from pathlib import Path
import json
from datetime import datetime

from ..backtest.pipeline import walkforward_backtest
from ..backtest.validator import validate_run
from ..memory.factor_registry import FactorSpec
from .compute_factor import compute_factor
from ..utils.manifest_generator import create_manifest


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
        if 'equity_curve' in backtest_result:
            equity_file = output_dir / "equity_curve.parquet"
            backtest_result['equity_curve'].to_frame('equity').to_parquet(equity_file)
            artifacts['equity_curve'] = str(equity_file)
        
        # Generate 3-panel chart
        try:
            from ..viz.plots import plot_equity_curve_3panel
            
            # Prepare chart directory
            charts_dir = output_dir / "charts"
            charts_dir.mkdir(parents=True, exist_ok=True)
            
            # Get equity curve
            equity = backtest_result.get('equity_curve')
            if equity is not None:
                # Prepare metadata for info box
                meta = {
                    'strategy_name': spec.name,
                    'period': f"{equity.index[0].date()} to {equity.index[-1].date()}",
                    'total_return': f"{(equity.iloc[-1] - 1.0) * 100:.2f}%",
                    'annual_return': f"{metrics.get('ann_ret', 0) * 100:.2f}%",
                    'sharpe': f"{metrics.get('sharpe', 0):.2f}",
                    'psr': f"{metrics.get('psr', 0):.2f}" if 'psr' in metrics else 'N/A',
                    'sortino': f"{metrics.get('sortino', 0):.2f}" if 'sortino' in metrics else 'N/A',
                    'calmar': f"{metrics.get('calmar', 0):.2f}" if 'calmar' in metrics else 'N/A',
                    'linearity': f"{metrics.get('linearity', 0):.2f}" if 'linearity' in metrics else 'N/A',
                    'maxdd': f"{metrics.get('maxdd', 0) * 100:.2f}%",
                    'var95': f"{metrics.get('var_95', 0) * 100:.2f}%" if 'var_95' in metrics else 'N/A',
                    'cvar': f"{metrics.get('cvar', 0) * 100:.2f}%" if 'cvar' in metrics else 'N/A',
                    'avg_turnover': f"{metrics.get('turnover_monthly', 0):.1f}%"
                }
                
                # Get turnover if available
                turnover = backtest_result.get('turnover')
                
                # Determine OOS start if available
                oos_start = None
                if split_cfg and 'oos_start' in split_cfg:
                    oos_start = split_cfg['oos_start']
                
                # Generate 3-panel chart
                chart_path = charts_dir / "equity_curve_3panel.png"
                plot_equity_curve_3panel(
                    equity=equity,
                    benchmark=None,  # TODO: Add benchmark support
                    turnover=turnover,
                    meta=meta,
                    out_path=chart_path,
                    oos_start=oos_start
                )
                
                if chart_path.exists():
                    artifacts['equity_curve_3panel'] = str(chart_path)
                else:
                    issues.append({
                        'type': 'chart_generation_failed',
                        'detail': '3-panel chart generation failed',
                        'severity': 'warning'
                    })
        except Exception as e:
            issues.append({
                'type': 'chart_generation_error',
                'detail': f'Error generating 3-panel chart: {str(e)}',
                'severity': 'warning'
            })
        
        # Generate manifest.json with checksums
        try:
            run_id = f"{spec.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Convert artifact paths to Path objects for manifest generator
            artifact_paths = {}
            for name, path_str in artifacts.items():
                if path_str and Path(path_str).exists():
                    artifact_paths[name] = Path(path_str)
            
            manifest_path = create_manifest(
                run_id=run_id,
                factor_name=spec.name,
                output_dir=output_dir,
                artifacts=artifact_paths,
                status='completed',
                metadata={
                    'backtest_config': split_cfg or {},
                    'is_valid': is_valid,
                    'num_issues': len(issues)
                }
            )
            
            artifacts['manifest'] = str(manifest_path)
        except Exception as e:
            issues.append({
                'type': 'manifest_generation_error',
                'detail': f'Error generating manifest: {str(e)}',
                'severity': 'warning'
            })
    
    return {
        'metrics': metrics,
        'artifacts': artifacts,
        'issues': issues,
        'is_valid': is_valid,
        'backtest_result': backtest_result
    }
