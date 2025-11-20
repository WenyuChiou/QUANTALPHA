"""Example: Using the hedge fund research workflow."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.research.research_workflow import ResearchWorkflow
from src.memory.store import ExperimentStore
from src.rag.retriever import HybridRetriever


def main():
    """Example research workflow."""
    
    # Initialize components
    store = ExperimentStore("experiments.db")
    retriever = HybridRetriever(index_path="./kb.index")
    
    # Create research workflow
    workflow = ResearchWorkflow(
        store=store,
        retriever=retriever
    )
    
    # Run complete research workflow
    results = workflow.run_complete_workflow(
        title="Momentum Factor with Volatility Scaling",
        description="""
        A momentum factor that uses past 12-month returns (excluding most recent month)
        scaled by realized volatility to target constant risk exposure.
        
        This factor is based on the Time Series Momentum literature (Moskowitz et al., 2012)
        and addresses the issue of varying risk exposure in traditional momentum strategies.
        """,
        motivation="""
        Traditional momentum factors suffer from varying risk exposure over time.
        By scaling positions by realized volatility, we can maintain more consistent
        risk-adjusted returns and improve Sharpe ratios.
        
        Empirical evidence suggests momentum effects persist across asset classes
        and time periods, making this a robust factor candidate.
        """,
        universe="sp500",
        reviewer="Senior Researcher",
        auto_approve=False  # Set to True to skip peer review
    )
    
    print("\n" + "="*70)
    print("RESEARCH WORKFLOW RESULTS")
    print("="*70)
    
    if 'hypothesis' in results:
        print(f"\nHypothesis: {results['hypothesis'].title}")
        print(f"Status: {results['hypothesis'].status.value}")
    
    if 'design' in results:
        print(f"\nFactor Design: {results['design'].name}")
    
    if 'analysis' in results:
        analysis = results['analysis']
        print(f"\nPerformance Summary:")
        print(f"  Sharpe Ratio: {analysis.sharpe_ratio:.2f}")
        print(f"  Max Drawdown: {analysis.max_drawdown:.2%}")
        print(f"  Information Coefficient: {analysis.information_coefficient:.4f}")
    
    if 'documentation' in results:
        print(f"\nDocumentation Status: {results['documentation']['status']}")


if __name__ == "__main__":
    main()

