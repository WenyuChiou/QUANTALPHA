"""Tests for code validator."""

import pytest
from src.factors.code_validator import CodeValidator, validate_python_code


class TestCodeValidator:
    """Test code validation functionality."""
    
    def test_valid_code(self):
        """Test that valid code passes validation."""
        code = """
import numpy as np
import pandas as pd

mom = returns.rolling(21).mean()
signal = mom / mom.rolling(252).std()
"""
        validator = CodeValidator()
        is_valid, errors, warnings = validator.validate(code)
        
        assert is_valid
        assert len(errors) == 0
    
    def test_syntax_error(self):
        """Test that syntax errors are caught."""
        code = "def foo(:\n    pass"
        
        validator = CodeValidator()
        is_valid, errors, warnings = validator.validate(code)
        
        assert not is_valid
        assert len(errors) > 0
        assert "syntax" in errors[0].lower()
    
    def test_forbidden_operations(self):
        """Test that forbidden operations are blocked."""
        forbidden_codes = [
            "open('file.txt', 'r')",
            "exec('print(1)')",
            "eval('1+1')",
            "__import__('os')",
            "os.system('ls')",
        ]
        
        validator = CodeValidator()
        
        for code in forbidden_codes:
            is_valid, errors, warnings = validator.validate(code)
            assert not is_valid, f"Should reject: {code}"
            assert any("forbidden" in e.lower() for e in errors)
    
    def test_forbidden_imports(self):
        """Test that forbidden modules cannot be imported."""
        forbidden_imports = [
            "import os",
            "import sys",
            "import subprocess",
            "from os import system",
            "import socket",
        ]
        
        validator = CodeValidator()
        
        for code in forbidden_imports:
            is_valid, errors, warnings = validator.validate(code)
            assert not is_valid, f"Should reject: {code}"
            assert any("forbidden" in e.lower() for e in errors)
    
    def test_allowed_imports(self):
        """Test that allowed modules can be imported."""
        allowed_imports = [
            "import numpy as np",
            "import pandas as pd",
            "from sklearn.ensemble import RandomForestRegressor",
            "import scipy.stats",
            "from statsmodels.api import OLS",
        ]
        
        validator = CodeValidator()
        
        for code in allowed_imports:
            is_valid, errors, warnings = validator.validate(code)
            assert is_valid, f"Should allow: {code}"
    
    def test_lookahead_detection(self):
        """Test that lookahead patterns trigger warnings."""
        code = """
# Using shift(-1) for target variable
y = returns.shift(-1)  # This is OK for target
"""
        validator = CodeValidator()
        is_valid, errors, warnings = validator.validate(code)
        
        # Should be valid but with warning
        assert is_valid
        assert len(warnings) > 0
        assert any("shift(-" in w for w in warnings)
    
    def test_infinite_loop_detection(self):
        """Test that infinite loops are detected."""
        code = """
while True:
    x = 1
"""
        validator = CodeValidator()
        is_valid, errors, warnings = validator.validate(code)
        
        assert not is_valid
        assert any("infinite loop" in e.lower() for e in errors)
    
    def test_while_loop_with_break(self):
        """Test that while True with break is allowed."""
        code = """
while True:
    if condition:
        break
"""
        validator = CodeValidator()
        is_valid, errors, warnings = validator.validate(code)
        
        # Should be valid (has break)
        assert is_valid
    
    def test_convenience_function(self):
        """Test validate_python_code convenience function."""
        code = "import numpy as np\nx = np.array([1, 2, 3])"
        
        is_valid, messages = validate_python_code(code)
        
        assert is_valid
        assert isinstance(messages, list)
