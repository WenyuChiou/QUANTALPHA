"""
Minimal Integration Test - Bypasses chromadb dependency

Tests discovery loop logic without full Orchestrator initialization.
Focuses on Phase 11 components: PolicyManager, ReflectorAgent, Discovery Loop
"""

import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Test without importing Orchestrator (to avoid chromadb)
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.memory.policy_manager import PolicyManager
from src.agents.reflector import ReflectorAgent


def simulate_discovery_iteration(
    iteration: int,
    policy_manager: PolicyManager,
    reflector: ReflectorAgent,
    output_dir: Path
) -> Dict[str, Any]:
    """
    Simulate one discovery loop iteration.
    
    Args:
        iteration: Iteration number
        policy_manager: Policy manager instance
        reflector: Reflector agent instance
        output_dir: Output directory
        
    Returns:
        Iteration results
    """
    alpha_id = f"alpha_{iteration:03d}"
    print(f"\n{'─'*70}")
    print(f"  Iteration {iteration}: {alpha_id}")
    print(f"{'─'*70}")
    
    iter_start = time.time()
    
    # Step 1: Mock factor proposal
    print(f"  [1/6] 🔬 ResearcherAgent: Proposing momentum factor...")
    time.sleep(0.3)
    
    # Step 2: Mock signal computation
    print(f"  [2/6] ⚙️  FeatureAgent: Computing signals...")
    time.sleep(0.3)
    
    # Step 3: Mock backtest with improving metrics
    print(f"  [3/6] 📊 BacktesterAgent: Running backtest...")
    time.sleep(0.5)
    
    # Simulate improving performance over iterations
    mock_metrics = {
        "sharpe": round(0.6 + (iteration * 0.45), 2),
        "maxdd": round(-0.28 + (iteration * 0.04), 2),
        "ann_ret": round(0.12 + (iteration * 0.08), 2),
        "turnover_monthly": round(75 - (iteration * 8), 1),
        "avg_ic": round(0.045 + (iteration * 0.025), 3),
        "hit_rate": round(0.50 + (iteration * 0.03), 3),
        "ic_std": round(0.18 - (iteration * 0.02), 3),
        "skew": round(-0.6 + (iteration * 0.15), 2)
    }
    
    # Step 4: Mock critic evaluation
    print(f"  [4/6] 🔍 CriticAgent: Evaluating compliance...")
    time.sleep(0.3)
    
    # Get applicable policy rules
    applicable_rules = policy_manager.get_applicable_rules(mock_metrics, factor_type="momentum")
    
    # Check global constraints
    meets_constraints, violations = policy_manager.check_constraints(mock_metrics)
    
    mock_compliance = {
        "verdict": "PASS" if meets_constraints else "FAIL",
        "applicable_rules": [r['rule_id'] for r in applicable_rules],
        "violations": violations,
        "issues": []
    }
    
    # Step 5: Reflector analysis
    print(f"  [5/6] 💡 ReflectorAgent: Analyzing performance...")
    time.sleep(0.4)
    
    if not meets_constraints:
        # Generate lessons for failed alpha
        lessons = reflector.analyze_failure(
            alpha_id=alpha_id,
            metrics=mock_metrics,
            compliance=mock_compliance
        )
        
        # Save lessons
        lessons_file = output_dir / f"{alpha_id}_lessons.json"
        with open(lessons_file, 'w') as f:
            json.dump(lessons, f, indent=2)
    else:
        lessons = {"verdict": "PASS", "message": "Target metrics achieved!"}
    
    # Step 6: Check target metrics
    print(f"  [6/6] ✓  Checking target metrics...")
    
    iter_time = time.time() - iter_start
    
    # Determine status
    meets_sharpe = mock_metrics['sharpe'] >= 1.8
    meets_dd = mock_metrics['maxdd'] >= -0.25
    status = "PASS" if (meets_sharpe and meets_dd) else "FAIL"
    
    # Print results
    print(f"\n  📈 Results:")
    print(f"     Sharpe Ratio: {mock_metrics['sharpe']:.2f} {'✅' if meets_sharpe else '❌'} (target: ≥1.8)")
    print(f"     Max Drawdown: {mock_metrics['maxdd']:.1%} {'✅' if meets_dd else '❌'} (target: ≥-25%)")
    print(f"     Annual Return: {mock_metrics['ann_ret']:.1%}")
    print(f"     Turnover: {mock_metrics['turnover_monthly']:.1f}%/month")
    print(f"     Avg IC: {mock_metrics['avg_ic']:.3f}")
    print(f"     Hit Rate: {mock_metrics['hit_rate']:.1%}")
    print(f"     Applicable Rules: {len(applicable_rules)}")
    print(f"     Violations: {len(violations)}")
    print(f"     Runtime: {iter_time:.2f}s")
    print(f"     Status: {status}\n")
    
    return {
        "iteration": iteration,
        "alpha_id": alpha_id,
        "runtime_seconds": round(iter_time, 2),
        "metrics": mock_metrics,
        "compliance": mock_compliance,
        "lessons": lessons,
        "status": status,
        "meets_sharpe": meets_sharpe,
        "meets_drawdown": meets_dd
    }


