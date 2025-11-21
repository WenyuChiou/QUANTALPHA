"""Real data loader - provides OHLCV data from Yahoo Finance."""
import pandas as pd
import yfinance as yf
from datetime import datetime
import numpy as np

def load_real_data(universe="sp500", start_date="2004-01-01", end_date="2024-12-31", num_tickers=20):
    """Load real market data from Yahoo Finance with full OHLCV data.
    
    Returns:
        dict with keys:
            - prices: DataFrame with Close prices
            - returns: DataFrame with daily returns
            - ohlcv: dict with DataFrames for Open, High, Low, Close, Volume
            - source: "yfinance"
            - is_real: True
            - provenance: metadata dict
    """
    print("\n" + "="*70)
    print("  DOWNLOADING REAL MARKET DATA FROM YAHOO FINANCE")
    print("="*70)
    print(f"Period: {start_date} to {end_date}, Tickers: {num_tickers}")
    print("="*70 + "\n")
    
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'V', 'JPM', 'WMT',
               'PG', 'MA', 'HD', 'CVX', 'MRK', 'ABBV', 'KO', 'PEP', 'COST', 'AVGO'][:num_tickers]
    
    # Download data (auto_adjust=True by default in newer yfinance)
    data = yf.download(' '.join(tickers), start=start_date, end=end_date, progress=True)
    
    # Extract OHLCV data
    ohlcv = {}
    
    # Handle different yfinance output structures
    if len(tickers) == 1:
        # Single ticker - simple DataFrame
        for field in ['Open', 'High', 'Low', 'Close', 'Volume']:
            if field in data.columns:
                ohlcv[field] = data[[field]].copy()
                ohlcv[field].columns = [tickers[0]]
    else:
        # Multiple tickers - MultiIndex format
        if isinstance(data.columns, pd.MultiIndex):
            # Get available fields from level 0
            available_fields = data.columns.get_level_values(0).unique().tolist()
            
            for field in ['Open', 'High', 'Low', 'Close', 'Volume']:
                if field in available_fields:
                    ohlcv[field] = data[field].copy()
        else:
            # Flat columns (fallback)
            for field in ['Open', 'High', 'Low', 'Close', 'Volume']:
                field_cols = [c for c in data.columns if field in str(c)]
                if field_cols:
                    ohlcv[field] = data[field_cols].copy()
                    ohlcv[field].columns = [c.replace(field, '').strip() for c in ohlcv[field].columns]
    
    # Use Close for prices (yfinance auto_adjust=True means Close is already adjusted)
    if 'Close' in ohlcv:
        prices = ohlcv['Close'].copy()
    else:
        raise ValueError("No Close data available")
    
    # Data quality filtering
    print("\n📊 Data Quality Check:")
    initial_tickers = len(prices.columns)
    
    # Remove tickers with insufficient data
    coverage = prices.notna().sum() / len(prices)
    valid_tickers = coverage[coverage > 0.5].index.tolist()
    
    # Filter all OHLCV data to valid tickers
    prices = prices[valid_tickers]
    for field in list(ohlcv.keys()):
        ohlcv[field] = ohlcv[field][valid_tickers]
    
    if len(valid_tickers) < initial_tickers:
        dropped = initial_tickers - len(valid_tickers)
        print(f"   ⚠️  Dropped {dropped} tickers with <50% data coverage")
    
    # Forward fill missing values (max 5 days)
    prices = prices.ffill(limit=5)
    for field in ohlcv:
        ohlcv[field] = ohlcv[field].ffill(limit=5)
    
    # Drop any remaining rows with NaN
    initial_rows = len(prices)
    prices = prices.dropna()
    
    # Align all OHLCV data to same index
    common_index = prices.index
    for field in ohlcv:
        ohlcv[field] = ohlcv[field].loc[common_index]
    
    if len(prices) < initial_rows:
        print(f"   ⚠️  Dropped {initial_rows - len(prices)} days with missing data")
    
    # Calculate returns
    returns = prices.pct_change().iloc[1:].copy()  # Drop first row of NaN
    
    # Remove any extreme outliers (>50% daily move, likely data errors)
    extreme_moves = (returns.abs() > 0.5).any(axis=1)
    if extreme_moves.sum() > 0:
        print(f"   ⚠️  Found {extreme_moves.sum()} days with extreme moves (>50%), removing...")
        returns = returns[~extreme_moves]
        prices = prices.loc[returns.index]
        for field in ohlcv:
            ohlcv[field] = ohlcv[field].loc[returns.index]
    
    print(f"\n✅ Successfully loaded:")
    print(f"   • Tickers: {len(valid_tickers)}")
    print(f"   • Trading days: {len(prices)}")
    print(f"   • Date range: {prices.index[0].date()} to {prices.index[-1].date()}")
    print(f"   • Total return observations: {len(returns)}")
    print(f"   • Years of data: ~{len(prices) / 252:.1f} years")
    print(f"   • OHLCV fields: {', '.join(ohlcv.keys())}")
    
    # Summary statistics
    print(f"\n📈 Data Summary:")
    print(f"   • Mean daily return: {returns.mean().mean():.4%}")
    print(f"   • Mean daily volatility: {returns.std().mean():.4%}")
    print(f"   • Missing data: {returns.isna().sum().sum()} cells")
    
    # Volume statistics
    if 'Volume' in ohlcv:
        print(f"   • Mean daily volume: {ohlcv['Volume'].mean().mean():,.0f} shares")
    
    return {
        "prices": prices,
        "returns": returns,
        "ohlcv": ohlcv,  # Full OHLCV data
        "source": "yfinance",
        "is_real": True,
        "provenance": {
            "data_source": "yfinance",
            "is_real_data": True,
            "total_days": len(prices),
            "total_stocks": len(valid_tickers),
            "tickers": valid_tickers,
            "download_timestamp": datetime.now().isoformat(),
            "start_date": str(prices.index[0].date()),
            "end_date": str(prices.index[-1].date()),
            "fields_available": list(ohlcv.keys())
        }
    }

if __name__ == "__main__":
    # Test with 20 years of data (2004-2024)
    print("Testing with 5 tickers and 20 years of data (2004-2024):")
    d = load_real_data(num_tickers=5, start_date="2004-01-01", end_date="2024-12-31")
    print(f"\n✅ Test passed! Prices shape: {d['prices'].shape}, Returns shape: {d['returns'].shape}")
    print(f"   Tickers: {', '.join(d['provenance']['tickers'][:5])}")
    print(f"   Years: ~{d['provenance']['total_days'] / 252:.1f} years")
    print(f"   OHLCV fields: {', '.join(d['provenance']['fields_available'])}")
    
    # Verify OHLCV data
    print(f"\n📊 OHLCV Data Shapes:")
    for field, df in d['ohlcv'].items():
        print(f"   • {field}: {df.shape}")