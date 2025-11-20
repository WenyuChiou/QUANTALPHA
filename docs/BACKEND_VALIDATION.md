# Backend Validation Process

## Overview

Before displaying factor results in the frontend dashboard, we must ensure all backend components are working correctly. This document describes the validation process.

## Validation Steps

### 1. Backend Component Tests

Run the comprehensive backend test suite:

```bash
python scripts/test_backend.py
```

This tests:
- **Database Operations**: Factor creation, run creation, metrics storage/retrieval
- **Factor DSL Parsing**: YAML parsing, validation, parameter extraction
- **Factor Primitives**: RET_LAG, ROLL_STD, ZSCORE, etc.
- **Metrics Calculation**: Sharpe, MaxDD, IC calculations
- **Data Fetching**: yfinance integration
- **Backtest Pipeline**: Walk-forward backtest initialization
- **RAG System**: Embeddings and indexing

### 2. Dashboard Health Check

The dashboard automatically checks backend health before displaying data:

```python
def check_backend_health():
    """Check if backend components are working."""
    # Tests:
    # 1. Database connection
    # 2. Core imports (DSLParser, metrics)
    # 3. Basic functionality
```

If backend is not healthy:
- Dashboard shows error message
- User is directed to run backend tests
- No data is displayed until backend is verified

### 3. Data Validation

Before displaying factor results:
- Verify database connection is active
- Check that runs data can be loaded
- Validate metrics are properly formatted
- Ensure all required fields are present

## Error Handling

### Backend Not Ready

**Symptoms**:
- Database connection fails
- Import errors
- Component initialization fails

**Actions**:
1. Check error message in dashboard
2. Run `python scripts/test_backend.py` to diagnose
3. Fix identified issues
4. Re-run tests until all pass

### No Data Available

**Symptoms**:
- Backend is healthy
- Database is empty or has no runs

**Actions**:
1. Backend is working correctly
2. Start factor discovery process
3. Run backtests to generate data
4. Dashboard will display results once data exists

## Testing Workflow

### Development Workflow

1. **Make Changes**: Modify backend code
2. **Run Tests**: `python scripts/test_backend.py`
3. **Fix Issues**: Address any test failures
4. **Verify Dashboard**: Check dashboard health check passes
5. **Commit**: Only commit when tests pass

### Production Workflow

1. **Pre-deployment**: Run full test suite
2. **Health Check**: Verify all components working
3. **Deploy**: Deploy only if tests pass
4. **Monitor**: Dashboard health check monitors continuously

## Best Practices

1. **Always Test First**: Run backend tests before frontend changes
2. **Health Checks**: Dashboard checks backend health automatically
3. **Error Messages**: Clear error messages guide users to solutions
4. **Documentation**: Keep this document updated with new components

## Component Dependencies

```
Dashboard
  └─> Database (SQLite)
  └─> Factor DSL Parser
  └─> Metrics Calculator
  └─> Data Loader
```

All components must be healthy for dashboard to function.

## Troubleshooting

### Database Issues
- Check database file exists: `experiments.db`
- Verify SQLAlchemy models are correct
- Test database operations directly

### Import Issues
- Verify all dependencies installed: `pip install -r requirements.txt`
- Check Python path includes `src/`
- Verify module structure is correct

### Function Signature Mismatches
- Check function signatures match between test and implementation
- Verify parameter names and types
- Update tests when signatures change

## Continuous Improvement

- Add new tests as components are added
- Update health checks for new dependencies
- Document any new validation requirements
- Keep test coverage high

