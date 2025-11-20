"""Research hypothesis formation - first step in hedge fund factor research."""

from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from ..memory.store import ExperimentStore
from ..rag.retriever import HybridRetriever


class HypothesisStatus(Enum):
    """Status of research hypothesis."""
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    IN_TESTING = "in_testing"
    VALIDATED = "validated"
    DEPLOYED = "deployed"


@dataclass
class ResearchHypothesis:
    """Research hypothesis for factor discovery.
    
    Represents the initial research idea before implementation.
    """
    title: str
    description: str
    motivation: str  # Why this factor might work
    theoretical_basis: str  # Academic/empirical support
    expected_behavior: str  # What we expect to see
    risk_factors: List[str]  # Potential risks
    related_factors: List[str]  # Similar factors to compare
    universe: str  # Target universe
    frequency: str  # Trading frequency
    status: HypothesisStatus = HypothesisStatus.DRAFT
    created_by: Optional[str] = None
    created_at: datetime = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialize timestamps."""
        if self.created_at is None:
            self.created_at = datetime.now()


class HypothesisManager:
    """Manage research hypotheses."""
    
    def __init__(self, store: ExperimentStore, retriever: HybridRetriever):
        """Initialize hypothesis manager.
        
        Args:
            store: Experiment store for persistence
            retriever: RAG retriever for knowledge search
        """
        self.store = store
        self.retriever = retriever
    
    def form_hypothesis(
        self,
        title: str,
        description: str,
        motivation: str,
        universe: str = "sp500"
    ) -> ResearchHypothesis:
        """Form a new research hypothesis.
        
        Args:
            title: Hypothesis title
            description: Detailed description
            motivation: Why this factor might work
            universe: Target universe
        
        Returns:
            Research hypothesis
        """
        # Search knowledge base for related research
        # PRIORITIZE momentum-related research
        query = f"{title} {description}"
        if "momentum" not in query.lower():
            # Enhance query to include momentum if not already present
            query = f"{query} momentum factor"
        
        related_research = self.retriever.search(
            query=query,
            n_results=5
        )
        
        # Also search specifically for momentum factors (they are critical)
        momentum_research = self.retriever.search(
            query="momentum factor time series momentum TSMOM",
            n_results=3
        )
        related_research = momentum_research + related_research
        
        # Extract theoretical basis from research
        theoretical_basis = "\n".join([
            r.get('text', '')[:200] for r in related_research
        ])
        
        hypothesis = ResearchHypothesis(
            title=title,
            description=description,
            motivation=motivation,
            theoretical_basis=theoretical_basis,
            expected_behavior="To be determined through backtesting",
            risk_factors=["Data quality", "Lookahead bias", "Overfitting"],
            related_factors=[],
            universe=universe,
            frequency="D"
        )
        
        return hypothesis
    
    def review_hypothesis(
        self,
        hypothesis: ResearchHypothesis,
        reviewer: str,
        approved: bool,
        comments: str = ""
    ) -> ResearchHypothesis:
        """Review and approve/reject hypothesis.
        
        Args:
            hypothesis: Hypothesis to review
            reviewer: Name of reviewer
            approved: Whether hypothesis is approved
            comments: Review comments
        
        Returns:
            Updated hypothesis
        """
        hypothesis.reviewed_by = reviewer
        hypothesis.reviewed_at = datetime.now()
        
        if approved:
            hypothesis.status = HypothesisStatus.APPROVED
        else:
            hypothesis.status = HypothesisStatus.REJECTED
        
        return hypothesis
    
    def get_hypothesis_summary(self, hypothesis: ResearchHypothesis) -> Dict[str, Any]:
        """Get summary of hypothesis for reporting.
        
        Args:
            hypothesis: Hypothesis to summarize
        
        Returns:
            Summary dictionary
        """
        return {
            'title': hypothesis.title,
            'status': hypothesis.status.value,
            'universe': hypothesis.universe,
            'created_at': hypothesis.created_at.isoformat(),
            'reviewed_at': hypothesis.reviewed_at.isoformat() if hypothesis.reviewed_at else None,
            'risk_factors': hypothesis.risk_factors
        }

