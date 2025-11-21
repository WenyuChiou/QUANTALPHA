# nonlinear_momentum_demo

**Archived**: 2025-11-20T23:09:54.872532

## Performance Metrics

- **Sharpe Ratio**: -0.47
- **Max Drawdown**: -12.23%
- **Average IC**: 0.0000
- **Turnover**: 0.0%

## Archive Contents

- `metadata.json` - Factor information and metrics
- `factor_spec.yaml` - Complete factor specification
- `agent_outputs/` - All agent responses
  - `researcher_proposal.json` - Original proposal
  - `feature_computation.json` - Computation log
  - `backtest_results.json` - Backtest results
  - `critic_evaluation.json` - Critique
- `computations/` - Computed data
  - `signals.parquet` - Factor signals
  - `returns.parquet` - Portfolio returns
  - `equity_curve.parquet` - Equity curve
- `backtest/` - Backtest details
  - `metrics.json` - Performance metrics
  - `split_results.json` - Walk-forward split results
- `conversation_log.json` - Complete agent dialogue

## Success Criteria

This factor met the following criteria:
- Sharpe Ratio >= 1.8
- Max Drawdown >= -25%
- Average IC >= 0.05
