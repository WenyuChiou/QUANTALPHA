"""Backtest analysis - comprehensive analysis of factor performance."""

from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
import pandas as pd
import numpy as np

from ..backtest.metrics import (
    sharpe, max_drawdown, information_coefficient,
    information_ratio, turnover_monthly, hit_rate
)
from ..backtest.multidim_eval import MultiDimensionalEvaluator
from ..backtest.decay_monitor import AlphaDecayMonitor
from ..analysis.guidelines import get_analysis_guidelines


@dataclass
class BacktestAnalysis:
    """Comprehensive backtest analysis report."""
    run_id: str
    factor_name: str
    
    # Performance metrics
    sharpe_ratio: float
    max_drawdown: float
    annual_return: float
    annual_volatility: float
    information_ratio: float
    information_coefficient: float
    turnover_monthly: float
    hit_rate: float
    
    # Risk metrics
    var_95: float  # Value at Risk (95%)
    cvar_95: float  # Conditional VaR
    tail_ratio: float  # Ratio of 95th to 5th percentile returns
    
    # Stability metrics
    rolling_sharpe_stability: float  # Std of rolling Sharpe
    ic_stability: float  # Std of rolling IC
    
    # Regime analysis
    bull_market_performance: Dict[str, float]
    bear_market_performance: Dict[str, float]
    high_vol_performance: Dict[str, float]
    low_vol_performance: Dict[str, float]
    
    # Decay analysis
    ic_decay_rate: float
    performance_decay: bool
    
    # Multi-dimensional evaluation
    predictive_power_score: float
    stability_score: float
    robustness_score: float
    
    # Issues and concerns
    issues: List[str]
    warnings: List[str]
    
    analysis_date: datetime = None
    
    def __post_init__(self):
        """Initialize timestamps."""
        if self.analysis_date is None:
            self.analysis_date = datetime.now()


