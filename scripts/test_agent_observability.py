"""
Test script to verify Agent Observability and Communication.
Runs a simplified workflow using the Orchestrator and checks for standardized AgentResult outputs.
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import pandas as pd
import shutil

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.agents.orchestrator import Orchestrator
from src.memory.schemas import AgentResult, ConversationContext

def main():
    print("="*80)
    print("TESTING AGENT OBSERVABILITY")
    print("="*80)
    
    # Setup temporary test directory
    test_dir = project_root / "test_observability_output"
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir()
    
    # Initialize Orchestrator with test DB
    db_path = str(test_dir / "test_experiments.db")
    orchestrator = Orchestrator(db_path=db_path)
    
    # Mock data to avoid fetching
    print("\n1. Setting up mock data...")
    dates = pd.date_range(start="2020-01-01", end="2020-12-31", freq="B")
    tickers = ["AAPL", "MSFT", "GOOGL"]
    
    # Create random prices
    import numpy as np
    np.random.seed(42)
    prices = pd.DataFrame(
        np.random.randn(len(dates), len(tickers)).cumsum(axis=0) + 100,
        index=dates,
        columns=tickers
    )
    orchestrator.prices_df = prices
    orchestrator.returns_df = prices.pct_change()
    
    print(f"  Created mock data: {prices.shape}")
    
    # Run a single iteration
    print("\n2. Running Orchestrator iteration...")
    # We expect the orchestrator to use the new AgentResult flow
    
    try:
        results = orchestrator.run_iteration(n_candidates=1)
        
        print("\n3. Verifying Results...")
        print(f"  Candidates processed: {len(results['candidates'])}")
        print(f"  Successful: {len(results['successful'])}")
        print(f"  Failed: {len(results['failed'])}")
        
        if results['summary']:
            print(f"\n  Iteration Summary:\n{results['summary']}")
        
        # Verify that we can find the archived factor if successful
        if results['successful']:
            print("\n4. Verifying Archive...")
            # Check success_factors directory
            success_dir = project_root / "success_factors"
            if success_dir.exists():
                factors = list(success_dir.glob("*"))
                if factors:
                    latest_factor = max(factors, key=os.path.getctime)
                    print(f"  Found archived factor: {latest_factor.name}")
                    
                    # Check for conversation_log.json
                    log_file = latest_factor / "conversation_log.json"
                    if log_file.exists():
                        print("  ✓ conversation_log.json exists")
                        import json
                        with open(log_file, 'r') as f:
                            logs = json.load(f)
                            print(f"  ✓ Log contains {len(logs)} entries")
                            
                            # Verify structure
                            if len(logs) > 0:
                                first_entry = logs[0]
                                print(f"  Sample entry keys: {list(first_entry.keys())}")
                                # We expect keys from AgentResult (agent, step, status, content, etc.)
                                expected_keys = ['agent', 'step', 'status', 'content', 'metadata', 'timestamp']
                                missing = [k for k in expected_keys if k not in first_entry]
                                if not missing:
                                    print("  ✓ Log entry has correct AgentResult structure")
                                else:
                                    print(f"  ✗ Log entry missing keys: {missing}")
                    else:
                        print("  ✗ conversation_log.json MISSING")
                else:
                    print("  No factors found in success_factors dir")
            else:
                print("  success_factors dir does not exist")
        else:
            print("\n  No successful factors to verify archive for.")
            
    except Exception as e:
        print(f"\n❌ Error during execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
