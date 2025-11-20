# Momentum Factors in Quantitative Finance

## Overview
Momentum is one of the most well-documented anomalies in financial markets. It refers to the tendency of assets that have performed well (poorly) in the recent past to continue performing well (poorly) in the near future.

## Key Findings

### Time-Series Momentum (TSMOM)
- **Definition**: A strategy that goes long assets with positive past returns and short assets with negative past returns
- **Typical Lookback**: 12 months minus 1 month (to avoid short-term reversal)
- **Volatility Scaling**: Often scaled by realized volatility to target constant risk
- **Performance**: Historically strong Sharpe ratios (1.5-2.0) in equity markets

### Cross-Sectional Momentum
- **Definition**: Ranking assets by past returns and going long top decile, short bottom decile
- **Rebalancing**: Typically monthly or quarterly
- **Turnover**: Can be high (200-300% annually)

## Best Practices

1. **Avoid Lookahead**: Always use RET_LAG with lag >= 1 day
2. **Volatility Scaling**: Scale signals by realized volatility to control risk
3. **Regime Awareness**: Momentum performs better in trending markets, worse in mean-reverting regimes
4. **Transaction Costs**: Account for high turnover in momentum strategies

## Common Pitfalls

1. **Lookahead Bias**: Using future data in signal calculation
2. **Overfitting**: Optimizing parameters on in-sample data
3. **Ignoring Costs**: High turnover can erode returns significantly
4. **Regime Blindness**: Not accounting for market regime changes

## References
- Jegadeesh & Titman (1993): "Returns to Buying Winners and Selling Losers"
- Moskowitz et al. (2012): "Time Series Momentum"

