# Low Volatility Anomaly

## Overview
The low volatility anomaly refers to the empirical finding that low-volatility stocks tend to outperform high-volatility stocks on a risk-adjusted basis, contradicting the capital asset pricing model (CAPM).

## Key Findings

### Inverse Volatility Effect
- Low-volatility stocks have higher risk-adjusted returns than high-volatility stocks
- This anomaly persists across markets and time periods
- Often attributed to leverage constraints and behavioral biases

### Implementation
- **Signal**: Inverse of realized volatility (1 / volatility)
- **Normalization**: Z-score normalization over rolling window
- **Portfolio**: Long low-vol stocks, short high-vol stocks
- **Turnover**: Typically lower than momentum strategies

## Best Practices

1. **Volatility Calculation**: Use rolling standard deviation of returns (21-day window common)
2. **Avoid Division by Zero**: Add small epsilon (0.001) when inverting volatility
3. **Regime Considerations**: Low-vol strategies may underperform in strong bull markets
4. **Sector Neutrality**: Consider sector-neutral construction to avoid sector biases

## Common Pitfalls

1. **Lookahead**: Using future volatility in signal calculation
2. **Insufficient History**: Need sufficient data for stable volatility estimates
3. **Sector Concentration**: Low-vol may concentrate in certain sectors

## References
- Ang et al. (2006): "The Cross-Section of Volatility and Expected Returns"
- Baker et al. (2011): "Benchmarks as Limits to Arbitrage"

