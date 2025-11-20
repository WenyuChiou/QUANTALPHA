# Hedge Fund Research Workflow

## Overview

This framework implements a professional hedge fund research workflow for factor discovery. The process follows industry-standard practices used by quantitative hedge funds.

## Research Process

### Phase 1: Hypothesis Formation

**Objective**: Formulate a research hypothesis based on market intuition, academic literature, or empirical observations.

**Steps**:
1. Define research question
2. Search knowledge base for related research
3. Formulate hypothesis with theoretical basis
4. Identify expected behavior and risk factors

**Example**:
```python
from src.research.research_workflow import ResearchWorkflow

workflow = ResearchWorkflow(store, retriever)

hypothesis = workflow.phase1_hypothesis_formation(
    title="Momentum Factor with Volatility Scaling",
    description="A momentum factor scaled by realized volatility...",
    motivation="Traditional momentum has varying risk exposure...",
    universe="sp500"
)
```

### Phase 2: Peer Review

**Objective**: Get peer review and approval before proceeding to implementation.

**Steps**:
1. Submit hypothesis for review
2. Reviewer evaluates theoretical basis
3. Approve or reject with comments
4. Only proceed if approved

**Example**:
```python
hypothesis = workflow.phase2_peer_review(
    hypothesis=hypothesis,
    reviewer="Senior Researcher",
    approved=True,
    comments="Strong theoretical basis, proceed to design"
)
```

### Phase 3: Factor Design

**Objective**: Translate approved hypothesis into implementable Factor DSL specification.

**Steps**:
1. Generate Factor DSL from hypothesis
2. Select appropriate primitives
3. Choose parameters (lags, windows, normalization)
4. Validate design (no lookahead, proper structure)

**Example**:
```python
design = workflow.phase3_factor_design(hypothesis)
# Design includes YAML spec, rationale, parameter choices
```

### Phase 4: Backtesting

**Objective**: Run comprehensive backtest to evaluate factor performance.

**Steps**:
1. Compute factor signals
2. Run walk-forward backtest
3. Calculate performance metrics
4. Check for data quality issues

**Example**:
```python
backtest_result = workflow.phase4_backtesting(
    design=design,
    prices_df=prices,
    returns_df=returns
)
```

### Phase 5: Comprehensive Analysis

**Objective**: Perform deep-dive analysis of backtest results.

**Metrics Analyzed**:
- **Performance**: Sharpe, MaxDD, IC, IR, turnover, hit rate
- **Risk**: VaR, CVaR, tail ratio
- **Stability**: Rolling Sharpe stability, IC stability
- **Regime Analysis**: Bull/bear, high/low volatility performance
- **Decay Analysis**: IC decay over time
- **Multi-dimensional**: Predictive power, stability, robustness scores

**Example**:
```python
analysis = workflow.phase5_analysis(
    design=design,
    backtest_result=backtest_result,
    signals=signals,
    returns=returns,
    prices=prices,
    equity_curve=equity_curve
)

# Generate report
report = workflow.analyst.generate_report(analysis)
print(report)
```

### Phase 6: Documentation

**Objective**: Document research findings for knowledge base.

**Steps**:
1. Write success/failure cards
2. Document key insights
3. Record regime-specific performance
4. Update knowledge base

**Example**:
```python
documentation = workflow.phase6_documentation(
    hypothesis=hypothesis,
    design=design,
    analysis=analysis
)
```

## Complete Workflow

Run the complete workflow in one call:

```python
results = workflow.run_complete_workflow(
    title="Momentum Factor with Volatility Scaling",
    description="...",
    motivation="...",
    universe="sp500",
    reviewer="Senior Researcher",
    auto_approve=False
)
```

## Research Standards

### Hypothesis Requirements

- **Clear Research Question**: What are we trying to discover?
- **Theoretical Basis**: Academic or empirical support
- **Expected Behavior**: What do we expect to see?
- **Risk Factors**: What could go wrong?

### Design Requirements

- **No Lookahead**: All data must be available at signal time
- **Proper Normalization**: Appropriate scaling for signals
- **Parameter Justification**: Why these specific parameters?
- **Alternative Designs**: What other approaches were considered?

### Analysis Requirements

- **Comprehensive Metrics**: Performance, risk, stability
- **Regime Analysis**: How does it perform in different market conditions?
- **Decay Analysis**: Does performance degrade over time?
- **Multi-dimensional Evaluation**: Beyond just Sharpe ratio

### Documentation Requirements

- **Success Cards**: What worked and why
- **Failure Cards**: What didn't work and why
- **Key Insights**: Actionable learnings
- **Regime Performance**: When does it work best?

## Best Practices

1. **Start with Strong Hypothesis**: Well-founded research question
2. **Peer Review**: Always get peer review before implementation
3. **Comprehensive Analysis**: Don't just look at Sharpe ratio
4. **Document Everything**: Learnings go into knowledge base
5. **Iterate**: Refine based on analysis results

## Comparison with Standard Workflow

| Standard Workflow | Hedge Fund Workflow |
|------------------|---------------------|
| Generate factors | Form hypothesis |
| Run backtest | Design factor |
| Check metrics | Comprehensive analysis |
| Done | Documentation & peer review |

The hedge fund workflow adds:
- **Hypothesis formation** (research question)
- **Peer review** (quality control)
- **Comprehensive analysis** (deep dive)
- **Documentation** (knowledge capture)

## Example Output

```
BACKTEST ANALYSIS REPORT
========================

Factor: Momentum_VolScaled
Run ID: research_20250101_120000

PERFORMANCE METRICS
-------------------
Sharpe Ratio:        1.45
Max Drawdown:        -28.5%
Annual Return:       12.3%
Annual Volatility:    8.5%
Information Ratio:    0.67
Information Coeff:    0.062
Turnover (monthly):   45.2%
Hit Rate:            54.3%

RISK METRICS
-----------
VaR (95%):          -0.0234
CVaR (95%):         -0.0345
Tail Ratio:         1.23

REGIME ANALYSIS
---------------
Bull Market:
  Sharpe: 1.65
  Return: 15.2%

Bear Market:
  Sharpe: 0.89
  Return: -5.3%

...
```

## Next Steps

- Review analysis results
- Decide on production deployment
- Monitor live performance
- Iterate and refine

