"""Tests for sandbox executor."""

import pytest
import pandas as pd
import numpy as np
from src.factors.sandbox import SandboxExecutor, execute_code_safely, TimeoutException


class TestSandboxExecutor:
    """Test sandboxed code execution."""
    
    def test_simple_execution(self):
        """Test simple code execution."""
        code = """
x = 1 + 1
result = x
"""
        sandbox = SandboxExecutor(timeout=5)
        result = sandbox.execute(code)
        
        assert result['success']
        assert result['result'] == 2
        assert result['error'] is None
    
    def test_numpy_pandas_available(self):
        """Test that numpy and pandas are available."""
        code = """
import numpy as np
import pandas as pd

arr = np.array([1, 2, 3])
df = pd.DataFrame({'a': [1, 2, 3]})
result = len(df)
"""
        sandbox = SandboxExecutor(timeout=5)
        result = sandbox.execute(code)
        
        assert result['success']
        assert result['result'] == 3
    
    def test_forbidden_operations_blocked(self):
        """Test that forbidden operations fail."""
        # Note: These should be caught by validator, but sandbox provides defense in depth
        forbidden_codes = [
            "import os\nos.system('ls')",  # Will fail on import
        ]
        
        sandbox = SandboxExecutor(timeout=5)
        
        for code in forbidden_codes:
            result = sandbox.execute(code)
            # Should fail (either import error or execution error)
            assert not result['success']
    
    def test_timeout_enforcement_unix(self):
        """Test timeout enforcement (Unix only)."""
        import sys
        if sys.platform == 'win32':
            pytest.skip("Timeout not enforced on Windows")
        
        code = """
import time
time.sleep(10)  # Sleep longer than timeout
"""
        sandbox = SandboxExecutor(timeout=2)
        result = sandbox.execute(code)
        
        assert not result['success']
        assert "timeout" in result['error'].lower()
    
    def test_exception_handling(self):
        """Test that exceptions are caught and reported."""
        code = """
x = 1 / 0  # ZeroDivisionError
"""
        sandbox = SandboxExecutor(timeout=5)
        result = sandbox.execute(code)
        
        assert not result['success']
        assert "ZeroDivisionError" in result['error']
    
    def test_global_variables(self):
        """Test passing global variables."""
        code = """
result = prices.mean()
"""
        prices = pd.DataFrame({'A': [100, 101, 102]})
        
        sandbox = SandboxExecutor(timeout=5)
        result = sandbox.execute(code, global_vars={'prices': prices})
        
        assert result['success']
        assert isinstance(result['result'], pd.Series)
    
    def test_local_variables(self):
        """Test that local variables are captured."""
        code = """
x = 42
y = x * 2
"""
        sandbox = SandboxExecutor(timeout=5)
        result = sandbox.execute(code)
        
        assert result['success']
        assert result['locals']['x'] == 42
        assert result['locals']['y'] == 84
    
    def test_convenience_function(self):
        """Test execute_code_safely convenience function."""
        code = """
signal = prices * 2
result = signal
"""
        prices = pd.DataFrame({'A': [1, 2, 3]})
        
        result = execute_code_safely(code, timeout=5, prices=prices)
        
        assert result['success']
        assert isinstance(result['result'], pd.DataFrame)
