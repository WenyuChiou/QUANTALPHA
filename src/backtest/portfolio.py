"""Portfolio construction: long-short deciles, weighting, costs, borrow limits."""

import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple
import yaml
from pathlib import Path


def load_costs_config(config_path: Optional[Path] = None) -> Dict:
    """Load costs configuration."""
    if config_path is None:
        config_path = Path("configs/costs.yml")
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def long_short_deciles(
    scores: pd.Series,
    scheme: str = "long_short_deciles",
    weight: str = "equal",
    notional: float = 1.0,
    long_pct: float = 0.1,
    short_pct: float = 0.1
) -> pd.Series:
    """Construct long-short portfolio from factor scores.
    
    Args:
        scores: Factor scores (higher = better)
        scheme: Portfolio scheme (currently only "long_short_deciles")
        weight: Weighting scheme ("equal" or "score_weighted")
        notional: Total notional (1.0 = 100% long, 100% short)
        long_pct: Top percentile to go long (0.1 = top 10%)
        short_pct: Bottom percentile to go short (0.1 = bottom 10%)
    
    Returns:
        Position weights (positive = long, negative = short)
    """
    if scheme != "long_short_deciles":
        raise ValueError(f"Unknown scheme: {scheme}")
    
    # Calculate decile thresholds
    long_threshold = scores.quantile(1 - long_pct)
    short_threshold = scores.quantile(short_pct)
    
    # Initialize positions
    positions = pd.Series(0.0, index=scores.index)
    
    # Long positions (top decile)
    long_mask = scores >= long_threshold
    n_long = long_mask.sum()
    
    # Short positions (bottom decile)
    short_mask = scores <= short_threshold
    n_short = short_mask.sum()
    
    if n_long > 0:
        if weight == "equal":
            positions[long_mask] = (notional / 2) / n_long
        elif weight == "score_weighted":
            # Weight by normalized scores
            long_scores = scores[long_mask]
            long_scores_norm = (long_scores - long_scores.min()) / (long_scores.max() - long_scores.min() + 1e-10)
            positions[long_mask] = (notional / 2) * long_scores_norm / long_scores_norm.sum()
        else:
            raise ValueError(f"Unknown weight scheme: {weight}")
    
    if n_short > 0:
        if weight == "equal":
            positions[short_mask] = -(notional / 2) / n_short
        elif weight == "score_weighted":
            # Weight by normalized scores (inverted for shorts)
            short_scores = scores[short_mask]
            short_scores_norm = (short_scores - short_scores.min()) / (short_scores.max() - short_scores.min() + 1e-10)
            positions[short_mask] = -(notional / 2) * short_scores_norm / short_scores_norm.sum()
        else:
            raise ValueError(f"Unknown weight scheme: {weight}")
    
    return positions


def apply_costs(
    positions: pd.DataFrame,
    returns: pd.DataFrame,
    costs_config: Optional[Dict] = None
) -> pd.Series:
    """Apply trading costs to returns.
    
    Args:
        positions: DataFrame of positions (columns = tickers, rows = dates)
        returns: DataFrame of returns (columns = tickers, rows = dates)
        costs_config: Costs configuration dict
    
    Returns:
        Portfolio returns after costs
    """
    if costs_config is None:
        costs_config = load_costs_config()
    
    # Calculate position changes (turnover)
    position_changes = positions.diff().abs()
    
    # Calculate costs
    slippage_bps = costs_config['slippage']['bps_per_trade']
    commission_per_trade = costs_config['fees']['commission_per_trade']
    
    # Cost per dollar traded
    cost_per_dollar = (slippage_bps / 10000) + (commission_per_trade / 10000)  # Simplified
    
    # Daily costs
    daily_costs = position_changes.sum(axis=1) * cost_per_dollar
    
    # Portfolio returns
    portfolio_returns = (positions.shift(1) * returns).sum(axis=1)
    
    # Apply costs
    net_returns = portfolio_returns - daily_costs
    
    return net_returns


