"""Walk-forward backtest pipeline with purged CV splits and embargo periods."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import yaml

from .portfolio import construct_portfolio, load_costs_config
from .metrics import calculate_all_metrics
from ..memory.factor_registry import FactorSpec


def load_constraints_config(config_path: Optional[Path] = None) -> Dict:
    """Load constraints configuration."""
    if config_path is None:
        config_path = Path("configs/constraints.yml")
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def create_walk_forward_splits(
    start_date: datetime,
    end_date: datetime,
    n_splits: int = 5,
    min_train_days: int = 252,
    min_test_days: int = 63,
    purge_gap_days: int = 21
) -> List[Dict[str, datetime]]:
    """Create purged walk-forward splits.
    
    Args:
        start_date: Start of data
        end_date: End of data
        n_splits: Number of splits
        min_train_days: Minimum training period (days)
        min_test_days: Minimum test period (days)
        purge_gap_days: Embargo period between train/test (days)
    
    Returns:
        List of split dictionaries with 'train_start', 'train_end', 'test_start', 'test_end'
    """
    total_days = (end_date - start_date).days
    available_days = total_days - (min_train_days + min_test_days + purge_gap_days)
    
    if available_days < 0:
        raise ValueError("Insufficient data for walk-forward splits")
    
    # Calculate split size
    split_size = available_days // n_splits
    
    splits = []
    current_start = start_date
    
    for i in range(n_splits):
        # Expanding window: start is fixed, end moves forward
        train_start = start_date
        train_end = train_start + timedelta(days=min_train_days + i * split_size)
        
        # Purge gap (embargo) prevents leakage from training data into test data
        # especially for overlapping labels (e.g., 1-month returns)
        test_start = train_end + timedelta(days=purge_gap_days)
        test_end = test_start + timedelta(days=min_test_days)
        
        if test_end > end_date:
            break
        
        splits.append({
            'train_start': train_start,
            'train_end': train_end,
            'test_start': test_start,
            'test_end': test_end
        })
        
        # current_start not needed for expanding window
        # current_start = train_start + timedelta(days=split_size)
    
    return splits


def walkforward_backtest(
    signals_df: pd.DataFrame,
    prices_df: pd.DataFrame,
    returns_df: pd.DataFrame,
    factor_spec: FactorSpec,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Run purged walk-forward backtest.
    
    Args:
        signals_df: DataFrame of factor signals (columns = tickers, rows = dates)
        prices_df: DataFrame of prices (columns = tickers, rows = dates)
        returns_df: DataFrame of returns (columns = tickers, rows = dates)
        factor_spec: Factor specification
        config: Additional configuration (constraints, costs, etc.)
    
    Returns:
        Dictionary with:
        - splits: List of split results
        - overall_metrics: Aggregated metrics
        - equity_curves: List of equity curves per split
        - positions: Final positions DataFrame
    """
    if config is None:
        config = {}
    
    constraints = load_constraints_config()
    costs_config = load_costs_config()
    
    # Get date range
    common_dates = signals_df.index.intersection(returns_df.index)
    start_date = common_dates.min()
    end_date = common_dates.max()
    
    # Create splits
    splits_config = constraints.get('walk_forward', {})
    splits = create_walk_forward_splits(
        start_date=start_date,
        end_date=end_date,
        n_splits=splits_config.get('n_splits', 5),
        min_train_days=splits_config.get('min_train_days', 252),
        min_test_days=splits_config.get('min_test_days', 63),
        purge_gap_days=splits_config.get('purge_gap_days', 21)
    )
    
    if len(splits) == 0:
        raise ValueError("No valid splits created")
    
    # Run backtest for each split
    split_results = []
    all_equity_curves = []
    all_positions = []
    
    for split in splits:
        # Extract test period data
        test_mask = (common_dates >= split['test_start']) & (common_dates <= split['test_end'])
        test_dates = common_dates[test_mask]
        
        if len(test_dates) == 0:
            continue
        
        test_signals = signals_df.loc[test_dates]
        test_returns = returns_df.loc[test_dates]
        
        # Construct portfolio
        positions, portfolio_returns = construct_portfolio(
            scores_df=test_signals,
            returns_df=test_returns,
            scheme=factor_spec.portfolio.scheme,
            weight=factor_spec.portfolio.weight,
            notional=factor_spec.portfolio.notional,
            costs_config=costs_config,
            max_leverage=config.get('max_leverage', 2.0),
            max_single_position=config.get('max_single_position', 0.1)
        )
        
        # Calculate equity curve
        equity_curve = (1 + portfolio_returns).cumprod()
        
        # Calculate metrics
        metrics = calculate_all_metrics(
            returns=portfolio_returns,
            equity_curve=equity_curve,
            positions=positions,
            scores=test_signals.mean(axis=1),  # Average signal across tickers
            next_returns=test_returns.mean(axis=1).shift(-1)  # Next period average return
        )
        
        split_result = {
            'split': split,
            'metrics': metrics,
            'equity_curve': equity_curve,
            'positions': positions,
            'returns': portfolio_returns
        }
        
        split_results.append(split_result)
        all_equity_curves.append(equity_curve)
        all_positions.append(positions)
    
    # Aggregate metrics across splits
    all_returns = pd.concat([sr['returns'] for sr in split_results])
    overall_equity = (1 + all_returns).cumprod()
    
    # Combine positions (use last split's positions as representative)
    final_positions = all_positions[-1] if all_positions else pd.DataFrame()
    
    overall_metrics = calculate_all_metrics(
        returns=all_returns,
        equity_curve=overall_equity,
        positions=final_positions
    )
    
    # Calculate split-level statistics
    split_sharpes = [sr['metrics']['sharpe'] for sr in split_results]
    split_ics = [sr['metrics']['avg_ic'] for sr in split_results]
    
    overall_metrics['split_sharpe_mean'] = np.mean(split_sharpes)
    overall_metrics['split_sharpe_std'] = np.std(split_sharpes)
    overall_metrics['split_ic_mean'] = np.mean(split_ics)
    overall_metrics['split_ic_std'] = np.std(split_ics)
    
    return {
        'splits': split_results,
        'overall_metrics': overall_metrics,
        'equity_curves': all_equity_curves,
        'positions': final_positions,
        'returns': all_returns,
        'equity_curve': overall_equity,
        'start_date': start_date,
        'end_date': end_date
    }


