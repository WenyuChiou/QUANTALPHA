"""Generate resolved alpha_spec.json from Factor DSL YAML."""

import yaml
import json
from typing import Dict, Any, List
from pathlib import Path


def parse_expression(expr: str) -> Dict[str, Any]:
    """Parse a signal expression into structured format.
    
    Args:
        expr: Expression string like "RET_252 - RET_21"
    
    Returns:
        Structured expression definition
    """
    # This is a simplified parser - in production, you'd want more robust parsing
    expr = expr.strip()
    
    # Handle common patterns
    if "RET_" in expr:
        # Extract window size
        import re
        windows = re.findall(r'RET_(\d+)', expr)
        if windows:
            return {
                'type': 'return',
                'windows': [int(w) for w in windows],
                'expr': expr
            }
    
    if "ROLL_STD" in expr:
        return {
            'type': 'rolling_std',
            'expr': expr
        }
    
    if "VOL_TARGET" in expr:
        return {
            'type': 'vol_target',
            'expr': expr
        }
    
    return {
        'type': 'custom',
        'expr': expr
    }


def resolve_signal_definitions(signals: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Resolve signal definitions into explicit formulas.
    
    Args:
        signals: List of signal definitions from DSL
    
    Returns:
        List of resolved signal definitions
    """
    definitions = []
    
    # Always start with daily return
    definitions.append({
        'id': 'r_d',
        'expr': 'ln(P_t/P_{t-1})',
        'lag': 1
    })
    
    for signal in signals:
        signal_id = signal['id']
        expr = signal['expr']
        
        # Parse expression
        parsed = parse_expression(expr)
        
        if parsed['type'] == 'return':
            # Add return calculations
            for window in parsed['windows']:
                ret_id = f"ret_{window}"
                if ret_id not in [d['id'] for d in definitions]:
                    definitions.append({
                        'id': ret_id,
                        'expr': f"exp(sum_{{k=1..{window}}}(r_{{t-k}}))-1"
                    })
        
        # Add the main signal
        if 'standardize' in signal:
            std_method = signal['standardize']
            if 'zscore' in std_method:
                window = std_method.replace('zscore_', '')
                definitions.append({
                    'id': signal_id,
                    'expr': f"({expr}-mean_{{{window}}}({expr}))/std_{{{window}}}({expr})"
                })
            else:
                definitions.append({
                    'id': signal_id,
                    'expr': expr
                })
        else:
            definitions.append({
                'id': signal_id,
                'expr': expr
            })
    
    return definitions


def dsl_to_alpha_spec(factor_yaml: str, output_path: Path = None) -> Dict[str, Any]:
    """Convert Factor DSL YAML to resolved alpha_spec.json.
    
    Args:
        factor_yaml: Factor DSL YAML string
        output_path: Optional path to save JSON file
    
    Returns:
        Resolved alpha spec dictionary
    """
    # Parse YAML
    spec = yaml.safe_load(factor_yaml)
    
    # Resolve signal definitions
    signal_defs = resolve_signal_definitions(spec.get('signals', []))
    
    # Build resolved spec
    alpha_spec = {
        'name': spec['name'],
        'universe': spec.get('universe', 'sp500'),
        'frequency': spec.get('frequency', 'D'),
        'signal': {
            'definitions': signal_defs,
            'gating': spec.get('gating', [])
        },
        'portfolio': {
            'construction': spec.get('portfolio', {}).get('scheme', 'long_short_deciles'),
            'weighting': spec.get('portfolio', {}).get('weight', 'equal'),
            'rebalance': spec.get('portfolio', {}).get('rebalance', 'D'),
            'costs': spec.get('portfolio', {}).get('costs', {
                'bps_per_trade': 5,
                'borrow_bps': 50
            }),
            'turnover_cap_monthly': 2.0
        },
        'validation': {
            'no_lookahead': True,
            'purge_days': spec.get('validation', {}).get('purge_days', 21),
            'embargo_days': spec.get('validation', {}).get('embargo_days', 5),
            'min_history_days': spec.get('validation', {}).get('min_history_days', 800)
        }
    }
    
    # Save to file if path provided
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(alpha_spec, f, indent=2)
    
    return alpha_spec


def test_dsl_conversion():
    """Test DSL to alpha_spec conversion."""
    print("="*70)
    print(" DSL → Resolved Alpha Spec Conversion Test")
    print("="*70)
    
    # Example DSL from blueprint
    dsl_yaml = """
name: "TSMOM_252_minus_21_volTarget"
universe: "sp500"
frequency: "D"
signals:
  - id: "mom12_1"
    expr: "RET_252 - RET_21"
    standardize: "zscore_252"
  - id: "rv_21"
    expr: "ROLL_STD(RET_D, 21) * sqrt(252)"
  - id: "w_vol"
    expr: "VOL_TARGET(0.15, rv_21)"
gating:
  - when: "regime=='high_vol'"
    condition: "z(mom12_1,252) > 0.5"
    else_weight: 0.0
portfolio:
  scheme: "long_short_deciles"
  weight: "equal * w_vol"
  rebalance: "W-FRI"
  costs:
    bps_per_trade: 5
    borrow_bps: 50
validation:
  purge_days: 21
  embargo_days: 5
  min_history_days: 800
"""
    
    print("\nInput DSL:")
    print("-" * 70)
    print(dsl_yaml)
    
    # Convert to alpha_spec
    output_path = Path('test_results/mcp_tools/alpha_spec.json')
    alpha_spec = dsl_to_alpha_spec(dsl_yaml, output_path)
    
    print("\nResolved alpha_spec.json:")
    print("-" * 70)
    print(json.dumps(alpha_spec, indent=2))
    
    print(f"\n✓ Saved to: {output_path}")
    print(f"  File size: {output_path.stat().st_size} bytes")
    
    # Verify structure
    required_keys = ['name', 'universe', 'frequency', 'signal', 'portfolio', 'validation']
    missing_keys = [k for k in required_keys if k not in alpha_spec]
    
    if not missing_keys:
        print("\n✓ All required keys present")
        print("✓ Signal definitions:", len(alpha_spec['signal']['definitions']))
        print("✓ Gating rules:", len(alpha_spec['signal']['gating']))
        print("✓ Validation rules:", len(alpha_spec['validation']))
        return True
    else:
        print(f"\n✗ Missing keys: {missing_keys}")
        return False


if __name__ == '__main__':
    import sys
    success = test_dsl_conversion()
    sys.exit(0 if success else 1)
