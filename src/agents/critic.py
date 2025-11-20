"""Critic agent: validates runs, detects issues, writes failure/success cards."""

from typing import Dict, Any, List, Optional
from langchain.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

from ..memory.lessons import LessonManager
from ..memory.store import ExperimentStore
from ..tools.write_lesson import write_lesson


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
        
        self.critique_prompt = PromptTemplate(
            input_variables=["metrics", "issues", "factor_yaml"],
            template="""You are a quantitative research critic evaluating a factor backtest.

## Factor Specification
```yaml
{factor_yaml}
```

## Performance Metrics
{metrics}

## Validation Issues
{issues}

## Task
Analyze this run and determine:
1. Did it pass validation? (yes/no)
2. What are the key strengths/weaknesses?
3. What are the root causes of any failures?
4. What lessons can be learned?

Provide a structured critique.
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

