# Momentum Factor Priority

## Overview

**MOMENTUM FACTORS ARE EXTREMELY IMPORTANT** and have been given the highest priority across all agents in the framework. This document describes how momentum factors are emphasized throughout the system.

## Why Momentum Factors?

Momentum factors have demonstrated:

- **Strong Empirical Evidence**: Decades of research across multiple asset classes
- **Robust Performance**: Sharpe ratios typically 1.0-2.0
- **Persistent Predictive Power**: Information coefficients typically 0.05-0.10
- **Academic Support**: Well-documented in academic literature (Jegadeesh & Titman, Moskowitz et al.)
- **Regime Robustness**: Performance persists across different market conditions

## Agent Prompts Updated

### 1. Researcher Agent

**Priority**: **HIGHEST** - Momentum factors are the top priority

**Prompt Changes**:
- Explicitly states: "MOMENTUM FACTORS ARE EXTREMELY IMPORTANT AND SHOULD BE GIVEN HIGHEST PRIORITY"
- Requires at least 2 out of 3 factors to be momentum-based
- Default context queries prioritize momentum factors
- Requirements emphasize momentum factor design

**Example Momentum Factors Prioritized**:
- Time Series Momentum (TSMOM): `RET_LAG(1,252) - RET_LAG(1,21)`
- Cross-sectional momentum: Ranking past returns
- Volatility-scaled momentum: Momentum scaled by realized volatility
- Industry-neutralized momentum: Momentum after removing industry effects

### 2. Critic Agent

**Evaluation Context**: Momentum factors evaluated with momentum-specific benchmarks

**Prompt Changes**:
- Notes that momentum factors have strong empirical support
- Uses momentum-specific performance benchmarks (Sharpe 1.0-2.0, IC 0.05-0.10)
- Gives special consideration to momentum factors during validation
- Evaluates momentum factors against momentum literature expectations

### 3. Reporter Agent

**Reporting Emphasis**: Highlights momentum factor importance

**Prompt Changes**:
- Summary generation emphasizes momentum factor significance
- Iteration planning prioritizes momentum factor mutations
- Strongly recommends exploring momentum factors if not already present
- Emphasizes momentum factors in all reports

### 4. Librarian Agent

**Search Priority**: Momentum-related content prioritized in searches

**Implementation**:
- `search_knowledge()` method automatically enhances queries with momentum terms
- Prioritizes momentum-related results in search results
- Combines momentum-specific searches with general searches

### 5. Hypothesis Manager

**Research Priority**: Momentum research searched first

**Implementation**:
- Automatically includes momentum terms in research queries
- Searches momentum-specific research before general research
- Prioritizes momentum-related knowledge base content

## Momentum Factor Benchmarks

When evaluating momentum factors, use these benchmarks:

| Metric | Typical Range | Good Performance |
|--------|---------------|------------------|
| Sharpe Ratio | 1.0 - 2.0 | ≥ 1.2 |
| Information Coefficient | 0.05 - 0.10 | ≥ 0.06 |
| Max Drawdown | -20% to -35% | ≤ -30% |
| Turnover (monthly) | 30% - 60% | ≤ 50% |
| Hit Rate | 50% - 60% | ≥ 52% |

## Implementation Details

### Factor Generation Priority

1. **First Priority**: Momentum-based factors
   - Time Series Momentum
   - Cross-sectional Momentum
   - Volatility-scaled Momentum

2. **Second Priority**: Momentum-related factors
   - Momentum + Volatility combinations
   - Momentum + Mean Reversion combinations
   - Regime-adjusted Momentum

3. **Third Priority**: Other factors
   - Value factors
   - Quality factors
   - Other anomalies

### Search Enhancement

When searching the knowledge base:
- If query doesn't mention momentum, automatically enhance with momentum terms
- Prioritize momentum-related results
- Include momentum research even when not explicitly requested

### Evaluation Standards

When evaluating factors:
- Momentum factors: Use momentum-specific benchmarks
- Non-momentum factors: Use general benchmarks
- Always note if a factor is momentum-based in reports

## Usage Examples

### Generating Momentum Factors

```python
from src.agents.researcher import ResearcherAgent

researcher = ResearcherAgent()

# Automatically prioritizes momentum factors
factors = researcher.propose_factors(n_factors=3)
# At least 2 out of 3 will be momentum-based
```

### Searching Knowledge Base

```python
from src.agents.librarian import LibrarianAgent

librarian = LibrarianAgent()

# Automatically prioritizes momentum results
results = librarian.search_knowledge(
    query="factor design",
    prioritize_momentum=True  # Default: True
)
```

### Evaluating Momentum Factors

```python
from src.agents.critic import CriticAgent

critic = CriticAgent()

# Automatically uses momentum benchmarks
critique = critic.critique_run(
    run_id=run_id,
    metrics=metrics,
    issues=issues,
    factor_yaml=momentum_factor_yaml
)
```

## Best Practices

1. **Always Prioritize Momentum**: When generating factors, momentum should be first choice
2. **Use Momentum Benchmarks**: Evaluate momentum factors with appropriate benchmarks
3. **Document Momentum Importance**: Always note momentum factor significance in reports
4. **Search Momentum First**: When researching, start with momentum-related content
5. **Mutate Momentum Factors**: When mutating successful factors, prioritize momentum factors

## References

- Jegadeesh, N., & Titman, S. (1993). Returns to buying winners and selling losers: Implications for stock market efficiency.
- Moskowitz, T. J., Ooi, Y. H., & Pedersen, L. H. (2012). Time series momentum.
- Asness, C. S., Moskowitz, T. J., & Pedersen, L. H. (2013). Value and momentum everywhere.

## Summary

**MOMENTUM FACTORS ARE EXTREMELY IMPORTANT** and are prioritized throughout the entire framework:

- ✅ Researcher Agent: Highest priority for momentum factors
- ✅ Critic Agent: Momentum-specific evaluation benchmarks
- ✅ Reporter Agent: Emphasis on momentum in all reports
- ✅ Librarian Agent: Prioritized momentum search results
- ✅ Hypothesis Manager: Momentum research searched first

All agents now explicitly recognize and prioritize momentum factors as critical components of quantitative factor research.

