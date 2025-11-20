# Metrics Requirements Update

## Updated Requirements (2025-01-XX)

The metrics requirements have been updated to stricter standards:

### Previous Requirements
- Sharpe Ratio: >= 1.0
- Max Drawdown: <= -35%

### New Requirements (CRITICAL)
- **Sharpe Ratio: >= 1.8** (increased from 1.0)
- **Max Drawdown: <= -25%** (stricter, changed from -35%)

## Impact

### Factor Generation
- All factors must now target Sharpe >= 1.8
- All factors must maintain drawdowns <= -25%
- Factors failing these requirements are automatically rejected

### Agent Behavior
- **Researcher Agent**: Generates factors targeting Sharpe >= 1.8, MaxDD <= -25%
- **Critic Agent**: Rejects factors with Sharpe < 1.8 or MaxDD < -25%
- **Reporter Agent**: Highlights metrics failures more prominently

### Evaluation Standards

| Metric | Previous | New | Change |
|--------|----------|-----|--------|
| Sharpe Ratio | >= 1.0 | >= 1.8 | +0.8 (80% increase) |
| Max Drawdown | <= -35% | <= -25% | -10% (stricter) |

## Updated Files

All following files have been updated:
- `configs/constraints.yml` - Configuration targets
- `src/agents/researcher.py` - Factor generation prompts
- `src/agents/critic.py` - Evaluation prompts
- `src/agents/reporter.py` - Reporting prompts
- `src/factors/recipes.py` - All factor templates
- `src/research/factor_design.py` - Design templates
- `src/workflows/*.py` - Workflow targets
- `src/backtest/validator.py` - Validation defaults
- `src/memory/factor_registry.py` - Default values
- `docs/METRICS_REQUIREMENTS.md` - Documentation
- All test files and examples

## Rationale

These stricter requirements ensure:
1. **Higher Quality**: Only factors with strong risk-adjusted returns pass
2. **Better Risk Control**: Stricter drawdown limits protect capital
3. **Production Ready**: Factors meeting these standards are suitable for live trading
4. **Competitive Edge**: Higher Sharpe ratios indicate superior factor quality

## Migration Notes

If you have existing factors:
- Factors with Sharpe < 1.8 will be marked as FAILED
- Factors with MaxDD < -25% will be marked as FAILED
- Consider refining or discarding factors that don't meet new standards
- Focus on momentum factors which have higher probability of meeting these targets

## Next Steps

1. Review existing factors against new requirements
2. Refine factor designs to meet higher standards
3. Focus on momentum factors (they have best chance of meeting requirements)
4. Use continuous improvement loop to optimize factors

