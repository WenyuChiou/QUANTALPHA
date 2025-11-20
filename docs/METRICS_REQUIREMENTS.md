# Metrics Requirements

## Overview

All factors must meet specific performance metrics requirements. These requirements are enforced throughout the factor research, design, and evaluation process.

## Required Performance Metrics

### 1. Sharpe Ratio

**Requirement**: >= 1.8

**Targets**:
- Excellent: >= 2.5
- Good: 2.0 - 2.5
- Acceptable: 1.8 - 2.0
- **FAIL**: < 1.8

**For Momentum Factors**:
- Target: >= 2.0
- Typical range: 1.0 - 2.0
- **CRITICAL**: Below 1.8 is considered insufficient

### 2. Maximum Drawdown

**Requirement**: >= -25% (less negative is better)

**Targets**:
- Excellent: >= -15%
- Good: -15% to -20%
- Acceptable: -20% to -25%
- **FAIL**: < -25%

**For Momentum Factors**:
- Target: >= -20%
- **CRITICAL**: Drawdowns above -25% are unacceptable

### 3. Information Coefficient (IC)

**Requirement**: >= 0.05

**Targets**:
- Excellent: >= 0.08
- Good: 0.06 - 0.08
- Acceptable: 0.05 - 0.06
- **FAIL**: < 0.05

**For Momentum Factors**:
- Target: >= 0.06
- Typical range: 0.05 - 0.10
- Below 0.05 indicates weak predictive power

### 4. Information Ratio (IR)

**Requirement**: >= 0.5

**Targets**:
- Excellent: >= 0.8
- Good: 0.6 - 0.8
- Acceptable: 0.5 - 0.6
- **FAIL**: < 0.5

**Description**:
- IR measures risk-adjusted IC
- Below 0.5 indicates poor risk-adjusted performance

### 5. Hit Rate

**Requirement**: >= 52%

**Targets**:
- Excellent: >= 56%
- Good: 54% - 56%
- Acceptable: 52% - 54%
- **FAIL**: < 52%

**Description**:
- Percentage of periods with positive IC
- Below 52% indicates inconsistent performance

### 6. Monthly Turnover

**Requirement**: <= 250%

**Targets**:
- Excellent: <= 100%
- Good: 100% - 150%
- Acceptable: 150% - 250%
- **FAIL**: > 250%

**For Momentum Factors**:
- Target: < 200%
- Typical range: 30% - 60% monthly turnover
- High turnover increases transaction costs

## Additional Quality Metrics

### Stability Requirements

- **Rolling Sharpe Stability**: Rolling Sharpe should not drop more than 50% from peak
- **IC Stability**: IC should not drop below 0.03 in any rolling period
- **Sample Size**: Must have >= 800 days of history

### Regime Robustness

- Must perform in at least 3 out of 4 regimes:
  - High volatility
  - Low volatility
  - Bull market
  - Bear market
- Minimum Sharpe of 0.5 in each regime

## Evaluation Process

### Factor Generation (Researcher Agent)

When generating factors, the Researcher Agent:
1. Ensures all factors specify metrics targets in YAML
2. Designs factors to meet all requirements
3. Prioritizes momentum factors that can achieve higher targets

### Factor Evaluation (Critic Agent)

When evaluating factors, the Critic Agent:
1. Checks each metric against requirements
2. Determines pass/fail status for each metric
3. Provides detailed evaluation with explicit pass/fail statements
4. Uses momentum-specific benchmarks for momentum factors

### Reporting (Reporter Agent)

When reporting results, the Reporter Agent:
1. States whether each metric passed or failed
2. Provides performance assessment relative to requirements
3. Highlights metrics that need improvement
4. Emphasizes momentum factor importance

## Factor DSL Specification

All factors must specify metrics targets in their YAML:

```yaml
targets:
  min_sharpe: 1.8          # Required: Minimum Sharpe ratio (1.8)
  max_maxdd: 0.25          # Required: Maximum drawdown (-25%)
  min_avg_ic: 0.05         # Required: Minimum average IC
  min_ir: 0.5              # Required: Minimum Information Ratio
  min_hit_rate: 0.52       # Required: Minimum hit rate (52%)
  max_turnover_monthly: 250.0  # Required: Maximum monthly turnover (250%)
```

## Momentum Factor Benchmarks

Momentum factors are evaluated with momentum-specific benchmarks:

| Metric | Standard Requirement | Momentum Target |
|--------|---------------------|----------------|
| Sharpe Ratio | >= 1.8 | >= 2.0 |
| Max Drawdown | >= -25% | >= -20% |
| IC | >= 0.05 | >= 0.06 |
| IR | >= 0.5 | >= 0.6 |
| Hit Rate | >= 52% | >= 54% |
| Turnover | <= 250% | < 200% |

## Best Practices

1. **Design for Metrics**: Consider metrics requirements during factor design
2. **Test Early**: Check metrics early in the research process
3. **Iterate**: Refine factors that fail metrics requirements
4. **Document**: Record which metrics passed/failed and why
5. **Prioritize**: Focus on factors that can meet all requirements

## Summary

**ALL FACTORS MUST MEET ALL METRICS REQUIREMENTS:**

✅ Sharpe Ratio: >= 1.8 (target: 2.0+) - **CRITICAL**
✅ Max Drawdown: >= -25% (target: -20% or better) - **CRITICAL**
✅ Average IC: >= 0.05 (target: 0.06+)
✅ Information Ratio: >= 0.5 (target: 0.6+)
✅ Hit Rate: >= 52% (target: 54%+)
✅ Monthly Turnover: <= 250% (target: <200%)

**CRITICAL**: Factors with Sharpe < 1.8 or MaxDD < -25% are automatically rejected.

Factors that fail any metric requirement are considered insufficient for production use.

