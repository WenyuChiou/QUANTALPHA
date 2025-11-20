# Analysis Guidelines

## Overview

This document describes the comprehensive analysis guidelines that all factor evaluations must follow. These guidelines ensure consistent, thorough, and professional analysis of all factors.

## Analysis Framework

### 1. Performance Metrics Analysis

**Required Metrics** (All must be evaluated):

| Metric | Requirement | Excellent | Good | Acceptable | Fail |
|--------|-------------|-----------|------|------------|------|
| Sharpe Ratio | >= 1.8 | >= 2.5 | 2.0-2.5 | 1.8-2.0 | < 1.8 |
| Max Drawdown | >= -25% | >= -15% | -15% to -20% | -20% to -25% | < -25% |
| IC | >= 0.05 | >= 0.08 | 0.06-0.08 | 0.05-0.06 | < 0.05 |
| IR | >= 0.5 | >= 0.8 | 0.6-0.8 | 0.5-0.6 | < 0.5 |
| Hit Rate | >= 52% | >= 56% | 54%-56% | 52%-54% | < 52% |
| Turnover | <= 250% | <= 100% | 100%-150% | 150%-250% | > 250% |

**Critical Rules**:
- Factors with Sharpe < 1.8 are **REJECTED**
- Factors with MaxDD < -25% are **REJECTED**
- Other metrics generate warnings but don't automatically reject

### 2. Stability Analysis

**Required Checks**:

1. **Rolling Sharpe Stability**
   - Calculate rolling Sharpe over multiple periods
   - Standard deviation should be < 50% of mean
   - Check for excessive volatility

2. **IC Stability**
   - Calculate rolling IC over time
   - IC should not drop below 0.03 in any period
   - Check for consistency

3. **Sharpe Drawdown**
   - Rolling Sharpe should not drop >50% from peak
   - Indicates performance degradation

**Evaluation Criteria**:
- ✅ Stable: Low volatility, consistent performance
- ⚠️ Moderate: Some volatility, acceptable
- ❌ Unstable: High volatility, inconsistent

### 3. Risk Analysis

**Required Metrics**:

1. **Value at Risk (VaR)**
   - VaR(95%) should be >= -2%
   - Measures tail risk

2. **Conditional VaR (CVaR)**
   - Expected loss given VaR breach
   - Should be reasonable

3. **Tail Ratio**
   - Ratio of 95th to 5th percentile returns
   - Should be >= 1.0
   - Measures return distribution symmetry

4. **Drawdown Analysis**
   - Maximum drawdown magnitude
   - Drawdown duration
   - Recovery time

**Evaluation Criteria**:
- ✅ Low Risk: VaR >= -2%, good tail ratio
- ⚠️ Moderate Risk: Acceptable but monitor
- ❌ High Risk: VaR < -2%, poor tail ratio

### 4. Regime Robustness Analysis

**Required Regimes** (Must test in all):

1. **Bull Market**
   - Periods with positive returns
   - Minimum Sharpe: 0.5

2. **Bear Market**
   - Periods with negative returns
   - Minimum Sharpe: 0.5

3. **High Volatility**
   - Periods with volatility > 75th percentile
   - Minimum Sharpe: 0.5

4. **Low Volatility**
   - Periods with volatility < 25th percentile
   - Minimum Sharpe: 0.5

**Evaluation Criteria**:
- ✅ Robust: Works in 4/4 regimes
- ✅ Good: Works in 3/4 regimes (minimum requirement)
- ⚠️ Moderate: Works in 2/4 regimes
- ❌ Poor: Works in < 2/4 regimes

### 5. Decay Analysis

**Required Checks**:

1. **IC Decay Rate**
   - Calculate IC over time
   - Decay rate should be < 50%
   - Indicates factor persistence

2. **Performance Persistence**
   - Check if performance degrades over time
   - Early vs. late period comparison

