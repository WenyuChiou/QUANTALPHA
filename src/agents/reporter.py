"""Reporter agent: generates summaries, dashboard notes, iteration plans."""

from typing import Dict, Any, Optional, List
from datetime import datetime
from langchain.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

from ..memory.store import ExperimentStore


class ReporterAgent:
    """Agent that generates human-readable reports."""
    
    def __init__(self, model_name: str = "deepseek-r1", db_path: str = "experiments.db"):
        """Initialize reporter agent.
        
        Args:
            model_name: Ollama model name
            db_path: Database path
        """
        self.llm = Ollama(model=model_name, temperature=0.5)
        self.store = ExperimentStore(db_path)
        
        self.summary_prompt = PromptTemplate(
            input_variables=["run_data", "metrics", "issues"],
            template="""Generate a concise summary of this backtest run.

Run Data:
{run_data}

Metrics:
{metrics}

Issues:
{issues}

Provide a 2-3 paragraph summary highlighting key findings.
"""
        )
    
    def generate_run_summary(
        self,
        run_id: int
    ) -> str:
        """Generate summary for a run.
        
        Args:
            run_id: Run ID
        
        Returns:
            Summary text
        """
        session = self.store.get_session()
        try:
            run = session.query(self.store.Run).filter(self.store.Run.id == run_id).first()
            if not run:
                return f"Run {run_id} not found"
            
            factor = self.store.get_factor(run.factor_id)
            metrics = run.metrics[0] if run.metrics else None
            issues = [i.detail for i in run.issues]
            
            run_data = f"""
Factor: {factor.name if factor else 'Unknown'}
Date Range: {run.start_date} to {run.end_date}
Regime: {run.regime_label or 'N/A'}
"""
            
            metrics_str = ""
            if metrics:
                metrics_str = f"""
Sharpe: {metrics.sharpe:.2f}
MaxDD: {metrics.maxdd:.2%}
Avg IC: {metrics.avg_ic:.4f}
Turnover: {metrics.turnover_monthly:.1f}%
"""
            
            issues_str = "\n".join(issues) if issues else "None"
            
            chain = LLMChain(llm=self.llm, prompt=self.summary_prompt)
            summary = chain.run(
                run_data=run_data,
                metrics=metrics_str,
                issues=issues_str
            )
            
            return summary
        finally:
            session.close()
    
    def generate_dashboard_notes(self) -> Dict[str, Any]:
        """Generate notes for dashboard display.
        
        Returns:
            Dictionary with dashboard notes
        """
        top_runs = self.store.get_top_runs(limit=10, order_by="sharpe")
        failed_runs = self.store.get_failed_runs(limit=10)
        
        notes = {
            'top_performers': [
                {
                    'run_id': run.id,
                    'sharpe': run.metrics[0].sharpe if run.metrics else 0,
                    'factor_id': run.factor_id
                }
                for run in top_runs
            ],
            'recent_failures': [
                {
                    'run_id': run.id,
                    'issues': len(run.issues),
                    'factor_id': run.factor_id
                }
                for run in failed_runs
            ],
            'last_updated': datetime.now().isoformat()
        }
        
        return notes
    
    def generate_iteration_plan(
        self,
        successful_factors: List[Dict[str, Any]],
        failed_factors: List[Dict[str, Any]]
    ) -> str:
        """Generate plan for next iteration.
        
        Args:
            successful_factors: List of successful factor info
            failed_factors: List of failed factor info
        
        Returns:
            Iteration plan text
        """
        plan_prompt = PromptTemplate(
            input_variables=["successful", "failed"],
            template="""Based on these results, generate a plan for the next iteration.

Successful Factors:
{successful}

Failed Factors:
{failed}

Provide:
1. Recommended mutations to try
2. New directions to explore
3. Pitfalls to avoid
"""
        )
        
        successful_str = "\n".join([str(f) for f in successful_factors[:5]])
        failed_str = "\n".join([str(f) for f in failed_factors[:5]])
        
        chain = LLMChain(llm=self.llm, prompt=plan_prompt)
        plan = chain.run(successful=successful_str, failed=failed_str)
        
        return plan

