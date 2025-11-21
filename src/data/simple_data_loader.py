"""
Simplified real data loader for testing.
"""

import pandas as pd
import yfinance as yf
from pathlib import Path
import json
from datetime import datetime


def load_real_data_simple(num_tickers=20):
    """
    Load real market data - simplified version for testing.
    
    Args:
        num_tickers: Number of tickers to load
        
    Returns:
        Dictionary with prices, returns, and provenance
    """
    print("\n" + "="*70)
    print("  LOADING REAL MARKET DATA (Simplified)")
    print("="*70)
    
    # Top 20 SP500 tickers (most liquid)
    tickers = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA',
        'META', 'TSLA', 'V', 'JPM', 'WMT',
        'PG', 'MA', 'HD', 'CVX', 'MRK',
        'ABBV', 'KO', 'PEP', 'COST', 'AVGO'
    ][:num_tickers]
    
    print(f"Tickers: {len(tickers)}")
    print(f"Period: 2004-01-01 to 2024-12-31")
    print("="*70 + "\n")
    
    # Download data
    data = yf.download(
        tickers,
        start="2004-01-01",
        end="2024-12-31",
        progress=True
    )
    
    # Extract Adj Close
    if len(tickers) == 1:
        prices_df = data[['Adj Close']].copy()
        prices_df.columns = [tickers[0]]
    else:
        prices_df = data['Adj Close'].copy()
    
    # Calculate returns
    returns_df = prices_df.pct_change()
    
    # Fill NaN
    prices_df = prices_df.fillna(method='ffill', limit=5)
    returns_df = returns_df.fillna(0)
    
    print(f"\n✅ Data loaded successfully:")
    print(f"   - Tickers: {len(prices_df.columns)}")
    print(f"   - Days: {len(prices_df)}")
    print(f"   - Period: {prices_df.index[0]} to {prices_df.index[-1]}")
    
    provenance = {
        "data_source": "yfinance",
        "is_real_data": True,
        "universe": "sp500_top20",
        "start_date": "2004-01-01",
        "end_date": "2024-12-31",
        "actual_start": str(prices_df.index[0].date()),
        "actual_end": str(prices_df.index[-1].date()),
        "total_days": len(prices_df),
        "total_stocks": len(prices_df.columns),
        "download_timestamp": datetime.now().isoformat()
    }
    
    return {
        "prices": prices_df,
        "returns": returns_df,
        "source": "yfinance",
        "is_real": True,
        "provenance": provenance
    }


if __name__ == "__main__":
    # Test
    data = load_real_data_simple(num_tickers=10)
    print(f"\n✅ Test successful!")
    print(f"   Prices shape: {data['prices'].shape}")
    print(f"   Returns shape: {data['returns'].shape}")
