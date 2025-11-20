# Time Series Momentum (Moskowitz et al., 2012)

## Key Findings

Time Series Momentum (TSMOM) is a robust anomaly that predicts future returns based on past returns of the same asset.

### Core Strategy
- **Signal**: Past 12-month return (excluding most recent month to avoid short-term reversal)
- **Implementation**: Long assets with positive past returns, short assets with negative past returns
- **Volatility Scaling**: Scale positions by realized volatility to target constant risk

### Performance Characteristics
- **Sharpe Ratio**: Historically 1.5-2.0 in equity markets
- **Regime Dependency**: Performs better in trending markets, worse in mean-reverting regimes
- **Persistence**: Effect persists across different asset classes and time periods

### Implementation Details
- **Lookback Period**: 252 trading days (12 months)
- **Skip Period**: 21 days (1 month) to avoid reversal
- **Volatility Window**: 21-day rolling standard deviation
- **Target Volatility**: Typically 15% annualized

### Best Practices
1. Always use RET_LAG(1, 252) - RET_LAG(1, 21) to avoid lookahead
2. Scale by realized volatility: VOL_TARGET(ann_vol=0.15)
3. Apply z-score normalization: zscore_252
4. Monitor regime conditions (momentum works better in trending markets)

### Common Pitfalls
1. **Lookahead**: Using future returns in signal calculation
2. **No Volatility Scaling**: Leads to inconsistent risk exposure
3. **Ignoring Regimes**: Performance degrades in mean-reverting markets
4. **Transaction Costs**: High turnover can erode returns significantly

## References
- Moskowitz, T. J., Ooi, Y. H., & Pedersen, L. H. (2012). "Time series momentum." Journal of Financial Economics, 104(2), 228-250.

