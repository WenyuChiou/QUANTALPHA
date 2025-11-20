#!/usr/bin/env python3
"""Code improvement script: review and fix common issues."""

import ast
import sys
from pathlib import Path
from typing import List, Dict


def check_imports(file_path: Path) -> List[str]:
    """Check for missing imports or import issues.
    
    Args:
        file_path: Path to Python file
    
    Returns:
        List of issues found
    """
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            tree = ast.parse(content)
        
        # Check for common missing imports
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
        
        # Check for potential issues
        if 'pd' in content and 'pandas' not in imports:
            issues.append("Potential missing import: pandas (used as 'pd')")
        if 'np' in content and 'numpy' not in imports:
            issues.append("Potential missing import: numpy (used as 'np')")
        
    except SyntaxError as e:
        issues.append(f"Syntax error: {e}")
    except Exception as e:
        issues.append(f"Error parsing file: {e}")
    
    return issues


def check_docstrings(file_path: Path) -> List[str]:
    """Check for missing docstrings.
    
    Args:
        file_path: Path to Python file
    
    Returns:
        List of issues found
    """
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            tree = ast.parse(content)
        
        # Check classes
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if not ast.get_docstring(node):
                    issues.append(f"Class '{node.name}' missing docstring")
        
        # Check functions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not ast.get_docstring(node) and not node.name.startswith('_'):
                    issues.append(f"Function '{node.name}' missing docstring")
    
    except Exception as e:
        pass  # Skip if can't parse
    
    return issues


def main():
    """Main improvement function."""
    print("="*70)
    print("Code Review and Improvement")
    print("="*70)
    
    src_dir = Path("src")
    if not src_dir.exists():
        print("Error: src/ directory not found")
        return 1
    
    all_issues = {}
    
    # Check all Python files
    for py_file in src_dir.rglob("*.py"):
        relative_path = py_file.relative_to(Path("."))
        
        import_issues = check_imports(py_file)
        docstring_issues = check_docstrings(py_file)
        
        if import_issues or docstring_issues:
            all_issues[str(relative_path)] = {
                'imports': import_issues,
                'docstrings': docstring_issues
            }
    
    # Report
    if all_issues:
        print("\nIssues found:")
        for file_path, issues in all_issues.items():
            print(f"\n{file_path}:")
            if issues['imports']:
                for issue in issues['imports']:
                    print(f"  - {issue}")
            if issues['docstrings']:
                for issue in issues['docstrings']:
                    print(f"  - {issue}")
    else:
        print("\nNo issues found!")
    
    print("\n" + "="*70)
    return 0


if __name__ == "__main__":
    sys.exit(main())

