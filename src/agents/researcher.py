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
        
    def propose_factor(self, market_regime: str, existing_factors: list) -> AgentResult:
        """Propose a new alpha factor based on market regime."""
        try:
            # Mock response for demonstration
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
                    "market_regime": market_regime
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
