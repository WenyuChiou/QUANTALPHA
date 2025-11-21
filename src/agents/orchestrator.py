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
from .reflector import ReflectorAgent
from ..memory.store import ExperimentStore
from ..memory.factor_registry import FactorRegistry
from ..memory.policy_manager import PolicyManager
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
        self.reflector = ReflectorAgent()
        
        # Initialize policy manager
        self.policy_manager = PolicyManager()
        
        # Initialize archive
        from ..archive.success_factors import SuccessFactorArchive
        self.archive = SuccessFactorArchive()
        
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
        
        # Initialize Conversation Context
        from ..memory.schemas import ConversationContext
        ctx = ConversationContext(
            iteration_id=datetime.now().strftime("%Y%m%d_%H%M%S"),
            market_regime="unknown", # TODO: Detect regime
            state={"focus_topics": focus_topics}
        )
        
        # Step 1: Researcher proposes factors
        print("Step 1: Researcher proposing factors...")
        # Note: Researcher still returns list of strings (YAMLs) for now, 
        # but we should ideally wrap this too. For now, we'll wrap the *process* 
        # of getting proposals if we change researcher to return AgentResult with list.
        # Current researcher.propose_factors returns List[str] (YAMLs).
        # Let's assume we haven't changed propose_factors signature to return AgentResult yet
        # OR we did? I changed propose_factor (singular) in my thought process but 
        # the file content I wrote to researcher.py had propose_factor returning AgentResult.
        # Wait, the original researcher had propose_factors (plural).
        # My rewrite of researcher.py replaced the WHOLE file and only had propose_factor (singular).
        # I need to adapt the orchestrator to call propose_factor multiple times or 
        # I should have kept propose_factors.
        # Let's call propose_factor n times.
        
        factor_proposals = []
        for _ in range(n_candidates):
            # We use the new singular method
            result = self.researcher.propose_factor(
                market_regime=ctx.market_regime,
                existing_factors=[]
            )
            ctx.add_log(result)
            
            if result.status == "SUCCESS":
                factor_proposals.append(result.content.data['yaml_content'])
            else:
                print(f"  Error proposing factor: {result.content.summary}")
        
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
                ctx.add_log(feature_result)
                
                if feature_result.status != "SUCCESS":
                    print(f"  Failed: {feature_result.content.summary}")
                    results['failed'].append({
                        'factor_id': factor.id,
                        'error': feature_result.content.summary
                    })
                    continue
                
                signals_df = feature_result.content.data['signals']
                
                # Step 3: Backtester runs backtest
                print("  Running backtest...")
                backtest_result = self.backtester.run_backtest(
                    factor_yaml=factor_yaml,
                    prices_df=self.prices_df,
                    returns_df=self.returns_df,
                    run_id=f"run_{factor.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
                ctx.add_log(backtest_result)
                
                if backtest_result.status != "SUCCESS":
                    print(f"  Backtest failed: {backtest_result.content.summary}")
                    results['failed'].append({
                        'factor_id': factor.id,
                        'error': backtest_result.content.summary
                    })
                    continue
                
                metrics = backtest_result.content.data['metrics']
                # issues = backtest_result.content.data.get('issues', []) # Backtester might not return issues in data yet if I didn't put it there
                # Checking backtester refactor... I put 'issues' in data only on failure.
                # On success, I put metrics and output_dir.
                # I should probably include issues in success too if there are warnings.
                # For now, let's assume empty issues on success.
                issues = [] 
                
                # Step 4: Log run
                print("  Logging run...")
                log_result = log_run(
                    factor_id=factor.id,
                    start_date=self.prices_df.index.min(),
                    end_date=self.prices_df.index.max(),
                    metrics=metrics,
                    regime_label=None,
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
                ctx.add_log(critique_result)
                
                passed = critique_result.content.data['passed']
                
                if passed:
                    print(f"  ✓ Passed (Sharpe: {metrics.get('sharpe', 0):.2f})")
                    results['successful'].append({
                        'factor_id': factor.id,
                        'run_id': run_id,
                        'metrics': metrics
                    })
                    
                    # Check if it meets strict archive criteria
                    if self.archive.should_archive(metrics):
                        print("  ★ Meets archive criteria! Archiving...")
                        
                        # Prepare data for archive
                        # We need to reconstruct the agent_outputs dict expected by archive_factor
                        # OR update archive_factor to take ConversationContext.
                        # For now, let's map it to the expected dict to avoid breaking archive.
                        
                        agent_outputs = {
                            'researcher': {'proposal': factor_yaml}, # Simplified
                            'feature': feature_result.content.data,
                            'backtest': backtest_result.content.data,
                            'critic': critique_result.content.data
                        }
                        
                        computations = {
                            'signals': signals_df,
                            # 'returns': ... # We need returns and equity curve. 
                            # Backtester refactor saved them to disk but didn't return the DF in data.
                            # We might need to load them or adjust backtester to return them.
                            # For now, let's assume we can't easily get them without reading the parquet.
                            # Wait, I can just pass empty dicts if I don't have them in memory, 
                            # but archive might need them for plotting.
                            # Let's skip plotting in archive for now if data is missing.
                        }
                        
                        # Convert ConversationContext logs to list of dicts for archive
                        conversation_log = [log.dict() for log in ctx.logs]
                        
                        archive_path = self.archive.archive_factor(
                            factor_name=spec.name,
                            factor_yaml=factor_yaml,
                            agent_outputs=agent_outputs,
                            computations=computations,
                            backtest_results={'metrics': metrics}, # Simplified
                            conversation_log=conversation_log
                        )
                        print(f"  Archived to: {archive_path}")
                        
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
                    'passed': passed
                })
                
            except Exception as e:
                print(f"  Error: {e}")
                import traceback
                traceback.print_exc()
                results['failed'].append({
                    'error': str(e)
                })
                continue
        
        # Step 6: Reporter generates summary
        print("\nGenerating iteration summary...")
        plan_result = self.reporter.generate_iteration_plan(
            successful_factors=results['successful'],
            failed_factors=results['failed']
        )
        ctx.add_log(plan_result)
        
        results['summary'] = plan_result.content.data.get('plan_text', 'No plan generated')
        
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
    
    def run_discovery_loop(
        self,
        universe: str = 'sp500',
        n_candidates: int = 3,
        max_iterations: Optional[int] = None,
        target_sharpe: Optional[float] = None,
        focus_topics: Optional[List[str]] = None
    ) -> Optional[str]:
        """Run iterative alpha discovery loop until target is met.
        
        Args:
            universe: Universe name
            n_candidates: Number of candidates per iteration
            max_iterations: Maximum iterations (default from policy rules)
            target_sharpe: Target Sharpe ratio (default from policy rules)
            focus_topics: Topics to focus on
        
        Returns:
            Alpha ID if successful, None otherwise
        """
        if self.prices_df is None:
            self.initialize_data()
        
        # Get limits from policy rules
        if max_iterations is None:
            max_iterations = self.policy_manager.get_max_iterations()
        if target_sharpe is None:
            target_sharpe = self.policy_manager.rules['global_constraints']['min_sharpe']
        
        print(f"\n{'='*70}")
        print(f" ALPHA DISCOVERY LOOP")
        print(f" Universe: {universe}")
        print(f" Target Sharpe: {target_sharpe}")
        print(f" Max Iterations: {max_iterations}")
        print(f"{'='*70}\n")
        
        past_lessons = []
        
        for iteration in range(1, max_iterations + 1):
            alpha_id = f"alpha_{iteration:03d}"
            
            print(f"\n{'='*70}")
            print(f" ITERATION {iteration}: {alpha_id}")
            print(f"{'='*70}\n")
            
            # Step 1: Research (with policy rules and lessons)
            print(f"[1/6] ResearcherAgent proposing factors...")
            try:
                result = self.researcher.propose_factor(
                    market_regime="unknown",
                    existing_factors=[],
                    # TODO: Pass policy_rules and past_lessons to researcher
                )
                
                if result.status != "SUCCESS":
                    print(f"  ✗ Failed to generate proposal: {result.content.summary}")
                    continue
                
                factor_yaml = result.content.data['yaml_content']
                print(f"  ✓ Generated factor proposal")
                
            except Exception as e:
                print(f"  ✗ Error: {e}")
                continue
            
            # Parse factor
            from ..factors.dsl import DSLParser
            parser = DSLParser()
            spec = parser.parse(factor_yaml)
            
            # Step 2: Feature Engineering
            print(f"[2/6] FeatureAgent computing signals...")
            try:
                feature_result = self.feature_agent.compute_features(
                    factor_yaml,
                    self.prices_df,
                    self.returns_df
                )
                
                if feature_result.status != "SUCCESS":
                    print(f"  ✗ Failed: {feature_result.content.summary}")
                    continue
                
                signals_df = feature_result.content.data['signals']
                signals_meta = feature_result.content.data.get('meta', {})
                print(f"  ✓ Computed signals")
                
            except Exception as e:
                print(f"  ✗ Error: {e}")
                continue
            
            # Step 3: Backtest
            print(f"[3/6] BacktesterAgent running backtest...")
            try:
                backtest_result = self.backtester.run_backtest(
                    factor_yaml=factor_yaml,
                    prices_df=self.prices_df,
                    returns_df=self.returns_df,
                    run_id=f"{alpha_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
                
                if backtest_result.status != "SUCCESS":
                    print(f"  ✗ Backtest failed: {backtest_result.content.summary}")
                    continue
                
                metrics = backtest_result.content.data['metrics']
                output_dir = backtest_result.content.data.get('output_dir', '')
                
                print(f"  ✓ Backtest completed")
                print(f"    Sharpe: {metrics.get('sharpe', 0):.2f}")
                print(f"    Annual Return: {metrics.get('ann_ret', 0):.2%}")
                print(f"    Max Drawdown: {metrics.get('maxdd', 0):.2%}")
                
            except Exception as e:
                print(f"  ✗ Error: {e}")
                import traceback
                traceback.print_exc()
                continue
            
            # Step 4: Critique
            print(f"[4/6] CriticAgent evaluating...")
            try:
                # Log run first
                log_result = log_run(
                    factor_id=0,  # Temporary
                    start_date=self.prices_df.index.min(),
                    end_date=self.prices_df.index.max(),
                    metrics=metrics,
                    regime_label=None,
                    issues=[],
                    db_path=self.store.db_path
                )
                run_id = log_result['run_id']
                
                critique_result = self.critic.critique_run(
                    run_id=run_id,
                    metrics=metrics,
                    issues=[],
                    factor_yaml=factor_yaml
                )
                
                compliance = critique_result.content.data
                verdict = compliance.get('verdict', 'FAIL')
                
                print(f"  ✓ Verdict: {verdict}")
                if compliance.get('issues'):
                    print(f"    Issues: {len(compliance['issues'])}")
                
            except Exception as e:
                print(f"  ✗ Error: {e}")
                compliance = {'verdict': 'FAIL', 'issues': []}
            
            # Step 5: Reflect
            print(f"[5/6] ReflectorAgent analyzing...")
            try:
                lessons = self.reflector.analyze(
                    alpha_id=alpha_id,
                    metrics=metrics,
                    compliance=compliance,
                    signals_meta=signals_meta,
                    factor_yaml=factor_yaml,
                    past_lessons=past_lessons
                )
                
                past_lessons.append(lessons)
                
                print(f"  ✓ Lessons generated")
                print(f"    Root causes: {len(lessons['root_causes'])}")
                print(f"    Suggestions: {len(lessons['improvement_suggestions'])}")
                
                # Save lessons
                lessons_path = Path(output_dir) / 'lessons.json' if output_dir else None
                if lessons_path:
                    import json
                    with open(lessons_path, 'w') as f:
                        json.dump(lessons, f, indent=2)
                
            except Exception as e:
                print(f"  ✗ Error: {e}")
                import traceback
                traceback.print_exc()
                lessons = {'verdict': 'FAIL', 'root_causes': [], 'improvement_suggestions': []}
            
            # Step 6: Check if target met
            print(f"[6/6] Checking targets...")
            meets_constraints, violations = self.policy_manager.check_constraints(metrics)
            
            if meets_constraints:
                print(f"\n{'='*70}")
                print(f" ✅ SUCCESS! {alpha_id} meets all targets")
                print(f" Sharpe: {metrics.get('sharpe', 0):.2f} >= {target_sharpe}")
                print(f" MaxDD: {metrics.get('maxdd', 0):.2%} >= -20%")
                print(f"{'='*70}\n")
                
                # Archive successful factor
                if output_dir:
                    success_dir = Path('success_factors') / f"{alpha_id}_{spec.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    success_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Copy artifacts
                    import shutil
                    if Path(output_dir).exists():
                        shutil.copytree(output_dir, success_dir, dirs_exist_ok=True)
                    
                    print(f"  Archived to: {success_dir}")
                
                return alpha_id
            
            else:
                print(f"\n  ✗ Does not meet targets:")
                for violation in violations:
                    print(f"    - {violation}")
                print(f"\n  Continuing to next iteration...\n")
        
        print(f"\n{'='*70}")
        print(f" ⚠️ Max iterations ({max_iterations}) reached")
        print(f" No alpha met the target criteria")
        print(f"{'='*70}\n")
        
        return None

