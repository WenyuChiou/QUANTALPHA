# Common Pitfalls in Factor Design

## Lookahead Issues

### Problem: Future Data Leakage
- Using future returns in signal calculation
- Normalizing with future mean/std
- Using data from the same day as signal

### Solution:
- Always use RET_LAG with lag >= 1
- Use rolling windows that only look backward
- Validate with lookahead detection tools

## Overfitting

### Problem: Over-optimization
- Optimizing parameters on test data
- Too many parameters relative to sample size
- Cherry-picking best results

### Solution:
- Use walk-forward validation
- Keep factor designs simple
- Test on out-of-sample data

## Cost Neglect

### Problem: Ignoring Transaction Costs
- High turnover strategies may be unprofitable after costs
- Borrow costs for short positions
- Slippage and market impact

### Solution:
- Include realistic cost assumptions (5 bps per trade)
- Monitor turnover metrics
- Test with different cost scenarios

## Regime Blindness

### Problem: Factor Only Works in Specific Regimes
- Factor fails in different volatility regimes
- Performance degrades in bear markets
- Not robust across time periods

### Solution:
- Test across different regimes (high/low vol, bull/bear)
- Use regime-aware factor design
- Monitor regime-specific performance

## Sample Size Issues

### Problem: Insufficient Data
- Not enough history for stable estimates
- Too few tickers in universe
- Unstable rolling statistics

### Solution:
- Require minimum 800 days of history
- Ensure sufficient ticker coverage
- Use appropriate rolling windows

