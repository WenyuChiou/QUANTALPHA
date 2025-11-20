"""MCP tool: Fetch data from yfinance with caching."""

import yfinance as yf
import pandas as pd
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import yaml


def load_universe_config(config_path: Optional[Path] = None) -> Dict:
    """Load universe configuration."""
    if config_path is None:
        config_path = Path("configs/universe.yml")
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def fetch_data(
    tickers: List[str],
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    fields: Optional[List[str]] = None,
    cache_dir: Optional[Path] = None
) -> pd.DataFrame:
    """Fetch data from yfinance with caching.
    
    Args:
        tickers: List of ticker symbols
        start: Start date
        end: End date
        fields: Fields to fetch (default: ['Close', 'Open', 'High', 'Low', 'Volume'])
        cache_dir: Cache directory (default: data/cache)
    
    Returns:
        DataFrame with MultiIndex (Date, Ticker) and columns as fields
    """
    if cache_dir is None:
        cache_dir = Path("data/cache")
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    if fields is None:
        fields = ['Close', 'Open', 'High', 'Low', 'Volume']
    
    if start is None:
        # Default: 10 years back
        start = datetime.now() - pd.Timedelta(days=2500)
    
    if end is None:
        end = datetime.now()
    
    # Check cache
    cache_file = cache_dir / f"{'_'.join(sorted(tickers))}_{start.date()}_{end.date()}.parquet"
    
    if cache_file.exists():
        try:
            cached_data = pd.read_parquet(cache_file)
            # Check if cached data covers the requested range
            if cached_data.index.min() <= pd.Timestamp(start) and cached_data.index.max() >= pd.Timestamp(end):
                return cached_data
        except:
            pass
    
    # Fetch from yfinance
    data_dict = {}
    
    for ticker in tickers:
        try:
            ticker_obj = yf.Ticker(ticker)
            hist = ticker_obj.history(start=start, end=end)
            
            if len(hist) == 0:
                continue
            
            # Select requested fields
            available_fields = [f for f in fields if f in hist.columns]
            ticker_data = hist[available_fields].copy()
            ticker_data['Ticker'] = ticker
            
            data_dict[ticker] = ticker_data
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            continue
    
    if len(data_dict) == 0:
        raise ValueError("No data fetched for any ticker")
    
    # Combine all tickers
    all_data = pd.concat(data_dict.values())
    all_data = all_data.reset_index().set_index(['Date', 'Ticker'])
    
    # Save to cache
    try:
        all_data.to_parquet(cache_file)
    except:
        pass
    
    return all_data


def fetch_index_data(
    index_symbol: str,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    cache_dir: Optional[Path] = None
) -> pd.Series:
    """Fetch index-level data.
    
    Args:
        index_symbol: Index symbol (e.g., "^GSPC" for S&P 500)
        start: Start date
        end: End date
        cache_dir: Cache directory
    
    Returns:
        Series of index prices
    """
    if cache_dir is None:
        cache_dir = Path("data/cache")
    
    data = fetch_data([index_symbol], start=start, end=end, fields=['Close'], cache_dir=cache_dir)
    
    # Extract Close prices
    if 'Close' in data.columns:
        return data['Close'].unstack(level='Ticker')[index_symbol]
    else:
        return data.iloc[:, 0].unstack(level='Ticker')[index_symbol]


def get_universe_tickers(universe_name: str = "sp500") -> List[str]:
    """Get ticker list for a universe.
    
    Args:
        universe_name: Universe name (sp500, nasdaq100, russell1000)
    
    Returns:
        List of ticker symbols
    """
    # For now, return a sample list
    # In production, this would fetch from a proper source
    
    if universe_name == "sp500":
        # Sample S&P 500 tickers (in production, fetch full list)
        return ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B", "V", "JNJ"]
    elif universe_name == "nasdaq100":
        return ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO", "COST", "NFLX"]
    elif universe_name == "russell1000":
        # Sample (would need full list)
        return ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]
    else:
        raise ValueError(f"Unknown universe: {universe_name}")