3. **Complexity Assessment**
   - Factor complexity score
   - Should be < 10.0
   - Simpler factors are preferred

**Evaluation Criteria**:
- ✅ Persistent: Low decay, stable performance
- ⚠️ Moderate Decay: Some degradation
- ❌ High Decay: Significant performance loss

### 6. Sample Quality Analysis

**Required Checks**:

1. **History Length**
   - Must have >= 800 days
   - Ensures statistical significance

2. **Observation Count**
   - Must have >= 800 observations
   - Sufficient for reliable estimates

3. **Data Quality**
   - Check for missing data
   - Identify outliers
   - Verify data consistency

**Evaluation Criteria**:
- ✅ Good Quality: >= 800 days, clean data
- ⚠️ Acceptable: >= 500 days, minor issues
- ❌ Poor Quality: < 500 days, data issues

## Analysis Checklist

When analyzing a factor, follow this checklist:

### Performance Metrics
- [ ] Sharpe Ratio evaluated (>= 1.8 required)
- [ ] Max Drawdown evaluated (<= -25% required)
- [ ] IC evaluated (>= 0.05 required)
- [ ] IR evaluated (>= 0.5 required)
- [ ] Hit Rate evaluated (>= 52% required)
- [ ] Turnover evaluated (<= 250% required)

### Stability Analysis
- [ ] Rolling Sharpe stability checked
- [ ] IC stability checked
- [ ] Sharpe drawdown analyzed

### Risk Analysis
- [ ] VaR(95%) calculated
- [ ] CVaR(95%) calculated
- [ ] Tail ratio calculated
- [ ] Drawdown analysis completed

### Regime Robustness
- [ ] Bull market performance evaluated
- [ ] Bear market performance evaluated
- [ ] High volatility performance evaluated
- [ ] Low volatility performance evaluated

### Decay Analysis
- [ ] IC decay rate calculated
- [ ] Performance persistence checked
- [ ] Complexity assessed

### Sample Quality
- [ ] History length verified (>= 800 days)
- [ ] Observation count verified (>= 800)
- [ ] Data quality checked

## Analysis Report Structure

All analysis reports must include:

1. **Executive Summary**
   - Overall pass/fail status
   - Key metrics summary
   - Critical issues

2. **Performance Metrics**
   - All metrics with pass/fail status
   - Comparison to requirements
   - Grade (Excellent/Good/Acceptable/Fail)

3. **Stability Analysis**
   - Rolling metrics analysis
   - Stability assessment
   - Volatility evaluation

4. **Risk Analysis**
   - Risk metrics
   - Tail risk assessment
   - Drawdown analysis

5. **Regime Analysis**
   - Performance by regime
   - Robustness assessment
   - Regime-specific insights

6. **Decay Analysis**
   - IC decay assessment
   - Performance persistence
   - Complexity evaluation

7. **Recommendations**
   - Pass/Reject decision
   - Improvement suggestions
   - Next steps

## Implementation

Analysis guidelines are implemented in:

- `src/analysis/guidelines.py` - Core guidelines class
- `src/research/backtest_analysis.py` - Uses guidelines in analysis
- `src/agents/critic.py` - Uses guidelines in evaluation

## Best Practices

1. **Be Thorough**: Check all required metrics
2. **Be Consistent**: Use same standards for all factors
3. **Be Objective**: Base decisions on data, not intuition
4. **Document Everything**: Record all findings
5. **Provide Context**: Explain why metrics pass/fail

## Summary

**All factors must pass comprehensive analysis following these guidelines:**

✅ Performance Metrics: Sharpe >= 1.8, MaxDD <= -25%
✅ Stability: Consistent performance over time
✅ Risk: Acceptable tail risk and drawdowns
✅ Regime Robustness: Works in at least 3/4 regimes
✅ Decay: Low IC decay, persistent performance
✅ Sample Quality: >= 800 days of clean data

Factors failing any critical requirement are rejected. Factors with warnings may be accepted but require monitoring.

