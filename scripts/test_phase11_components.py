"""Simple test for ReflectorAgent and PolicyManager"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.reflector import ReflectorAgent
from src.memory.policy_manager import PolicyManager
import json


def test_policy_manager():
    """Test policy manager."""
    print("="*70)
    print(" TEST 1: Policy Manager")
    print("="*70)
    
    pm = PolicyManager()
    
    # Test metrics
    metrics = {
        'sharpe': 0.5,
        'maxdd': -0.25,
        'turnover_monthly': 150,
        'avg_ic': 0.03
    }
    
    # Get applicable rules
    rules = pm.get_applicable_rules(metrics)
    print(f"\nApplicable rules: {len(rules)}")
    for rule in rules:
        print(f"  - {rule['rule_id']}: {rule['action']}")
    
    # Check constraints
    meets, violations = pm.check_constraints(metrics)
    print(f"\nMeets constraints: {meets}")
    if violations:
        print("Violations:")
        for v in violations:
            print(f"  - {v}")
    
    print("\n✅ Policy Manager test passed")
    return True


def test_reflector_agent():
    """Test reflector agent."""
    print("\n" + "="*70)
    print(" TEST 2: Reflector Agent")
    print("="*70)
    
    reflector = ReflectorAgent()
    
    # Test metrics (failed alpha)
    metrics = {
        'sharpe': 0.5,
        'ann_ret': -0.05,
        'maxdd': -0.25,
        'turnover_monthly': 150,
        'avg_ic': 0.03,
        'ann_vol': 0.12,
        'hit_rate': 0.48
    }
    
    compliance = {
        'verdict': 'FAIL',
        'issues': [
            {
                'type': 'low_sharpe',
                'severity': 'critical',
                'detail': 'Sharpe ratio 0.5 is below target 1.0',
                'recommendation': 'Improve signal quality'
            }
        ]
    }
    
    signals_meta = {
        'coverage': 0.95,
        'null_rate': 0.05
    }
    
    # Analyze
    lessons = reflector.analyze(
        alpha_id='alpha_001',
        metrics=metrics,
        compliance=compliance,
        signals_meta=signals_meta,
        factor_yaml='name: test_factor\nuniverse: sp500',
        past_lessons=[]
    )
    
    print(f"\nLessons generated:")
    print(f"  Alpha ID: {lessons['alpha_id']}")
    print(f"  Verdict: {lessons['verdict']}")
    print(f"  Root causes: {len(lessons['root_causes'])}")
    for cause in lessons['root_causes']:
        print(f"    - {cause['issue']}: {cause['detail']}")
    
    print(f"\n  Improvement suggestions: {len(lessons['improvement_suggestions'])}")
    for i, suggestion in enumerate(lessons['improvement_suggestions'], 1):
        print(f"    {i}. {suggestion}")
    
    # Save lessons
    output_path = Path('test_results/test_lessons.json')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(lessons, f, indent=2)
    
    print(f"\n  Saved to: {output_path}")
    print("\n✅ Reflector Agent test passed")
    return True


if __name__ == '__main__':
    try:
        test_policy_manager()
        test_reflector_agent()
        
        print("\n" + "="*70)
        print(" ✅ ALL TESTS PASSED")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
