"""Error handling utilities for production."""

import traceback
from typing import Optional, Dict, Any
from functools import wraps
import logging

logger = logging.getLogger("quantalpha.error")


class QuantAlphaError(Exception):
    """Base exception for QuantAlpha framework."""
    pass


class FactorComputationError(QuantAlphaError):
    """Error during factor computation."""
    pass


class BacktestError(QuantAlphaError):
    """Error during backtest execution."""
    pass


class ValidationError(QuantAlphaError):
    """Error during validation."""
    pass


class DataError(QuantAlphaError):
    """Error with data."""
    pass


def handle_errors(
    error_type: type = QuantAlphaError,
    default_return: Any = None,
    log_error: bool = True
):
    """Decorator for error handling.
    
    Args:
        error_type: Exception type to catch
        default_return: Value to return on error
        log_error: Whether to log errors
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except error_type as e:
                if log_error:
                    logger.error(
                        f"Error in {func.__name__}: {str(e)}\n{traceback.format_exc()}"
                    )
                return default_return
            except Exception as e:
                if log_error:
                    logger.error(
                        f"Unexpected error in {func.__name__}: {str(e)}\n{traceback.format_exc()}"
                    )
                raise
        return wrapper
    return decorator


def safe_execute(
    func,
    *args,
    error_return: Any = None,
    log_error: bool = True,
    **kwargs
) -> Any:
    """Safely execute a function with error handling.
    
    Args:
        func: Function to execute
        *args: Positional arguments
        error_return: Value to return on error
        log_error: Whether to log errors
        **kwargs: Keyword arguments
    
    Returns:
        Function result or error_return on error
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_error:
            logger.error(
                f"Error executing {func.__name__}: {str(e)}\n{traceback.format_exc()}"
            )
        return error_return

