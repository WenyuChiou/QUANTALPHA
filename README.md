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
- **Hedge Fund Workflow**: Professional research process (hypothesis → design → backtest → analysis)

## Research Workflow

The framework implements a **professional hedge fund research workflow**:

1. **Hypothesis Formation**: Form research hypothesis with theoretical basis
2. **Peer Review**: Get approval before implementation
3. **Factor Design**: Translate hypothesis to Factor DSL
4. **Backtesting**: Run comprehensive backtests
5. **Analysis**: Deep-dive performance, risk, regime analysis
6. **Documentation**: Document findings for knowledge base

See [Research Workflow Documentation](docs/RESEARCH_WORKFLOW.md) for details.

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

# Setup environment
make setup
# Or manually:
python scripts/setup_env.py
```

### Verify Installation

```bash
# Quick verification
python scripts/verify_pipeline.py

# Or run complete pipeline test
make run-full-pipeline
```

### Usage

#### Run Complete Pipeline

```bash
# Generate alpha factor and evaluation report
make run-full-pipeline

# Or directly:
python scripts/run_full_pipeline.py
```

#### Run Orchestrator

```bash
make run-orchestrator
```

#### Start Dashboard

```bash
make run-dashboard
```

#### Index Knowledge Base

```bash
make index-kb
```

## Architecture

### Agents

1. **Researcher**: Proposes Factor DSL specs using RAG-seeded ideation (prioritizes momentum factors)
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

## Metrics Requirements

All factors must meet these performance targets:

- **Sharpe Ratio**: >= 1.0 (target: 1.2+)
- **Max Drawdown**: >= -35% (target: -30% or better)
- **Information Coefficient**: >= 0.05 (target: 0.06+)
- **Information Ratio**: >= 0.5 (target: 0.6+)
- **Hit Rate**: >= 52% (target: 54%+)
- **Monthly Turnover**: <= 250% (target: <200%)

See [Metrics Requirements](docs/METRICS_REQUIREMENTS.md) for details.

## Momentum Factor Priority

**MOMENTUM FACTORS ARE EXTREMELY IMPORTANT** and are prioritized throughout the framework. See [Momentum Factor Priority](docs/MOMENTUM_FACTOR_PRIORITY.md) for details.

## Documentation

- [User Guide](docs/USER_GUIDE.md) - Getting started guide
- [API Reference](docs/API_REFERENCE.md) - API documentation
- [Research Workflow](docs/RESEARCH_WORKFLOW.md) - Hedge fund research process
- [Metrics Requirements](docs/METRICS_REQUIREMENTS.md) - Performance standards
- [Momentum Factor Priority](docs/MOMENTUM_FACTOR_PRIORITY.md) - Why momentum matters
- [Best Practices](docs/BEST_PRACTICES.md) - Development guidelines
- [Project Maintenance](docs/PROJECT_MAINTENANCE.md) - Keeping project clean

## Project Structure

```
QuantAlpha/
├── configs/          # Configuration files
├── data/            # Data cache (gitignored)
├── docs/            # Documentation
├── examples/        # Example scripts
├── experiments/     # Experiment outputs (gitignored)
├── kb/              # Knowledge base
├── scripts/          # Utility scripts
├── src/             # Source code
│   ├── agents/      # LLM agents
│   ├── backtest/    # Backtesting engine
│   ├── factors/     # Factor DSL and primitives
│   ├── memory/      # Database layer
│   ├── rag/         # RAG system
│   ├── research/    # Research workflow
│   └── utils/       # Utilities
└── tests/           # Test files
```

## Testing

```bash
# Run all tests
make test

# Run backend tests
python scripts/test_backend.py

# Verify pipeline
python scripts/verify_pipeline.py

# Run complete pipeline
make run-full-pipeline
```

## Maintenance

```bash
# Clean temporary files
make clean

# Or use cleanup script
python scripts/cleanup.py
```

## License

MIT

## Contributing

See [Project Maintenance](docs/PROJECT_MAINTENANCE.md) for guidelines.
