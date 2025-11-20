"""MCP tool: Log run to database and generate summary card."""

from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from ..memory.store import ExperimentStore
from ..memory.lessons import LessonManager


def log_run(
    factor_id: int,
    start_date: datetime,
    end_date: datetime,
    metrics: Dict[str, Any],
    in_sample_start: Optional[datetime] = None,
    in_sample_end: Optional[datetime] = None,
    out_sample_start: Optional[datetime] = None,
    out_sample_end: Optional[datetime] = None,
    regime_label: Optional[str] = None,
    issues: Optional[list] = None,
    db_path: str = "experiments.db"
) -> Dict[str, Any]:
    """Log a run to the database.
    
    Args:
        factor_id: Factor ID
        start_date: Start date
        end_date: End date
        metrics: Metrics dictionary
        in_sample_start: In-sample start
        in_sample_end: In-sample end
        out_sample_start: Out-of-sample start
        out_sample_end: Out-of-sample end
        regime_label: Regime label
        issues: List of issues
        db_path: Database path
    
    Returns:
        Dictionary with run_id and summary
    """
    store = ExperimentStore(db_path)
    
    # Create run
    run = store.create_run(
        factor_id=factor_id,
        start_date=start_date,
        end_date=end_date,
        in_sample_start=in_sample_start,
        in_sample_end=in_sample_end,
        out_sample_start=out_sample_start,
        out_sample_end=out_sample_end,
        regime_label=regime_label,
        status="completed"
    )
    
    # Create metrics
    metric = store.create_metrics(run.id, metrics)
    
    # Create issues
    if issues:
        for issue in issues:
            store.create_issue(
                run_id=run.id,
                issue_type=issue.get('type', 'unknown'),
                detail=issue.get('detail', ''),
                severity=issue.get('severity', 'warning')
            )
    
    # Generate summary card
    summary = generate_summary_card(run, metric, issues or [])
    
    return {
        'run_id': run.id,
        'summary': summary
    }


def generate_summary_card(run, metric, issues: list) -> str:
    """Generate human-readable summary card.
    
    Args:
        run: Run object
        metric: Metric object
        issues: List of issues
    
    Returns:
        Summary card text
    """
    card = f"""# Run Summary: {run.id}

## Factor
- Factor ID: {run.factor_id}
- Date Range: {run.start_date.date()} to {run.end_date.date()}
- Regime: {run.regime_label or 'N/A'}

## Performance Metrics
- Sharpe Ratio: {metric.sharpe:.2f}
- Annual Return: {metric.ann_ret:.2%}
- Annual Volatility: {metric.ann_vol:.2%}
- Max Drawdown: {metric.maxdd:.2%}
- Avg IC: {metric.avg_ic:.4f}
- Information Ratio: {metric.ir:.2f}
- Turnover (monthly): {metric.turnover_monthly:.1f}%
- Hit Rate: {metric.hit_rate:.2%}

## Issues
"""
    
    if len(issues) == 0:
        card += "- No issues detected\n"
    else:
        for issue in issues:
            card += f"- **{issue.get('type', 'Unknown')}** ({issue.get('severity', 'warning')}): {issue.get('detail', '')}\n"
    
    return card