def apply_borrow_costs(
    positions: pd.DataFrame,
    borrow_config: Optional[Dict] = None
) -> pd.Series:
    """Apply short borrowing costs.
    
    Args:
        positions: DataFrame of positions (negative = short)
        borrow_config: Borrow configuration dict
    
    Returns:
        Daily borrow costs
    """
    if borrow_config is None:
        costs_config = load_costs_config()
        borrow_config = costs_config['borrow']
    
    borrow_bps_annual = borrow_config['bps_annual']
    borrow_bps_daily = borrow_bps_annual / 252 / 10000
    
    # Short positions (negative)
    short_positions = positions[positions < 0].abs()
    
    # Daily borrow cost
    daily_borrow_cost = short_positions.sum(axis=1) * borrow_bps_daily
    
    return daily_borrow_cost


def enforce_borrow_limits(
    positions: pd.DataFrame,
    max_leverage: float = 2.0,
    max_single_position: float = 0.1
) -> pd.DataFrame:
    """Enforce borrowing and position limits.
    
    Args:
        positions: Position weights DataFrame
        max_leverage: Maximum leverage (e.g., 2.0 = 200% long, 200% short)
        max_single_position: Maximum single position size (e.g., 0.1 = 10%)
    
    Returns:
        Adjusted positions
    """
    positions = positions.copy()
    
    # Enforce single position limit
    positions = positions.clip(-max_single_position, max_single_position)
    
    # Enforce leverage limit
    long_exposure = positions[positions > 0].sum(axis=1)
    short_exposure = positions[positions < 0].abs().sum(axis=1)
    total_exposure = long_exposure + short_exposure
    
    # Scale down if exceeds leverage
    scale_factor = (max_leverage / total_exposure).clip(0, 1)
    positions = positions.multiply(scale_factor, axis=0)
    
    return positions


def construct_portfolio(
    scores_df: pd.DataFrame,
    returns_df: pd.DataFrame,
    scheme: str = "long_short_deciles",
    weight: str = "equal",
    notional: float = 1.0,
    costs_config: Optional[Dict] = None,
    max_leverage: float = 2.0,
    max_single_position: float = 0.1
) -> Tuple[pd.DataFrame, pd.Series]:
    """Construct portfolio from factor scores.
    
    Args:
        scores_df: DataFrame of factor scores (columns = tickers, rows = dates)
        returns_df: DataFrame of returns (columns = tickers, rows = dates)
        scheme: Portfolio scheme
        weight: Weighting scheme
        notional: Total notional
        costs_config: Costs configuration
        max_leverage: Maximum leverage
        max_single_position: Maximum single position size
    
    Returns:
        (positions DataFrame, portfolio returns Series)
    """
    # Align dates
    common_dates = scores_df.index.intersection(returns_df.index)
    scores_df = scores_df.loc[common_dates]
    returns_df = returns_df.loc[common_dates]
    
    # Construct positions for each date
    positions_list = []
    
    for date in scores_df.index:
        scores = scores_df.loc[date]
        positions = long_short_deciles(
            scores,
            scheme=scheme,
            weight=weight,
            notional=notional
        )
        positions_list.append(positions)
    
    positions_df = pd.DataFrame(positions_list, index=scores_df.index)
    
    # Enforce limits
    positions_df = enforce_borrow_limits(
        positions_df,
        max_leverage=max_leverage,
        max_single_position=max_single_position
    )
    
    # Calculate returns
    portfolio_returns = (positions_df.shift(1) * returns_df).sum(axis=1)
    
    # Apply costs
    net_returns = apply_costs(positions_df, returns_df, costs_config)
    
    # Apply borrow costs
    borrow_costs = apply_borrow_costs(positions_df, costs_config.get('borrow') if costs_config else None)
    net_returns = net_returns - borrow_costs
    
    return positions_df, net_returns

