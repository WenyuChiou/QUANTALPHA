"""Performance optimization utilities."""

import functools
import pickle
from pathlib import Path
from typing import Any, Callable, Optional
import hashlib
import logging

logger = logging.getLogger("quantalpha.performance")


def cache_to_disk(
    cache_dir: str = "cache",
    ttl_seconds: Optional[int] = None
):
    """Decorator to cache function results to disk.
    
    Args:
        cache_dir: Directory for cache files
        ttl_seconds: Time-to-live in seconds (None = no expiration)
    
    Example:
        @cache_to_disk(cache_dir="cache", ttl_seconds=3600)
        def expensive_function(x, y):
            return x + y
    """
    cache_path = Path(cache_dir)
    cache_path.mkdir(exist_ok=True)
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key_data = f"{func.__name__}_{args}_{kwargs}".encode()
            cache_key = hashlib.md5(key_data).hexdigest()
            cache_file = cache_path / f"{cache_key}.pkl"
            
            # Check cache
            if cache_file.exists():
                if ttl_seconds is None:
                    # No expiration
                    try:
                        with open(cache_file, 'rb') as f:
                            cached_data = pickle.load(f)
                        logger.debug(f"Cache hit for {func.__name__}")
                        return cached_data
                    except Exception as e:
                        logger.warning(f"Cache read error: {e}")
                else:
                    # Check expiration
                    import time
                    age = time.time() - cache_file.stat().st_mtime
                    if age < ttl_seconds:
                        try:
                            with open(cache_file, 'rb') as f:
                                cached_data = pickle.load(f)
                            logger.debug(f"Cache hit for {func.__name__}")
                            return cached_data
                        except Exception as e:
                            logger.warning(f"Cache read error: {e}")
            
            # Compute result
            result = func(*args, **kwargs)
            
            # Save to cache
            try:
                with open(cache_file, 'wb') as f:
                    pickle.dump(result, f)
                logger.debug(f"Cached result for {func.__name__}")
            except Exception as e:
                logger.warning(f"Cache write error: {e}")
            
            return result
        
        return wrapper
    return decorator


def parallel_map(
    func: Callable,
    items: list,
    n_workers: int = 4
) -> list:
    """Apply function to items in parallel.
    
    Args:
        func: Function to apply
        items: List of items
        n_workers: Number of worker processes
    
    Returns:
        List of results
    """
    from concurrent.futures import ProcessPoolExecutor
    
    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        results = list(executor.map(func, items))
    
    return results

