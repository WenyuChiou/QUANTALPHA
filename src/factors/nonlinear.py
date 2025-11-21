"""Nonlinear factor executor for custom Python code.

This module executes custom Python code to generate factor signals,
with security validation and sandboxed execution.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path

from .code_validator import CodeValidator
from .sandbox import SandboxExecutor


class NonlinearFactorExecutor:
    """Execute custom Python code for nonlinear alpha factors."""
    
    def __init__(
        self,
        timeout: int = 60,
        validate_code: bool = True
    ):
        """Initialize nonlinear factor executor.
        
        Args:
            timeout: Maximum execution time in seconds
            validate_code: Whether to validate code before execution
        """
        self.timeout = timeout
        self.validate_code_flag = validate_code
        self.validator = CodeValidator()
        self.sandbox = SandboxExecutor(timeout=timeout)
    
    def execute_custom_code(
        self,
        code: str,
        prices: pd.DataFrame,
        returns: pd.DataFrame,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute custom Python code to generate factor signals.
        
        Args:
            code: Python code to execute
            prices: Price DataFrame (dates x tickers)
            returns: Returns DataFrame (dates x tickers)
            **kwargs: Additional variables to pass to code
            
        Returns:
            Dictionary with:
            {
                'success': bool,
                'signals': pd.DataFrame (if success),
                'error': str (if failure),
                'warnings': List[str]
            }
        """
        warnings = []
        
        # 1. Validate code
        if self.validate_code_flag:
            is_valid, errors, val_warnings = self.validator.validate(code)
            warnings.extend(val_warnings)
            
            if not is_valid:
                return {
                    'success': False,
                    'signals': None,
                    'error': f"Code validation failed: {'; '.join(errors)}",
                    'warnings': warnings
                }
        
        # 2. Prepare execution environment
        global_vars = {
            'prices': prices,
            'returns': returns,
            'pd': pd,
            'np': np,
            **kwargs
        }
        
        # 3. Execute code in sandbox
        result = self.sandbox.execute(code, global_vars=global_vars)
        
        if not result['success']:
            return {
                'success': False,
                'signals': None,
                'error': result['error'],
                'warnings': warnings
            }
        
        # 4. Extract signals from result
        signals = self._extract_signals(result['locals'], prices.shape)
        
        if signals is None:
            return {
                'success': False,
                'signals': None,
                'error': "Code did not return valid signals (expected pd.DataFrame or pd.Series)",
                'warnings': warnings
            }
        
        # 5. Validate signals shape
        if signals.shape[0] != prices.shape[0]:
            warnings.append(
                f"Signal length ({signals.shape[0]}) != price length ({prices.shape[0]})"
            )
        
        return {
            'success': True,
            'signals': signals,
            'error': None,
            'warnings': warnings
        }
    
    def _extract_signals(
        self,
        locals_dict: Dict[str, Any],
        expected_shape: Tuple[int, int]
    ) -> Optional[pd.DataFrame]:
        """Extract signals from execution locals.
        
        Looks for:
        1. Variable named 'result'
        2. Variable named 'return' (legacy)
        3. Last pd.DataFrame or pd.Series in locals
        4. Any pd.DataFrame or pd.Series
        
        Args:
            locals_dict: Local variables from execution
            expected_shape: Expected (n_dates, n_tickers)
            
        Returns:
            Signals DataFrame or None
        """
        # 1. Check for explicit 'result' variable (preferred)
        if 'result' in locals_dict:
            data = locals_dict['result']
            if isinstance(data, (pd.DataFrame, pd.Series)):
                return self._ensure_dataframe(data, expected_shape)
        
        # 2. Check for 'return' variable (legacy)
        if 'return' in locals_dict:
            data = locals_dict['return']
            if isinstance(data, (pd.DataFrame, pd.Series)):
                return self._ensure_dataframe(data, expected_shape)
        
        # 3. Find last DataFrame or Series
        dataframes = []
        for key, value in locals_dict.items():
            if isinstance(value, (pd.DataFrame, pd.Series)) and not key.startswith('_'):
                dataframes.append((key, value))
        
        if dataframes:
            # Return the last one
            _, last_df = dataframes[-1]
            return self._ensure_dataframe(last_df, expected_shape)
        
        return None
    
    def _ensure_dataframe(
        self,
        data: Any,
        expected_shape: Tuple[int, int]
    ) -> pd.DataFrame:
        """Ensure data is a DataFrame with correct shape.
        
        Args:
            data: pd.Series or pd.DataFrame
            expected_shape: (n_dates, n_tickers)
            
        Returns:
            DataFrame
        """
        if isinstance(data, pd.Series):
            # Convert Series to DataFrame
            # Assume it's a single column
            data = data.to_frame()
        
        # Ensure it's a DataFrame
        if not isinstance(data, pd.DataFrame):
            raise ValueError(f"Expected DataFrame, got {type(data)}")
        
        return data


def execute_nonlinear_factor(
    code: str,
    prices: pd.DataFrame,
    returns: pd.DataFrame,
    timeout: int = 60,
    **kwargs
) -> Dict[str, Any]:
    """Convenience function to execute nonlinear factor code.
    
    Args:
        code: Python code to execute
        prices: Price DataFrame
        returns: Returns DataFrame
        timeout: Timeout in seconds
        **kwargs: Additional variables
        
    Returns:
        Execution result dictionary
    """
    executor = NonlinearFactorExecutor(timeout=timeout)
    return executor.execute_custom_code(code, prices, returns, **kwargs)
