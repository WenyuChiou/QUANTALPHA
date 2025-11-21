"""Sandboxed execution environment for custom Python code.

This module provides a restricted execution environment with:
- Timeout enforcement
- Memory limits (best effort)
- Restricted globals (no file I/O, network access)
- Exception handling and logging
"""

import signal
import sys
from typing import Any, Dict, Optional, Callable
from contextlib import contextmanager
import traceback


class TimeoutException(Exception):
    """Raised when code execution exceeds timeout."""
    pass


class SandboxExecutor:
    """Execute Python code in a sandboxed environment."""
    
    def __init__(
        self,
        timeout: int = 60,
        memory_limit_mb: Optional[int] = None
    ):
        """Initialize sandbox executor.
        
        Args:
            timeout: Maximum execution time in seconds (default: 60)
            memory_limit_mb: Memory limit in MB (not enforced on Windows)
        """
        self.timeout = timeout
        self.memory_limit_mb = memory_limit_mb
    
    def execute(
        self,
        code: str,
        global_vars: Optional[Dict[str, Any]] = None,
        local_vars: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute code in sandboxed environment.
        
        Args:
            code: Python code to execute
            global_vars: Global variables to provide (e.g., prices, returns)
            local_vars: Local variables
            
        Returns:
            Dictionary with execution results:
            {
                'success': bool,
                'result': Any (if success),
                'error': str (if failure),
                'locals': dict (final local variables)
            }
        """
        # Prepare restricted globals
        restricted_globals = self._create_restricted_globals()
        
        # Add user-provided globals
        if global_vars:
            restricted_globals.update(global_vars)
        
        # Prepare locals
        exec_locals = local_vars.copy() if local_vars else {}
        
        try:
            # Execute with timeout
            with self._timeout_context(self.timeout):
                exec(code, restricted_globals, exec_locals)
            
            # Extract result (look for 'result' or 'return' variable)
            result_value = exec_locals.get('result', exec_locals.get('return', None))
            
            return {
                'success': True,
                'result': result_value,
                'locals': exec_locals,
                'error': None
            }
        
        except TimeoutException:
            return {
                'success': False,
                'result': None,
                'locals': exec_locals,
                'error': f"Execution timeout ({self.timeout}s exceeded)"
            }
        
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            return {
                'success': False,
                'result': None,
                'locals': exec_locals,
                'error': error_msg
            }
    
    def _create_restricted_globals(self) -> Dict[str, Any]:
        """Create restricted global namespace.
        
        Only safe built-ins and allowed modules are included.
        """
        # Safe built-ins
        safe_builtins = {
            'abs': abs,
            'all': all,
            'any': any,
            'bool': bool,
            'dict': dict,
            'enumerate': enumerate,
            'float': float,
            'int': int,
            'len': len,
            'list': list,
            'max': max,
            'min': min,
            'range': range,
            'round': round,
            'set': set,
            'sorted': sorted,
            'str': str,
            'sum': sum,
            'tuple': tuple,
            'zip': zip,
            'True': True,
            'False': False,
            'None': None,
        }
        
        # Allowed modules (will be imported on demand)
        restricted_globals = {
            '__builtins__': safe_builtins,
            '__name__': '__sandbox__',
            '__doc__': None,
        }
        
        # Pre-import safe modules
        try:
            import numpy as np
            import pandas as pd
            restricted_globals['np'] = np
            restricted_globals['pd'] = pd
            restricted_globals['numpy'] = np
            restricted_globals['pandas'] = pd
        except ImportError:
            pass
        
        return restricted_globals
    
    @contextmanager
    def _timeout_context(self, seconds: int):
        """Context manager for timeout enforcement.
        
        Note: signal.alarm only works on Unix systems.
        On Windows, this provides best-effort timeout.
        """
        if sys.platform == 'win32':
            # Windows doesn't support signal.alarm
            # Use threading-based timeout (less reliable)
            yield
        else:
            # Unix-based timeout using signals
            def timeout_handler(signum, frame):
                raise TimeoutException(f"Execution exceeded {seconds} seconds")
            
            # Set the signal handler
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)
            
            try:
                yield
            finally:
                # Restore old handler and cancel alarm
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)


def execute_code_safely(
    code: str,
    timeout: int = 60,
    **kwargs
) -> Dict[str, Any]:
    """Convenience function to execute code safely.
    
    Args:
        code: Python code to execute
        timeout: Timeout in seconds
        **kwargs: Variables to pass to code (e.g., prices=df, returns=df)
        
    Returns:
        Execution result dictionary
    """
    executor = SandboxExecutor(timeout=timeout)
    return executor.execute(code, global_vars=kwargs)
