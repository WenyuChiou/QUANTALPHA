"""Analysis guidelines and standards for factor evaluation."""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class AnalysisStandard(Enum):
    """Analysis standards for different evaluation aspects."""
    STRICT = "strict"
    MODERATE = "moderate"
    LENIENT = "lenient"


@dataclass
class AnalysisGuidelines:
    """Guidelines for comprehensive factor analysis."""
    
    # Performance thresholds
    min_sharpe: float = 1.8
    max_maxdd: float = 0.25
    min_ic: float = 0.05
    min_ir: float = 0.5
    min_hit_rate: float = 0.52
    max_turnover: float = 250.0
    
    # Stability requirements
    max_sharpe_volatility: float = 0.5  # Rolling Sharpe std should be < 50% of mean
    min_ic_stability: float = 0.03  # IC should not drop below this
    max_sharpe_drawdown: float = 0.5  # Rolling Sharpe should not drop >50%
    
    # Risk requirements
    max_var_95: float = -0.02  # VaR(95%) should be >= -2%
    min_tail_ratio: float = 1.0  # Tail ratio (95th/5th percentile)
    
    # Regime requirements
    min_regime_sharpe: float = 0.5  # Minimum Sharpe in each regime
    required_regime_count: int = 3  # Must work in at least 3/4 regimes
    
    # Decay requirements
    max_ic_decay_rate: float = 0.5  # IC decay rate should be < 50%
    max_complexity_score: float = 10.0  # Factor complexity score
    
    # Sample size requirements
    min_history_days: int = 800
    min_observations: int = 800
    
    def evaluate_performance(self, metrics: Dict[str, float]) -> Dict[str, Any]:
        """Evaluate performance metrics against guidelines.
        
        Args:
            metrics: Dictionary of performance metrics
        
        Returns:
            Evaluation results with pass/fail status
        """
        results = {
            'passed': True,
            'failures': [],
            'warnings': [],
            'scores': {}
        }
        
        # Sharpe evaluation
        sharpe = metrics.get('sharpe', 0)
        if sharpe < self.min_sharpe:
            results['passed'] = False
            results['failures'].append(f"Sharpe {sharpe:.2f} < {self.min_sharpe} (REQUIRED)")
        else:
            results['scores']['sharpe'] = 'PASS'
            if sharpe >= 2.5:
                results['scores']['sharpe_grade'] = 'EXCELLENT'
            elif sharpe >= 2.0:
                results['scores']['sharpe_grade'] = 'GOOD'
            else:
                results['scores']['sharpe_grade'] = 'ACCEPTABLE'
        
        # Drawdown evaluation
        maxdd = abs(metrics.get('maxdd', 0))
        if maxdd > self.max_maxdd:
            results['passed'] = False
            results['failures'].append(f"MaxDD {maxdd:.2%} > {self.max_maxdd:.2%} (REQUIRED)")
        else:
            results['scores']['maxdd'] = 'PASS'
            if maxdd <= 0.15:
                results['scores']['maxdd_grade'] = 'EXCELLENT'
            elif maxdd <= 0.20:
                results['scores']['maxdd_grade'] = 'GOOD'
            else:
                results['scores']['maxdd_grade'] = 'ACCEPTABLE'
        
        # IC evaluation
        ic = metrics.get('avg_ic', 0)
        if ic < self.min_ic:
            results['warnings'].append(f"IC {ic:.4f} < {self.min_ic} (weak predictive power)")
        else:
            results['scores']['ic'] = 'PASS'
        
        # IR evaluation
        ir = metrics.get('ir', 0)
        if ir < self.min_ir:
            results['warnings'].append(f"IR {ir:.2f} < {self.min_ir} (poor risk-adjusted performance)")
        else:
            results['scores']['ir'] = 'PASS'
        
        # Hit rate evaluation
        hit_rate = metrics.get('hit_rate', 0)
        if hit_rate < self.min_hit_rate:
            results['warnings'].append(f"Hit rate {hit_rate:.2%} < {self.min_hit_rate:.2%} (inconsistent)")
        else:
            results['scores']['hit_rate'] = 'PASS'
        
        # Turnover evaluation
        turnover = metrics.get('turnover_monthly', 0)
        if turnover > self.max_turnover:
            results['warnings'].append(f"Turnover {turnover:.1f}% > {self.max_turnover:.1f}% (high costs)")
        else:
            results['scores']['turnover'] = 'PASS'
        
        return results
    
    def evaluate_stability(self, stability_metrics: Dict[str, float]) -> Dict[str, Any]:
        """Evaluate stability metrics.
        
        Args:
            stability_metrics: Dictionary of stability metrics
        
        Returns:
            Stability evaluation results
        """
        results = {
            'passed': True,
            'issues': []
        }
        
        # Sharpe stability
        sharpe_std = stability_metrics.get('rolling_sharpe_std', 0)
        sharpe_mean = stability_metrics.get('rolling_sharpe_mean', 1.8)
        if sharpe_mean > 0 and sharpe_std / sharpe_mean > self.max_sharpe_volatility:
            results['issues'].append(f"High Sharpe volatility: {sharpe_std:.2f} (std/mean > {self.max_sharpe_volatility:.0%})")
        
        # IC stability
        ic_std = stability_metrics.get('ic_stability', 0)
        if ic_std > 0.1:  # IC std should be reasonable
            results['issues'].append(f"High IC volatility: {ic_std:.4f}")
        
        return results
    
    def evaluate_regime_robustness(self, regime_metrics: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """Evaluate regime robustness.
        
        Args:
            regime_metrics: Dictionary of regime-specific metrics
        
        Returns:
            Regime evaluation results
        """
        results = {
            'passed': True,
            'regime_count': 0,
            'failed_regimes': []
        }
        
        for regime, metrics in regime_metrics.items():
            sharpe = metrics.get('sharpe', 0)
            if sharpe >= self.min_regime_sharpe:
                results['regime_count'] += 1
            else:
                results['failed_regimes'].append(regime)
        
        if results['regime_count'] < self.required_regime_count:
            results['passed'] = False
            results['issues'] = [f"Only {results['regime_count']}/{len(regime_metrics)} regimes pass (need {self.required_regime_count})"]
        
        return results
    
    def evaluate_decay(self, decay_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate decay metrics.
        
        Args:
            decay_metrics: Dictionary of decay metrics
        
        Returns:
            Decay evaluation results
        """
        results = {
            'passed': True,
            'warnings': []
        }
        
        decay_rate = decay_metrics.get('decay_rate', 0)
        if decay_rate > self.max_ic_decay_rate:
            results['warnings'].append(f"High IC decay rate: {decay_rate:.2%} > {self.max_ic_decay_rate:.2%}")
        
        decay_detected = decay_metrics.get('decay_detected', False)
        if decay_detected:
            results['warnings'].append("Performance decay detected - factor may be losing effectiveness")
        
        return results
    
    def get_analysis_checklist(self) -> List[str]:
        """Get comprehensive analysis checklist.
        
        Returns:
            List of analysis items to check
        """
        return [
            "Performance Metrics",
            "  ✓ Sharpe Ratio >= 1.8",
            "  ✓ Max Drawdown <= -25%",
            "  ✓ IC >= 0.05",
            "  ✓ IR >= 0.5",
            "  ✓ Hit Rate >= 52%",
            "  ✓ Turnover <= 250%",
            "",
            "Stability Analysis",
            "  ✓ Rolling Sharpe stability",
            "  ✓ IC stability over time",
            "  ✓ No excessive volatility in metrics",
            "",
            "Risk Analysis",
            "  ✓ VaR(95%) evaluation",
            "  ✓ Tail ratio assessment",
            "  ✓ Drawdown analysis",
            "",
            "Regime Robustness",
            "  ✓ Performance in bull markets",
            "  ✓ Performance in bear markets",
            "  ✓ Performance in high volatility",
            "  ✓ Performance in low volatility",
            "",
            "Decay Analysis",
            "  ✓ IC decay rate",
            "  ✓ Performance persistence",
            "  ✓ Complexity assessment",
            "",
            "Sample Quality",
            "  ✓ Sufficient history (>= 800 days)",
            "  ✓ Adequate observations",
            "  ✓ Data quality checks"
        ]


# Global guidelines instance
_default_guidelines = AnalysisGuidelines()


def get_analysis_guidelines() -> AnalysisGuidelines:
    """Get default analysis guidelines.
    
    Returns:
        Analysis guidelines instance
    """
    return _default_guidelines

