"""Monitoring utilities for production."""

import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

logger = logging.getLogger("quantalpha.monitoring")


class SystemMonitor:
    """System resource monitoring."""
    
    def __init__(self):
        """Initialize system monitor."""
        self.start_time = time.time()
        self.metrics_history = []
    
    def get_cpu_usage(self) -> float:
        """Get current CPU usage percentage.
        
        Returns:
            CPU usage percentage
        """
        if not PSUTIL_AVAILABLE:
            return 0.0
        return psutil.cpu_percent(interval=0.1)
    
    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage.
        
        Returns:
            Dictionary with memory usage info
        """
        if not PSUTIL_AVAILABLE:
            return {
                'total_gb': 0.0,
                'used_gb': 0.0,
                'available_gb': 0.0,
                'percent': 0.0
            }
        mem = psutil.virtual_memory()
        return {
            'total_gb': mem.total / (1024**3),
            'used_gb': mem.used / (1024**3),
            'available_gb': mem.available / (1024**3),
            'percent': mem.percent
        }
    
    def get_disk_usage(self, path: str = ".") -> Dict[str, float]:
        """Get disk usage for a path.
        
        Args:
            path: Path to check
        
        Returns:
            Dictionary with disk usage info
        """
        if not PSUTIL_AVAILABLE:
            return {
                'total_gb': 0.0,
                'used_gb': 0.0,
                'free_gb': 0.0,
                'percent': 0.0
            }
        disk = psutil.disk_usage(path)
        return {
            'total_gb': disk.total / (1024**3),
            'used_gb': disk.used / (1024**3),
            'free_gb': disk.free / (1024**3),
            'percent': disk.percent
        }
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get all system metrics.
        
        Returns:
            Dictionary with all system metrics
        """
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': self.get_cpu_usage(),
            'memory': self.get_memory_usage(),
            'disk': self.get_disk_usage(),
            'uptime_seconds': time.time() - self.start_time
        }
    
    def log_metrics(self):
        """Log current metrics."""
        metrics = self.get_system_metrics()
        self.metrics_history.append(metrics)
        
        logger.info(
            f"System Metrics - CPU: {metrics['cpu_percent']:.1f}%, "
            f"Memory: {metrics['memory']['percent']:.1f}%, "
            f"Disk: {metrics['disk']['percent']:.1f}%"
        )
        
        # Keep only last 1000 entries
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]


class PerformanceMonitor:
    """Performance monitoring for operations."""
    
    def __init__(self):
        """Initialize performance monitor."""
        self.operation_times = {}
    
    def time_operation(self, operation_name: str):
        """Context manager for timing operations.
        
        Args:
            operation_name: Name of the operation
        
        Example:
            with monitor.time_operation("backtest"):
                run_backtest()
        """
        return OperationTimer(self, operation_name)
    
    def record_time(self, operation_name: str, elapsed_time: float):
        """Record operation time.
        
        Args:
            operation_name: Name of the operation
            elapsed_time: Elapsed time in seconds
        """
        if operation_name not in self.operation_times:
            self.operation_times[operation_name] = []
        
        self.operation_times[operation_name].append(elapsed_time)
        
        logger.debug(f"Operation '{operation_name}' took {elapsed_time:.2f}s")
    
    def get_stats(self, operation_name: str) -> Optional[Dict[str, float]]:
        """Get statistics for an operation.
        
        Args:
            operation_name: Name of the operation
        
        Returns:
            Dictionary with statistics or None if no data
        """
        if operation_name not in self.operation_times:
            return None
        
        times = self.operation_times[operation_name]
        return {
            'count': len(times),
            'mean': sum(times) / len(times),
            'min': min(times),
            'max': max(times),
            'total': sum(times)
        }


class OperationTimer:
    """Context manager for timing operations."""
    
    def __init__(self, monitor: PerformanceMonitor, operation_name: str):
        """Initialize timer.
        
        Args:
            monitor: Performance monitor instance
            operation_name: Name of the operation
        """
        self.monitor = monitor
        self.operation_name = operation_name
        self.start_time = None
    
    def __enter__(self):
        """Start timing."""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and record."""
        elapsed = time.time() - self.start_time
        self.monitor.record_time(self.operation_name, elapsed)


# Global instances
_system_monitor = None
_performance_monitor = None


def get_system_monitor() -> SystemMonitor:
    """Get global system monitor instance.
    
    Returns:
        System monitor instance
    """
    global _system_monitor
    if _system_monitor is None:
        _system_monitor = SystemMonitor()
    return _system_monitor


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance.
    
    Returns:
        Performance monitor instance
    """
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor

