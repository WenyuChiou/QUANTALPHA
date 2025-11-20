"""Orchestrator: supervisor coordinating all agents with iteration loop."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import pandas as pd

from .researcher import ResearcherAgent
from .feature_agent import FeatureAgent
from .backtester import BacktesterAgent
from .critic import CriticAgent
from .librarian import LibrarianAgent
from .reporter import ReporterAgent
from ..memory.store import ExperimentStore
from ..memory.factor_registry import FactorRegistry
from ..tools.fetch_data import fetch_data, get_universe_tickers
from ..tools.logbook import log_run


class Orchestrator:
    """Supervisor that coordinates all agents in the factor mining loop."""
    
    def __init__(
        self,
        universe: str = "sp500",
        db_path: str = "experiments.db",
        index_path: str = "./kb.index"
    ):
        """Initialize orchestrator.
        
        Args:
            universe: Universe name
            db_path: Database path
            index_path: RAG index path
        """
        self.universe = universe
        self.store = ExperimentStore(db_path)
        self.registry = FactorRegistry()
        
        # Initialize agents
        self.researcher = ResearcherAgent(db_path=db_path, index_path=index_path)
        self.feature_agent = FeatureAgent()
        self.backtester = BacktesterAgent()
        self.critic = CriticAgent(db_path=db_path)
        self.librarian = LibrarianAgent(db_path=db_path, index_path=index_path)
        self.reporter = ReporterAgent(db_path=db_path)
        
        # Data cache
        self.prices_df = None
        self.returns_df = None
    
    def initialize_data(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None):
        """Initialize data for backtesting.
        
        Args:
            start_date: Start date
            end_date: End date
        """
        print("Fetching data...")
        tickers = get_universe_tickers(self.universe)
        
        # Fetch prices
        data = fetch_data(tickers, start=start_date, end=end_date)
        
        # Extract prices and returns
        if 'Close' in data.columns:
            self.prices_df = data['Close'].unstack(level='Ticker')
        else:
            self.prices_df = data.iloc[:, 0].unstack(level='Ticker')
        
        self.returns_df = self.prices_df.pct_change(1)
        
        print(f"Loaded data: {len(self.prices_df)} dates, {len(self.prices_df.columns)} tickers")
    
    def run_iteration(
        self,
        n_candidates: int = 3,
        focus_topics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Run one iteration of the factor mining loop.
        
        Args:
            n_candidates: Number of factor candidates to generate
            focus_topics: Topics to focus on
        
        Returns:
            Dictionary with iteration results
        """
        if self.prices_df is None:
            self.initialize_data()
        
        results = {
            'candidates': [],
            'successful': [],
            'failed': []
        }
        
        # Step 1: Researcher proposes factors
        print("Step 1: Researcher proposing factors...")
        factor_proposals = self.researcher.propose_factors(
            n_factors=n_candidates,
            focus_topics=focus_topics
        )
        
        for i, factor_yaml in enumerate(factor_proposals):
            print(f"\nProcessing candidate {i+1}/{len(factor_proposals)}...")
            
            try:
                # Parse factor spec
                from ..factors.dsl import DSLParser
                parser = DSLParser()
                spec = parser.parse(factor_yaml)
                
                # Register factor
                factor = self.store.create_factor(
                    name=spec.name,
                    yaml=factor_yaml,
                    tags=focus_topics or []
                )
                
                # Step 2: Feature agent computes signals
                print("  Computing features...")
                feature_result = self.feature_agent.compute_features(
                    factor_yaml,
                    self.prices_df,
                    self.returns_df
                )
                
                if not feature_result['success']:
                    print(f"  Failed: {feature_result.get('error', 'Unknown error')}")
                    results['failed'].append({
                        'factor_id': factor.id,
                        'error': feature_result.get('error')
                    })
                    continue
                
                signals_df = feature_result['signals']
                
                # Step 3: Backtester runs backtest
                print("  Running backtest...")
                backtest_result = self.backtester.run_backtest(
                    factor_yaml=factor_yaml,
                    prices_df=self.prices_df,
                    returns_df=self.returns_df,
                    run_id=f"run_{factor.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
                
                if backtest_result.get('metrics') is None:
                    print("  Backtest failed")
                    results['failed'].append({
                        'factor_id': factor.id,
                        'error': backtest_result.get('error', 'Backtest failed')
                    })
                    continue
                
                metrics = backtest_result['metrics']
                issues = backtest_result.get('issues', [])
                
                # Step 4: Log run
                print("  Logging run...")
                log_result = log_run(
                    factor_id=factor.id,
                    start_date=self.prices_df.index.min(),
                    end_date=self.prices_df.index.max(),
                    metrics=metrics,
                    regime_label=None,  # Could be determined from data
                    issues=issues,
                    db_path=self.store.db_path
                )
                
                run_id = log_result['run_id']
                
                # Step 5: Critic validates and writes lessons
                print("  Critic evaluating...")
                critique_result = self.critic.critique_run(
                    run_id=run_id,
                    metrics=metrics,
                    issues=issues,
                    factor_yaml=factor_yaml
                )
                
                if critique_result['passed']:
                    print(f"  ✓ Passed (Sharpe: {metrics.get('sharpe', 0):.2f})")
                    results['successful'].append({
                        'factor_id': factor.id,
                        'run_id': run_id,
                        'metrics': metrics
                    })
                else:
                    print(f"  ✗ Failed")
                    results['failed'].append({
                        'factor_id': factor.id,
                        'run_id': run_id,
                        'issues': issues
                    })
                
                results['candidates'].append({
                    'factor_id': factor.id,
                    'run_id': run_id,
                    'passed': critique_result['passed']
                })
                
            except Exception as e:
                print(f"  Error: {e}")
                results['failed'].append({
                    'error': str(e)
                })
                continue
        
        # Step 6: Reporter generates summary
        print("\nGenerating iteration summary...")
        summary = self.reporter.generate_iteration_plan(
            successful_factors=results['successful'],
            failed_factors=results['failed']
        )
        
        results['summary'] = summary
        
        return results
    
    def run_multiple_iterations(
        self,
        n_iterations: int = 3,
        n_candidates_per_iteration: int = 3,
        focus_topics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Run multiple iterations.
        
        Args:
            n_iterations: Number of iterations
            n_candidates_per_iteration: Candidates per iteration
            focus_topics: Topics to focus on
        
        Returns:
            Dictionary with all iteration results
        """
        all_results = {
            'iterations': [],
            'total_successful': 0,
            'total_failed': 0
        }
        
        for iteration in range(n_iterations):
            print(f"\n{'='*60}")
            print(f"Iteration {iteration + 1}/{n_iterations}")
            print(f"{'='*60}\n")
            
            iteration_result = self.run_iteration(
                n_candidates=n_candidates_per_iteration,
                focus_topics=focus_topics
            )
            
            all_results['iterations'].append(iteration_result)
            all_results['total_successful'] += len(iteration_result['successful'])
            all_results['total_failed'] += len(iteration_result['failed'])
        
        return all_results

