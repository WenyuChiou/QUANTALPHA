#!/usr/bin/env python
import os
import re
from pathlib import Path

def scan_issues(filepath):
    """扫描文件中的潜在问题"""
    issues = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
            lines = content.split('\n')
            
            # 检查 Pydantic V1 问题
            if '@validator' in content and 'from pydantic' in content:
                for i, line in enumerate(lines):
                    if '@validator' in line:
                        issues.append({
                            'type': 'pydantic_v1_deprecated',
                            'line': i+1,
                            'code': line.strip(),
                            'file': filepath
                        })
            
            # 检查 SQLAlchemy 问题
            if 'declarative_base()' in content:
                for i, line in enumerate(lines):
                    if 'declarative_base()' in line:
                        issues.append({
                            'type': 'sqlalchemy_v2_deprecated',
                            'line': i+1,
                            'code': line.strip(),
                            'file': filepath
                        })
            
            # 检查没有类型注解的函数
            if re.search(r'def \w+\([^)]*\)\s*:', content):
                for i, line in enumerate(lines):
                    if re.search(r'def \w+\([^)]*\)\s*:', line):
                        if '->' not in line:
                            issues.append({
                                'type': 'missing_return_type',
                                'line': i+1,
                                'code': line.strip(),
                                'file': filepath
                            })
    except Exception as e:
        pass
    
    return issues

def main():
    all_issues = []
    
    for root, dirs, files in os.walk('src'):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                issues = scan_issues(filepath)
                all_issues.extend(issues)
    
    # 分类统计
    by_type = {}
    for issue in all_issues:
        t = issue['type']
        if t not in by_type:
            by_type[t] = []
        by_type[t].append(issue)
    
    print("\n=== Code Quality Review Report ===\n")
    print(f"Total Issues: {len(all_issues)}\n")
    
    for issue_type, issues in sorted(by_type.items()):
        print(f"\n### {issue_type} ({len(issues)})")
        for issue in issues[:3]:
            print(f"  {issue['file']}:{issue['line']}")
            print(f"    {issue['code'][:80]}")

if __name__ == '__main__':
    main()
