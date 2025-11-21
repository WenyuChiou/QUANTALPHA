"""Backtester agent: runs backtests and collects metrics."""

import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Add src to path if needed
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.memory.schemas import AgentResult, AgentContent, AgentArtifact
from src.tools.run_backtest import run_backtest


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
    ) -> AgentResult:
        """Run a backtest.
        
        Args:
            factor_yaml: Factor DSL YAML
            prices_df: Prices DataFrame
            returns_df: Returns DataFrame
            run_id: Optional run ID for output directory
            split_cfg: Walk-forward split configuration
        
        Returns:
            AgentResult with backtest metrics and artifacts
        """
        # Create output directory
        if run_id:
            output_dir = self.output_base_dir / run_id
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = self.output_base_dir / timestamp
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Run backtest
            result = run_backtest(
                factor_yaml=factor_yaml,
                prices_df=prices_df,
                returns_df=returns_df,
                split_cfg=split_cfg,
                output_dir=output_dir
            )
            
            if not result.get('is_valid', False):
                return AgentResult(
                    agent="Backtester",
                    step="RunBacktest",
                    status="FAILURE",
                    content=AgentContent(
                        summary="Backtest failed or produced invalid results.",
                        data={
                            "issues": result.get('issues', []),
                            "error": result.get('error')
                        }
                    )
                )
            
            metrics = result.get('metrics', {})
            sharpe = metrics.get('sharpe', 0)
            
            return AgentResult(
                agent="Backtester",
                step="RunBacktest",
                status="SUCCESS",
                content=AgentContent(
                    summary=f"Backtest complete. Sharpe: {sharpe:.2f}",
                    data={
                        "metrics": metrics,
                        "output_dir": str(output_dir)
                    },
                    artifacts=[
                        AgentArtifact(name="metrics", path=str(output_dir / "metrics.json"), type="json", description="Performance metrics"),
                        AgentArtifact(name="equity_curve", path=str(output_dir / "equity_curve.parquet"), type="parquet", description="Equity curve")
                    ]
                )
            )
            
        except Exception as e:
            return AgentResult(
                agent="Backtester",
                step="RunBacktest",
                status="FAILURE",
                content=AgentContent(
                    summary=f"Backtest execution error: {str(e)}",
                    data={"error": str(e)}
                )
            )


