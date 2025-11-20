"""Backtester agent: runs backtests and collects metrics."""

from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from ..tools.run_backtest import run_backtest


class BacktesterAgent:
    """Agent that orchestrates backtest runs."""
    
    def __init__(self, output_base_dir: Path = Path("experiments/runs")):
        """Initialize backtester agent.
        
        Args:
            output_base_dir: Base directory for backtest outputs
        """
        self.output_base_dir = output_base_dir
        self.output_base_dir.mkdir(parents=True, exist_ok=True)
    
    def run_backtest(
        self,
        factor_yaml: str,
        prices_df,
        returns_df,
        run_id: Optional[str] = None,
        split_cfg: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Run a backtest.
        
        Args:
            factor_yaml: Factor DSL YAML
            prices_df: Prices DataFrame
            returns_df: Returns DataFrame
            run_id: Optional run ID for output directory
            split_cfg: Walk-forward split configuration
        
        Returns:
            Backtest results dictionary
        """
        # Create output directory
        if run_id:
            output_dir = self.output_base_dir / run_id
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = self.output_base_dir / timestamp
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Run backtest
        result = run_backtest(
            factor_yaml=factor_yaml,
            prices_df=prices_df,
            returns_df=returns_df,
            split_cfg=split_cfg,
            output_dir=output_dir
        )
        
        result['output_dir'] = str(output_dir)
        
        return result

