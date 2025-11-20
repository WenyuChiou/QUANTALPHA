# API Reference

## Core Modules

### Memory Store

```python
from src.memory.store import ExperimentStore

store = ExperimentStore("experiments.db")

# Create factor
factor = store.create_factor(
    name="MyFactor",
    yaml="...",
    tags=["momentum"]
)

# Create run
run = store.create_run(
    factor_id=factor.id,
    start_date=datetime(2020, 1, 1),
    end_date=datetime(2023, 12, 31)
)

# Create metrics
metrics = store.create_metrics(run.id, {
    'sharpe': 1.5,
    'maxdd': -0.2,
    'avg_ic': 0.08
})
```

### Factor DSL

```python
from src.factors.dsl import DSLParser

parser = DSLParser()
spec = parser.parse(yaml_string)

# Validate
is_valid, warnings = parser.validate_no_lookahead(spec)

# Extract parameters
params = parser.extract_parameters(spec)
```

### Primitives

```python
from src.factors.primitives import PRIMITIVES

# Available primitives:
# RET_LAG, TS_RANK, DECAY_LINEAR, DELTA, CORRELATION, etc.
```

### Backtesting

```python
from src.backtest.pipeline import WalkForwardBacktest

backtest = WalkForwardBacktest(
    n_splits=5,
    embargo_days=21
)

results = backtest.run(
    signals_df=signals,
    returns_df=returns,
    prices_df=prices
)
```

### RAG

```python
from src.rag.retriever import HybridRetriever

retriever = HybridRetriever(index_path="./kb.index")
results = retriever.search("momentum factor", n_results=5)
```

## Agents

### Researcher Agent

```python
from src.agents.researcher import ResearcherAgent

researcher = ResearcherAgent(
    model_name="deepseek-r1",
    db_path="experiments.db",
    index_path="./kb.index"
)

# Propose factors
factors = researcher.propose_factors(n_factors=3)

# Generate mutations
mutations = researcher.propose_mutations(base_yaml, n_mutations=2)
```

### Feature Agent

```python
from src.agents.feature_agent import FeatureAgent

feature_agent = FeatureAgent()

result = feature_agent.compute_features(
    factor_yaml=yaml_string,
    prices_df=prices,
    returns_df=returns
)
```

### Backtester Agent

```python
from src.agents.backtester import BacktesterAgent

backtester = BacktesterAgent(output_base_dir="./experiments")

result = backtester.run_backtest(
    factor_yaml=yaml_string,
    prices_df=prices,
    returns_df=returns,
    run_id="run_001"
)
```

### Critic Agent

```python
from src.agents.critic import CriticAgent

critic = CriticAgent(
    model_name="deepseek-r1",
    db_path="experiments.db"
)

critique = critic.critique_run(
    run_id=run.id,
    metrics=metrics,
    issues=issues,
    factor_yaml=yaml_string
)
```

## Workflows

### Daily Workflow

```python
from src.workflows.daily_workflow import DailyWorkflow

workflow = DailyWorkflow(universe="sp500")
results = workflow.run_daily_cycle(n_candidates=3)
```

### Continuous Improvement

```python
from src.workflows.continuous_improvement import ContinuousImprovementLoop

improvement = ContinuousImprovementLoop()
results = improvement.run_improvement_cycle()
```

## Tools

### Fetch Data

```python
from src.tools.fetch_data import fetch_data

prices, returns = fetch_data(
    tickers=["AAPL", "MSFT"],
    start_date="2020-01-01",
    end_date="2023-12-31"
)
```

### Compute Factor

```python
from src.tools.compute_factor import compute_factor

signals = compute_factor(
    factor_yaml=yaml_string,
    prices_df=prices,
    returns_df=returns
)
```

### RAG Search

```python
from src.tools.rag_search import rag_search

results = rag_search(
    query="momentum factor",
    n_results=5,
    filters={"topic": "momentum"}
)
```

