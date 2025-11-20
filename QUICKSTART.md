# Quick Start Guide

## Complete Pipeline Execution

To run the complete pipeline and generate an alpha factor with evaluation report:

```bash
# Method 1: Using Makefile
make run-full-pipeline

# Method 2: Direct execution
python scripts/run_full_pipeline.py
```

## What This Does

The complete pipeline executes:

1. **Data Generation**: Creates sample price/return data
2. **Factor Generation**: Generates TSMOM momentum factor
3. **Signal Computation**: Computes factor signals
4. **Backtest Execution**: Runs backtest and calculates metrics
5. **Comprehensive Analysis**: Performs deep-dive analysis
6. **Database Storage**: Stores results in database
7. **Report Generation**: Creates evaluation report

## Output

After running, you will get:

- **Alpha Factor**: TSMOM_252_minus_21_volTarget
- **Performance Metrics**: Sharpe, MaxDD, IC, IR, etc.
- **Evaluation Report**: Located in `experiments/reports/alpha_report_*.md`

## Quick Verification

To quickly verify all components work:

```bash
python scripts/verify_pipeline.py
```

This checks:
- ✅ All imports work
- ✅ Factor generation works
- ✅ Database operations work
- ✅ Metrics calculation works

## Next Steps

1. **Review the Report**: Check `experiments/reports/` for evaluation report
2. **View Dashboard**: Run `make run-dashboard` to see results
3. **Generate More Factors**: Use orchestrator or research workflow
4. **Customize**: Modify factor recipes or create new ones

## Troubleshooting

If pipeline fails:

1. **Check Dependencies**: `pip install -r requirements.txt`
2. **Verify Backend**: `python scripts/test_backend.py`
3. **Check Logs**: Look for error messages in output
4. **Clean and Retry**: `make clean && make run-full-pipeline`

## Example Output

```
======================================================================
Complete Pipeline Test: Generate Alpha and Evaluate
======================================================================

Generating Sample Data
======================================================================
✓ Generated 1000 days of data for 50 tickers

Step 1: Factor Generation
======================================================================
✓ Generated factor: TSMOM_252_minus_21_volTarget
  Validation: PASSED
  Parameters: 5 extracted

Step 2: Factor Signal Computation
======================================================================
✓ Signals computed: (999, 50)
  Date range: 2015-01-02 to 2023-12-31
  Tickers: 50

Step 3: Backtest Execution
======================================================================
✓ Backtest completed
  Sharpe Ratio: 1.2345
  Max Drawdown: -0.1234
  IC: 0.0567
  Total Return: 45.67%

...

Report Location: experiments/reports/alpha_report_20250101_120000.md
======================================================================
✅ Pipeline test completed successfully!
======================================================================
```

