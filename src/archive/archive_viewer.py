"""Archive viewer and comparison tools."""

import pandas as pd
from typing import List, Dict, Any, Optional
from pathlib import Path
from .success_factors import SuccessFactorArchive


class ArchiveViewer:
    """Tools for viewing and comparing archived factors."""
    
    def __init__(self, archive_dir: str = "success_factors"):
        """Initialize viewer.
        
        Args:
            archive_dir: Directory containing archived factors
        """
        self.archive = SuccessFactorArchive(archive_dir)
    
    def list_factors(
        self,
        min_sharpe: Optional[float] = None,
        min_ic: Optional[float] = None,
        top_n: Optional[int] = None
    ) -> pd.DataFrame:
        """List archived factors as DataFrame.
        
        Args:
            min_sharpe: Minimum Sharpe ratio filter
            min_ic: Minimum IC filter
            top_n: Return only top N factors by Sharpe
            
        Returns:
            DataFrame with factor information
        """
        factors = self.archive.list_archived_factors(min_sharpe, min_ic)
        
        if top_n is not None:
            factors = factors[:top_n]
        
        # Convert to DataFrame
        rows = []
        for f in factors:
            metrics = f['metrics']
            rows.append({
                'Name': f['name'],
                'Timestamp': f['timestamp'],
                'Sharpe': metrics.get('sharpe', 0),
                'MaxDD': metrics.get('max_drawdown', 0),
                'AvgIC': metrics.get('avg_ic', 0),
                'Turnover': metrics.get('turnover', 0),
                'Path': f['path']
            })
        
        return pd.DataFrame(rows)
    
    def compare_factors(
        self,
        factor_paths: List[str],
        metrics: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """Compare multiple factors side-by-side.
        
        Args:
            factor_paths: List of paths to archived factors
            metrics: List of metrics to compare (default: all)
            
        Returns:
            Comparison DataFrame
        """
        if metrics is None:
            metrics = ['sharpe', 'max_drawdown', 'avg_ic', 'turnover']
        
        comparison = []
        
        for path in factor_paths:
            data = self.archive.load_factor(path)
            metadata = data['metadata']
            factor_metrics = metadata.get('metrics', {})
            
            row = {
                'Factor': metadata.get('factor_name'),
                'Timestamp': metadata.get('timestamp')
            }
            
            for metric in metrics:
                row[metric] = factor_metrics.get(metric, None)
            
            comparison.append(row)
        
        return pd.DataFrame(comparison)
    
    def get_factor_details(self, factor_path: str) -> Dict[str, Any]:
        """Get detailed information about a factor.
        
        Args:
            factor_path: Path to archived factor
            
        Returns:
            Dictionary with factor details
        """
        data = self.archive.load_factor(factor_path)
        
        return {
            'metadata': data['metadata'],
            'yaml_spec': data['factor_yaml'],
            'agent_outputs': data['agent_outputs'],
            'backtest_metrics': data['backtest_results'].get('metrics', {}),
            'conversation_summary': self._summarize_conversation(data['conversation_log'])
        }
    
    def get_equity_curve(self, factor_path: str) -> pd.DataFrame:
        """Get equity curve for a factor.
        
        Args:
            factor_path: Path to archived factor
            
        Returns:
            Equity curve DataFrame
        """
        data = self.archive.load_factor(factor_path)
        
        if 'equity_curve' in data['computations']:
            return data['computations']['equity_curve']
        
        # If not available, compute from returns
        if 'returns' in data['computations']:
            returns = data['computations']['returns']
            equity = (1 + returns).cumprod()
            return equity
        
        raise ValueError("No equity curve or returns data available")
    
    def get_signals(self, factor_path: str) -> pd.DataFrame:
        """Get factor signals.
        
        Args:
            factor_path: Path to archived factor
            
        Returns:
            Signals DataFrame
        """
        data = self.archive.load_factor(factor_path)
        
        if 'signals' not in data['computations']:
            raise ValueError("No signals data available")
        
        return data['computations']['signals']
    
    def _summarize_conversation(self, conversation_log: List[Dict[str, str]]) -> Dict[str, Any]:
        """Summarize conversation log.
        
        Args:
            conversation_log: List of conversation messages
            
        Returns:
            Summary dictionary
        """
        if not conversation_log:
            return {'total_messages': 0}
        
        agents = set()
        for msg in conversation_log:
            if 'agent' in msg:
                agents.add(msg['agent'])
        
        return {
            'total_messages': len(conversation_log),
            'agents_involved': list(agents),
            'first_message': conversation_log[0].get('content', '')[:100] if conversation_log else '',
            'last_message': conversation_log[-1].get('content', '')[:100] if conversation_log else ''
        }


def print_factor_summary(factor_path: str):
    """Print a formatted summary of a factor.
    
    Args:
        factor_path: Path to archived factor
    """
    viewer = ArchiveViewer()
    details = viewer.get_factor_details(factor_path)
    
    metadata = details['metadata']
    metrics = details['backtest_metrics']
    
    print(f"\n{'='*60}")
    print(f"Factor: {metadata.get('factor_name')}")
    print(f"Archived: {metadata.get('archived_at')}")
    print(f"{'='*60}\n")
    
    print("Performance Metrics:")
    print(f"  Sharpe Ratio:    {metrics.get('sharpe', 0):.2f}")
    print(f"  Max Drawdown:    {metrics.get('max_drawdown', 0):.2%}")
    print(f"  Average IC:      {metrics.get('avg_ic', 0):.4f}")
    print(f"  Turnover:        {metrics.get('turnover', 0):.1f}%")
    
    print(f"\nAgent Outputs: {len(details['agent_outputs'])} agents")
    for agent in details['agent_outputs'].keys():
        print(f"  - {agent}")
    
    conv_summary = details['conversation_summary']
    print(f"\nConversation: {conv_summary.get('total_messages', 0)} messages")
    print(f"Agents: {', '.join(conv_summary.get('agents_involved', []))}")
    
    print(f"\n{'='*60}\n")
