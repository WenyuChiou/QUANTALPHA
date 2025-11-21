"""Feature agent: executes Factor DSL and computes features."""

import sys
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd

# Add src to path if needed
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.memory.schemas import AgentResult, AgentContent, AgentArtifact
from src.factors.dsl import DSLParser
from src.tools.compute_factor import compute_factor


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
    ) -> AgentResult:
        """Compute factor features from DSL.
        
        Args:
            factor_yaml: Factor DSL YAML string
            prices_df: Prices DataFrame
            returns_df: Optional returns DataFrame
        
        Returns:
            AgentResult with signals and validation status
        """
        # Parse and validate
        try:
            spec = self.parser.parse(factor_yaml)
        except Exception as e:
            return AgentResult(
                agent="FeatureEngineer",
                step="ValidateAndCompute",
                status="FAILURE",
                content=AgentContent(
                    summary=f"DSL Parsing failed: {str(e)}",
                    data={"error": str(e)}
                )
            )
        
        # Validate no-lookahead
        is_valid, warnings = self.parser.validate_no_lookahead(spec)
        
        if not is_valid:
            return AgentResult(
                agent="FeatureEngineer",
                step="ValidateAndCompute",
                status="FAILURE",
                content=AgentContent(
                    summary="Lookahead bias detected in factor definition.",
                    data={
                        "error": "Lookahead validation failed",
                        "warnings": warnings
                    }
                )
            )
        
        # Compute signals
        result = compute_factor(factor_yaml, prices_df, returns_df)
        
        if result['signals'] is None:
            return AgentResult(
                agent="FeatureEngineer",
                step="ValidateAndCompute",
                status="FAILURE",
                content=AgentContent(
                    summary="Factor computation failed.",
                    data={
                        "error": result.get('error', 'Unknown error'),
                        "warnings": result.get('warnings', [])
                    }
                )
            )
        
        return AgentResult(
            agent="FeatureEngineer",
            step="ValidateAndCompute",
            status="SUCCESS",
            content=AgentContent(
                summary="Factor signals computed successfully.",
                data={
                    "signals": result['signals'], # Note: This might be large for JSON serialization, consider saving to parquet
                    "schema": result['schema'],
                    "warnings": result.get('warnings', [])
                },
                artifacts=[
                    AgentArtifact(name="signals", path="memory", type="dataframe", description="Computed factor signals")
                ]
            )
        )


