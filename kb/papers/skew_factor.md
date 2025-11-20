# Skewness Factor in Equity Returns

## Overview

Skewness (third moment of returns) has predictive power for future returns. Assets with negative skewness (left tail risk) tend to underperform.

## Key Findings

### Negative Skewness Premium
- Stocks with negative skewness (crash risk) have lower future returns
- This is consistent with investors demanding compensation for tail risk
- Effect is stronger in high-volatility regimes

### Implementation
- **Signal**: Rolling skewness of returns (typically 252-day window)
- **Portfolio**: Long low-skew stocks, short high-skew stocks
- **Normalization**: Z-score normalization

### Performance
- Sharpe ratios typically 0.8-1.2
- Stronger in bear markets and high-volatility periods
- Complements momentum and low-volatility factors

## Best Practices
1. Use sufficient lookback window (252+ days) for stable skewness estimates
2. Combine with volatility filters to avoid noise
3. Monitor regime conditions (stronger in high-vol regimes)

## References
- Harvey, C. R., & Siddique, A. (2000). "Conditional skewness in asset pricing tests." Journal of Finance, 55(3), 1263-1295.

