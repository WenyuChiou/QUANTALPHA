# User Guide

## Overview

The Alpha-Mining LLM Agent Framework is an automated system for discovering and validating quantitative trading factors using Large Language Models (LLMs) and a Plan-Do-Review-Replan (PDRR) cycle.

## Quick Start

### 1. Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install -r requirements-dev.txt
```

### 2. Setup

```bash
# Run setup script
python setup_env.py

# Or manually:
# 1. Ensure Ollama is running: ollama serve
# 2. Pull model: ollama pull deepseek-r1
# 3. Initialize database: python -c "from src.memory.store import ExperimentStore; ExperimentStore('experiments.db')"
# 4. Index knowledge base: python scripts/index_kb.py
```

### 3. Run First Iteration

```bash
# Test pipeline
python test_pipeline.py

# Run daily workflow
python -m src.workflows.daily_workflow --n_candidates 3

# Start dashboard
streamlit run src/dashboard/app.py
```

## Core Concepts

### Factor DSL

Factors are defined using a YAML-based Domain-Specific Language (DSL):

```yaml
name: "TSMOM"
universe: "sp500"
frequency: "D"
signals:
  - id: "momentum"
    expr: "RET_LAG(1,252) - RET_LAG(1,21)"
    normalize: "zscore_252"
portfolio:
  scheme: "long_short_deciles"
  weight: "equal"
validation:
  min_history_days: 252
targets:
  min_sharpe: 1.8  # Updated requirement: minimum Sharpe 1.8
  max_maxdd: 0.25  # Updated requirement: maximum drawdown -25%
  min_avg_ic: 0.05
```

### Agents

The framework uses specialized agents:

- **Researcher**: Proposes new factor designs using RAG
- **Feature Agent**: Computes factor signals from DSL
- **Backtester**: Runs backtests and collects metrics
- **Critic**: Validates results and extracts lessons
- **Librarian**: Manages knowledge base
- **Reporter**: Generates summaries and reports

### Workflow

1. **Planning**: Researcher generates factor proposals
2. **Execution**: Feature Agent computes signals, Backtester runs tests
3. **Review**: Critic validates and extracts lessons
4. **Re-planning**: Reporter updates knowledge, plans next iteration

## Daily Workflow

### Morning Planning

```python
from src.workflows.daily_workflow import DailyWorkflow

workflow = DailyWorkflow(universe="sp500")
planning = workflow.morning_planning(n_candidates=5)
```

### Execution

```python
execution = workflow.execution(planning['factor_proposals'])
```

### Review

```python
review = workflow.afternoon_review(execution)
```

### Re-planning

```python
replan = workflow.evening_replanning(review)
```

### Complete Cycle

```python
results = workflow.run_daily_cycle(n_candidates=3)
```

## Continuous Improvement

```python
from src.workflows.continuous_improvement import ContinuousImprovementLoop

improvement = ContinuousImprovementLoop()
cycle_results = improvement.run_improvement_cycle(
    n_mutations=3,
    focus_on_top=5
)
```

## Configuration

### Universe

Edit `configs/universe.yml` to define trading universes:

```yaml
universes:
  sp500:
    tickers: "sp500_tickers.csv"
    calendar: "NYSE"
```

### Costs

Edit `configs/costs.yml` to set trading costs:

```yaml
slippage_bps: 5
fees_bps: 1
borrow_cost_bps: 50
```

### Constraints

Edit `configs/constraints.yml` to set validation rules:

```yaml
min_history_days: 800
max_turnover_monthly: 250.0
min_sharpe: 1.8  # Updated requirement: minimum Sharpe 1.8
```

## Dashboard

Access the dashboard at `http://localhost:8501` after running:

```bash
streamlit run src/dashboard/app.py
```

Features:
- Factor leaderboard
- Performance charts
- IC analysis
- Regime analysis
- Post-mortems
- Real-time monitoring

## Knowledge Base

Add papers and notes to `kb/` directory:

```
kb/
  papers/
    tsmom_paper.md
    skew_factor.md
  lessons/
    success_cards/
    failure_cards/
  templates/
```

Index the knowledge base:

```bash
python scripts/index_kb.py
```

## Best Practices

1. **Start Small**: Begin with 1-3 candidates per iteration
2. **Monitor Closely**: Watch dashboard for early failures
3. **Learn from Failures**: Review failure cards regularly
4. **Iterate Gradually**: Increase targets slowly
5. **Document Everything**: Keep knowledge base updated

## Troubleshooting

### Ollama Connection Issues

```bash
# Check Ollama is running
ollama list

# Restart Ollama
ollama serve
```

### Database Issues

```bash
# Recreate database
rm experiments.db
python -c "from src.memory.store import ExperimentStore; ExperimentStore('experiments.db')"
```

### Index Issues

```bash
# Rebuild index
rm -rf kb.index
python scripts/index_kb.py
```

## Next Steps

- Read [API Reference](API_REFERENCE.md)
- Review [Workflow Documentation](WORKFLOWS.md)
- Check [Best Practices](BEST_PRACTICES.md)