def oos_evaluation(
    signals_df: pd.DataFrame,
    returns_df: pd.DataFrame,
    in_sample_start: datetime,
    in_sample_end: datetime,
    out_sample_start: datetime,
    out_sample_end: datetime,
    factor_spec: FactorSpec,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Out-of-sample evaluation with explicit train/test split.
    
    Args:
        signals_df: Factor signals DataFrame
        returns_df: Returns DataFrame
        in_sample_start: In-sample start date
        in_sample_end: In-sample end date
        out_sample_start: Out-of-sample start date
        out_sample_end: Out-of-sample end date
        factor_spec: Factor specification
        config: Additional configuration
    
    Returns:
        Dictionary with in-sample and out-of-sample metrics
    """
    if config is None:
        config = {}
    
    costs_config = load_costs_config()
    
    # In-sample period
    is_mask = (signals_df.index >= in_sample_start) & (signals_df.index <= in_sample_end)
    is_signals = signals_df[is_mask]
    is_returns = returns_df[is_mask]
    
    # Out-of-sample period
    oos_mask = (signals_df.index >= out_sample_start) & (signals_df.index <= out_sample_end)
    oos_signals = signals_df[oos_mask]
    oos_returns = returns_df[oos_mask]
    
    results = {}
    
    # In-sample backtest
    if len(is_signals) > 0:
        is_positions, is_portfolio_returns = construct_portfolio(
            scores_df=is_signals,
            returns_df=is_returns,
            scheme=factor_spec.portfolio.scheme,
            weight=factor_spec.portfolio.weight,
            notional=factor_spec.portfolio.notional,
            costs_config=costs_config
        )
        is_equity = (1 + is_portfolio_returns).cumprod()
        is_metrics = calculate_all_metrics(
            returns=is_portfolio_returns,
            equity_curve=is_equity,
            positions=is_positions
        )
        results['in_sample'] = {
            'metrics': is_metrics,
            'equity_curve': is_equity,
            'returns': is_portfolio_returns
        }
    
    # Out-of-sample backtest
    if len(oos_signals) > 0:
        oos_positions, oos_portfolio_returns = construct_portfolio(
            scores_df=oos_signals,
            returns_df=oos_returns,
            scheme=factor_spec.portfolio.scheme,
            weight=factor_spec.portfolio.weight,
            notional=factor_spec.portfolio.notional,
            costs_config=costs_config
        )
        oos_equity = (1 + oos_portfolio_returns).cumprod()
        oos_metrics = calculate_all_metrics(
            returns=oos_portfolio_returns,
            equity_curve=oos_equity,
            positions=oos_positions
        )
        results['out_sample'] = {
            'metrics': oos_metrics,
            'equity_curve': oos_equity,
            'returns': oos_portfolio_returns
        }
    
    return results

