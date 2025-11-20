# Workflow Documentation

## Plan-Do-Review-Replan (PDRR) Cycle

### Phase 1: Planning

**Goal**: Generate factor candidates using RAG and historical knowledge.

**Steps**:
1. Query knowledge base for successful patterns
2. Retrieve error bank to avoid pitfalls
3. Generate N candidate factors (default: 3-5)
4. Create Factor DSL YAML for each candidate

**Agent**: Researcher

**Output**: List of factor YAML specifications

### Phase 2: Execution

**Goal**: Compute signals and run backtests.

**Steps**:
1. Parse Factor DSL specifications
2. Compute signals for all tickers and dates
3. Validate no-lookahead compliance
4. Run walk-forward backtest
5. Calculate performance metrics

**Agents**: Feature Agent, Backtester

**Output**: Backtest results with metrics

### Phase 3: Review

**Goal**: Validate results and extract lessons.

**Steps**:
1. Check validation constraints
2. Detect issues (leakage, instability)
3. Classify as passed/failed
4. Extract success/failure patterns
5. Write lessons to knowledge base

**Agent**: Critic

**Output**: Validation results, lessons

### Phase 4: Re-planning

**Goal**: Update knowledge and plan next iteration.

**Steps**:
1. Update RAG index with new lessons
2. Analyze success/failure patterns
3. Generate mutations of top performers
4. Adjust targets based on performance
5. Plan next iteration focus

**Agents**: Librarian, Reporter

**Output**: Updated knowledge base, next iteration plan

## Daily Workflow

### Morning (9:00 AM)

**Planning Phase**:
- Review previous day's results
- Generate new factor candidates
- Set daily targets

### Midday (12:00 PM)

**Execution Phase**:
- Compute features for new factors
- Run backtests
- Calculate metrics

### Afternoon (3:00 PM)

**Review Phase**:
- Validate results
- Classify successes/failures
- Extract lessons

### Evening (6:00 PM)

**Re-planning Phase**:
- Generate summary reports
- Update knowledge base
- Plan next day's focus

## Weekly Workflow

### Monday
- Comprehensive review of week's results
- Identify top performers
- Update targets

### Tuesday-Thursday
- Focus on mutations and exploration
- Test variations of successful factors
- Explore new directions

### Friday
- Comprehensive review
- Update knowledge base
- Generate weekly report

### Weekend
- Deep analysis
- Framework improvements
- Research new ideas

## Monthly Workflow

### Week 1: Evaluation
- Comprehensive evaluation of all factors
- Performance ranking
- Identify patterns

### Week 2: Mutation
- Focus on top performers
- Generate mutations
- Test variations

### Week 3: Exploration
- Explore new directions
- Test hypotheses
- Expand knowledge base

### Week 4: Review & Planning
- Review month's results
- Plan next month's strategy
- Update framework

## Continuous Improvement

### Pattern Recognition

**Success Patterns**:
- Extract common motifs from successful factors
- Identify parameter ranges that work
- Map regime-specific patterns

**Failure Patterns**:
- Identify recurring failure modes
- Update error bank
- Refine validation rules

### Mutation Generation

**Types**:
- **Parameter Mutation**: Vary lags, windows, thresholds
- **Structural Mutation**: Change factor structure
- **Combination**: Combine multiple mutations

### Target Adjustment

**Dynamic Targets**:
- Adjust based on current best performance
- Increase targets gradually (10% improvement rate)
- Maintain realistic expectations

## Best Practices

1. **Start Conservative**: Begin with low targets, increase gradually
2. **Monitor Closely**: Watch for early failures and patterns
3. **Learn Continuously**: Update knowledge base regularly
4. **Iterate Systematically**: Follow PDRR cycle strictly
5. **Document Everything**: Keep detailed records of all runs

