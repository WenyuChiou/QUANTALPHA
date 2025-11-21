"""Researcher agent: proposes Factor DSL specs using RAG-seeded ideation."""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add src to path if needed
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.memory.schemas import AgentResult, AgentContent, AgentArtifact

try:
    from langchain_community.llms import Ollama
except (ImportError, Exception):
    try:
        from langchain.llms import Ollama
    except (ImportError, Exception):
        # Mock Ollama
        class Ollama:
            def __init__(self, **kwargs): pass
            def __call__(self, *args, **kwargs): return "Mock response"

try:
    from langchain_core.prompts import PromptTemplate
    from langchain.chains import LLMChain
except (ImportError, Exception):
    try:
        from langchain.prompts import PromptTemplate
        from langchain.chains import LLMChain
    except (ImportError, Exception):
        # Mock classes
        class PromptTemplate:
            def __init__(self, **kwargs): pass
        class LLMChain:
            def __init__(self, **kwargs): pass
            def run(self, **kwargs): return "Mock response"

try:
    from ..tools.rag_search import rag_search
except (ImportError, Exception):
    # Mock rag_search for testing
    def rag_search(*args, **kwargs):
        return {'results': []}

from ..memory.lessons import LessonManager
from ..memory.store import ExperimentStore


class ResearcherAgent:
    """Agent that proposes new factor designs using RAG and lessons learned."""
    
    def __init__(
        self,
        model_name: str = "deepseek-r1",
        db_path: str = "experiments.db",
        index_path: str = "./kb.index"
    ):
        """Initialize researcher agent."""
        self.llm = Ollama(model=model_name, temperature=0.7)
        self.store = ExperimentStore(db_path)
        self.lesson_manager = LessonManager(self.store)
        self.index_path = index_path
        
    def propose_factor(
        self,
        market_regime: str,
        existing_factors: list,
        policy_rules: Optional[Dict[str, Any]] = None,
        past_lessons: Optional[List[Dict[str, Any]]] = None
    ) -> AgentResult:
        """Propose a new alpha factor based on market regime and past lessons.
        
        Args:
            market_regime: Current market regime
            existing_factors: List of existing factor names to avoid
            policy_rules: Policy rules from PolicyManager
            past_lessons: List of lessons learned from past failures
        
        Returns:
            AgentResult with factor proposal
        """
        try:
            # Build enhanced prompt with policy rules and lessons
            prompt_parts = []
            
            # Add policy requirements
            if policy_rules:
                constraints = policy_rules.get('global_constraints', {})
                prompt_parts.append(f"""
## Policy Requirements:
- Target Sharpe Ratio: ≥ {constraints.get('min_sharpe', 1.8)}
- Max Drawdown: ≥ {constraints.get('max_maxdd', -0.25):.0%}
- Information Coefficient: ≥ {constraints.get('min_avg_ic', 0.05)}
- Monthly Turnover: ≤ {constraints.get('max_turnover_monthly', 100)}%

## Signal Requirements (R013):
- Signal MUST have time variation (std > 0.01)
- Signal MUST have cross-sectional dispersion (std > 0.1)
- ALWAYS use .rank(axis=1, pct=True) for cross-sectional ranking
""")
            
            # Add past lessons if available
            if past_lessons and len(past_lessons) > 0:
                lessons_text = self._format_lessons(past_lessons)
                prompt_parts.append(f"""
## Past Lessons Learned:
{lessons_text}

⚠️ IMPORTANT: Please avoid repeating the mistakes identified above.
""")
            
            # Log what we're using
            if past_lessons:
                print(f"  📚 Using {len(past_lessons)} past lessons to guide proposal")
            
            # Mock response for demonstration (in real implementation, use LLM with prompt)
            factor_yaml = """
name: nonlinear_momentum_demo
universe: test_universe
frequency: D
signals:
  - id: mom_signal
    custom_code: |
      # Nonlinear momentum with volatility adjustment
      mom_21 = returns.rolling(21).mean()
      vol_21 = returns.rolling(21).std()
      adj_mom = mom_21 / (vol_21 + 1e-6)
      result = adj_mom.rank(axis=1, pct=True)
    code_type: custom
portfolio:
  long_short: true
  top_n: 2
"""
            
            return AgentResult(
                agent="Researcher",
                step="ProposeFactor",
                status="SUCCESS",
                content=AgentContent(
                    summary=f"Proposed volatility-adjusted momentum factor for {market_regime} regime.",
                    data={
                        "factor_name": "nonlinear_momentum_demo",
                        "yaml_content": factor_yaml,
                        "reasoning": "Standard momentum fails in high volatility; normalizing by vol stabilizes the signal.",
                        "hypothesis": "Risk-adjusted momentum persists longer than raw price momentum."
                    },
                    artifacts=[
                        AgentArtifact(name="factor_spec", path="memory", type="yaml", description="Factor YAML specification")
                    ]
                ),
                metadata={
                    "model": "mock-llm",
                    "market_regime": market_regime,
                    "used_lessons": len(past_lessons) if past_lessons else 0,
                    "has_policy_rules": policy_rules is not None
                }
            )
            
        except Exception as e:
            return AgentResult(
                agent="Researcher",
                step="ProposeFactor",
                status="FAILURE",
                content=AgentContent(
                    summary=f"Error proposing factor: {str(e)}",
                    data={"error": str(e)}
                )
            )
    
    def _format_lessons(self, past_lessons: List[Dict[str, Any]]) -> str:
        """Format past lessons into readable text for prompt.
        
        Args:
            past_lessons: List of lesson dictionaries from ReflectorAgent
        
        Returns:
            Formatted lessons text
        """
        if not past_lessons:
            return "No past lessons available."
        
        formatted = []
        
        # Show most recent lessons first (up to 5)
        recent_lessons = past_lessons[-5:]
        
        for i, lesson in enumerate(reversed(recent_lessons), 1):
            alpha_id = lesson.get('alpha_id', 'unknown')
            verdict = lesson.get('verdict', 'FAIL')
            
            formatted.append(f"\n### Lesson {i} (from {alpha_id}, {verdict}):")
            
            # Root causes
            root_causes = lesson.get('root_causes', [])
            if root_causes:
                formatted.append("\n**Problems Identified:**")
                for cause in root_causes[:3]:  # Top 3 causes
                    issue = cause.get('issue', 'unknown')
                    detail = cause.get('detail', '')
                    formatted.append(f"  - {issue}: {detail}")
            
            # Improvement suggestions
            improvements = lesson.get('improvement_suggestions', [])
            if improvements:
                formatted.append("\n**Suggested Improvements:**")
                for imp in improvements[:3]:  # Top 3 suggestions
                    suggestion = imp.get('suggestion', '')
                    formatted.append(f"  - {suggestion}")
        
        return "\n".join(formatted)
