"""Continuous improvement loop: pattern recognition, mutation generation, target adjustment."""

from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np

from ..memory.store import ExperimentStore
from ..memory.lessons import LessonManager
from ..agents.researcher import ResearcherAgent
from ..backtest.decay_monitor import AlphaDecayMonitor
from ..backtest.multidim_eval import MultiDimensionalEvaluator


class ContinuousImprovementLoop:
    """Continuous improvement loop for factor discovery."""
    
    def __init__(
        self,
        db_path: str = "experiments.db",
        index_path: str = "./kb.index"
    ):
        """Initialize continuous improvement loop.
        
        Args:
            db_path: Database path
            index_path: RAG index path
        """
        self.store = ExperimentStore(db_path)
        self.lesson_manager = LessonManager(self.store)
        self.researcher = ResearcherAgent(db_path=db_path, index_path=index_path)
        self.decay_monitor = AlphaDecayMonitor(store=self.store)
        self.evaluator = MultiDimensionalEvaluator()
    
    def recognize_success_patterns(
        self,
        min_sharpe: float = 1.8,  # Updated requirement: minimum Sharpe 1.8
        min_ic: float = 0.06,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Recognize patterns in successful factors.
        
        Args:
            min_sharpe: Minimum Sharpe for success
            min_ic: Minimum IC for success
            limit: Maximum number of factors to analyze
        
        Returns:
            Dictionary with recognized patterns
        """
        print("\n识别成功模式...")
        
        top_runs = self.store.get_top_runs(limit=limit, order_by="sharpe")
        successful_runs = [
            r for r in top_runs
            if r.metrics and r.metrics[0].sharpe >= min_sharpe and r.metrics[0].avg_ic >= min_ic
        ]
        
        if len(successful_runs) == 0:
            return {
                'patterns': [],
                'common_motifs': [],
                'parameter_ranges': {},
                'regime_patterns': {}
            }
        
        # Extract common motifs
        motifs = []
        parameter_ranges = {}
        
        for run in successful_runs:
            factor = self.store.get_factor(run.factor_id)
            if factor:
                # Extract parameters
                from ..factors.dsl import DSLParser
                parser = DSLParser()
                params = parser.extract_parameters(factor)
                
                # Collect parameter ranges
                for key, value in params.items():
                    if isinstance(value, (int, float)):
                        if key not in parameter_ranges:
                            parameter_ranges[key] = []
                        parameter_ranges[key].append(value)
        
        # Calculate parameter ranges
        param_stats = {}
        for key, values in parameter_ranges.items():
            if values:
                param_stats[key] = {
                    'min': min(values),
                    'max': max(values),
                    'mean': np.mean(values),
                    'median': np.median(values)
                }
        
        # Regime patterns
        regime_patterns = {}
        for run in successful_runs:
            regime = run.regime_label or 'unknown'
            if regime not in regime_patterns:
                regime_patterns[regime] = []
            if run.metrics:
                regime_patterns[regime].append({
                    'sharpe': run.metrics[0].sharpe,
                    'ic': run.metrics[0].avg_ic
                })
        
        print(f"✓ 找到 {len(successful_runs)} 个成功因子")
        print(f"✓ 识别了 {len(param_stats)} 个参数模式")
        
        return {
            'patterns': successful_runs,
            'common_motifs': motifs,
            'parameter_ranges': param_stats,
            'regime_patterns': regime_patterns,
            'n_successful': len(successful_runs)
        }
    
    def recognize_failure_patterns(
        self,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Recognize patterns in failed factors.
        
        Args:
            limit: Maximum number of failures to analyze
        
        Returns:
            Dictionary with failure patterns
        """
        print("\n识别失败模式...")
        
        failed_runs = self.store.get_failed_runs(limit=limit)
        
        # Categorize failures
        failure_categories = {}
        for run in failed_runs:
            for issue in run.issues:
                issue_type = issue.type
                if issue_type not in failure_categories:
                    failure_categories[issue_type] = []
                failure_categories[issue_type].append({
                    'run_id': run.id,
                    'severity': issue.severity,
                    'detail': issue.detail
                })
        
        # Most common failure types
        common_failures = sorted(
            failure_categories.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )[:10]
        
        print(f"✓ 分析了 {len(failed_runs)} 个失败运行")
        print(f"✓ 识别了 {len(failure_categories)} 种失败类型")
        
        return {
            'failure_categories': failure_categories,
            'common_failures': common_failures,
            'n_failed': len(failed_runs)
        }
    
    def generate_mutations(
        self,
        base_factor_yaml: str,
        n_mutations: int = 3,
        mutation_types: List[str] = None
    ) -> List[str]:
        """Generate mutations of a successful factor.
        
        Args:
            base_factor_yaml: Base factor YAML
            n_mutations: Number of mutations to generate
            mutation_types: Types of mutations ('parameter', 'structural', 'both')
        
        Returns:
            List of mutated factor YAMLs
        """
        if mutation_types is None:
            mutation_types = ['parameter', 'structural']
        
        print(f"\n生成 {n_mutations} 个变异...")
        
        # Use researcher agent for mutation
        mutations = self.researcher.propose_mutations(
            base_factor_yaml=base_factor_yaml,
            n_mutations=n_mutations
        )
        
        print(f"✓ 生成了 {len(mutations)} 个变异")
        
        return mutations
    
    def adjust_targets(
        self,
        current_performance: Dict[str, float],
        improvement_rate: float = 0.1
    ) -> Dict[str, float]:
        """Adjust targets based on current performance.
        
        Args:
            current_performance: Current performance metrics
            improvement_rate: Rate of improvement (10% = 1.1x)
        
        Returns:
            Adjusted targets
        """
        print("\n调整目标...")
        
        # Get current top performers
        top_runs = self.store.get_top_runs(limit=10, order_by="sharpe")
        
        if len(top_runs) > 0:
            top_sharpes = [r.metrics[0].sharpe for r in top_runs if r.metrics]
            top_ics = [r.metrics[0].avg_ic for r in top_runs if r.metrics]
            
            if top_sharpes:
                current_best_sharpe = max(top_sharpes)
                current_best_ic = max(top_ics) if top_ics else 0.05
                
                # Adjust targets upward
                new_targets = {
                    'min_sharpe': max(1.8, current_best_sharpe * (1 - improvement_rate)),  # Minimum 1.8
                    'min_avg_ic': max(0.05, current_best_ic * (1 - improvement_rate)),
                    'max_maxdd': 0.25  # Maximum -25% drawdown
                }
                
                print(f"✓ 新目标: Sharpe ≥ {new_targets['min_sharpe']:.2f}, IC ≥ {new_targets['min_avg_ic']:.4f}")
                return new_targets
        
        # Default targets
        return {
            'min_sharpe': 1.8,  # Updated requirement: minimum Sharpe 1.8
            'min_avg_ic': 0.05,
            'max_maxdd': 0.25  # Updated requirement: maximum drawdown -25%
        }
    
    def run_improvement_cycle(
        self,
        n_mutations: int = 3,
        focus_on_top: int = 5
    ) -> Dict[str, Any]:
        """Run complete improvement cycle.
        
        Args:
            n_mutations: Number of mutations per successful factor
            focus_on_top: Number of top factors to mutate
        
        Returns:
            Improvement cycle results
        """
        print("\n" + "="*70)
        print("Continuous Improvement Cycle")
        print("="*70)
        
        # 1. Recognize success patterns
        success_patterns = self.recognize_success_patterns()
        
        # 2. Recognize failure patterns
        failure_patterns = self.recognize_failure_patterns()
        
        # 3. Generate mutations from top performers
        mutations = []
        if success_patterns['n_successful'] > 0:
            top_factors = success_patterns['patterns'][:focus_on_top]
            for run in top_factors:
                factor = self.store.get_factor(run.factor_id)
                if factor:
                    factor_mutations = self.generate_mutations(
                        base_factor_yaml=factor.yaml,
                        n_mutations=n_mutations
                    )
                    mutations.extend(factor_mutations)
        
        # 4. Adjust targets
        current_perf = {
            'sharpe': success_patterns['patterns'][0].metrics[0].sharpe 
                     if success_patterns['patterns'] else 0.0,
            'ic': success_patterns['patterns'][0].metrics[0].avg_ic
                  if success_patterns['patterns'] else 0.0
        }
        new_targets = self.adjust_targets(current_perf)
        
        print("\n" + "="*70)
        print("Improvement Cycle Summary")
        print("="*70)
        print(f"Success Patterns: {success_patterns['n_successful']}")
        print(f"Failure Patterns: {failure_patterns['n_failed']}")
        print(f"Mutations Generated: {len(mutations)}")
        print(f"New Targets: Sharpe ≥ {new_targets['min_sharpe']:.2f}")
        print("="*70)
        
        return {
            'success_patterns': success_patterns,
            'failure_patterns': failure_patterns,
            'mutations': mutations,
            'new_targets': new_targets
        }

