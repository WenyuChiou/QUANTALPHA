"""Alpha decay monitoring and mitigation.

Tracks IC decay over time and implements regularized exploration and complexity control.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta

from .metrics import information_coefficient
from ..memory.store import ExperimentStore


class AlphaDecayMonitor:
    """Monitor alpha decay and implement mitigation strategies."""
    
    def __init__(self, store: Optional[ExperimentStore] = None):
        """Initialize decay monitor.
        
        Args:
            store: Experiment store for retrieving historical runs
        """
        self.store = store
    
    def track_ic_decay(
        self,
        signals: pd.Series,
        returns: pd.Series,
        window: int = 63,
        min_periods: int = 10
    ) -> Dict[str, Any]:
        """Track IC decay over time.
        
        Args:
            signals: Factor signals
            returns: Next period returns
            window: Rolling window for IC calculation
            min_periods: Minimum periods required
        
        Returns:
            Dictionary with decay metrics
        """
        # Align data
        aligned = pd.DataFrame({
            'signals': signals,
            'returns': returns
        }).dropna()
        
        if len(aligned) < min_periods:
            return {
                'decay_rate': 0.0,
                'initial_ic': 0.0,
                'final_ic': 0.0,
                'decay_detected': False,
                'half_life': None
            }
        
        # Calculate rolling IC
        rolling_ic = []
        ic_dates = []
        
        for i in range(window, len(aligned)):
            window_signals = aligned['signals'].iloc[i-window:i]
            window_returns = aligned['returns'].iloc[i-window:i]
            ic = information_coefficient(window_signals, window_returns)
            rolling_ic.append(ic)
            ic_dates.append(aligned.index[i])
        
        if len(rolling_ic) < min_periods:
            return {
                'decay_rate': 0.0,
                'initial_ic': 0.0,
                'final_ic': 0.0,
                'decay_detected': False,
                'half_life': None
            }
        
        ic_series = pd.Series(rolling_ic, index=ic_dates)
        
        # Calculate decay metrics
        initial_ic = ic_series.iloc[:len(ic_series)//3].mean()  # First third
        final_ic = ic_series.iloc[-len(ic_series)//3:].mean()  # Last third
        
        # Decay rate (negative = decay, positive = improvement)
        decay_rate = (final_ic - initial_ic) / (abs(initial_ic) + 0.01)
        
        # Detect decay
        decay_detected = decay_rate < -0.2  # More than 20% decay
        
        # Half-life estimation (simplified)
        if decay_rate < -0.1:
            # Estimate half-life using exponential decay model
            try:
                # Fit exponential decay: IC(t) = IC(0) * exp(-lambda * t)
                x = np.arange(len(ic_series))
                y = ic_series.values
                
                # Remove zeros and negatives for log
                mask = (y > 0) & (np.isfinite(y))
                if mask.sum() > 5:
                    log_y = np.log(y[mask])
                    x_masked = x[mask]
                    
                    # Linear regression: log(IC) = log(IC0) - lambda * t
                    coeffs = np.polyfit(x_masked, log_y, 1)
                    lambda_param = -coeffs[0]  # Decay parameter
                    
                    if lambda_param > 0:
                        half_life = np.log(2) / lambda_param
                    else:
                        half_life = None
                else:
                    half_life = None
            except:
                half_life = None
        else:
            half_life = None
        
        return {
            'decay_rate': decay_rate,
            'initial_ic': initial_ic,
            'final_ic': final_ic,
            'decay_detected': decay_detected,
            'half_life': half_life,
            'ic_series': ic_series,
            'n_periods': len(rolling_ic)
        }
    
    def calculate_complexity(
        self,
        factor_yaml: str
    ) -> Dict[str, Any]:
        """Calculate factor complexity.
        
        Args:
            factor_yaml: Factor DSL YAML string
        
        Returns:
            Complexity metrics
        """
        import yaml
        import re
        
        try:
            spec = yaml.safe_load(factor_yaml)
        except:
            return {
                'complexity_score': 0.0,
                'n_signals': 0,
                'n_operations': 0,
                'max_nesting': 0,
                'details': 'Failed to parse factor'
            }
        
        signals = spec.get('signals', [])
        n_signals = len(signals)
        
        # Count operations in expressions
        n_operations = 0
        max_nesting = 0
        
        for signal in signals:
            expr = signal.get('expr', '')
            
            # Count function calls
            function_calls = len(re.findall(r'\w+\s*\(', expr))
            n_operations += function_calls
            
            # Estimate nesting depth (parentheses)
            depth = 0
            max_depth = 0
            for char in expr:
                if char == '(':
                    depth += 1
                    max_depth = max(max_depth, depth)
                elif char == ')':
                    depth -= 1
            max_nesting = max(max_nesting, max_depth)
        
        # Complexity score (normalized)
        # Higher = more complex
        complexity_score = min(
            (n_signals * 0.3 + n_operations * 0.4 + max_nesting * 0.3) / 10.0,
            1.0
        )
        
        return {
            'complexity_score': complexity_score,
            'n_signals': n_signals,
            'n_operations': n_operations,
            'max_nesting': max_nesting,
            'details': f"Signals={n_signals}, Ops={n_operations}, Nesting={max_nesting}"
        }
    
    def regularized_exploration(
        self,
        candidate_factors: List[Dict[str, Any]],
        historical_factors: Optional[List[Dict[str, Any]]] = None,
        complexity_penalty: float = 0.1,
        similarity_penalty: float = 0.2
    ) -> List[Dict[str, Any]]:
        """Apply regularized exploration to factor candidates.
        
        Penalizes:
        - High complexity
        - Similarity to historical factors
        - Overfitting patterns
        
        Args:
            candidate_factors: List of candidate factor dicts with 'yaml' and 'metrics'
            historical_factors: List of historical factor dicts
            complexity_penalty: Penalty weight for complexity
            similarity_penalty: Penalty weight for similarity
        
        Returns:
            Scored and ranked candidates
        """
        scored_candidates = []
        
        for candidate in candidate_factors:
            score = candidate.get('metrics', {}).get('sharpe', 0.0) or 0.0
            
            # Complexity penalty
            complexity = self.calculate_complexity(candidate.get('yaml', ''))
            complexity_penalty_score = complexity['complexity_score'] * complexity_penalty
            score -= complexity_penalty_score
            
            # Similarity penalty (if historical factors provided)
            if historical_factors:
                similarity_scores = []
                for hist_factor in historical_factors:
                    # Simple similarity: compare YAML structure
                    similarity = self._calculate_similarity(
                        candidate.get('yaml', ''),
                        hist_factor.get('yaml', '')
                    )
                    similarity_scores.append(similarity)
                
                if similarity_scores:
                    max_similarity = max(similarity_scores)
                    similarity_penalty_score = max_similarity * similarity_penalty
                    score -= similarity_penalty_score
            
            scored_candidates.append({
                **candidate,
                'regularized_score': score,
                'complexity': complexity,
                'original_score': candidate.get('metrics', {}).get('sharpe', 0.0)
            })
        
        # Sort by regularized score
        scored_candidates.sort(key=lambda x: x['regularized_score'], reverse=True)
        
        return scored_candidates
    
    def _calculate_similarity(
        self,
        yaml1: str,
        yaml2: str
    ) -> float:
        """Calculate similarity between two factor YAMLs.
        
        Args:
            yaml1: First factor YAML
            yaml2: Second factor YAML
        
        Returns:
            Similarity score [0, 1]
        """
        import re
        
        # Extract key patterns
        def extract_patterns(yaml_str):
            # Extract function names
            functions = set(re.findall(r'(\w+)\s*\(', yaml_str))
            # Extract numbers (parameters)
            numbers = set(re.findall(r'\b(\d+)\b', yaml_str))
            return functions, numbers
        
        patterns1 = extract_patterns(yaml1)
        patterns2 = extract_patterns(yaml2)
        
        # Jaccard similarity
        func_intersection = len(patterns1[0] & patterns2[0])
        func_union = len(patterns1[0] | patterns2[0])
        func_similarity = func_intersection / func_union if func_union > 0 else 0.0
        
        num_intersection = len(patterns1[1] & patterns2[1])
        num_union = len(patterns1[1] | patterns2[1])
        num_similarity = num_intersection / num_union if num_union > 0 else 0.0
        
        # Combined similarity
        similarity = (func_similarity * 0.7 + num_similarity * 0.3)
        
        return similarity
    
    def detect_decay_patterns(
        self,
        run_id: int
    ) -> Dict[str, Any]:
        """Detect decay patterns from historical run.
        
        Args:
            run_id: Run ID to analyze
        
        Returns:
            Decay pattern analysis
        """
        if not self.store:
            return {'error': 'Store not available'}
        
        run = self.store.get_session().query(self.store.Run).filter(
            self.store.Run.id == run_id
        ).first()
        
        if not run:
            return {'error': 'Run not found'}
        
        # Get metrics over time (would need time-series metrics stored)
        # For now, return basic analysis
        metrics = run.metrics[0] if run.metrics else None
        
        if not metrics:
            return {'error': 'No metrics found'}
        
        # Check if IC is declining (would need historical IC data)
        # Simplified: check if current IC is below threshold
        ic_below_threshold = metrics.avg_ic < 0.05
        
        return {
            'run_id': run_id,
            'current_ic': metrics.avg_ic,
            'ic_below_threshold': ic_below_threshold,
            'decay_suspected': ic_below_threshold,
            'recommendation': 'Monitor closely' if ic_below_threshold else 'Stable'
        }

