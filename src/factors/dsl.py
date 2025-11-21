"""Factor DSL parser with YAML validation and no-lookahead checks."""

import yaml
import re
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

from ..memory.factor_registry import FactorSpec, FactorRegistry


class DSLParser:
    """Parser for Factor DSL YAML specifications."""
    
    def __init__(self):
        self.registry = FactorRegistry()
    
    def parse(self, yaml_str: str) -> FactorSpec:
        """Parse YAML string into FactorSpec."""
        try:
            spec = FactorSpec.from_yaml(yaml_str)
            return spec
        except Exception as e:
            raise ValueError(f"Failed to parse Factor DSL: {e}")
    
    def parse_file(self, file_path: Path) -> FactorSpec:
        """Parse YAML file into FactorSpec."""
        return FactorSpec.from_file(file_path)
    
    def validate_no_lookahead(self, spec: FactorSpec) -> Tuple[bool, List[str]]:
        """Validate that the factor has no lookahead issues.
        
        Handles both DSL expressions and custom Python code.
        
        Returns:
            (is_valid, list_of_warnings)
        """
        warnings = []
        
        # Check each signal
        for signal in spec.signals:
            # Handle DSL expression
            if signal.expr:
                expr_warnings = self._check_expression(signal.expr, signal.id)
                warnings.extend(expr_warnings)
            
            # Handle custom code
            if signal.custom_code:
                code_warnings = self._check_custom_code(signal.custom_code, signal.id)
                warnings.extend(code_warnings)
            
            # Check normalization
            if signal.normalize:
                norm_warnings = self._check_expression(signal.normalize, f"{signal.id}_normalize")
                warnings.extend(norm_warnings)
        
        # Check for common lookahead patterns in YAML
        yaml_str = spec.to_yaml().lower()
        if "future" in yaml_str or "forward" in yaml_str:
            warnings.append("Found 'future' or 'forward' keywords - potential lookahead")
        
        is_valid = len([w for w in warnings if "ERROR" in w]) == 0
        return is_valid, warnings
    
    def _check_custom_code(self, code: str, context: str) -> List[str]:
        """Check custom Python code for lookahead issues.
        
        Uses the code validator from the nonlinear module.
        """
        warnings = []
        
        try:
            from ..factors.code_validator import CodeValidator
            
            validator = CodeValidator()
            is_valid, errors, code_warnings = validator.validate(code)
            
            # Convert errors to warnings with context
            for error in errors:
                warnings.append(f"ERROR in {context}: {error}")
            
            # Add code warnings with context
            for warning in code_warnings:
                warnings.append(f"WARNING in {context}: {warning}")
        
        except ImportError:
            warnings.append(f"WARNING: Could not import code validator for {context}")
        
        return warnings
    
    def _check_expression(self, expr: str, context: str) -> List[str]:
        """Check an expression for lookahead issues."""
        warnings = []
        expr_lower = expr.lower()
        
        # Check for future-looking function names
        future_patterns = [
            r'\bfuture\w*\s*\(',     # Matches future_return(), future_val(), etc.
            r'\bforward\w*\s*\(',    # Matches forward_return(), etc.
            r'\blead\s*\(',          # Matches lead() which is opposite of lag()
            r'\bshift\s*\(\s*-\d+',  # Matches shift(-n) which shifts data from future to present
        ]
        
        for pattern in future_patterns:
            if re.search(pattern, expr_lower):
                warnings.append(f"ERROR: {context} contains potential lookahead: {expr}")
        
        # Check RET_LAG usage - ensure positive lags
        lag_matches = re.findall(r'RET_LAG\s*\(\s*(\d+)\s*,\s*(\d+)', expr)
        for lag, period in lag_matches:
            if int(lag) < 1:
                warnings.append(f"ERROR: {context} RET_LAG has lag < 1 (lookahead): {expr}")
        
        # Check DELTA usage - ensure positive periods
        delta_matches = re.findall(r'DELTA\s*\(\s*[^,]+,\s*(\d+)', expr_lower)
        for period in delta_matches:
            if int(period) < 1:
                warnings.append(f"WARNING: {context} DELTA has period < 1: {expr}")
        
        # Check TS_RANK, TS_ARGMAX, TS_ARGMIN - ensure positive windows
        ts_functions = ['ts_rank', 'ts_argmax', 'ts_argmin']
        for func in ts_functions:
            func_matches = re.findall(rf'{func}\s*\(\s*[^,]+,\s*(\d+)', expr_lower)
            for window in func_matches:
                if int(window) < 1:
                    warnings.append(f"ERROR: {context} {func.upper()} has window < 1: {expr}")
        
        # Check DECAY_LINEAR - ensure positive windows
        decay_matches = re.findall(r'decay_linear\s*\(\s*[^,]+,\s*(\d+)', expr_lower)
        for window in decay_matches:
            if int(window) < 1:
                warnings.append(f"ERROR: {context} DECAY_LINEAR has window < 1: {expr}")
        
        # Check CORRELATION - ensure positive windows
        corr_matches = re.findall(r'correlation\s*\(\s*[^,]+,\s*[^,]+,\s*(\d+)', expr_lower)
        for window in corr_matches:
            if int(window) < 1:
                warnings.append(f"ERROR: {context} CORRELATION has window < 1: {expr}")
        
        # Check INDNEUTRALIZE syntax
        if 'indneutralize' in expr_lower or 'indclass_neutralize' in expr_lower:
            # Industry neutralization is safe (no lookahead)
            pass
        
        # Check for direct future return references
        if re.search(r'RET\[.*\+.*\]', expr) or re.search(r'RET\.shift\s*\(\s*-\d+', expr):
            warnings.append(f"ERROR: {context} may reference future returns: {expr}")
        
        return warnings
    
    def extract_parameters(self, spec: FactorSpec) -> Dict[str, Any]:
        """Extract parameterizable values from a factor spec."""
        params = {}
        
        # Extract from signals
        for signal in spec.signals:
            # Extract numeric parameters from expressions
            numbers = re.findall(r'\d+', signal.expr)
            if numbers:
                params[f"{signal.id}_params"] = [int(n) for n in numbers]
            
            # Extract function-specific parameters
            # RET_LAG(lag, period)
            lag_matches = re.findall(r'RET_LAG\s*\(\s*(\d+)\s*,\s*(\d+)', signal.expr)
            if lag_matches:
                params[f"{signal.id}_lag"] = int(lag_matches[0][0])
                params[f"{signal.id}_period"] = int(lag_matches[0][1])
            
            # DELTA(series, periods)
            delta_matches = re.findall(r'DELTA\s*\(\s*[^,]+,\s*(\d+)', signal.expr)
            if delta_matches:
                params[f"{signal.id}_delta_periods"] = int(delta_matches[0])
            
            # TS_RANK(series, window)
            ts_rank_matches = re.findall(r'TS_RANK\s*\(\s*[^,]+,\s*(\d+)', signal.expr, re.IGNORECASE)
            if ts_rank_matches:
                params[f"{signal.id}_ts_rank_window"] = int(ts_rank_matches[0])
            
            # DECAY_LINEAR(series, window)
            decay_matches = re.findall(r'DECAY_LINEAR\s*\(\s*[^,]+,\s*(\d+)', signal.expr, re.IGNORECASE)
            if decay_matches:
                params[f"{signal.id}_decay_window"] = int(decay_matches[0])
            
            # CORRELATION(series1, series2, window)
            corr_matches = re.findall(r'CORRELATION\s*\(\s*[^,]+,\s*[^,]+,\s*(\d+)', signal.expr, re.IGNORECASE)
            if corr_matches:
                params[f"{signal.id}_corr_window"] = int(corr_matches[0])
            
            # Check for industry neutralization
            if 'INDNEUTRALIZE' in signal.expr.upper() or 'INDCLASS_NEUTRALIZE' in signal.expr.upper():
                params[f"{signal.id}_industry_neutralized"] = True
            
            # Extract normalization window if present
            if signal.normalize:
                norm_nums = re.findall(r'\d+', signal.normalize)
                if norm_nums:
                    params[f"{signal.id}_norm_window"] = int(norm_nums[0])
        
        # Extract validation parameters
        params["min_history_days"] = spec.validation.min_history_days
        params["purge_gap_days"] = spec.validation.purge_gap_days
        
        # Extract target parameters
        params["min_sharpe"] = spec.targets.min_sharpe
        params["max_maxdd"] = spec.targets.max_maxdd
        params["min_avg_ic"] = spec.targets.min_avg_ic
        
        return params
    
    def mutate(self, spec: FactorSpec, mutations: Dict[str, Any]) -> FactorSpec:
        """Create a mutated version of a factor spec.
        
        Args:
            spec: Original factor spec
            mutations: Dictionary of mutations to apply
                e.g., {"signals.0.expr": "RET_LAG(1,126)", "targets.min_sharpe": 1.8}
        """
        spec_dict = spec.dict()
        
        # Apply mutations using dot notation
        for key, value in mutations.items():
            keys = key.split('.')
            target = spec_dict
            for k in keys[:-1]:
                if k.isdigit():
                    target = target[int(k)]
                else:
                    target = target[k]
            target[keys[-1]] = value
        
        # Recreate spec from mutated dict
        return FactorSpec(**spec_dict)
    
    def validate_supported_operations(self, spec: FactorSpec) -> Tuple[bool, List[str]]:
        """Validate that all operations in the factor are supported.
        
        Returns:
            (is_valid, list_of_warnings)
        """
        warnings = []
        supported_ops = [
            'RET_LAG', 'RET_D', 'ROLL_STD', 'ROLL_MEAN', 'ROLL_MAX', 'ROLL_MIN',
            'VOL_TARGET', 'ZSCORE', 'CORRELATION_DECAY', 'DRAWDOWN_RECOVERY',
            'SKEW', 'KURTOSIS', 'RANK', 'QUANTILE', 'REGIME_VOLATILITY', 'REGIME_TREND',
            'DELTA', 'DECAY_LINEAR', 'TS_RANK', 'TS_ARGMAX', 'TS_ARGMIN',
            'CORRELATION', 'COVARIANCE', 'VWAP', 'ADV', 'INDNEUTRALIZE',
            'INDCLASS_NEUTRALIZE', 'SCALE', 'SUM', 'PRODUCT', 'SIGN', 'POWER',
            'LOG', 'ABS', 'MAX', 'MIN'
        ]
        
        for signal in spec.signals:
            # Extract function names from expression
            func_matches = re.findall(r'(\w+)\s*\(', signal.expr.upper())
            for func in func_matches:
                if func not in [op.upper() for op in supported_ops] and func not in ['ZSCORE_252', 'ZSCORE_63', 'ZSCORE_21']:
                    warnings.append(f"ERROR: {signal.id} uses unsupported operation: {func}")
        
        is_valid = len([w for w in warnings if "ERROR" in w]) == 0
        return is_valid, warnings
    
    def get_operation_complexity(self, spec: FactorSpec) -> Dict[str, Any]:
        """Calculate complexity metrics for the factor.
        
        Returns:
            Dictionary with complexity metrics
        """
        from ..backtest.decay_monitor import AlphaDecayMonitor
        
        monitor = AlphaDecayMonitor()
        return monitor.calculate_complexity(spec.to_yaml())

