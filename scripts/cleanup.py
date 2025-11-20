#!/usr/bin/env python3
"""Cleanup script to remove temporary files and keep project tidy."""

import os
import shutil
from pathlib import Path


def cleanup_pycache():
    """Remove all __pycache__ directories."""
    print("Cleaning __pycache__ directories...")
    count = 0
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            pycache_path = Path(root) / '__pycache__'
            shutil.rmtree(pycache_path, ignore_errors=True)
            count += 1
    print(f"  Removed {count} __pycache__ directories")
    return count


def cleanup_temp_files():
    """Remove temporary files."""
    print("Cleaning temporary files...")
    patterns = ['*.pyc', '*.py~', '*.bak', '*.tmp', '*.swp', '*.swo']
    count = 0
    
    for pattern in patterns:
        for path in Path('.').rglob(pattern):
            try:
                path.unlink()
                count += 1
            except Exception:
                pass
    
    print(f"  Removed {count} temporary files")
    return count


def cleanup_test_databases():
    """Remove test database files."""
    print("Cleaning test databases...")
    patterns = ['test_*.db', '*_test.db']
    count = 0
    
    for pattern in patterns:
        for path in Path('.').rglob(pattern):
            try:
                path.unlink()
                count += 1
            except Exception:
                pass
    
    print(f"  Removed {count} test database files")
    return count


def cleanup_logs():
    """Remove log files."""
    print("Cleaning log files...")
    count = 0
    
    # Remove log files in root and logs directory
    for path in Path('.').rglob('*.log'):
        # Skip if in .git directory
        if '.git' not in str(path):
            try:
                path.unlink()
                count += 1
            except Exception:
                pass
    
    print(f"  Removed {count} log files")
    return count


def cleanup_empty_dirs():
    """Remove empty directories (except important ones)."""
    print("Cleaning empty directories...")
    important_dirs = {'.git', 'src', 'tests', 'scripts', 'docs', 'configs', 'kb', 'examples'}
    count = 0
    
    for root, dirs, files in os.walk('.', topdown=False):
        root_path = Path(root)
        if root_path.name in important_dirs:
            continue
        
        try:
            if not any(root_path.iterdir()):
                root_path.rmdir()
                count += 1
        except Exception:
            pass
    
    print(f"  Removed {count} empty directories")
    return count


def main():
    """Main cleanup function."""
    print("="*70)
    print("Project Cleanup")
    print("="*70)
    
    total_removed = 0
    
    total_removed += cleanup_pycache()
    total_removed += cleanup_temp_files()
    total_removed += cleanup_test_databases()
    total_removed += cleanup_logs()
    total_removed += cleanup_empty_dirs()
    
    print("\n" + "="*70)
    print(f"Cleanup complete! Removed {total_removed} items.")
    print("="*70)


if __name__ == "__main__":
    main()

