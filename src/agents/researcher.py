"""Researcher agent: proposes Factor DSL specs using RAG-seeded ideation."""

from typing import List, Dict, Any, Optional
from langchain.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

from ..tools.rag_search import rag_search
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
        """Initialize researcher agent.
        
        Args:
            model_name: Ollama model name
            db_path: Database path
            index_path: RAG index path
        """
        self.llm = Ollama(model=model_name, temperature=0.7)
        self.store = ExperimentStore(db_path)
        self.lesson_manager = LessonManager(self.store)
        self.index_path = index_path
        
        # Prompt template for factor proposal
        self.proposal_prompt = PromptTemplate(
            input_variables=["context", "success_examples", "error_examples", "requirements"],
            template="""You are a quantitative researcher designing factor strategies for US large-cap equities.

## Context
{context}

## Successful Factor Patterns (from knowledge base)
{success_examples}

## Common Pitfalls to Avoid (error bank)
{error_examples}

## Requirements
{requirements}

## Task
Design 3 Factor DSL YAML specifications that:
1. Focus on momentum/volatility factors
2. Avoid lookahead (use RET_LAG with lag >= 1)
3. Include proper normalization (zscore_252, zscore_63, etc.)
4. Specify validation constraints and targets
5. Are simple, leak-free transforms

Output each factor as a complete YAML block following this structure:

```yaml
name: "FactorName_Description"
universe: "sp500"
frequency: "D"
signals:
  - id: "signal_id"
    expr: "RET_LAG(1,252) - RET_LAG(1,21)"
    normalize: "zscore_252"
portfolio:
  scheme: "long_short_deciles"
  weight: "equal"
  notional: 1.0
validation:
  min_history_days: 800
  purge_gap_days: 21
  max_turnover_monthly: 250.0
targets:
  min_sharpe: 1.0
  max_maxdd: 0.35
  min_avg_ic: 0.05
```

Provide 3 complete YAML factor specifications.
"""
        )
    
    def propose_factors(
        self,
        n_factors: int = 3,
        focus_topics: Optional[List[str]] = None,
        regime: Optional[str] = None,
        requirements: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Propose new factor designs.
        
        Args:
            n_factors: Number of factors to propose
            focus_topics: Topics to focus on (e.g., ["momentum", "volatility"])
            regime: Regime context (e.g., "high_vol")
            requirements: Additional requirements string
        
        Returns:
            List of factor proposals (YAML strings)
        """
        # Gather context from RAG
        context_queries = []
        if focus_topics:
            context_queries.extend([f"{topic} factor design" for topic in focus_topics])
        else:
            context_queries.append("momentum volatility factor design")
        
        # Search knowledge base
        context_results = []
        for query in context_queries:
            results = rag_search(query, n_results=3, regime=regime, index_path=self.index_path)
            context_results.extend(results.get('results', []))
        
        context_text = "\n".join([r['text'] for r in context_results[:5]])
        
        # Get success examples
        success_lessons = self.lesson_manager.get_success_ledger(limit=3)
        success_examples = "\n".join([lesson.body[:500] for lesson in success_lessons])
        
        # Get error examples
        error_lessons = self.lesson_manager.get_error_bank(limit=3)
        error_examples = "\n".join([lesson.body[:500] for lesson in error_lessons])
        
        # Build requirements
        req_text = requirements or """
- Target: Sharpe >= 1.0, MaxDD <= 35%, Avg IC >= 0.05
- Universe: US large-cap (S&P 500)
- Frequency: Daily
- Avoid lookahead, ensure sufficient sample size
"""
        
        # Generate proposals
        chain = LLMChain(llm=self.llm, prompt=self.proposal_prompt)
        
        response = chain.run(
            context=context_text,
            success_examples=success_examples,
            error_examples=error_examples,
            requirements=req_text
        )
        
        # Parse YAML blocks from response
        factors = self._extract_yaml_blocks(response)
        
        return factors[:n_factors]
    
    def propose_mutations(
        self,
        base_factor_yaml: str,
        n_mutations: int = 3
    ) -> List[str]:
        """Propose mutations of an existing factor.
        
        Args:
            base_factor_yaml: Base factor YAML
            n_mutations: Number of mutations to propose
        
        Returns:
            List of mutated factor YAML strings
        """
        mutation_prompt = PromptTemplate(
            input_variables=["base_factor"],
            template="""Given this factor specification, propose {n_mutations} mutations that:
1. Vary parameters (e.g., lag periods, windows)
2. Try different normalization methods
3. Combine with complementary signals
4. Maintain the core logic but explore variations

Base factor:
```yaml
{base_factor}
```

Provide {n_mutations} mutated YAML specifications, each as a complete YAML block.
"""
        )
        
        chain = LLMChain(llm=self.llm, prompt=mutation_prompt)
        response = chain.run(base_factor=base_factor_yaml, n_mutations=n_mutations)
        
        return self._extract_yaml_blocks(response)[:n_mutations]
    
    def _extract_yaml_blocks(self, text: str) -> List[str]:
        """Extract YAML blocks from LLM response.
        
        Args:
            text: Response text
        
        Returns:
            List of YAML strings
        """
        import re
        
        # Find YAML blocks
        yaml_pattern = r'```yaml\s*(.*?)\s*```'
        matches = re.findall(yaml_pattern, text, re.DOTALL)
        
        if not matches:
            # Try without yaml marker
            yaml_pattern = r'```\s*(.*?)\s*```'
            matches = re.findall(yaml_pattern, text, re.DOTALL)
        
        return matches

