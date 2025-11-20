"""Functions for writing and reading lessons learned."""

from typing import List, Optional, Dict, Any
from datetime import datetime

from .store import ExperimentStore, Lesson, Run


class LessonManager:
    """Manages lessons learned from runs."""
    
    def __init__(self, store: ExperimentStore):
        self.store = store
    
    def write_failure_card(
        self,
        run_id: int,
        root_cause: str,
        traces: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> Lesson:
        """Write a failure card from a failed run."""
        run = self.store.get_session().query(Run).filter(Run.id == run_id).first()
        if not run:
            raise ValueError(f"Run {run_id} not found")
        
        factor = self.store.get_factor(run.factor_id)
        title = f"Failure: {factor.name if factor else 'Unknown Factor'}"
        
        body = f"""## Root Cause
{root_cause}

## Run Details
- Run ID: {run_id}
- Factor ID: {run.factor_id}
- Date Range: {run.start_date} to {run.end_date}
- Regime: {run.regime_label or 'N/A'}

## Traces
{self._format_traces(traces or {})}

## Recommendations
- Avoid similar patterns in future factor designs
- Check for common pitfalls: lookahead, insufficient sample size, overfitting
"""
        
        tags = (tags or []) + ["failure", "error"]
        if run.regime_label:
            tags.append(f"regime_{run.regime_label}")
        
        return self.store.create_lesson(
            title=title,
            body=body,
            tags=tags,
            source_run_id=run_id,
            lesson_type="failure",
            metadata={"traces": traces or {}}
        )
    
    def write_success_card(
        self,
        run_id: int,
        key_params: Dict[str, Any],
        where_it_shines: str,
        where_it_fails: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Lesson:
        """Write a success card from a successful run."""
        run = self.store.get_session().query(Run).filter(Run.id == run_id).first()
        if not run:
            raise ValueError(f"Run {run_id} not found")
        
        factor = self.store.get_factor(run.factor_id)
        title = f"Success: {factor.name if factor else 'Unknown Factor'}"
        
        body = f"""## Key Parameters
{self._format_dict(key_params)}

## Performance Highlights
- Run ID: {run_id}
- Factor ID: {run.factor_id}
- Date Range: {run.start_date} to {run.end_date}
- Regime: {run.regime_label or 'N/A'}

## Where It Shines
{where_it_shines}

## Limitations
{where_it_fails or 'None identified'}

## Recommended Mutations
- Parameter sweeps around successful values
- Structural variations maintaining core logic
- Ensemble combinations with complementary factors
"""
        
        tags = (tags or []) + ["success", "passed"]
        if run.regime_label:
            tags.append(f"regime_{run.regime_label}")
        
        return self.store.create_lesson(
            title=title,
            body=body,
            tags=tags,
            source_run_id=run_id,
            lesson_type="success",
            metadata={"key_params": key_params}
        )
    
    def get_lessons_by_tags(self, tags: List[str], limit: int = 10) -> List[Lesson]:
        """Get lessons matching specific tags."""
        session = self.store.get_session()
        try:
            # Simple tag matching (can be improved with proper JSON queries)
            all_lessons = session.query(Lesson).all()
            matching = []
            for lesson in all_lessons:
                if lesson.tags and any(tag in lesson.tags for tag in tags):
                    matching.append(lesson)
            return matching[:limit]
        finally:
            session.close()
    
    def get_error_bank(self, limit: int = 50) -> List[Lesson]:
        """Get all failure lessons (error bank)."""
        session = self.store.get_session()
        try:
            return session.query(Lesson).filter(
                Lesson.lesson_type == "failure"
            ).order_by(Lesson.created_at.desc()).limit(limit).all()
        finally:
            session.close()
    
    def get_success_ledger(self, limit: int = 50) -> List[Lesson]:
        """Get all success lessons (success ledger)."""
        session = self.store.get_session()
        try:
            return session.query(Lesson).filter(
                Lesson.lesson_type == "success"
            ).order_by(Lesson.created_at.desc()).limit(limit).all()
        finally:
            session.close()
    
    def _format_traces(self, traces: Dict[str, Any]) -> str:
        """Format traces dictionary for display."""
        if not traces:
            return "No traces available."
        return "\n".join(f"- **{k}**: {v}" for k, v in traces.items())
    
    def _format_dict(self, d: Dict[str, Any]) -> str:
        """Format dictionary for display."""
        return "\n".join(f"- **{k}**: {v}" for k, v in d.items())

