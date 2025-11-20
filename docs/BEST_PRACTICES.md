# Best Practices

## Factor Design

### 1. Avoid Lookahead

**Always**:
- Use `RET_LAG(1, N)` not `RET_LAG(0, N)`
- Ensure all data used is available at signal time
- Test with purged walk-forward validation

**Never**:
- Use future returns in signal calculation
- Include data from the same day
- Assume perfect execution timing

### 2. Use Appropriate Normalization

**Common Normalizations**:
- `zscore_252`: Cross-sectional z-score (252-day window)
- `rank`: Cross-sectional rank
- `quantile`: Quantile-based normalization

**When to Use**:
- Z-score: For continuous signals
- Rank: For non-parametric signals
- Quantile: For robust signals

### 3. Volatility Scaling

**Always**:
- Scale positions by realized volatility
- Target constant risk exposure
- Use `VOL_TARGET(ann_vol=0.15)` for 15% target

### 4. Industry Neutralization

**When to Use**:
- For factors that may have industry bias
- Use `INDNEUTRALIZE(signal, industry)` to remove bias

## Backtesting

### 1. Walk-Forward Validation

**Always**:
- Use purged walk-forward splits
- Apply embargo periods (21 days)
- Test on out-of-sample data

### 2. Cost Modeling

**Include**:
- Slippage (5 bps default)
- Fees (1 bp default)
- Borrow costs (50 bps default)

### 3. Portfolio Construction

**Best Practices**:
- Use decile-based long-short portfolios
- Equal weighting within deciles
- Apply borrow limits

## Validation

### 1. Sample Size

**Requirements**:
- Minimum 800 days of history
- At least 252 days for each split
- Sufficient cross-sectional coverage

### 2. Stability Checks

**Monitor**:
- Rolling Sharpe ratio stability
- IC stability over time
- Regime-specific performance

### 3. Robustness Tests

**Test**:
- Performance across different regimes
- Outlier resistance
- Parameter sensitivity

## Knowledge Management

### 1. Document Successes

**Include**:
- Factor design rationale
- Key parameters
- Regime conditions
- Performance metrics

### 2. Document Failures

**Include**:
- Root cause analysis
- Error type and severity
- Avoidance recommendations
- Related patterns

### 3. Keep Knowledge Base Updated

**Regularly**:
- Index new papers and notes
- Update success/failure patterns
- Tag by topic and regime

## Agent Usage

### 1. Researcher Agent

**Best Practices**:
- Use RAG to seed ideation
- Query error bank before proposing
- Focus on regime-specific insights

### 2. Feature Agent

**Best Practices**:
- Validate DSL before computation
- Check for lookahead
- Handle errors gracefully

### 3. Critic Agent

**Best Practices**:
- Be thorough in validation
- Extract actionable lessons
- Classify failures accurately

## Performance Optimization

### 1. Caching

**Cache**:
- Price data (parquet format)
- Computed signals
- Backtest results

### 2. Parallelization

**Parallelize**:
- Multiple factor computations
- Independent backtests
- RAG indexing

### 3. Resource Management

**Monitor**:
- Memory usage
- Database size
- Index size

## Common Pitfalls

### 1. Overfitting

**Avoid**:
- Too many parameters
- Over-optimization
- Ignoring out-of-sample performance

### 2. Data Leakage

**Prevent**:
- Using future data
- Including same-day returns
- Ignoring embargo periods

### 3. Ignoring Costs

**Always**:
- Include realistic trading costs
- Account for borrow costs
- Model slippage

### 4. Neglecting Regimes

**Consider**:
- Regime-specific performance
- Market conditions
- Economic cycles

## Troubleshooting

### Low Success Rate

**Check**:
- Target thresholds too high
- Data quality issues
- Validation too strict

### High Failure Rate

**Review**:
- Error bank for patterns
- Common failure modes
- Validation rules

### Slow Performance

**Optimize**:
- Enable caching
- Use parallel processing
- Optimize database queries

