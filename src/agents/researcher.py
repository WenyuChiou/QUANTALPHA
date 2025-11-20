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

## CRITICAL PRIORITY: MOMENTUM FACTORS
**MOMENTUM FACTORS ARE EXTREMELY IMPORTANT AND SHOULD BE GIVEN HIGHEST PRIORITY.**

Momentum factors have shown:
- Strong empirical evidence across decades of research
- Robust performance across different market regimes
- High Sharpe ratios (typically 1.0-2.0, **must achieve >= 1.8 to pass**)
- Persistent predictive power (IC typically 0.05-0.10)
- Well-documented academic support (Jegadeesh & Titman, Moskowitz et al.)
- **CRITICAL**: Must achieve Sharpe >= 1.8 and MaxDD <= -25% to be acceptable

**ALWAYS PRIORITIZE MOMENTUM-BASED FACTORS** such as:
- Time Series Momentum (TSMOM): RET_LAG(1,252) - RET_LAG(1,21)
- Cross-sectional momentum: Ranking past returns
- Volatility-scaled momentum: Momentum scaled by realized volatility
- Industry-neutralized momentum: Momentum after removing industry effects

## Context
{context}

## Successful Factor Patterns (from knowledge base)
{success_examples}

## Common Pitfalls to Avoid (error bank)
{error_examples}

## Requirements
{requirements}

## METRICS REQUIREMENTS (CRITICAL)
**ALL FACTORS MUST MEET THESE PERFORMANCE TARGETS:**

### Required Performance Metrics:
1. **Sharpe Ratio**: Minimum 1.8 (target: 2.0+ for momentum factors)
   - Momentum factors typically achieve 1.0-2.0 Sharpe
   - **CRITICAL**: Below 1.8 is considered insufficient
   - Target 2.0+ for production-ready momentum factors

2. **Maximum Drawdown**: Maximum -25% (target: -20% or better)
   - **CRITICAL**: Drawdowns above -25% are unacceptable
   - Momentum factors must maintain drawdowns below -25%
   - Target -20% or better for production use

3. **Information Coefficient (IC)**: Minimum 0.05 (target: 0.06+ for momentum)
   - IC below 0.05 indicates weak predictive power
   - Momentum factors typically show IC of 0.05-0.10

4. **Information Ratio (IR)**: Minimum 0.5 (target: 0.6+)
   - IR measures risk-adjusted IC
   - Below 0.5 indicates poor risk-adjusted performance

5. **Hit Rate**: Minimum 52% (target: 54%+)
   - Percentage of periods with positive IC
   - Below 52% indicates inconsistent performance

6. **Turnover**: Maximum 250% monthly (target: <200%)
   - High turnover increases transaction costs
   - Momentum factors should aim for 30-60% monthly turnover

### Additional Quality Metrics:
- **Stability**: Rolling Sharpe should not drop more than 50% from peak
- **Regime Robustness**: Must perform in at least 3 out of 4 regimes (high_vol, low_vol, bull, bear)
- **IC Stability**: IC should not drop below 0.03 in any rolling period
- **Sample Size**: Minimum 800 days of history required

## Task
Design 3 Factor DSL YAML specifications that:
1. **PRIORITIZE MOMENTUM FACTORS** - At least 2 out of 3 should be momentum-based
2. **MEET ALL METRICS REQUIREMENTS** - Ensure targets section specifies all required metrics
3. Focus on momentum/volatility factors (momentum is most important)
4. Avoid lookahead (use RET_LAG with lag >= 1)
5. Include proper normalization (zscore_252, zscore_63, etc.)
6. Specify validation constraints and targets (must include all metrics above)
7. Are simple, leak-free transforms
8. Consider volatility scaling for momentum factors (VOL_TARGET)

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
  min_sharpe: 1.8          # Required: Minimum Sharpe ratio (1.8)
  max_maxdd: 0.25          # Required: Maximum drawdown (-25%)
  min_avg_ic: 0.05         # Required: Minimum average IC
  min_ir: 0.5              # Required: Minimum Information Ratio
  min_hit_rate: 0.52       # Required: Minimum hit rate (52%)
  max_turnover_monthly: 250.0  # Required: Maximum monthly turnover (250%)
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
        # ALWAYS prioritize momentum factors in search
        context_queries = []
        if focus_topics:
            # Ensure momentum is included if not already present
            if "momentum" not in [t.lower() for t in focus_topics]:
                context_queries.append("momentum factor design time series momentum")
            context_queries.extend([f"{topic} factor design" for topic in focus_topics])
        else:
            # Default: prioritize momentum
            context_queries.append("momentum factor design time series momentum TSMOM")
            context_queries.append("volatility scaled momentum factor")
            context_queries.append("cross-sectional momentum factor")
        
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
- **PRIORITY: MOMENTUM FACTORS ARE CRITICAL** - Prioritize momentum-based designs
- **METRICS REQUIREMENTS (MUST MEET ALL)**:
  * Sharpe Ratio: >= 1.8 (target: 2.0+ for momentum) - **CRITICAL: Must be >= 1.8**
  * Max Drawdown: <= -25% (target: -20% or better) - **CRITICAL: Must be <= -25%**
  * Average IC: >= 0.05 (target: 0.06+ for momentum)
  * Information Ratio: >= 0.5 (target: 0.6+)
  * Hit Rate: >= 52% (target: 54%+)
  * Monthly Turnover: <= 250% (target: <200%)
- Universe: US large-cap (S&P 500)
- Frequency: Daily
- Avoid lookahead, ensure sufficient sample size (min 800 days)
- Momentum factors typically use: RET_LAG(1,252) for 12-month momentum, RET_LAG(1,21) to skip recent month
- Consider volatility scaling: VOL_TARGET(ann_vol=0.15) for momentum factors
- All factors must pass stability and regime robustness checks
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

