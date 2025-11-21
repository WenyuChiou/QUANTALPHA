# Momentum with Volatility Adjustment (20-Year Backtest)

## Overview

This alpha demonstrates a momentum strategy enhanced with volatility adjustment, backtested over 20 years (2004-2024).

## Factor Specification

```yaml
name: "momentum_vol_adjusted_20y"
description: "20-day momentum adjusted by 60-day volatility with regime awareness"
universe: "sp500"
frequency: "D"
lookback_days: 252

signals:
  - id: "mom_20"
    expr: "RET_20"
    standardize: "zscore_252"
    description: "20-day momentum signal"
  
  - id: "vol_60"
    expr: "ROLL_STD(RET_D, 60)"
    standardize: "zscore_252"
    description: "60-day volatility"
  
  - id: "mom_vol_ratio"
    expr: "RET_20 / (ROLL_STD(RET_D, 60) + 0.01)"
    standardize: "zscore_252"
    description: "Momentum-to-volatility ratio"

portfolio:
  scheme: "long_short_deciles"
  weight: "equal"
  rebalance: "W-FRI"
  costs:
    bps_per_trade: 5
    borrow_bps: 50

metadata:
  category: "momentum"
  research_basis: "Jegadeesh & Titman (1993), enhanced with volatility adjustment"
  target_sharpe: 1.8
  target_maxdd: -0.25

```

## Performance Summary

| Metric | Value |
|--------|-------|
| **Sharpe Ratio** | 1.00 |
| **Annual Return** | 28.88% |
| **Annual Volatility** | 28.80% |
| **Max Drawdown** | -14.46% |
| **Calmar Ratio** | 0.00 |
| **Average IC** | 0.000 |
| **Hit Rate** | 45.62% |
| **Monthly Turnover** | 0.0% |

## Equity Curve

![Equity Curve](charts/equity_curve_3panel.png)

## Research Basis

Based on Jegadeesh & Titman (1993) momentum research, enhanced with:
- Volatility normalization to improve risk-adjusted returns
- Weekly rebalancing to reduce transaction costs
- Long-short decile portfolio construction

## Files

- `factor.yaml` - Factor specification
- `metrics.json` - Complete performance metrics
- `manifest.json` - Artifact checksums
- `charts/equity_curve_3panel.png` - 3-panel visualization
- `signals_meta.json` - Signal metadata
- `data_provenance.json` - Data source tracking

---

**Generated**: 2025-11-21 07:52:53  
**Backtest Period**: 2004-2024 (20 years)  
**Universe**: SP500
