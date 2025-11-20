# Factor Design Guidelines

## No-Lookahead Rules

1. **Always Lag Returns**: Use RET_LAG(1, period) with lag >= 1
2. **No Future Data**: Never use data from future periods in signal calculation
3. **Calendar Alignment**: Ensure all data is aligned to trading calendar
4. **Validation**: Run lookahead checks before backtesting

## Normalization Best Practices

1. **Rolling Windows**: Use rolling windows (zscore_252, zscore_63) rather than full-sample
2. **Avoid Future Mean**: Never normalize using future mean/std
3. **Handle Missing Data**: Fill or forward-fill missing values appropriately

## Portfolio Construction

1. **Decile Construction**: Use top/bottom deciles for long/short
2. **Equal Weighting**: Start with equal weights, consider score-weighted variants
3. **Costs**: Always include transaction costs and borrow costs
4. **Turnover Limits**: Enforce maximum turnover constraints

## Validation Requirements

1. **Sample Size**: Minimum 800 days of history
2. **Walk-Forward**: Use purged walk-forward splits with embargo periods
3. **Stability**: Check rolling Sharpe/IC for stability
4. **Regime Robustness**: Test across different market regimes

## Common Mistakes to Avoid

1. **Lookahead**: Using future returns in normalization or signal calculation
2. **Overfitting**: Optimizing parameters on test data
3. **Ignoring Costs**: Not accounting for transaction and borrow costs
4. **Insufficient Validation**: Not running proper walk-forward tests
5. **Regime Blindness**: Not testing across different market conditions

