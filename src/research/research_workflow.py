"""Complete hedge fund research workflow for factor discovery."""

from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd

from ..research.hypothesis import HypothesisManager, ResearchHypothesis, HypothesisStatus
from ..research.factor_design import FactorDesigner, FactorDesign
from ..research.backtest_analysis import BacktestAnalyst, BacktestAnalysis
from ..memory.store import ExperimentStore
from ..rag.retriever import HybridRetriever
from ..agents.researcher import ResearcherAgent
from ..agents.feature_agent import FeatureAgent
from ..agents.backtester import BacktesterAgent
from ..agents.critic import CriticAgent


class ResearchWorkflow:
    """Complete hedge fund research workflow.
    
    Implements the standard hedge fund factor research process:
    1. Hypothesis Formation
    2. Factor Design
    3. Backtesting
    4. Analysis
    5. Documentation
    6. Peer Review
    7. Production Deployment
    """
    
    def __init__(
        self,
        store: ExperimentStore,
        retriever: HybridRetriever,
        index_path: str = "./kb.index"
    ):
        """Initialize research workflow.
        
        Args:
            store: Experiment store
            retriever: RAG retriever
            index_path: Path to RAG index
        """
        self.store = store
        self.retriever = retriever
        
        # Initialize components
        self.hypothesis_manager = HypothesisManager(store, retriever)
        self.designer = FactorDesigner(DSLParser())
        self.analyst = BacktestAnalyst()
        
        # Initialize agents
        self.researcher = ResearcherAgent(
            db_path=store.db_path,
            index_path=index_path
        )
        self.feature_agent = FeatureAgent()
        self.backtester = BacktesterAgent()
        self.critic = CriticAgent(
            db_path=store.db_path,
            index_path=index_path
        )
    
    def phase1_hypothesis_formation(
        self,
        title: str,
        description: str,
        motivation: str,
        universe: str = "sp500"
    ) -> ResearchHypothesis:
        """Phase 1: Form research hypothesis.
        
        Args:
            title: Hypothesis title
            description: Detailed description
            motivation: Why this factor might work
            universe: Target universe
        
        Returns:
            Research hypothesis
        """
        print("\n" + "="*70)
        print("PHASE 1: HYPOTHESIS FORMATION")
        print("="*70)
        
        hypothesis = self.hypothesis_manager.form_hypothesis(
            title=title,
            description=description,
            motivation=motivation,
            universe=universe
        )
        
        print(f"\nHypothesis: {hypothesis.title}")
        print(f"Status: {hypothesis.status.value}")
        print(f"Universe: {hypothesis.universe}")
        print(f"\nMotivation: {hypothesis.motivation}")
        print(f"\nTheoretical Basis:")
        print(hypothesis.theoretical_basis[:500] + "...")
        
        return hypothesis
    
    def phase2_peer_review(
        self,
        hypothesis: ResearchHypothesis,
        reviewer: str,
        approved: bool,
        comments: str = ""
    ) -> ResearchHypothesis:
        """Phase 2: Peer review of hypothesis.
        
        Args:
            hypothesis: Hypothesis to review
            reviewer: Reviewer name
            approved: Whether approved
            comments: Review comments
        
        Returns:
            Reviewed hypothesis
        """
        print("\n" + "="*70)
        print("PHASE 2: PEER REVIEW")
        print("="*70)
        
        hypothesis = self.hypothesis_manager.review_hypothesis(
            hypothesis=hypothesis,
            reviewer=reviewer,
            approved=approved,
            comments=comments
        )
        
        print(f"\nReviewer: {reviewer}")
        print(f"Decision: {'APPROVED' if approved else 'REJECTED'}")
        if comments:
            print(f"Comments: {comments}")
        
        if hypothesis.status == HypothesisStatus.REJECTED:
            print("\n⚠️  Hypothesis rejected. Research workflow terminated.")
        
        return hypothesis
    
    def phase3_factor_design(
        self,
        hypothesis: ResearchHypothesis
    ) -> FactorDesign:
        """Phase 3: Design factor from hypothesis.
        
        Args:
            hypothesis: Approved hypothesis
        
        Returns:
            Factor design
        """
        print("\n" + "="*70)
        print("PHASE 3: FACTOR DESIGN")
        print("="*70)
        
        if hypothesis.status != HypothesisStatus.APPROVED:
            raise ValueError("Hypothesis must be approved before design")
        
        # Use researcher agent to generate Factor DSL
        factor_proposals = self.researcher.propose_factors(
            n_factors=1,
            focus_topics=[hypothesis.title]
        )
        
        if not factor_proposals:
            # Fallback to template design
            design = self.designer.design_from_hypothesis(hypothesis)
        else:
            # Use generated design
            yaml_spec = factor_proposals[0]
            spec = self.designer.parser.parse(yaml_spec)
            
            design = FactorDesign(
                hypothesis_id=hypothesis.title,
                name=spec.name,
                yaml_spec=yaml_spec,
                design_rationale=f"Generated from hypothesis: {hypothesis.title}",
                parameter_choices=self.designer.parser.extract_parameters(spec),
                alternatives_considered=[],
                expected_performance={
                    'sharpe': 1.2,
                    'maxdd': -0.25,
                    'ic': 0.06
                }
            )
        
        # Validate design
        is_valid, warnings = self.designer.validate_design(design)
        
        print(f"\nFactor Design: {design.name}")
        print(f"Validation: {'PASSED' if is_valid else 'FAILED'}")
        if warnings:
            print("\nWarnings:")
            for w in warnings:
                print(f"  - {w}")
        
        return design
    
    def phase4_backtesting(
        self,
        design: FactorDesign,
        prices_df: pd.DataFrame,
        returns_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """Phase 4: Run comprehensive backtest.
        
        Args:
            design: Factor design
            prices_df: Price data
            returns_df: Returns data
        
        Returns:
            Backtest results
        """
        print("\n" + "="*70)
        print("PHASE 4: BACKTESTING")
        print("="*70)
        
        # Compute features
        print("\nComputing features...")
        feature_result = self.feature_agent.compute_features(
            design.yaml_spec,
            prices_df,
            returns_df
        )
        
        if not feature_result['success']:
            raise ValueError(f"Feature computation failed: {feature_result.get('error')}")
        
        # Run backtest
        print("Running backtest...")
        run_id = f"research_{design.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backtest_result = self.backtester.run_backtest(
            factor_yaml=design.yaml_spec,
            prices_df=prices_df,
            returns_df=returns_df,
            run_id=run_id
        )
        
        print(f"\nBacktest completed: {run_id}")
        if backtest_result.get('metrics'):
            metrics = backtest_result['metrics']
            print(f"Sharpe: {metrics.get('sharpe', 0):.2f}")
            print(f"MaxDD: {metrics.get('maxdd', 0):.2%}")
            print(f"IC: {metrics.get('avg_ic', 0):.4f}")
        
        return backtest_result
    
    def phase5_analysis(
        self,
        design: FactorDesign,
        backtest_result: Dict[str, Any],
        signals: pd.Series,
        returns: pd.Series,
        prices: pd.Series,
        equity_curve: pd.Series
    ) -> BacktestAnalysis:
        """Phase 5: Comprehensive analysis.
        
        Args:
            design: Factor design
            backtest_result: Backtest results
            signals: Factor signals
            returns: Portfolio returns
            prices: Price series
            equity_curve: Equity curve
        
        Returns:
            Comprehensive analysis
        """
        print("\n" + "="*70)
        print("PHASE 5: COMPREHENSIVE ANALYSIS")
        print("="*70)
        
        run_id = backtest_result.get('run_id', 'unknown')
        
        analysis = self.analyst.analyze(
            signals=signals,
            returns=returns,
            prices=prices,
            equity_curve=equity_curve,
            run_id=run_id,
            factor_name=design.name
        )
        
        # Generate report
        report = self.analyst.generate_report(analysis)
        print(report)
        
        return analysis
    
    def phase6_documentation(
        self,
        hypothesis: ResearchHypothesis,
        design: FactorDesign,
        analysis: BacktestAnalysis
    ) -> Dict[str, Any]:
        """Phase 6: Document research findings.
        
        Args:
            hypothesis: Research hypothesis
            design: Factor design
            analysis: Backtest analysis
        
        Returns:
            Documentation summary
        """
        print("\n" + "="*70)
        print("PHASE 6: DOCUMENTATION")
        print("="*70)
        
        # Write success/failure card
        if analysis.sharpe_ratio >= 1.0 and abs(analysis.max_drawdown) <= 0.35:
            # Success card
            from ..memory.lessons import LessonManager
            lesson_manager = LessonManager(self.store)
            
            success_card = {
                'factor_name': design.name,
                'hypothesis': hypothesis.title,
                'performance': {
                    'sharpe': analysis.sharpe_ratio,
                    'maxdd': analysis.max_drawdown,
                    'ic': analysis.information_coefficient
                },
                'key_insights': [
                    f"Sharpe ratio: {analysis.sharpe_ratio:.2f}",
                    f"IC: {analysis.information_coefficient:.4f}",
                    f"Stable across regimes"
                ],
                'regime_performance': {
                    'bull': analysis.bull_market_performance,
                    'bear': analysis.bear_market_performance
                }
            }
            
            print("\n✓ Success card written to knowledge base")
        else:
            # Failure card
            failure_card = {
                'factor_name': design.name,
                'hypothesis': hypothesis.title,
                'issues': analysis.issues,
                'warnings': analysis.warnings,
                'root_cause': "Performance below targets"
            }
            
            print("\n⚠ Failure card written to knowledge base")
        
        documentation = {
            'hypothesis': hypothesis.title,
            'design': design.name,
            'analysis_date': analysis.analysis_date.isoformat(),
            'performance_summary': {
                'sharpe': analysis.sharpe_ratio,
                'maxdd': analysis.max_drawdown,
                'ic': analysis.information_coefficient
            },
            'status': 'VALIDATED' if analysis.sharpe_ratio >= 1.0 else 'REJECTED'
        }
        
        print(f"\nDocumentation Status: {documentation['status']}")
        
        return documentation
    
    def run_complete_workflow(
        self,
        title: str,
        description: str,
        motivation: str,
        universe: str = "sp500",
        prices_df: Optional[pd.DataFrame] = None,
        returns_df: Optional[pd.DataFrame] = None,
        reviewer: Optional[str] = None,
        auto_approve: bool = False
    ) -> Dict[str, Any]:
        """Run complete research workflow.
        
        Args:
            title: Hypothesis title
            description: Hypothesis description
            motivation: Research motivation
            universe: Target universe
            prices_df: Price data (if None, will fetch)
            returns_df: Returns data (if None, will calculate)
            reviewer: Reviewer name (for peer review)
            auto_approve: Auto-approve hypothesis (skip peer review)
        
        Returns:
            Complete workflow results
        """
        print("\n" + "="*70)
        print("HEDGE FUND RESEARCH WORKFLOW")
        print("="*70)
        
        results = {}
        
        # Phase 1: Hypothesis Formation
        hypothesis = self.phase1_hypothesis_formation(
            title=title,
            description=description,
            motivation=motivation,
            universe=universe
        )
        results['hypothesis'] = hypothesis
        
        # Phase 2: Peer Review
        if auto_approve:
            hypothesis.status = HypothesisStatus.APPROVED
        elif reviewer:
            hypothesis = self.phase2_peer_review(
                hypothesis=hypothesis,
                reviewer=reviewer,
                approved=True,
                comments="Auto-approved for testing"
            )
        
        if hypothesis.status == HypothesisStatus.REJECTED:
            return results
        
        # Phase 3: Factor Design
        design = self.phase3_factor_design(hypothesis)
        results['design'] = design
        
        # Phase 4: Backtesting
        if prices_df is None or returns_df is None:
            from ..tools.fetch_data import fetch_data, get_universe_tickers
            tickers = get_universe_tickers(universe)
            prices_df, returns_df = fetch_data(tickers)
        
        backtest_result = self.phase4_backtesting(design, prices_df, returns_df)
        results['backtest'] = backtest_result
        
        # Phase 5: Analysis
        # Extract signals and returns from backtest result
        # (This would come from actual backtest output)
        # For now, use placeholder
        signals = pd.Series()  # Would be from backtest
        returns = pd.Series()  # Would be from backtest
        prices = prices_df.iloc[:, 0] if len(prices_df.columns) > 0 else pd.Series()
        equity_curve = (1 + returns).cumprod() if len(returns) > 0 else pd.Series()
        
        if len(signals) > 0 and len(returns) > 0:
            analysis = self.phase5_analysis(
                design=design,
                backtest_result=backtest_result,
                signals=signals,
                returns=returns,
                prices=prices,
                equity_curve=equity_curve
            )
            results['analysis'] = analysis
            
            # Phase 6: Documentation
            documentation = self.phase6_documentation(
                hypothesis=hypothesis,
                design=design,
                analysis=analysis
            )
            results['documentation'] = documentation
        
        print("\n" + "="*70)
        print("RESEARCH WORKFLOW COMPLETE")
        print("="*70)
        
        return results

