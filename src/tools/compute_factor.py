"""MCP tool: Compute factor signals from Factor DSL YAML."""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from pathlib import Path
import yaml

from ..factors.dsl import DSLParser
from ..factors.primitives import PRIMITIVES
from ..memory.factor_registry import FactorSpec


def compute_factor(
    factor_yaml: str,
    prices_df: pd.DataFrame,
    returns_df: Optional[pd.DataFrame] = None
) -> Dict[str, Any]:
    """Compute factor signals from Factor DSL YAML.
    
    Args:
        factor_yaml: Factor DSL YAML string
        prices_df: DataFrame of prices (columns = tickers, rows = dates)
        returns_df: Optional DataFrame of returns (if None, computed from prices)
    
    Returns:
        Dictionary with:
        - signals: DataFrame of factor signals
        - schema: Schema report
        - warnings: List of warnings
    """
    parser = DSLParser()
    
    # Parse factor spec
    try:
        spec = parser.parse(factor_yaml)
    except Exception as e:
        return {
            'signals': None,
            'schema': None,
            'warnings': [f"Parse error: {e}"],
            'error': str(e)
        }
    
    # Validate no-lookahead
    is_valid, warnings = parser.validate_no_lookahead(spec)
    
    if not is_valid:
        return {
            'signals': None,
            'schema': None,
            'warnings': warnings,
            'error': "Lookahead validation failed"
        }
    
    # Compute returns if not provided
    if returns_df is None:
        returns_df = prices_df.pct_change(1)
    
    # Compute signals for each signal definition
    signal_dfs = {}
    
    for signal_spec in spec.signals:
        try:
            # Check if this is a custom code signal or DSL expression
            if signal_spec.custom_code:
                # Execute custom code
                signal_values = _compute_custom_signal(
                    signal_spec.custom_code,
                    prices_df,
                    returns_df,
                    signal_spec.normalize
                )
            else:
                # Execute DSL expression
                signal_values = _compute_signal(
                    signal_spec.expr,
                    prices_df,
                    returns_df,
                    signal_spec.normalize
                )
            signal_dfs[signal_spec.id] = signal_values
        except Exception as e:
            warnings.append(f"Error computing signal '{signal_spec.id}': {e}")
            continue
    
    if len(signal_dfs) == 0:
        return {
            'signals': None,
            'schema': None,
            'warnings': warnings,
            'error': "No signals computed successfully"
        }
    
    # Combine signals (use first signal as primary, or combine)
    primary_signal = list(signal_dfs.values())[0]
    
    # If multiple signals, combine them (simple average for now)
    if len(signal_dfs) > 1:
        combined_signals = pd.DataFrame(signal_dfs).mean(axis=1)
        signals_df = pd.DataFrame(index=combined_signals.index, columns=prices_df.columns)
        for ticker in prices_df.columns:
            signals_df[ticker] = combined_signals
    else:
        # Broadcast to all tickers
        signals_df = pd.DataFrame(index=primary_signal.index, columns=prices_df.columns)
        for ticker in prices_df.columns:
            signals_df[ticker] = primary_signal
    
    # Align with prices
    common_dates = signals_df.index.intersection(prices_df.index)
    signals_df = signals_df.loc[common_dates]
    
    schema_report = {
        'factor_name': spec.name,
        'universe': spec.universe,
        'signals_computed': list(signal_dfs.keys()),
        'date_range': (signals_df.index.min(), signals_df.index.max()),
        'n_tickers': len(signals_df.columns),
        'n_dates': len(signals_df)
    }
    
    return {
        'signals': signals_df,
        'schema': schema_report,
        'warnings': warnings,
        'error': None
    }


def _compute_signal(
    expr: str,
    prices_df: pd.DataFrame,
    returns_df: pd.DataFrame,
    normalize: Optional[str] = None
) -> pd.Series:
    """Compute a single signal expression.
    
    Args:
        expr: Signal expression (e.g., "RET_LAG(1,252) - RET_LAG(1,21)")
        prices_df: Prices DataFrame
        returns_df: Returns DataFrame
        normalize: Normalization method (e.g., "zscore_252")
    
    Returns:
        Signal series
    """
    # Simple expression evaluation
    # In production, use a proper expression parser
    
    # For now, handle common patterns
    expr_lower = expr.lower()
    
    # RET_LAG(lag, period) pattern
    if "ret_lag" in expr_lower:
        # Extract parameters (simplified)
        import re
        matches = re.findall(r'RET_LAG\s*\(\s*(\d+)\s*,\s*(\d+)', expr_lower)
        if matches:
            lag, period = int(matches[0][0]), int(matches[0][1])
            # Compute for average ticker
            avg_returns = returns_df.mean(axis=1)
            signal = avg_returns.pct_change(period).shift(lag)
        else:
            signal = returns_df.mean(axis=1)
    else:
        # Default: use average returns
        signal = returns_df.mean(axis=1)
    
    # Apply normalization
    if normalize:
        if normalize.startswith("zscore"):
            # Extract window
            window_match = re.search(r'zscore_(\d+)', normalize)
            if window_match:
                window = int(window_match.group(1))
                signal = (signal - signal.rolling(window).mean()) / signal.rolling(window).std()
            else:
                signal = (signal - signal.mean()) / signal.std()
    
    return signal


def _compute_custom_signal(
    code: str,
    prices_df: pd.DataFrame,
    returns_df: pd.DataFrame,
    normalize: Optional[str] = None
) -> pd.Series:
    """Compute a signal using custom Python code.
    
    Args:
        code: Python code to execute
        prices_df: Prices DataFrame
        returns_df: Returns DataFrame
        normalize: Normalization method
    
    Returns:
        Signal series
    """
    from ..factors.nonlinear import execute_nonlinear_factor
    
    # Execute custom code
    result = execute_nonlinear_factor(
        code,
        prices_df,
        returns_df,
        timeout=60
    )
    
    if not result['success']:
        raise ValueError(f"Custom code execution failed: {result['error']}")
    
    # Extract signals (should be DataFrame)
    signals_df = result['signals']
    
    # Convert to Series (average across tickers for now)
    if isinstance(signals_df, pd.DataFrame):
        signal = signals_df.mean(axis=1)
    else:
        signal = signals_df
    
    # Apply normalization
    if normalize:
        if normalize.startswith("zscore"):
            # Extract window
            import re
            window_match = re.search(r'zscore_(\d+)', normalize)
            if window_match:
                window = int(window_match.group(1))
                signal = (signal - signal.rolling(window).mean()) / signal.rolling(window).std()
            else:
                signal = (signal - signal.mean()) / signal.std()
    
    return signal

