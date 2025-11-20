"""Feature agent: executes Factor DSL and computes features."""

from typing import Dict, Any, Optional
import pandas as pd

from ..factors.dsl import DSLParser
from ..tools.compute_factor import compute_factor


class FeatureAgent:
    """Agent that computes factor signals from Factor DSL."""
    
    def __init__(self):
        """Initialize feature agent."""
        self.parser = DSLParser()
    
    def compute_features(
        self,
        factor_yaml: str,
        prices_df: pd.DataFrame,
        returns_df: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """Compute factor features from DSL.
        
        Args:
            factor_yaml: Factor DSL YAML string
            prices_df: Prices DataFrame
            returns_df: Optional returns DataFrame
        
        Returns:
            Dictionary with signals, schema, warnings, validation results
        """
        # Parse and validate
        try:
            spec = self.parser.parse(factor_yaml)
        except Exception as e:
            return {
                'success': False,
                'error': f"Parse error: {e}",
                'signals': None
            }
        
        # Validate no-lookahead
        is_valid, warnings = self.parser.validate_no_lookahead(spec)
        
        if not is_valid:
            return {
                'success': False,
                'error': "Lookahead validation failed",
                'warnings': warnings,
                'signals': None
            }
        
        # Compute signals
        result = compute_factor(factor_yaml, prices_df, returns_df)
        
        if result['signals'] is None:
            return {
                'success': False,
                'error': result.get('error', 'Unknown error'),
                'warnings': result.get('warnings', []),
                'signals': None
            }
        
        return {
            'success': True,
            'signals': result['signals'],
            'schema': result['schema'],
            'warnings': result.get('warnings', []),
            'spec': spec
        }

