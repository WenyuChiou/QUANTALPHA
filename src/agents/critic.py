"""Critic agent: validates runs, detects issues, writes failure/success cards."""

from typing import Dict, Any, List, Optional
from langchain.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

from ..memory.lessons import LessonManager
from ..memory.store import ExperimentStore
from ..tools.write_lesson import write_lesson
from ..analysis.guidelines import get_analysis_guidelines


class CriticAgent:
    """Agent that validates runs and writes lessons."""
    
    def __init__(
        self,
        model_name: str = "deepseek-r1",
        db_path: str = "experiments.db"
    ):
        """Initialize critic agent.
        
        Args:
            model_name: Ollama model name
            db_path: Database path
        """
        self.llm = Ollama(model=model_name, temperature=0.3)
        self.store = ExperimentStore(db_path)
        self.lesson_manager = LessonManager(self.store)
        self.guidelines = get_analysis_guidelines()
        
        self.critique_prompt = PromptTemplate(
            input_variables=["metrics", "issues", "factor_yaml"],
            template="""You are a quantitative research critic evaluating a factor backtest.

## IMPORTANT CONTEXT: MOMENTUM FACTORS
**MOMENTUM FACTORS ARE EXTREMELY IMPORTANT** in quantitative finance. When evaluating factors:
- Momentum factors have strong empirical support and should be given special consideration
- If this is a momentum factor, be aware that momentum typically shows:
  * Sharpe ratios of 1.0-2.0 are common, but **must be >= 1.8 to pass**
  * IC values of 0.05-0.10 are typical and acceptable
  * Drawdown must be <= -25% to pass (target: -20% or better)
- Momentum factors are among the most robust and well-documented factors in academic literature
- Pay special attention to momentum factors - they are critical for portfolio construction

## Factor Specification
```yaml
{factor_yaml}
```

## Performance Metrics
{metrics}

## Validation Issues
{issues}

## ANALYSIS GUIDELINES (MUST FOLLOW)

**Follow these comprehensive analysis guidelines:**

### Performance Metrics (CRITICAL):
1. **Sharpe Ratio**: Must be >= 1.8
   - Excellent: >= 2.5
   - Good: 2.0 - 2.5
   - Acceptable: 1.8 - 2.0
   - **FAIL**: < 1.8 → REJECT FACTOR

2. **Maximum Drawdown**: Must be >= -25%
   - Excellent: >= -15%
   - Good: -15% to -20%
   - Acceptable: -20% to -25%
   - **FAIL**: < -25% → REJECT FACTOR

3. **Information Coefficient (IC)**: Must be >= 0.05
   - Excellent: >= 0.08
   - Good: 0.06 - 0.08
   - Acceptable: 0.05 - 0.06
   - **WARNING**: < 0.05 (weak predictive power)

4. **Information Ratio (IR)**: Must be >= 0.5
   - Excellent: >= 0.8
   - Good: 0.6 - 0.8
   - Acceptable: 0.5 - 0.6
   - **WARNING**: < 0.5 (poor risk-adjusted performance)

5. **Hit Rate**: Must be >= 52%
   - Excellent: >= 56%
   - Good: 54% - 56%
   - Acceptable: 52% - 54%
   - **WARNING**: < 52% (inconsistent performance)

6. **Monthly Turnover**: Must be <= 250%
   - Excellent: <= 100%
   - Good: 100% - 150%
   - Acceptable: 150% - 250%
   - **WARNING**: > 250% (high transaction costs)

### Stability Analysis (REQUIRED):
- **Rolling Sharpe Stability**: Std should be < 50% of mean
- **IC Stability**: IC should not drop below 0.03 in any period
- **Sharpe Drawdown**: Rolling Sharpe should not drop >50% from peak

### Risk Analysis (REQUIRED):
- **VaR(95%)**: Should be >= -2%
- **Tail Ratio**: 95th/5th percentile ratio should be >= 1.0
- **Drawdown Analysis**: Maximum drawdown and recovery time

### Regime Robustness (REQUIRED):
- Must perform in at least 3 out of 4 regimes:
  - Bull market: Sharpe >= 0.5
  - Bear market: Sharpe >= 0.5
  - High volatility: Sharpe >= 0.5
  - Low volatility: Sharpe >= 0.5

### Decay Analysis (REQUIRED):
- **IC Decay Rate**: Should be < 50%
- **Performance Persistence**: Check if performance degrades over time
- **Complexity Assessment**: Factor complexity score

### Sample Quality (REQUIRED):
- **History**: Must have >= 800 days
- **Observations**: Must have >= 800 observations
- **Data Quality**: Check for missing data, outliers, etc.

## Task
Analyze this run and determine:
1. **Did it pass ALL metrics requirements?** Check each metric against requirements above
   - **CRITICAL**: Sharpe must be >= 1.8, MaxDD must be >= -25%
   - If either fails, the factor is REJECTED
2. **Is this a momentum factor?** If yes, evaluate with momentum-specific benchmarks
3. **Which metrics passed/failed?** List each metric and its status
   - Explicitly state: "Sharpe: PASS/FAIL (value vs 1.8 requirement)"
   - Explicitly state: "MaxDD: PASS/FAIL (value vs -25% requirement)"
4. What are the key strengths/weaknesses?
5. What are the root causes of any failures?
6. What lessons can be learned?
7. **For momentum factors**: Are the results consistent with momentum literature expectations?

**IMPORTANT**: Factors with Sharpe < 1.8 or MaxDD < -25% MUST be rejected.

Provide a structured critique with explicit evaluation of each metric requirement. If this is a momentum factor, note its importance and evaluate accordingly.
"""
        )
    
    def critique_run(
        self,
        run_id: int,
        metrics: Dict[str, Any],
        issues: List[Dict[str, Any]],
        factor_yaml: str
    ) -> Dict[str, Any]:
        """Critique a backtest run.
        
        Args:
            run_id: Run ID
            metrics: Performance metrics
            issues: Validation issues
            factor_yaml: Factor YAML
        
        Returns:
            Critique dictionary with recommendations
        """
        # Format metrics and issues
        metrics_str = "\n".join([f"- {k}: {v}" for k, v in metrics.items()])
        issues_str = "\n".join([f"- {i.get('type', 'Unknown')}: {i.get('detail', '')}" for i in issues]) if issues else "None"
        
        # Generate critique
        chain = LLMChain(llm=self.llm, prompt=self.critique_prompt)
        critique_text = chain.run(
            metrics=metrics_str,
            issues=issues_str,
            factor_yaml=factor_yaml
        )
        
        # Determine if passed
        critical_issues = [i for i in issues if i.get('severity') in ['error', 'critical']]
        passed = len(critical_issues) == 0
        
        # Write lesson
        if passed:
            # Success card
            lesson = self.lesson_manager.write_success_card(
                run_id=run_id,
                key_params=self._extract_key_params(factor_yaml),
                where_it_shines=self._extract_strengths(critique_text),
                where_it_fails=self._extract_weaknesses(critique_text),
                tags=["success", "passed"]
            )
        else:
            # Failure card
            root_cause = self._extract_root_cause(critique_text, issues)
            lesson = self.lesson_manager.write_failure_card(
                run_id=run_id,
                root_cause=root_cause,
                traces={"critique": critique_text},
                tags=["failure", "error"]
            )
        
        # Also write to vector index
        write_lesson(
            title=lesson.title,
            body=lesson.body,
            tags=lesson.tags,
            source_run_id=run_id,
            lesson_type=lesson.lesson_type
        )
        
        return {
            'passed': passed,
            'critique': critique_text,
            'lesson_id': lesson.id,
            'recommendations': self._extract_recommendations(critique_text)
        }
    
    def _extract_key_params(self, factor_yaml: str) -> Dict[str, Any]:
        """Extract key parameters from factor YAML."""
        # Simple extraction (could be improved)
        import re
        params = {}
        
        lag_matches = re.findall(r'RET_LAG\s*\(\s*(\d+)\s*,\s*(\d+)', factor_yaml)
        if lag_matches:
            params['lag'] = lag_matches[0][0]
            params['period'] = lag_matches[0][1]
        
        return params
    
    def _extract_strengths(self, critique: str) -> str:
        """Extract strengths from critique."""
        # Simple extraction
        if "strength" in critique.lower() or "strong" in critique.lower():
            return critique[:500]
        return "See critique for details"
    
    def _extract_weaknesses(self, critique: str) -> str:
        """Extract weaknesses from critique."""
        if "weakness" in critique.lower() or "weak" in critique.lower():
            return critique[:500]
        return "None identified"
    
    def _extract_root_cause(self, critique: str, issues: List[Dict[str, Any]]) -> str:
        """Extract root cause from critique and issues."""
        if issues:
            return issues[0].get('detail', 'Unknown')
        return critique[:300]
    
    def _extract_recommendations(self, critique: str) -> List[str]:
        """Extract recommendations from critique."""
        # Simple extraction
        recommendations = []
        if "recommend" in critique.lower():
            # Try to extract bullet points
            import re
            bullets = re.findall(r'[-*]\s*(.*)', critique)
            recommendations.extend(bullets[:5])
        return recommendations

