"""Success factor archive system.

This module archives complete factor lifecycle data for factors that meet
performance criteria (Sharpe >= 1.8, MaxDD <= -25%, IC >= 0.05).
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd


class SuccessFactorArchive:
    """Archive successful factors with complete outputs."""
    
    def __init__(self, archive_dir: str = "success_factors"):
        """Initialize archive.
        
        Args:
            archive_dir: Directory to store archived factors
        """
        self.archive_dir = Path(archive_dir)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
    
    def should_archive(self, metrics: Dict[str, float]) -> bool:
        """Check if factor meets archival criteria.
        
        Args:
            metrics: Performance metrics dictionary
            
        Returns:
            True if factor should be archived
        """
        sharpe = metrics.get('sharpe', 0)
        max_dd = metrics.get('max_drawdown', 0)
        avg_ic = metrics.get('avg_ic', 0)
        
        return (
            sharpe >= 1.8 and
            max_dd >= -0.25 and  # Note: max_dd is negative, so >= -0.25 means better than -25%
            avg_ic >= 0.05
        )
    
    def archive_factor(
        self,
        factor_name: str,
        factor_yaml: str,
        agent_outputs: Dict[str, Any],
        computations: Dict[str, pd.DataFrame],
        backtest_results: Dict[str, Any],
        conversation_log: List[Dict[str, str]]
    ) -> str:
        """Archive complete factor data.
        
        Args:
            factor_name: Name of the factor
            factor_yaml: Complete YAML specification
            agent_outputs: Dictionary of agent outputs
            computations: Dictionary of DataFrames (signals, returns, etc.)
            backtest_results: Backtest results dictionary
            conversation_log: List of conversation messages
            
        Returns:
            Path to archived factor directory
        """
        # Create timestamped directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_path = self.archive_dir / f"{factor_name}_{timestamp}"
        archive_path.mkdir(parents=True, exist_ok=True)
        
        # 1. Save metadata
        metadata = {
            "factor_name": factor_name,
            "timestamp": timestamp,
            "metrics": backtest_results.get('metrics', {}),
            "archived_at": datetime.now().isoformat(),
            "archive_reason": "Meets success criteria",
            "criteria": {
                "sharpe": ">= 1.8",
                "max_drawdown": ">= -0.25",
                "avg_ic": ">= 0.05"
            }
        }
        self._save_json(archive_path / "metadata.json", metadata)
        
        # 2. Save factor spec
        self._save_text(archive_path / "factor_spec.yaml", factor_yaml)
        
        # 3. Save agent outputs
        agent_dir = archive_path / "agent_outputs"
        agent_dir.mkdir(exist_ok=True)
        for agent_name, output in agent_outputs.items():
            self._save_json(agent_dir / f"{agent_name}.json", output)
        
        # 4. Save computations
        comp_dir = archive_path / "computations"
        comp_dir.mkdir(exist_ok=True)
        for name, df in computations.items():
            if df is not None and isinstance(df, pd.DataFrame):
                df.to_parquet(comp_dir / f"{name}.parquet")
        
        # 5. Save backtest results
        backtest_dir = archive_path / "backtest"
        backtest_dir.mkdir(exist_ok=True)
        self._save_json(backtest_dir / "metrics.json", backtest_results.get('metrics', {}))
        if 'splits' in backtest_results:
            self._save_json(backtest_dir / "split_results.json", backtest_results['splits'])
        
        # 6. Save conversation log
        self._save_json(archive_path / "conversation_log.json", conversation_log)
        
        # 7. Create README
        self._create_readme(archive_path, factor_name, metadata)
        
        return str(archive_path)
    
    def list_archived_factors(
        self,
        min_sharpe: Optional[float] = None,
        min_ic: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """List all archived factors with their metadata.
        
        Args:
            min_sharpe: Minimum Sharpe ratio filter
            min_ic: Minimum IC filter
            
        Returns:
            List of metadata dictionaries
        """
        factors = []
        
        for factor_dir in self.archive_dir.iterdir():
            if not factor_dir.is_dir():
                continue
            
            metadata_file = factor_dir / "metadata.json"
            if not metadata_file.exists():
                continue
            
            metadata = self._load_json(metadata_file)
            
            # Apply filters
            if min_sharpe is not None:
                if metadata.get('metrics', {}).get('sharpe', 0) < min_sharpe:
                    continue
            
            if min_ic is not None:
                if metadata.get('metrics', {}).get('avg_ic', 0) < min_ic:
                    continue
            
            factors.append({
                'path': str(factor_dir),
                'name': metadata.get('factor_name'),
                'timestamp': metadata.get('timestamp'),
                'metrics': metadata.get('metrics', {})
            })
        
        # Sort by Sharpe ratio (descending)
        factors.sort(key=lambda x: x['metrics'].get('sharpe', 0), reverse=True)
        
        return factors
    
    def load_factor(self, factor_path: str) -> Dict[str, Any]:
        """Load complete factor data from archive.
        
        Args:
            factor_path: Path to archived factor directory
            
        Returns:
            Dictionary with all factor data
        """
        path = Path(factor_path)
        
        if not path.exists():
            raise ValueError(f"Factor archive not found: {factor_path}")
        
        # Load all components
        data = {
            'metadata': self._load_json(path / "metadata.json"),
            'factor_yaml': self._load_text(path / "factor_spec.yaml"),
            'agent_outputs': {},
            'computations': {},
            'backtest_results': {},
            'conversation_log': self._load_json(path / "conversation_log.json")
        }
        
        # Load agent outputs
        agent_dir = path / "agent_outputs"
        if agent_dir.exists():
            for agent_file in agent_dir.glob("*.json"):
                agent_name = agent_file.stem
                data['agent_outputs'][agent_name] = self._load_json(agent_file)
        
        # Load computations
        comp_dir = path / "computations"
        if comp_dir.exists():
            for comp_file in comp_dir.glob("*.parquet"):
                comp_name = comp_file.stem
                data['computations'][comp_name] = pd.read_parquet(comp_file)
        
        # Load backtest results
        backtest_dir = path / "backtest"
        if backtest_dir.exists():
            data['backtest_results']['metrics'] = self._load_json(backtest_dir / "metrics.json")
            split_file = backtest_dir / "split_results.json"
            if split_file.exists():
                data['backtest_results']['splits'] = self._load_json(split_file)
        
        return data
    
    def _save_json(self, path: Path, data: Any):
        """Save data as JSON."""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    def _load_json(self, path: Path) -> Any:
        """Load JSON data."""
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _save_text(self, path: Path, text: str):
        """Save text file."""
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)
    
    def _load_text(self, path: Path) -> str:
        """Load text file."""
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _create_readme(self, archive_path: Path, factor_name: str, metadata: Dict[str, Any]):
        """Create README file for archived factor."""
        metrics = metadata.get('metrics', {})
        
        # Helper for safe formatting
        def fmt(val, format_spec):
            try:
                return f"{float(val):{format_spec}}"
            except (ValueError, TypeError):
                return "N/A"
        
        # Handle key variations
        sharpe = metrics.get('sharpe', 0)
        max_dd = metrics.get('max_drawdown', metrics.get('maxdd', 0))
        avg_ic = metrics.get('avg_ic', 0)
        turnover = metrics.get('turnover', 0)
        
        readme = f"""# {factor_name}

**Archived**: {metadata.get('archived_at')}

## Performance Metrics

- **Sharpe Ratio**: {fmt(sharpe, '.2f')}
- **Max Drawdown**: {fmt(max_dd, '.2%')}
- **Average IC**: {fmt(avg_ic, '.4f')}
- **Turnover**: {fmt(turnover, '.1f')}%

## Archive Contents

- `metadata.json` - Factor information and metrics
- `factor_spec.yaml` - Complete factor specification
- `agent_outputs/` - All agent responses
  - `researcher_proposal.json` - Original proposal
  - `feature_computation.json` - Computation log
  - `backtest_results.json` - Backtest results
  - `critic_evaluation.json` - Critique
- `computations/` - Computed data
  - `signals.parquet` - Factor signals
  - `returns.parquet` - Portfolio returns
  - `equity_curve.parquet` - Equity curve
- `backtest/` - Backtest details
  - `metrics.json` - Performance metrics
  - `split_results.json` - Walk-forward split results
- `conversation_log.json` - Complete agent dialogue

## Success Criteria

This factor met the following criteria:
- Sharpe Ratio >= 1.8
- Max Drawdown >= -25%
- Average IC >= 0.05
"""
        
        self._save_text(archive_path / "README.md", readme)
