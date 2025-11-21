"""
Simple verification test for Phase 13 enhancements

This test verifies that the core components are correctly updated:
1. ResearcherAgent accepts policy_rules and past_lessons
2. ReflectorAgent detects repeated errors
3. Suggestions have priority levels
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

def test_researcher_accepts_lessons():
    """Test that ResearcherAgent accepts policy_rules and past_lessons."""
    print("\n[Test 1/3] ResearcherAgent accepts policy_rules and past_lessons...")
    
    from src.agents.researcher import ResearcherAgent
    
    researcher = ResearcherAgent()
    
    # Create mock policy rules and lessons
    policy_rules = {
        'global_constraints': {
            'min_sharpe': 1.8,
            'max_maxdd': -0.25,
            'min_avg_ic': 0.05
        }
    }
    
    past_lessons = [
        {
            'alpha_id': 'alpha_001',
            'verdict': 'FAIL',
            'root_causes': [
                {'issue': 'Low Sharpe', 'detail': 'Sharpe 0.5 < 1.8'}
            ],
            'improvement_suggestions': [
                {'suggestion': 'Try different factor', 'priority': 'high'}
            ]
        }
    ]
    
    # Test that propose_factor accepts these parameters
    result = researcher.propose_factor(
        market_regime="test",
        existing_factors=[],
        policy_rules=policy_rules,
        past_lessons=past_lessons
    )
    
    assert result.status == "SUCCESS", "ResearcherAgent should succeed"
    assert result.metadata.get('used_lessons') == 1, "Should use 1 lesson"
    assert result.metadata.get('has_policy_rules') == True, "Should have policy rules"
    
    print("  ✓ ResearcherAgent correctly accepts policy_rules and past_lessons")
    print(f"    - Used lessons: {result.metadata.get('used_lessons')}")
    print(f"    - Has policy rules: {result.metadata.get('has_policy_rules')}")


def test_reflector_detects_repeated_errors():
    """Test that ReflectorAgent detects repeated errors."""
    print("\n[Test 2/3] ReflectorAgent detects repeated errors...")
    
    from src.agents.reflector import ReflectorAgent
    
    reflector = ReflectorAgent()
    
    # Create past lessons with repeated issues
    past_lessons = [
        {
            'alpha_id': 'alpha_001',
            'verdict': 'FAIL',
            'root_causes': [
                {'issue': 'Low Sharpe', 'detail': 'Sharpe 0.5 < 1.8'}
            ]
        },
        {
            'alpha_id': 'alpha_002',
            'verdict': 'FAIL',
            'root_causes': [
                {'issue': 'Low Sharpe', 'detail': 'Sharpe 0.6 < 1.8'}
            ]
        }
    ]
    
    current_causes = [
        {'issue': 'Low Sharpe', 'detail': 'Sharpe 0.7 < 1.8'}
    ]
    
    # Test repeated error detection
    repeated = reflector._detect_repeated_issues(past_lessons, current_causes)
    
    assert len(repeated) > 0, "Should detect repeated issues"
    assert repeated[0]['issue'] == 'Low Sharpe', "Should detect Low Sharpe"
    assert repeated[0]['count'] >= 3, "Should count 3 occurrences"
    
    print("  ✓ ReflectorAgent correctly detects repeated errors")
    print(f"    - Repeated issues: {len(repeated)}")
    print(f"    - Issue: {repeated[0]['issue']} (count: {repeated[0]['count']})")


def test_suggestions_have_priority():
    """Test that suggestions have priority levels."""
    print("\n[Test 3/3] Suggestions have priority levels...")
    
    from src.agents.reflector import ReflectorAgent
    
    reflector = ReflectorAgent()
    
    root_causes = [
        {'issue': 'Low Sharpe', 'detail': 'Sharpe 0.5 < 1.8', 'recommendation': 'Try different factor'}
    ]
    
    metrics = {
        'sharpe': 0.5,
        'avg_ic': 0.02,
        'turnover_monthly': 200
    }
    
    # Test suggestion generation
    suggestions = reflector._generate_improvements(root_causes, metrics, past_lessons=None)
    
    assert len(suggestions) > 0, "Should generate suggestions"
    assert all('priority' in sug for sug in suggestions), "All suggestions should have priority"
    assert all('suggestion' in sug for sug in suggestions), "All suggestions should have text"
    
    # Check priority levels
    priorities = [sug['priority'] for sug in suggestions]
    assert any(p in ['critical', 'high', 'normal'] for p in priorities), "Should have valid priorities"
    
    print("  ✓ Suggestions correctly have priority levels")
    print(f"    - Total suggestions: {len(suggestions)}")
    print(f"    - Priorities: {', '.join(set(priorities))}")
    for i, sug in enumerate(suggestions[:3], 1):
        print(f"    {i}. [{sug['priority'].upper()}] {sug['suggestion'][:60]}...")


def main():
    """Run all tests."""
    print("="*80)
    print(" PHASE 13: COMPONENT VERIFICATION TEST")
    print("="*80)
    
    try:
        test_researcher_accepts_lessons()
        test_reflector_detects_repeated_errors()
        test_suggestions_have_priority()
        
        print("\n" + "="*80)
        print(" ✅ ALL TESTS PASSED")
        print("="*80)
        print("\nPhase 13 enhancements verified:")
        print("  ✓ ResearcherAgent accepts policy_rules and past_lessons")
        print("  ✓ ReflectorAgent detects repeated errors")
        print("  ✓ Suggestions have priority levels (critical/high/normal)")
        print("\nThe continuous reflection loop is ready for integration testing.")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
