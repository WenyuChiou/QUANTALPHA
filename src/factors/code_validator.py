"""Code validator for custom Python code in nonlinear factors.

This module provides security validation for user-provided Python code
to ensure safe execution in the factor computation pipeline.
"""

import ast
import re
from typing import Tuple, List, Set, Dict, Any


class CodeValidator:
    """Validates custom Python code for security and correctness."""
    
    # Allowed imports (whitelist)
    ALLOWED_IMPORTS = {
        'numpy', 'np',
        'pandas', 'pd',
        'sklearn', 'sklearn.ensemble', 'sklearn.linear_model', 'sklearn.tree',
        'scipy', 'scipy.stats', 'scipy.signal',
        'statsmodels', 'statsmodels.api',
        'math', 'datetime', 'collections'
    }
    
    # Forbidden operations (blacklist)
    FORBIDDEN_OPERATIONS = {
        'open', 'file', 'input', 'raw_input',
        'exec', 'eval', 'compile', '__import__',
        'execfile', 'reload',
        'subprocess', 'os.system', 'os.popen', 'os.spawn',
        'socket', 'urllib', 'requests',
        'pickle', 'shelve', 'marshal',
        '__builtins__', 'globals', 'locals', 'vars',
        'delattr', 'setattr', 'getattr',
    }
    
    # Forbidden modules
    FORBIDDEN_MODULES = {
        'os', 'sys', 'subprocess', 'socket', 'urllib', 'urllib2', 'urllib3',
        'requests', 'http', 'ftplib', 'smtplib',
        'pickle', 'shelve', 'marshal', 'dill',
        'importlib', 'imp', '__builtin__', 'builtins'
    }
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate(self, code: str) -> Tuple[bool, List[str], List[str]]:
        """Validate code for security and correctness.
        
        Args:
            code: Python code string to validate
            
        Returns:
            (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []
        
        # 1. Check syntax
        if not self._check_syntax(code):
            return False, self.errors, self.warnings
        
        # 2. Parse AST
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            self.errors.append(f"Syntax error: {e}")
            return False, self.errors, self.warnings
        
        # 3. Check for forbidden operations
        self._check_forbidden_operations(tree)
        
        # 4. Check imports
        self._check_imports(tree)
        
        # 5. Check for lookahead patterns
        self._check_lookahead_patterns(code)
        
        # 6. Check for infinite loops
        self._check_loops(tree)
        
        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings
    
    def _check_syntax(self, code: str) -> bool:
        """Check basic syntax validity."""
        try:
            compile(code, '<string>', 'exec')
            return True
        except SyntaxError as e:
            self.errors.append(f"Syntax error at line {e.lineno}: {e.msg}")
            return False
    
    def _check_forbidden_operations(self, tree: ast.AST):
        """Check for forbidden function calls and operations."""
        for node in ast.walk(tree):
            # Check function calls
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func)
                if func_name in self.FORBIDDEN_OPERATIONS:
                    self.errors.append(
                        f"Forbidden operation: {func_name}() is not allowed"
                    )
            
            # Check attribute access (e.g., os.system)
            if isinstance(node, ast.Attribute):
                attr_name = f"{self._get_attr_base(node)}.{node.attr}"
                if attr_name in self.FORBIDDEN_OPERATIONS:
                    self.errors.append(
                        f"Forbidden operation: {attr_name} is not allowed"
                    )
    
    def _check_imports(self, tree: ast.AST):
        """Check that only allowed modules are imported."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name.split('.')[0]
                    if module in self.FORBIDDEN_MODULES:
                        self.errors.append(
                            f"Forbidden import: '{module}' is not allowed"
                        )
                    elif module not in self.ALLOWED_IMPORTS and not alias.name.startswith('sklearn.'):
                        self.warnings.append(
                            f"Unrecognized import: '{module}' (may not be available)"
                        )
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module = node.module.split('.')[0]
                    if module in self.FORBIDDEN_MODULES:
                        self.errors.append(
                            f"Forbidden import: 'from {module}' is not allowed"
                        )
                    elif module not in self.ALLOWED_IMPORTS and not node.module.startswith('sklearn.'):
                        self.warnings.append(
                            f"Unrecognized import: 'from {module}' (may not be available)"
                        )
    
    def _check_lookahead_patterns(self, code: str):
        """Check for potential lookahead bias patterns."""
        # Check for .shift(-n) which shifts future data to present
        shift_pattern = r'\.shift\s*\(\s*-\s*\d+\s*\)'
        if re.search(shift_pattern, code):
            self.warnings.append(
                "WARNING: Found .shift(-n) pattern - ensure this is used correctly "
                "for target variable creation, not for features"
            )
        
        # Check for forward-looking keywords
        lookahead_keywords = ['future', 'forward', 'next', 'ahead']
        code_lower = code.lower()
        for keyword in lookahead_keywords:
            if keyword in code_lower:
                # Check if it's in a comment
                if not self._is_in_comment(code, keyword):
                    self.warnings.append(
                        f"WARNING: Found '{keyword}' keyword - verify no lookahead bias"
                    )
    
    def _check_loops(self, tree: ast.AST):
        """Check for potentially infinite loops."""
        for node in ast.walk(tree):
            if isinstance(node, ast.While):
                # Check if while True without break
                if isinstance(node.test, ast.Constant) and node.test.value is True:
                    has_break = any(isinstance(n, ast.Break) for n in ast.walk(node))
                    if not has_break:
                        self.errors.append(
                            "Infinite loop detected: 'while True' without break statement"
                        )
    
    def _get_function_name(self, node: ast.AST) -> str:
        """Extract function name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_attr_base(node)}.{node.attr}"
        return ""
    
    def _get_attr_base(self, node: ast.Attribute) -> str:
        """Get base name of attribute access."""
        if isinstance(node.value, ast.Name):
            return node.value.id
        elif isinstance(node.value, ast.Attribute):
            return f"{self._get_attr_base(node.value)}.{node.value.attr}"
        return ""
    
    def _is_in_comment(self, code: str, keyword: str) -> bool:
        """Check if keyword appears only in comments."""
        lines = code.split('\n')
        for line in lines:
            if keyword in line.lower():
                # Check if it's after a # comment marker
                comment_pos = line.find('#')
                keyword_pos = line.lower().find(keyword)
                if comment_pos == -1 or keyword_pos < comment_pos:
                    return False
        return True


def validate_python_code(code: str) -> Tuple[bool, List[str]]:
    """Convenience function to validate Python code.
    
    Args:
        code: Python code string
        
    Returns:
        (is_valid, error_messages)
    """
    validator = CodeValidator()
    is_valid, errors, warnings = validator.validate(code)
    
    # Combine errors and warnings
    messages = errors + warnings
    
    return is_valid, messages
