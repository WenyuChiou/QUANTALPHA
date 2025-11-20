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

## IMPORTANT: MOMENTUM FACTORS
**MOMENTUM FACTORS ARE EXTREMELY IMPORTANT** in quantitative finance. If this is a momentum factor:
- Highlight its importance and significance
- Compare results to momentum literature benchmarks (Sharpe 1.0-2.0, IC 0.05-0.10)
- Note that momentum factors are among the most robust factors documented
- Emphasize the value of momentum factors for portfolio construction

## METRICS REQUIREMENTS EVALUATION
**EVALUATE EACH METRIC AGAINST REQUIREMENTS:**
- Sharpe Ratio: Required >= 1.8 (excellent: >= 2.5, good: 2.0-2.5, acceptable: 1.8-2.0, FAIL: < 1.8)
- Max Drawdown: Required >= -25% (excellent: >= -15%, good: -15% to -20%, acceptable: -20% to -25%, FAIL: < -25%)
- Average IC: Required >= 0.05 (excellent: >= 0.08, good: 0.06-0.08, acceptable: 0.05-0.06, FAIL: < 0.05)
- Information Ratio: Required >= 0.5 (excellent: >= 0.8, good: 0.6-0.8, acceptable: 0.5-0.6, FAIL: < 0.5)
- Hit Rate: Required >= 52% (excellent: >= 56%, good: 54%-56%, acceptable: 52%-54%, FAIL: < 52%)
- Monthly Turnover: Required <= 250% (excellent: <= 100%, good: 100%-150%, acceptable: 150%-250%, FAIL: > 250%)

**MUST STATE WHETHER EACH METRIC PASSED OR FAILED**

Run Data:
{run_data}

Metrics:
{metrics}

Issues:
{issues}

Provide a 2-3 paragraph summary highlighting:
1. **Metrics evaluation**: Which metrics passed/failed requirements
2. **Performance assessment**: Overall performance relative to requirements
3. **Key findings**: Important insights from the backtest
4. **If momentum factor**: Emphasize its importance and significance
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

## CRITICAL PRIORITY: MOMENTUM FACTORS
**MOMENTUM FACTORS ARE EXTREMELY IMPORTANT** and should be prioritized:
- Momentum factors have strong empirical support and robust performance
- Always consider momentum-based designs first
- If successful factors include momentum, prioritize mutations of momentum factors
- If no momentum factors exist, strongly recommend exploring momentum factors

## METRICS REQUIREMENTS (MUST BE MET)
**ALL FACTORS MUST MEET THESE METRICS:**
- Sharpe Ratio: >= 1.8 (target: 2.0+) - **CRITICAL: Must be >= 1.8**
- Max Drawdown: <= -25% (target: -20% or better) - **CRITICAL: Must be <= -25%**
- Average IC: >= 0.05 (target: 0.06+)
- Information Ratio: >= 0.5 (target: 0.6+)
- Hit Rate: >= 52% (target: 54%+)
- Monthly Turnover: <= 250% (target: <200%)

When recommending mutations or new directions:
- Ensure they can meet all metrics requirements above
- Focus on factors that can achieve Sharpe >= 1.2
- Prioritize designs that maintain IC >= 0.06
- Consider turnover constraints in design

Successful Factors:
{successful}

Failed Factors:
{failed}

Provide:
1. **PRIORITIZE MOMENTUM**: Recommended momentum factor mutations to try (must meet metrics requirements)
2. New directions to explore (with emphasis on momentum if not already explored, must meet metrics)
3. Pitfalls to avoid (especially metrics failures)
4. **Metrics-focused improvements**: How to improve factors that failed metrics requirements
5. **Emphasize the importance of momentum factors** in the plan
"""
        )
        
        successful_str = "\n".join([str(f) for f in successful_factors[:5]])
        failed_str = "\n".join([str(f) for f in failed_factors[:5]])
        
        chain = LLMChain(llm=self.llm, prompt=plan_prompt)
        plan = chain.run(successful=successful_str, failed=failed_str)
        
        return plan

