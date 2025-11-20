# Alpha-Mining LLM Agent Framework

A production-ready framework for automated factor discovery using LLM agents, RAG, and memory systems. The framework uses LangChain agents with Ollama (deepseek r1), yfinance for data, daily backtests, and a Streamlit dashboard.

## Features

- **RAG + Memory**: Agents learn from mistakes and exploit successful patterns
- **Factor DSL**: Human-readable, composable factor specifications
- **Daily Backtests**: Purged walk-forward validation with embargo periods
- **Comprehensive Metrics**: Sharpe, MaxDD, IC, IR, turnover, hit rate
- **Anti-Leakage**: Built-in lookahead detection and validation
- **Streamlit Dashboard**: Interactive visualization of results
- **Knowledge Base**: Curated papers, notes, and run summaries

## Architecture

### Agents
1. **Researcher**: Proposes Factor DSL specs using RAG-seeded ideation
2. **Feature Agent**: Executes Factor DSL and computes features
3. **Backtester**: Runs walk-forward backtests
4. **Critic**: Validates runs and writes failure/success cards
5. **Librarian**: Manages RAG index and knowledge curation
6. **Reporter**: Generates summaries and iteration plans

### Components
- **Factor DSL**: YAML-based factor specification language
- **RAG System**: Chroma vector DB with sentence-transformers (bge-m3)
- **Memory Layer**: SQLite database for experiments, runs, metrics, lessons
- **Backtest Engine**: Purged walk-forward with portfolio construction
- **Validation**: Leakage detection, stability checks, regime robustness

## Quick Start

### Prerequisites

1. **Python 3.9+**
2. **Ollama** with deepseek r1 model:
   ```bash
   ollama pull deepseek-r1
   ```

### Installation

```bash
# Clone repository
git clone git@github.com:WenyuChiou/QUANTALPHA.git
cd QuantAlpha

# Install dependencies
pip install -r requirements.txt

# Initialize knowledge base index
python -m src.rag.indexer --kb ./kb --out ./kb.index
```

### Usage

#### Run Orchestrator

```bash
# Run single iteration with 3 candidates
python -m src.agents.orchestrator --universe sp500 --n_candidates 3

# Run multiple iterations
python -m src.agents.orchestrator --universe sp500 --n_iterations 5 --n_candidates 3
```

#### Start Dashboard

```bash
streamlit run src/dashboard/app.py
```

#### Index Knowledge Base

```bash
python -m src.rag.indexer
```

## Project Structure

```
alpha-miner/
├── configs/              # Configuration files
│   ├── universe.yml      # Universe definitions
│   ├── costs.yml         # Trading costs
│   └── constraints.yml   # Validation constraints
├── data/
│   └── cache/            # yfinance cache
├── kb/                   # Knowledge base
│   ├── papers/          # Paper summaries
│   ├── notes/           # Design notes
│   └── run_summaries/   # Run post-mortems
├── experiments/
│   └── runs/            # Backtest outputs
└── src/
    ├── agents/          # LangChain agents
    ├── tools/           # MCP tools
    ├── rag/            # RAG system
    ├── memory/          # Memory layer
    ├── factors/        # Factor DSL
    ├── backtest/       # Backtest engine
    ├── viz/            # Visualization
    └── dashboard/      # Streamlit dashboard
```

## Factor DSL Example

```yaml
name: "TSMOM_252_minus_21_volTarget"
universe: "sp500"
frequency: "D"
signals:
  - id: "mom_long"
    expr: "RET_LAG(1,252) - RET_LAG(1,21)"
    normalize: "zscore_252"
portfolio:
  scheme: "long_short_deciles"
  weight: "equal"
  notional: 1.0
validation:
  min_history_days: 800
  purge_gap_days: 21
targets:
  min_sharpe: 1.0
  max_maxdd: 0.35
  min_avg_ic: 0.05
```

## Configuration

### Universe (`configs/universe.yml`)
Define universes (S&P 500, NASDAQ-100, Russell 1000) and trading calendars.

### Costs (`configs/costs.yml`)
Configure slippage (5 bps), fees, and borrow costs (50 bps annual).

### Constraints (`configs/constraints.yml`)
Set validation rules: min sample size (800 days), max turnover (250%/mo), targets.

## Learning Loop

1. **RAG-seeded ideation** → Researcher proposes factors using KB + Success Ledger
2. **Compute & Backtest** → Feature + Backtester produce signals and metrics
3. **Critique & Lessons** → Critic flags issues and writes lessons
4. **Log & Summarize** → Reporter creates summaries; Librarian indexes in vector DB
5. **Exploit** → Orchestrator requests mutations around best factors
6. **Repeat** with stricter targets or expanded universe

## Dashboard Features

- **Factor Leaderboard**: Sortable by Sharpe, MaxDD, IC, IR, turnover
- **Performance Analysis**: Equity curves, drawdown charts, metrics
- **IC Analysis**: Information coefficient timeline and statistics
- **Regime Analysis**: Performance across different market regimes
- **Post-Mortems**: Success stories and failure analysis

## Example Factors

Pre-built factor templates:
- **TSMOM**: Time-series momentum (12m - 1m returns)
- **Low Vol**: Inverse volatility factor
- **Vol-Scaled Momentum**: Momentum scaled by volatility

See `src/factors/recipes.py` for examples.

## Validation

The framework includes comprehensive validation:
- **No-lookahead**: Automatic detection of future data usage
- **Sample size**: Minimum history requirements
- **Stability**: Rolling Sharpe/IC checks
- **Regime robustness**: Performance across different regimes
- **Leakage detection**: Correlation with future returns

## Contributing

This is a research framework. Contributions welcome!

## License

[Specify your license]

## References

- Jegadeesh & Titman (1993): "Returns to Buying Winners and Selling Losers"
- Moskowitz et al. (2012): "Time Series Momentum"
- Ang et al. (2006): "The Cross-Section of Volatility and Expected Returns"

