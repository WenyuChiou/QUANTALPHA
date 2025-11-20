"""Daily workflow automation: Plan → Execute → Review → Replan."""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pathlib import Path
import json

from ..agents.orchestrator import Orchestrator
from ..memory.store import ExperimentStore
from ..memory.lessons import LessonManager


class DailyWorkflow:
    """Automated daily workflow for factor mining."""
    
    def __init__(
        self,
        universe: str = "sp500",
        db_path: str = "experiments.db",
        index_path: str = "./kb.index"
    ):
        """Initialize daily workflow.
        
        Args:
            universe: Universe name
            db_path: Database path
            index_path: RAG index path
        """
        self.universe = universe
        self.orchestrator = Orchestrator(universe=universe, db_path=db_path, index_path=index_path)
        self.store = ExperimentStore(db_path)
        self.lesson_manager = LessonManager(self.store)
    
    def morning_planning(
        self,
        n_candidates: int = 3,
        focus_topics: Optional[list] = None
    ) -> Dict[str, Any]:
        """Morning planning phase.
        
        Args:
            n_candidates: Number of factor candidates to generate
            focus_topics: Topics to focus on
        
        Returns:
            Planning results
        """
        print("\n" + "="*70)
        print("🌅 Morning Planning Phase")
        print("="*70)
        
        # Review previous day's results
        print("\n[1/3] Reviewing previous results...")
        top_runs = self.store.get_top_runs(limit=5, order_by="sharpe")
        print(f"  找到 {len(top_runs)} 个顶级运行")
        
        failed_runs = self.store.get_failed_runs(limit=5)
        print(f"  找到 {len(failed_runs)} 个失败运行")
        
        # Generate new candidates
        print(f"\n[2/3] Generating {n_candidates} new factor candidates...")
        if not self.orchestrator.prices_df:
            self.orchestrator.initialize_data()
        
        factor_proposals = self.orchestrator.researcher.propose_factors(
            n_factors=n_candidates,
            focus_topics=focus_topics
        )
        
        print(f"  ✓ 生成了 {len(factor_proposals)} 个因子提案")
        
        # Set daily targets
        print("\n[3/3] Setting daily targets...")
        targets = {
            'min_sharpe': 1.8,  # Updated requirement: minimum Sharpe 1.8
            'max_maxdd': 0.25,  # Updated requirement: maximum drawdown -25%
            'min_avg_ic': 0.05,
            'n_candidates': n_candidates
        }
        print(f"  目标: Sharpe ≥ {targets['min_sharpe']}, MaxDD ≤ {targets['max_maxdd']:.0%}")
        
        return {
            'factor_proposals': factor_proposals,
            'targets': targets,
            'top_runs': len(top_runs),
            'failed_runs': len(failed_runs)
        }
    
    def execution(
        self,
        factor_proposals: list,
        n_parallel: int = 1
    ) -> Dict[str, Any]:
        """Execution phase.
        
        Args:
            factor_proposals: List of factor YAML strings
            n_parallel: Number of parallel executions
        
        Returns:
            Execution results
        """
        print("\n" + "="*70)
        print("⚙️  Execution Phase")
        print("="*70)
        
        results = {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'runs': []
        }
        
        for i, factor_yaml in enumerate(factor_proposals):
            print(f"\n[{i+1}/{len(factor_proposals)}] Processing factor...")
            
            try:
                # Parse factor
                from ..factors.dsl import DSLParser
                parser = DSLParser()
                spec = parser.parse(factor_yaml)
                
                # Register factor
                factor = self.store.create_factor(
                    name=spec.name,
                    yaml=factor_yaml,
                    tags=[]
                )
                
                # Compute features
                print("  Computing features...")
                feature_result = self.orchestrator.feature_agent.compute_features(
                    factor_yaml,
                    self.orchestrator.prices_df,
                    self.orchestrator.returns_df
                )
                
                if not feature_result['success']:
                    print(f"  ✗ Feature computation failed: {feature_result.get('error')}")
                    results['failed'] += 1
                    continue
                
                # Run backtest
                print("  Running backtest...")
                backtest_result = self.orchestrator.backtester.run_backtest(
                    factor_yaml=factor_yaml,
                    prices_df=self.orchestrator.prices_df,
                    returns_df=self.orchestrator.returns_df,
                    run_id=f"daily_{datetime.now().strftime('%Y%m%d')}_{factor.id}"
                )
                
                if backtest_result.get('metrics'):
                    metrics = backtest_result['metrics']
                    print(f"  ✓ Backtest complete: Sharpe={metrics.get('sharpe', 0):.2f}")
                    results['successful'] += 1
                else:
                    print(f"  ✗ Backtest failed")
                    results['failed'] += 1
                
                results['processed'] += 1
                results['runs'].append({
                    'factor_id': factor.id,
                    'metrics': backtest_result.get('metrics'),
                    'success': backtest_result.get('metrics') is not None
                })
                
            except Exception as e:
                print(f"  ✗ Error: {e}")
                results['failed'] += 1
                continue
        
        print(f"\n执行完成: {results['successful']}/{results['processed']} 成功")
        return results
    
    def afternoon_review(
        self,
        execution_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Afternoon review phase.
        
        Args:
            execution_results: Results from execution phase
        
        Returns:
            Review results
        """
        print("\n" + "="*70)
        print("📊 Afternoon Review Phase")
        print("="*70)
        
        review_results = {
            'validated': 0,
            'passed': 0,
            'failed': 0,
            'lessons': []
        }
        
        for run_info in execution_results.get('runs', []):
            if not run_info.get('metrics'):
                continue
            
            factor_id = run_info['factor_id']
            metrics = run_info['metrics']
            
            # Get run from database
            session = self.store.get_session()
            try:
                run = session.query(self.store.Run).filter(
                    self.store.Run.factor_id == factor_id
                ).order_by(self.store.Run.created_at.desc()).first()
                
                if not run:
                    continue
                
                # Get factor
                factor = self.store.get_factor(factor_id)
                factor_yaml = factor.yaml if factor else ""
                
                # Critique
                print(f"\nReviewing run {run.id}...")
                critique_result = self.orchestrator.critic.critique_run(
                    run_id=run.id,
                    metrics=metrics,
                    issues=[],
                    factor_yaml=factor_yaml
                )
                
                review_results['validated'] += 1
                if critique_result['passed']:
                    review_results['passed'] += 1
                    print(f"  ✓ Passed validation")
                else:
                    review_results['failed'] += 1
                    print(f"  ✗ Failed validation")
                
                review_results['lessons'].append({
                    'run_id': run.id,
                    'passed': critique_result['passed'],
                    'lesson_id': critique_result.get('lesson_id')
                })
                
            finally:
                session.close()
        
        print(f"\n审查完成: {review_results['passed']}/{review_results['validated']} 通过")
        return review_results
    
    def evening_replanning(
        self,
        review_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evening replanning phase.
        
        Args:
            review_results: Results from review phase
        
        Returns:
            Replanning results
        """
        print("\n" + "="*70)
        print("🌙 Evening Re-planning Phase")
        print("="*70)
        
        # Generate summary
        print("\n[1/3] Generating summary report...")
        dashboard_notes = self.orchestrator.reporter.generate_dashboard_notes()
        print(f"  ✓ Dashboard notes generated")
        
        # Update knowledge base
        print("\n[2/3] Updating knowledge base...")
        success_count = review_results.get('passed', 0)
        failure_count = review_results.get('failed', 0)
        print(f"  Successes: {success_count}, Failures: {failure_count}")
        
        # Plan next day
        print("\n[3/3] Planning next day's focus...")
        top_runs = self.store.get_top_runs(limit=3, order_by="sharpe")
        
        if top_runs:
            print("  Top performers identified for mutation")
            next_focus = "mutation"
        else:
            print("  No top performers, focusing on exploration")
            next_focus = "exploration"
        
        return {
            'summary': dashboard_notes,
            'next_focus': next_focus,
            'success_count': success_count,
            'failure_count': failure_count
        }
    
    def run_daily_cycle(
        self,
        n_candidates: int = 3,
        focus_topics: Optional[list] = None
    ) -> Dict[str, Any]:
        """Run complete daily cycle.
        
        Args:
            n_candidates: Number of candidates per day
            focus_topics: Topics to focus on
        
        Returns:
            Complete cycle results
        """
        print("\n" + "="*70)
        print(f"Daily Workflow - {datetime.now().strftime('%Y-%m-%d')}")
        print("="*70)
        
        # Morning Planning
        planning_results = self.morning_planning(n_candidates, focus_topics)
        
        # Execution
        execution_results = self.execution(planning_results['factor_proposals'])
        
        # Afternoon Review
        review_results = self.afternoon_review(execution_results)
        
        # Evening Re-planning
        replan_results = self.evening_replanning(review_results)
        
        # Summary
        print("\n" + "="*70)
        print("Daily Cycle Summary")
        print("="*70)
        print(f"Candidates Generated: {len(planning_results['factor_proposals'])}")
        print(f"Successfully Executed: {execution_results['successful']}")
        print(f"Passed Validation: {review_results['passed']}")
        print(f"Next Focus: {replan_results['next_focus']}")
        print("="*70)
        
        return {
            'planning': planning_results,
            'execution': execution_results,
            'review': review_results,
            'replanning': replan_results
        }

