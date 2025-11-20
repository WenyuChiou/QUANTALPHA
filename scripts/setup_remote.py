#!/usr/bin/env python3
"""Setup git remote and push to GitHub."""

import subprocess
import sys

def run_command(cmd, description):
    """Run a git command and display results."""
    print(f"\n{'='*70}")
    print(f"执行: {description}")
    print(f"命令: {' '.join(cmd)}")
    print('='*70)
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"错误: {e}")
        return False

def main():
    """Main function."""
    print("="*70)
    print("Git Remote Setup and Push")
    print("="*70)
    
    # Check current status
    print("\n检查当前状态...")
    run_command(["git", "status"], "检查Git状态")
    
    # Add remote (ignore if already exists)
    print("\n添加远程仓库...")
    result = run_command(
        ["git", "remote", "add", "origin", "git@github.com:WenyuChiou/QUANTALPHA.git"],
        "添加远程仓库"
    )
    if not result:
        # Try to set URL if remote already exists
        print("\n远程仓库已存在，更新URL...")
        run_command(
            ["git", "remote", "set-url", "origin", "git@github.com:WenyuChiou/QUANTALPHA.git"],
            "更新远程仓库URL"
        )
    
    # Rename branch to main
    print("\n重命名分支为main...")
    run_command(["git", "branch", "-M", "main"], "重命名分支")
    
    # Check remote
    print("\n检查远程仓库配置...")
    run_command(["git", "remote", "-v"], "查看远程仓库")
    
    # Push to remote
    print("\n推送到远程仓库...")
    success = run_command(
        ["git", "push", "-u", "origin", "main"],
        "推送到GitHub"
    )
    
    if success:
        print("\n" + "="*70)
        print("✅ 成功推送到GitHub!")
        print("="*70)
    else:
        print("\n" + "="*70)
        print("⚠️  推送可能失败，请检查错误信息")
        print("="*70)
        print("\n可能的解决方案:")
        print("1. 检查SSH密钥是否配置: ssh -T git@github.com")
        print("2. 检查网络连接")
        print("3. 检查GitHub仓库权限")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