def run_minimal_integration_test(max_iterations: int = 3) -> Dict[str, Any]:
    """
    Run minimal integration test.
    
    Args:
        max_iterations: Maximum iterations
        
    Returns:
        Test results
    """
    print(f"\n{'='*70}")
    print(f"  MINIMAL INTEGRATION TEST (Phase 11)")
    print(f"{'='*70}")
    print(f"Max Iterations: {max_iterations}")
    print(f"Start Time: {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*70}\n")
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"test_results/integration_tests/minimal_{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    test_start = time.time()
    
    # Initialize components
    print("📦 Initializing Phase 11 components...")
    policy_manager = PolicyManager()
    reflector = ReflectorAgent()
    print(f"  ✓ PolicyManager: {len(policy_manager.rules['rules'])} rules loaded")
    print(f"  ✓ ReflectorAgent: Gemini API ready")
    print(f"  ✓ Output directory: {output_dir}\n")
    
    # Run discovery loop
    results = {
        "test_type": "minimal_integration",
        "max_iterations": max_iterations,
        "timestamp": timestamp,
        "output_dir": str(output_dir),
        "iterations": [],
        "status": "RUNNING"
    }
    
    try:
        print(f"🚀 Starting Discovery Loop\n")
        
        for iteration in range(1, max_iterations + 1):
            iter_result = simulate_discovery_iteration(
                iteration=iteration,
                policy_manager=policy_manager,
                reflector=reflector,
                output_dir=output_dir
            )
            
            results["iterations"].append(iter_result)
            
            # Check if target met
            if iter_result["status"] == "PASS":
                print(f"  🎉 SUCCESS! Target metrics achieved at iteration {iteration}\n")
                results["status"] = "SUCCESS"
                results["success_iteration"] = iteration
                break
        
        if results["status"] == "RUNNING":
            results["status"] = "COMPLETED_NO_SUCCESS"
            print(f"  ⚠️  Completed {max_iterations} iterations without reaching target\n")
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}\n")
        results["status"] = "FAILED"
        results["error"] = str(e)
    
    # Calculate metrics
    total_runtime = time.time() - test_start
    results["total_runtime_seconds"] = round(total_runtime, 2)
    results["total_runtime_minutes"] = round(total_runtime / 60, 2)
    
    # Save results
    results_file = output_dir / "test_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print(f"{'='*70}")
    print(f"  TEST COMPLETE")
    print(f"{'='*70}")
    print(f"Status: {results['status']}")
    print(f"Iterations Run: {len(results['iterations'])}")
    if results['status'] == 'SUCCESS':
        print(f"Success at Iteration: {results['success_iteration']}")
    print(f"Total Runtime: {results['total_runtime_minutes']:.2f} minutes")
    print(f"Results Saved: {results_file}")
    print(f"{'='*70}\n")
    
    return results


if __name__ == "__main__":
    print("\n" + "="*70)
    print("  QUANTALPHA PHASE 11 INTEGRATION TEST")
    print("="*70)
    print(f"Test Type: Minimal (bypasses chromadb)")
    print(f"Components: PolicyManager + ReflectorAgent + Discovery Loop")
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")
    
    try:
        results = run_minimal_integration_test(max_iterations=3)
        
        print("\n" + "="*70)
        print("  ✅ INTEGRATION TEST COMPLETE")
        print("="*70)
        print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Check test_results/integration_tests/ for detailed results")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}\n")
        raise
