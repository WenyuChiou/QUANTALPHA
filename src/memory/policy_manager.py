"""Policy Rules Manager - loads, updates, and applies policy rules."""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


class PolicyManager:
    """Manages policy rules for alpha discovery."""
    
    def __init__(self, rules_path: str = "src/memory/policy_rules.json"):
        """Initialize policy manager.
        
        Args:
            rules_path: Path to policy rules JSON file
        """
        self.rules_path = Path(rules_path)
        self.rules = self.load_rules()
    
    def load_rules(self) -> Dict[str, Any]:
        """Load policy rules from JSON file.
        
        Returns:
            Policy rules dictionary
        """
        if not self.rules_path.exists():
            # Return default rules if file doesn't exist
            return {
                "version": "1.0",
                "updated_at": datetime.now().isoformat(),
                "rules": [],
                "global_constraints": {
                    "min_sharpe": 1.0,
                    "max_maxdd": -0.20,
                    "max_turnover_monthly": 100.0,
                    "min_avg_ic": 0.05
                },
                "iteration_limits": {
                    "max_iterations": 10,
                    "early_stop_sharpe": 2.0
                }
            }
        
        with open(self.rules_path, 'r') as f:
            return json.load(f)
    
    def save_rules(self):
        """Save policy rules to JSON file."""
        self.rules['updated_at'] = datetime.now().isoformat()
        
        with open(self.rules_path, 'w') as f:
            json.dump(self.rules, f, indent=2)
    
    def get_applicable_rules(self, metrics: Dict[str, Any], factor_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get rules applicable to current metrics.
        
        Args:
            metrics: Performance metrics
            factor_type: Type of factor (e.g., 'momentum')
        
        Returns:
            List of applicable rules
        """
        applicable = []
        
        for rule in self.rules['rules']:
            condition = rule['condition']
            
            # Parse condition
            if self._evaluate_condition(condition, metrics, factor_type):
                applicable.append(rule)
        
        return applicable
    
    def _evaluate_condition(self, condition: str, metrics: Dict[str, Any], factor_type: Optional[str]) -> bool:
        """Evaluate a rule condition.
        
        Args:
            condition: Condition string (e.g., "sharpe < 1.0")
            metrics: Performance metrics
            factor_type: Type of factor
        
        Returns:
            True if condition is met
        """
        # Simple condition parser
        # Format: "metric_name operator value" or "factor_type == 'type' and metric_name operator value"
        
        if 'factor_type' in condition:
            # Handle factor_type conditions
            parts = condition.split(' and ')
            if len(parts) == 2:
                type_cond, metric_cond = parts
                # Check factor type
                if factor_type:
                    expected_type = type_cond.split("'")[1]
                    if factor_type != expected_type:
                        return False
                    condition = metric_cond.strip()
                else:
                    return False
        
        # Skip boolean conditions (e.g., "no_llm_features == true")
        # These are for future enhancements and not currently evaluated
        if '== true' in condition or '== false' in condition:
            return False
        
        # Parse metric condition
        for op in ['<', '>', '<=', '>=', '==', '!=']:
            if op in condition:
                parts = condition.split(op)
                if len(parts) == 2:
                    metric_name = parts[0].strip()
                    threshold_str = parts[1].strip()
                    
                    # Try to convert to float
                    try:
                        threshold = float(threshold_str)
                    except ValueError:
                        # Skip non-numeric conditions
                        return False
                    
                    # Get metric value
                    metric_value = metrics.get(metric_name)
                    if metric_value is None:
                        return False
                    
                    # Evaluate
                    if op == '<':
                        return metric_value < threshold
                    elif op == '>':
                        return metric_value > threshold
                    elif op == '<=':
                        return metric_value <= threshold
                    elif op == '>=':
                        return metric_value >= threshold
                    elif op == '==':
                        return metric_value == threshold
                    elif op == '!=':
                        return metric_value != threshold
        
        return False

    
    def check_constraints(self, metrics: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Check if metrics meet global constraints.
        
        Args:
            metrics: Performance metrics
        
        Returns:
            Tuple of (meets_constraints, violations)
        """
        constraints = self.rules['global_constraints']
        violations = []
        
        # Check each constraint
        if metrics.get('sharpe', 0) < constraints['min_sharpe']:
            violations.append(f"Sharpe {metrics.get('sharpe', 0):.2f} < {constraints['min_sharpe']}")
        
        if metrics.get('maxdd', 0) < constraints['max_maxdd']:
            violations.append(f"MaxDD {metrics.get('maxdd', 0):.2%} < {constraints['max_maxdd']:.2%}")
        
        if metrics.get('turnover_monthly', 0) > constraints['max_turnover_monthly']:
            violations.append(f"Turnover {metrics.get('turnover_monthly', 0):.1f}% > {constraints['max_turnover_monthly']}%")
        
        if metrics.get('avg_ic', 0) < constraints['min_avg_ic']:
            violations.append(f"Avg IC {metrics.get('avg_ic', 0):.3f} < {constraints['min_avg_ic']}")
        
        return len(violations) == 0, violations
    
    def update_rule(self, rule_id: str, learned_from: str):
        """Update a rule with new learning.
        
        Args:
            rule_id: Rule ID to update
            learned_from: Alpha ID that triggered this rule
        """
        for rule in self.rules['rules']:
            if rule['rule_id'] == rule_id:
                if 'learned_from' not in rule:
                    rule['learned_from'] = []
                if learned_from not in rule['learned_from']:
                    rule['learned_from'].append(learned_from)
                break
        
        self.save_rules()
    
    def add_rule(self, rule: Dict[str, Any]):
        """Add a new policy rule.
        
        Args:
            rule: Rule dictionary
        """
        # Generate rule_id if not provided
        if 'rule_id' not in rule:
            existing_ids = [r['rule_id'] for r in self.rules['rules']]
            max_id = max([int(rid[1:]) for rid in existing_ids if rid.startswith('R')], default=0)
            rule['rule_id'] = f"R{max_id + 1:03d}"
        
        self.rules['rules'].append(rule)
        self.save_rules()
    
    def get_max_iterations(self) -> int:
        """Get maximum iterations allowed.
        
        Returns:
            Max iterations
        """
        return self.rules['iteration_limits']['max_iterations']
    
    def get_early_stop_sharpe(self) -> float:
        """Get Sharpe threshold for early stopping.
        
        Returns:
            Early stop Sharpe threshold
        """
        return self.rules['iteration_limits']['early_stop_sharpe']
