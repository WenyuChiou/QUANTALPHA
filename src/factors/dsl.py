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
        
        Returns:
            (is_valid, list_of_warnings)
        """
        warnings = []
        
        # Check each signal expression
        for signal in spec.signals:
            expr_warnings = self._check_expression(signal.expr, signal.id)
            warnings.extend(expr_warnings)
            
            # Check normalization
            if signal.normalize:
                norm_warnings = self._check_expression(signal.normalize, f"{signal.id}_normalize")
                warnings.extend(norm_warnings)
        
        # Check for common lookahead patterns
        yaml_str = spec.to_yaml().lower()
        if "future" in yaml_str or "forward" in yaml_str:
            warnings.append("Found 'future' or 'forward' keywords - potential lookahead")
        
        is_valid = len([w for w in warnings if "ERROR" in w]) == 0
        return is_valid, warnings
    
    def _check_expression(self, expr: str, context: str) -> List[str]:
        """Check an expression for lookahead issues."""
        warnings = []
        expr_lower = expr.lower()
        
        # Check for future-looking function names
        future_patterns = [
            r'\bfuture\w*\s*\(',
            r'\bforward\w*\s*\(',
            r'\blead\s*\(',
            r'\bshift\s*\(\s*-\d+',  # Negative shift (future)
        ]
        
        for pattern in future_patterns:
            if re.search(pattern, expr_lower):
                warnings.append(f"ERROR: {context} contains potential lookahead: {expr}")
        
        # Check RET_LAG usage - ensure positive lags
        lag_matches = re.findall(r'RET_LAG\s*\(\s*(\d+)\s*,\s*(\d+)', expr)
        for lag, period in lag_matches:
            if int(lag) < 1:
                warnings.append(f"ERROR: {context} RET_LAG has lag < 1 (lookahead): {expr}")
        
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
                e.g., {"signals.0.expr": "RET_LAG(1,126)", "targets.min_sharpe": 1.5}
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

