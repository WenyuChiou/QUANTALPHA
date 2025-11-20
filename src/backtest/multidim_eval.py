"""Multi-dimensional evaluation framework (AlphaEval-inspired).

Evaluates factors across multiple dimensions:
- Predictive power
- Stability
- Robustness
- Financial logic
- Diversity
- Originality
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from scipy import stats
from scipy.spatial.distance import cosine

from .metrics import information_coefficient, sharpe, information_ratio
from ..factors.primitives import CORRELATION, TS_RANK


class MultiDimensionalEvaluator:
    """Multi-dimensional factor evaluator."""
    
    def __init__(self):
        """Initialize evaluator."""
        pass
    
    def evaluate(
        self,
        signals: pd.Series,
        returns: pd.Series,
        prices: Optional[pd.Series] = None,
        benchmark_signals: Optional[List[pd.Series]] = None
    ) -> Dict[str, Any]:
        """Comprehensive multi-dimensional evaluation.
        
        Args:
            signals: Factor signals
            returns: Next period returns
            prices: Price series (for financial logic)
            benchmark_signals: List of benchmark factor signals (for diversity/originality)
        
        Returns:
            Dictionary with scores for each dimension
        """
        results = {}
        
        # Align data
        aligned = pd.DataFrame({
            'signals': signals,
            'returns': returns
        }).dropna()
        
        if len(aligned) < 10:
            return self._empty_results()
        
        # 1. Predictive Power
        results['predictive_power'] = self._evaluate_predictive_power(
            aligned['signals'],
            aligned['returns']
        )
        
        # 2. Stability
        results['stability'] = self._evaluate_stability(
            aligned['signals'],
            aligned['returns']
        )
        
        # 3. Robustness
        results['robustness'] = self._evaluate_robustness(
            aligned['signals'],
            aligned['returns']
        )
        
        # 4. Financial Logic
        if prices is not None:
            results['financial_logic'] = self._evaluate_financial_logic(
                aligned['signals'],
                prices.loc[aligned.index]
            )
        else:
            results['financial_logic'] = {'score': 0.5, 'details': 'Price data not available'}
        
        # 5. Diversity
        if benchmark_signals:
            results['diversity'] = self._evaluate_diversity(
                aligned['signals'],
                benchmark_signals
            )
        else:
            results['diversity'] = {'score': 0.5, 'details': 'No benchmark signals provided'}
        
        # 6. Originality
        if benchmark_signals:
            results['originality'] = self._evaluate_originality(
                aligned['signals'],
                benchmark_signals
            )
        else:
            results['originality'] = {'score': 0.5, 'details': 'No benchmark signals provided'}
        
        # Overall score (weighted average)
        weights = {
            'predictive_power': 0.3,
            'stability': 0.2,
            'robustness': 0.2,
            'financial_logic': 0.1,
            'diversity': 0.1,
            'originality': 0.1
        }
        
        overall_score = sum(
            results[dim]['score'] * weights[dim]
            for dim in weights.keys()
            if 'score' in results[dim]
        )
        
        results['overall_score'] = overall_score
        results['weights'] = weights
        
        return results
    
    def _evaluate_predictive_power(
        self,
        signals: pd.Series,
        returns: pd.Series
    ) -> Dict[str, Any]:
        """Evaluate predictive power.
        
        Metrics: IC, IR, hit rate, monotonicity
        """
        # IC
        ic = information_coefficient(signals, returns)
        
        # Rolling IC for IR
        rolling_ic = []
        window = min(63, len(signals) // 4)  # ~1 quarter or 1/4 of data
        if window > 5:
            for i in range(window, len(signals)):
                window_signals = signals.iloc[i-window:i]
                window_returns = returns.iloc[i-window:i]
                window_ic = information_coefficient(window_signals, window_returns)
                rolling_ic.append(window_ic)
        
        ir = information_ratio(pd.Series(rolling_ic)) if rolling_ic else 0.0
        
        # Hit rate
        hit_rate = (np.sign(signals) == np.sign(returns)).mean()
        
        # Monotonicity: check if higher signals lead to higher returns
        # Divide into quintiles
        quintiles = pd.qcut(signals, q=5, duplicates='drop')
        quintile_returns = returns.groupby(quintiles).mean()
        monotonicity = 1.0 if quintile_returns.is_monotonic_increasing else 0.0
        
        score = (abs(ic) * 0.4 + min(abs(ir), 2.0) / 2.0 * 0.3 + hit_rate * 0.2 + monotonicity * 0.1)
        score = max(0.0, min(1.0, score))  # Clip to [0, 1]
        
        return {
            'score': score,
            'ic': ic,
            'ir': ir,
            'hit_rate': hit_rate,
            'monotonicity': monotonicity,
            'details': f"IC={ic:.4f}, IR={ir:.2f}, HitRate={hit_rate:.2%}"
        }
    
    def _evaluate_stability(
        self,
        signals: pd.Series,
        returns: pd.Series
    ) -> Dict[str, Any]:
        """Evaluate stability.
        
        Metrics: IC stability over time, signal stability, consistency
        """
        # IC stability
        rolling_ic = []
        window = min(63, len(signals) // 4)
        if window > 5:
            for i in range(window, len(signals)):
                window_signals = signals.iloc[i-window:i]
                window_returns = returns.iloc[i-window:i]
                window_ic = information_coefficient(window_signals, window_returns)
                rolling_ic.append(window_ic)
        
        if len(rolling_ic) > 1:
            ic_std = pd.Series(rolling_ic).std()
            ic_mean = pd.Series(rolling_ic).mean()
            ic_stability = 1.0 - min(ic_std / (abs(ic_mean) + 0.01), 1.0)  # Lower std = higher stability
        else:
            ic_stability = 0.5
        
        # Signal stability (low turnover in signal direction)
        signal_changes = (np.sign(signals) != np.sign(signals.shift(1))).sum()
        signal_stability = 1.0 - min(signal_changes / len(signals), 1.0)
        
        # Consistency: fraction of periods with positive IC
        if len(rolling_ic) > 0:
            positive_ic_ratio = (pd.Series(rolling_ic) > 0).mean()
        else:
            positive_ic_ratio = 0.5
        
        score = (ic_stability * 0.5 + signal_stability * 0.3 + positive_ic_ratio * 0.2)
        score = max(0.0, min(1.0, score))
        
        return {
            'score': score,
            'ic_stability': ic_stability,
            'signal_stability': signal_stability,
            'consistency': positive_ic_ratio,
            'details': f"IC stability={ic_stability:.2f}, Signal stability={signal_stability:.2f}"
        }
    
    def _evaluate_robustness(
        self,
        signals: pd.Series,
        returns: pd.Series
    ) -> Dict[str, Any]:
        """Evaluate robustness.
        
        Metrics: Performance across different market conditions, outlier resistance
        """
        # Divide into volatility regimes
        vol = returns.rolling(21).std()
        high_vol_threshold = vol.quantile(0.75)
        low_vol_threshold = vol.quantile(0.25)
        
        high_vol_mask = vol > high_vol_threshold
        low_vol_mask = vol < low_vol_threshold
        
        # IC in different regimes
        ic_high_vol = information_coefficient(signals[high_vol_mask], returns[high_vol_mask]) if high_vol_mask.sum() > 10 else 0.0
        ic_low_vol = information_coefficient(signals[low_vol_mask], returns[low_vol_mask]) if low_vol_mask.sum() > 10 else 0.0
        ic_overall = information_coefficient(signals, returns)
        
        # Robustness: similar IC across regimes
        regime_ic_diff = abs(ic_high_vol - ic_low_vol)
        robustness = 1.0 - min(regime_ic_diff / (abs(ic_overall) + 0.01), 1.0)
        
        # Outlier resistance: remove top/bottom 5% and check IC
        signals_trimmed = signals[(signals >= signals.quantile(0.05)) & (signals <= signals.quantile(0.95))]
        returns_trimmed = returns.loc[signals_trimmed.index]
        ic_trimmed = information_coefficient(signals_trimmed, returns_trimmed) if len(signals_trimmed) > 10 else ic_overall
        
        outlier_resistance = 1.0 - min(abs(ic_overall - ic_trimmed) / (abs(ic_overall) + 0.01), 1.0)
        
        score = (robustness * 0.6 + outlier_resistance * 0.4)
        score = max(0.0, min(1.0, score))
        
        return {
            'score': score,
            'robustness': robustness,
            'outlier_resistance': outlier_resistance,
            'ic_high_vol': ic_high_vol,
            'ic_low_vol': ic_low_vol,
            'details': f"Regime robustness={robustness:.2f}, Outlier resistance={outlier_resistance:.2f}"
        }
    
    def _evaluate_financial_logic(
        self,
        signals: pd.Series,
        prices: pd.Series
    ) -> Dict[str, Any]:
        """Evaluate financial logic.
        
        Metrics: Reasonableness of signal values, relationship to prices
        """
        # Signal reasonableness: not too extreme
        signal_zscore = (signals - signals.mean()) / (signals.std() + 1e-10)
        extreme_ratio = (abs(signal_zscore) > 3).mean()
        reasonableness = 1.0 - min(extreme_ratio, 1.0)
        
        # Relationship to prices: signals should correlate with price trends
        returns = prices.pct_change()
        price_correlation = signals.corr(returns)
        price_logic = (abs(price_correlation) + 1.0) / 2.0  # Normalize to [0, 1]
        
        # Signal smoothness (not too noisy)
        signal_changes = signals.diff().abs()
        smoothness = 1.0 - min(signal_changes.quantile(0.95) / (signals.std() + 1e-10), 1.0)
        
        score = (reasonableness * 0.4 + price_logic * 0.4 + smoothness * 0.2)
        score = max(0.0, min(1.0, score))
        
        return {
            'score': score,
            'reasonableness': reasonableness,
            'price_logic': price_logic,
            'smoothness': smoothness,
            'details': f"Reasonableness={reasonableness:.2f}, Price logic={price_logic:.2f}"
        }
    
    def _evaluate_diversity(
        self,
        signals: pd.Series,
        benchmark_signals: List[pd.Series]
    ) -> Dict[str, Any]:
        """Evaluate diversity.
        
        Measures how different this factor is from benchmark factors.
        """
        if not benchmark_signals:
            return {'score': 0.5, 'details': 'No benchmarks'}
        
        # Align all signals
        common_index = signals.index
        for bench in benchmark_signals:
            common_index = common_index.intersection(bench.index)
        
        if len(common_index) < 10:
            return {'score': 0.5, 'details': 'Insufficient overlap'}
        
        signals_aligned = signals.loc[common_index]
        
        # Calculate correlations with benchmarks
        correlations = []
        for bench in benchmark_signals:
            bench_aligned = bench.loc[common_index]
            corr = signals_aligned.corr(bench_aligned)
            if not np.isnan(corr):
                correlations.append(abs(corr))
        
        if not correlations:
            return {'score': 0.5, 'details': 'No valid correlations'}
        
        # Diversity: lower average correlation = higher diversity
        avg_correlation = np.mean(correlations)
        diversity_score = 1.0 - avg_correlation
        
        return {
            'score': max(0.0, min(1.0, diversity_score)),
            'avg_correlation': avg_correlation,
            'n_benchmarks': len(benchmark_signals),
            'details': f"Avg correlation with benchmarks={avg_correlation:.3f}"
        }
    
    def _evaluate_originality(
        self,
        signals: pd.Series,
        benchmark_signals: List[pd.Series]
    ) -> Dict[str, Any]:
        """Evaluate originality.
        
        Measures uniqueness and novelty of the factor.
        """
        if not benchmark_signals:
            return {'score': 0.5, 'details': 'No benchmarks'}
        
        # Similar to diversity but with cosine distance for pattern matching
        common_index = signals.index
        for bench in benchmark_signals:
            common_index = common_index.intersection(bench.index)
        
        if len(common_index) < 10:
            return {'score': 0.5, 'details': 'Insufficient overlap'}
        
        signals_aligned = signals.loc[common_index].values
        signals_normalized = (signals_aligned - signals_aligned.mean()) / (signals_aligned.std() + 1e-10)
        
        # Cosine distances to benchmarks
        distances = []
        for bench in benchmark_signals:
            bench_aligned = bench.loc[common_index].values
            bench_normalized = (bench_aligned - bench_aligned.mean()) / (bench_aligned.std() + 1e-10)
            
            # Cosine distance
            try:
                dist = cosine(signals_normalized, bench_normalized)
                distances.append(dist)
            except:
                pass
        
        if not distances:
            return {'score': 0.5, 'details': 'No valid distances'}
        
        # Originality: higher average distance = higher originality
        avg_distance = np.mean(distances)
        originality_score = min(avg_distance * 2, 1.0)  # Scale to [0, 1]
        
        return {
            'score': max(0.0, min(1.0, originality_score)),
            'avg_distance': avg_distance,
            'n_benchmarks': len(benchmark_signals),
            'details': f"Avg cosine distance={avg_distance:.3f}"
        }
    
    def _empty_results(self) -> Dict[str, Any]:
        """Return empty results structure."""
        return {
            'predictive_power': {'score': 0.0, 'details': 'Insufficient data'},
            'stability': {'score': 0.0, 'details': 'Insufficient data'},
            'robustness': {'score': 0.0, 'details': 'Insufficient data'},
            'financial_logic': {'score': 0.0, 'details': 'Insufficient data'},
            'diversity': {'score': 0.0, 'details': 'Insufficient data'},
            'originality': {'score': 0.0, 'details': 'Insufficient data'},
            'overall_score': 0.0,
            'weights': {}
        }

