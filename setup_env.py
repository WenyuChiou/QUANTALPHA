#!/usr/bin/env python3
"""Environment setup script for Alpha-Mining Framework."""

import subprocess
import sys
from pathlib import Path
import sqlite3

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*70}")
    print(f"执行: {description}")
    print(f"命令: {' '.join(cmd)}")
    print('='*70)
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"错误: {e}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return False

def check_ollama():
    """Check if Ollama is installed and deepseek-r1 is available."""
    print("\n检查 Ollama...")
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if "deepseek-r1" in result.stdout:
            print("✓ deepseek-r1 模型已安装")
            return True
        else:
            print("⚠ deepseek-r1 模型未找到，请运行: ollama pull deepseek-r1")
            return False
    except FileNotFoundError:
        print("⚠ Ollama 未安装，请先安装 Ollama")
        return False

def initialize_database():
    """Initialize SQLite database."""
    print("\n初始化数据库...")
    db_path = Path("experiments.db")
    if db_path.exists():
        print(f"✓ 数据库已存在: {db_path}")
    else:
        # Import and create tables
        try:
            from src.memory.store import ExperimentStore
            store = ExperimentStore(str(db_path))
            print(f"✓ 数据库已创建: {db_path}")
            return True
        except Exception as e:
            print(f"✗ 数据库创建失败: {e}")
            return False
    return True

def build_vector_index():
    """Build Chroma vector index from knowledge base."""
    print("\n构建向量索引...")
    try:
        from src.rag.indexer import KnowledgeBaseIndexer
        
        kb_dir = Path("kb")
        index_path = "./kb.index"
        
        if not kb_dir.exists():
            print(f"⚠ 知识库目录不存在: {kb_dir}")
            return False
        
        indexer = KnowledgeBaseIndexer(kb_dir=kb_dir, index_path=index_path)
        counts = indexer.rebuild_index()
        
        print("✓ 向量索引构建完成:")
        for subdir, count in counts.items():
            print(f"  - {subdir}: {count} 文档")
        
        return True
    except Exception as e:
        print(f"✗ 向量索引构建失败: {e}")
        return False

def validate_configs():
    """Validate configuration files."""
    print("\n验证配置文件...")
    import yaml
    
    configs = {
        "universe.yml": Path("configs/universe.yml"),
        "costs.yml": Path("configs/costs.yml"),
        "constraints.yml": Path("configs/constraints.yml")
    }
    
    all_valid = True
    for name, path in configs.items():
        if path.exists():
            try:
                with open(path, 'r') as f:
                    yaml.safe_load(f)
                print(f"✓ {name} 有效")
            except Exception as e:
                print(f"✗ {name} 无效: {e}")
                all_valid = False
        else:
            print(f"✗ {name} 不存在: {path}")
            all_valid = False
    
    return all_valid

def main():
    """Main setup function."""
    print("="*70)
    print("Alpha-Mining Framework 环境设置")
    print("="*70)
    
    # 1. Install dependencies
    print("\n[1/5] 安装依赖...")
    if not run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      "安装 Python 依赖"):
        print("⚠ 依赖安装可能有问题，请手动检查")
    
    # 2. Check Ollama
    print("\n[2/5] 检查 Ollama...")
    check_ollama()
    
    # 3. Initialize database
    print("\n[3/5] 初始化数据库...")
    initialize_database()
    
    # 4. Build vector index
    print("\n[4/5] 构建向量索引...")
    build_vector_index()
    
    # 5. Validate configs
    print("\n[5/5] 验证配置文件...")
    validate_configs()
    
    print("\n" + "="*70)
    print("环境设置完成！")
    print("="*70)
    print("\n下一步:")
    print("1. 确保 Ollama 运行: ollama serve")
    print("2. 拉取模型: ollama pull deepseek-r1")
    print("3. 运行测试: python -m pytest tests/")
    print("4. 启动仪表板: streamlit run src/dashboard/app.py")

if __name__ == "__main__":
    main()