class BacktestAnalyst:
    """Analyze backtest results comprehensively."""
    
    def __init__(self):
        """Initialize backtest analyst."""
        self.evaluator = MultiDimensionalEvaluator()
        self.decay_monitor = AlphaDecayMonitor()
        self.guidelines = get_analysis_guidelines()
    
    def analyze(
        self,
        signals: pd.Series,
        returns: pd.Series,
        prices: pd.Series,
        equity_curve: pd.Series,
        run_id: str,
        factor_name: str
    ) -> BacktestAnalysis:
        """Perform comprehensive backtest analysis.
        
        Args:
            signals: Factor signals
            returns: Portfolio returns
            prices: Price series (for regime analysis)
            equity_curve: Cumulative equity curve
            run_id: Run identifier
            factor_name: Factor name
        
        Returns:
            Comprehensive analysis report
        """
        # Basic performance metrics
        sharpe_ratio = sharpe(returns)
        max_dd = max_drawdown(equity_curve)
        ann_ret = returns.mean() * 252
        ann_vol = returns.std() * np.sqrt(252)
        ic = information_coefficient(signals, returns)
        ir = information_ratio(returns)
        turnover = turnover_monthly(signals)
        hit_rate_val = hit_rate(signals, returns)
        
        # Risk metrics
        var_95 = np.percentile(returns, 5)
        cvar_95 = returns[returns <= var_95].mean()
        tail_ratio = np.percentile(returns, 95) / abs(np.percentile(returns, 5))
        
        # Stability metrics
        rolling_sharpe = returns.rolling(63).apply(lambda x: sharpe(x))
        rolling_sharpe_std = rolling_sharpe.std()
        
        rolling_ic = []
        for i in range(63, len(signals)):
            window_signals = signals.iloc[i-63:i]
            window_returns = returns.iloc[i-63:i]
            if len(window_signals) > 0:
                rolling_ic.append(information_coefficient(window_signals, window_returns))
        ic_stability = np.std(rolling_ic) if rolling_ic else 0.0
        
        # Regime analysis (simplified)
        volatility = prices.pct_change(1).rolling(21).std()
        high_vol_threshold = volatility.quantile(0.75)
        low_vol_threshold = volatility.quantile(0.25)
        
        high_vol_mask = volatility > high_vol_threshold
        low_vol_mask = volatility < low_vol_threshold
        
        bull_market_performance = {
            'sharpe': sharpe(returns[returns > 0]) if len(returns[returns > 0]) > 0 else 0.0,
            'return': returns[returns > 0].mean() * 252 if len(returns[returns > 0]) > 0 else 0.0
        }
        
        bear_market_performance = {
            'sharpe': sharpe(returns[returns < 0]) if len(returns[returns < 0]) > 0 else 0.0,
            'return': returns[returns < 0].mean() * 252 if len(returns[returns < 0]) > 0 else 0.0
        }
        
        high_vol_performance = {
            'sharpe': sharpe(returns[high_vol_mask]) if high_vol_mask.sum() > 0 else 0.0,
            'return': returns[high_vol_mask].mean() * 252 if high_vol_mask.sum() > 0 else 0.0
        }
        
        low_vol_performance = {
            'sharpe': sharpe(returns[low_vol_mask]) if low_vol_mask.sum() > 0 else 0.0,
            'return': returns[low_vol_mask].mean() * 252 if low_vol_mask.sum() > 0 else 0.0
        }
        
        # Decay analysis
        decay_result = self.decay_monitor.track_ic_decay(signals, returns)
        ic_decay_rate = decay_result.get('decay_rate', 0.0)
        performance_decay = decay_result.get('decay_detected', False)
        
        # Multi-dimensional evaluation
        eval_results = self.evaluator.evaluate(signals, returns, prices)
        predictive_power = eval_results['predictive_power']['score']
        stability = eval_results['stability']['score']
        robustness = eval_results['robustness']['score']
        
        # Apply analysis guidelines
        metrics_dict = {
            'sharpe': sharpe_ratio,
            'maxdd': max_dd,
            'avg_ic': ic,
            'ir': ir,
            'hit_rate': hit_rate_val,
            'turnover_monthly': turnover
        }
        
        performance_eval = self.guidelines.evaluate_performance(metrics_dict)
        
        # Identify issues based on guidelines
        issues = performance_eval.get('failures', [])
        warnings = performance_eval.get('warnings', [])
        
        # Add stability evaluation
        stability_metrics = {
            'rolling_sharpe_std': rolling_sharpe_std,
            'rolling_sharpe_mean': sharpe_ratio,
            'ic_stability': ic_stability
        }
        stability_eval = self.guidelines.evaluate_stability(stability_metrics)
        warnings.extend(stability_eval.get('issues', []))
        
        # Add regime evaluation
        regime_metrics = {
            'bull': bull_market_performance,
            'bear': bear_market_performance,
            'high_vol': high_vol_performance,
            'low_vol': low_vol_performance
        }
        regime_eval = self.guidelines.evaluate_regime_robustness(regime_metrics)
        if not regime_eval['passed']:
            warnings.extend(regime_eval.get('issues', []))
        
        # Add decay evaluation
        decay_metrics = {
            'decay_rate': ic_decay_rate,
            'decay_detected': performance_decay
        }
        decay_eval = self.guidelines.evaluate_decay(decay_metrics)
        warnings.extend(decay_eval.get('warnings', []))
        
        # Additional checks based on guidelines
        if var_95 < self.guidelines.max_var_95:
            warnings.append(f"High VaR(95%): {var_95:.4f} < {self.guidelines.max_var_95:.4f}")
        
        if tail_ratio < self.guidelines.min_tail_ratio:
            warnings.append(f"Low tail ratio: {tail_ratio:.2f} < {self.guidelines.min_tail_ratio:.2f}")
        
        analysis = BacktestAnalysis(
            run_id=run_id,
            factor_name=factor_name,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_dd,
            annual_return=ann_ret,
            annual_volatility=ann_vol,
            information_ratio=ir,
            information_coefficient=ic,
            turnover_monthly=turnover,
            hit_rate=hit_rate_val,
            var_95=var_95,
            cvar_95=cvar_95,
            tail_ratio=tail_ratio,
            rolling_sharpe_stability=rolling_sharpe_std,
            ic_stability=ic_stability,
            bull_market_performance=bull_market_performance,
            bear_market_performance=bear_market_performance,
            high_vol_performance=high_vol_performance,
            low_vol_performance=low_vol_performance,
            ic_decay_rate=ic_decay_rate,
            performance_decay=performance_decay,
            predictive_power_score=predictive_power,
            stability_score=stability,
            robustness_score=robustness,
            issues=issues,
            warnings=warnings
        )
        
        return analysis
    
    def generate_report(self, analysis: BacktestAnalysis) -> str:
        """Generate human-readable analysis report following analysis guidelines.
        
        Args:
            analysis: Analysis to report
        
        Returns:
            Report text
        """
        # Evaluate against guidelines
        metrics_dict = {
            'sharpe': analysis.sharpe_ratio,
            'maxdd': analysis.max_drawdown,
            'avg_ic': analysis.information_coefficient,
            'ir': analysis.information_ratio,
            'hit_rate': analysis.hit_rate,
            'turnover_monthly': analysis.turnover_monthly
        }
        performance_eval = self.guidelines.evaluate_performance(metrics_dict)
        
        report = f"""
BACKTEST ANALYSIS REPORT
========================

Factor: {analysis.factor_name}
Run ID: {analysis.run_id}
Analysis Date: {analysis.analysis_date.strftime('%Y-%m-%d %H:%M:%S')}

ANALYSIS GUIDELINES COMPLIANCE
-------------------------------
Overall Status: {'✅ PASSED' if performance_eval['passed'] else '❌ FAILED'}

PERFORMANCE METRICS (vs Requirements)
--------------------------------------
Sharpe Ratio:        {analysis.sharpe_ratio:.2f} {'✅' if analysis.sharpe_ratio >= 1.8 else '❌'} (Required: >= 1.8)
Max Drawdown:        {analysis.max_drawdown:.2%} {'✅' if abs(analysis.max_drawdown) <= 0.25 else '❌'} (Required: <= -25%)
Annual Return:       {analysis.annual_return:.2%}
Annual Volatility:   {analysis.annual_volatility:.2%}
Information Ratio:   {analysis.information_ratio:.2f} {'✅' if analysis.information_ratio >= 0.5 else '⚠️'} (Required: >= 0.5)
Information Coeff:   {analysis.information_coefficient:.4f} {'✅' if analysis.information_coefficient >= 0.05 else '⚠️'} (Required: >= 0.05)
Turnover (monthly): {analysis.turnover_monthly:.1f}% {'✅' if analysis.turnover_monthly <= 250 else '⚠️'} (Required: <= 250%)
Hit Rate:           {analysis.hit_rate:.2%} {'✅' if analysis.hit_rate >= 0.52 else '⚠️'} (Required: >= 52%)

RISK METRICS
-----------
VaR (95%):          {analysis.var_95:.4f}
CVaR (95%):         {analysis.cvar_95:.4f}
Tail Ratio:         {analysis.tail_ratio:.2f}

STABILITY METRICS
----------------
Rolling Sharpe Std: {analysis.rolling_sharpe_stability:.2f}
IC Stability:       {analysis.ic_stability:.4f}

REGIME ANALYSIS
---------------
Bull Market:
  Sharpe: {analysis.bull_market_performance['sharpe']:.2f}
  Return: {analysis.bull_market_performance['return']:.2%}

Bear Market:
  Sharpe: {analysis.bear_market_performance['sharpe']:.2f}
  Return: {analysis.bear_market_performance['return']:.2%}

High Volatility:
  Sharpe: {analysis.high_vol_performance['sharpe']:.2f}
  Return: {analysis.high_vol_performance['return']:.2%}

Low Volatility:
  Sharpe: {analysis.low_vol_performance['sharpe']:.2f}
  Return: {analysis.low_vol_performance['return']:.2%}

DECAY ANALYSIS
-------------
IC Decay Rate:      {analysis.ic_decay_rate:.2%}
Decay Detected:     {analysis.performance_decay}

MULTI-DIMENSIONAL EVALUATION
----------------------------
Predictive Power:   {analysis.predictive_power_score:.2f}
Stability:          {analysis.stability_score:.2f}
Robustness:         {analysis.robustness_score:.2f}

ISSUES & WARNINGS
-----------------
"""
        if analysis.issues:
            report += "\nIssues:\n"
            for issue in analysis.issues:
                report += f"  - {issue}\n"
        
        if analysis.warnings:
            report += "\nWarnings:\n"
            for warning in analysis.warnings:
                report += f"  - {warning}\n"
        
        return report

