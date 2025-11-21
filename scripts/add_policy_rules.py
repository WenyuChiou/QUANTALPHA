"""
Script to add R013 and R014 policy rules to policy_rules.json
"""

import json
from pathlib import Path

# Load existing policy rules
policy_file = Path("src/memory/policy_rules.json")
with open(policy_file, 'r', encoding='utf-8') as f:
    policy_data = json.load(f)

# Define new rules R013 and R014
r013 = {
    "rule_id": "R013",
    "category": "pre_backtest_validation",
    "condition": "signal_std < 0.01 OR time_std < 0.01 OR cross_std < 0.1",
    "action": "CRITICAL: Signal validation failed. Ensure signals have time variation, cross-sectional dispersion, and use .rank(axis=1, pct=True). Reject alpha immediately.",
    "priority": "critical",
    "research_basis": "Grinold & Kahn (2000): Signals must vary both temporally and cross-sectionally to generate alpha",
    "ai_enhancement": "Use LLM to analyze signal construction code and suggest improvements for variation",
    "learned_from": []
}

r014 = {
    "rule_id": "R014",
    "category": "post_backtest_validation",
    "condition": "turnover_monthly == 0 OR avg_ic == 0 OR abs(kurt) > 30 OR split_sharpe_mean < -0.5",
    "action": "CRITICAL: Backtest results unrealistic. Check: (1) turnover > 0, (2) IC != 0, (3) kurtosis < 30, (4) OOS Sharpe > -0.5. Reject alpha immediately.",
    "priority": "critical",
    "research_basis": "Harvey et al. (2016): Realistic backtests require non-zero turnover, predictive IC, and stable OOS performance",
    "ai_enhancement": "Use LLM to diagnose root cause of unrealistic results and suggest fixes",
    "learned_from": []
}

# Check if R013 and R014 already exist
existing_ids = [rule['rule_id'] for rule in policy_data['rules']]

if 'R013' not in existing_ids:
    policy_data['rules'].append(r013)
    print("✅ Added R013")
else:
    print("⚠️  R013 already exists")

if 'R014' not in existing_ids:
    policy_data['rules'].append(r014)
    print("✅ Added R014")
else:
    print("⚠️  R014 already exists")

# Save updated policy rules
with open(policy_file, 'w', encoding='utf-8') as f:
    json.dump(policy_data, f, indent=4, ensure_ascii=False)

print(f"\n✅ Policy rules updated: {len(policy_data['rules'])} total rules")
print(f"   File: {policy_file}")
