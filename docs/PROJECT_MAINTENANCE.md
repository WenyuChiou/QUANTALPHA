# Project Maintenance Guide

## Overview

This document describes how to keep the project clean and maintainable.

## Project Structure

```
QuantAlpha/
├── configs/          # Configuration files (YAML)
├── data/            # Data cache (gitignored)
├── docs/            # Documentation
├── examples/        # Example scripts
├── experiments/     # Experiment outputs (gitignored)
├── kb/              # Knowledge base
├── scripts/         # Utility scripts
├── src/             # Source code
├── tests/           # Test files
├── .gitignore       # Git ignore rules
├── Makefile         # Build commands
├── README.md        # Main documentation
└── requirements.txt # Dependencies
```

## Temporary Files to Clean

### Automatically Ignored (via .gitignore)

- `__pycache__/` - Python cache directories
- `*.pyc`, `*.pyo` - Compiled Python files
- `*.log` - Log files
- `*.db` - Database files (except templates)
- `*.tmp`, `*.bak` - Temporary files
- `*.swp`, `*.swo` - Editor swap files
- `test_*.db` - Test databases
- `backups/` - Backup directories
- `.vscode/`, `.idea/` - IDE directories

### Manual Cleanup

Run the cleanup script:

```bash
python scripts/cleanup.py
```

This will remove:
- All `__pycache__` directories
- Temporary files (`*.pyc`, `*.py~`, `*.bak`, `*.tmp`)
- Test database files
- Log files
- Empty directories

## File Organization

### Scripts Directory

All utility scripts should be in `scripts/`:
- `setup_env.py` - Environment setup
- `test_backend.py` - Backend testing
- `index_kb.py` - Knowledge base indexing
- `run_tests.py` - Test runner
- `improve_code.py` - Code quality checks
- `cleanup.py` - Project cleanup

### Tests Directory

All test files should be in `tests/`:
- `test_pipeline.py` - Pipeline integration tests
- `tests/agents/` - Agent unit tests
- `tests/integration/` - Integration tests
- `tests/e2e/` - End-to-end tests
- `tests/performance/` - Performance tests

### Examples Directory

Example scripts demonstrating usage:
- `research_workflow_example.py` - Research workflow example

## Maintenance Tasks

### Regular Cleanup

Run cleanup before committing:

```bash
python scripts/cleanup.py
git add -A
git commit -m "Clean up temporary files"
```

### Before Committing

1. **Run cleanup script**:
   ```bash
   python scripts/cleanup.py
   ```

2. **Check for temporary files**:
   ```bash
   git status
   ```

3. **Verify .gitignore**:
   - Ensure temporary files are ignored
   - Check that important files are not ignored

4. **Run tests**:
   ```bash
   python scripts/test_backend.py
   python -m pytest tests/
   ```

### Code Quality

Run code quality checks:

```bash
python scripts/improve_code.py
```

### Database Maintenance

- Test databases (`test_*.db`) are automatically ignored
- Production database (`experiments.db`) should be backed up regularly
- Use `src/utils/backup.py` for database backups

### Knowledge Base Maintenance

- Index knowledge base after adding new content:
  ```bash
  python scripts/index_kb.py
  ```

- Keep knowledge base organized:
  - `kb/papers/` - Academic papers
  - `kb/notes/` - Design notes
  - `kb/run_summaries/` - Run summaries

## Files That Should NOT Be Committed

- Temporary scripts (`push.bat`, `temp_*.py`)
- Test databases (`test_*.db`)
- Log files (`*.log`)
- Cache files (`__pycache__/`, `*.pyc`)
- IDE files (`.vscode/`, `.idea/`)
- OS files (`.DS_Store`, `Thumbs.db`)
- Environment files (`.env`, `.env.local`)

## Files That SHOULD Be Committed

- Source code (`src/**/*.py`)
- Tests (`tests/**/*.py`)
- Scripts (`scripts/**/*.py`)
- Configuration (`configs/**/*.yml`)
- Documentation (`docs/**/*.md`)
- Knowledge base (`kb/**/*.md`)
- Examples (`examples/**/*.py`)
- Build files (`Makefile`, `requirements.txt`, `pytest.ini`)

## Best Practices

1. **Keep scripts organized**: All utility scripts in `scripts/`
2. **Run cleanup regularly**: Before each commit
3. **Update .gitignore**: When adding new temporary file types
4. **Document changes**: Update this file when structure changes
5. **Test before commit**: Run tests and cleanup before committing

## Automated Cleanup

Add to your pre-commit hook (optional):

```bash
#!/bin/bash
python scripts/cleanup.py
```

Or use Git hooks:

```bash
# .git/hooks/pre-commit
#!/bin/bash
python scripts/cleanup.py
```

## Troubleshooting

### Too many files to commit

Run cleanup:
```bash
python scripts/cleanup.py
git add -A
```

### Temporary files keep appearing

Check `.gitignore` and add patterns for new file types.

### Important files being ignored

Check `.gitignore` and use `git add -f <file>` to force add.

## Summary

- ✅ Run `python scripts/cleanup.py` before committing
- ✅ Keep all scripts in `scripts/` directory
- ✅ Keep all tests in `tests/` directory
- ✅ Update `.gitignore` for new temporary file types
- ✅ Document any structural changes

