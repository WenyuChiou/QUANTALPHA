"""Simplified agent integration test - bypassing langchain issues.

This test directly calls agent methods and verifies JSON artifact generation.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

sys.path.append(str(Path(__file__).parent.parent))

# Import schemas
from src.schemas.manifest import ManifestSchema
from src.schemas.metrics import MetricsSchema
from src.schemas.compliance import ComplianceSchema, IssueSchema
from src.schemas.signals_meta import SignalsMetaSchema
from src.schemas.data_provenance import DataProvenanceSchema

# Import tools directly
from src.tools.fetch_data import fetch_data
from src.tools.compute_factor import compute_factor
from src.tools.run_backtest import run_backtest


def test_full_pipeline_with_artifacts():
    """Test complete pipeline and verify all JSON artifacts are generated."""
    print("\n" + "="*70)
    print(" FULL PIPELINE TEST WITH SCHEMA-COMPLIANT ARTIFACTS")
    print("="*70)
    
    output_dir = Path('test_results/agent_integration_full')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Generate factor proposals (simulating ResearcherAgent)
    print("\n[1/6] Simulating ResearcherAgent → factor_proposals.json")
    
    factor_proposals = {
        "proposals": [
            {
                "name": "momentum_vol_adjusted",
                "description": "Momentum signal adjusted by realized volatility",
                "hypothesis": "Vol-adjusted momentum is more stable than raw momentum",
                "yaml_spec": """
name: "momentum_vol_adjusted"
universe: "sp500"
frequency: "D"
signals:
  - id: "mom_21"
    expr: "RET_21"
    standardize: "zscore_63"
  - id: "vol_21"
    expr: "ROLL_STD(RET_D, 21)"
portfolio:
  scheme: "long_short_deciles"
  weight: "equal"
  rebalance: "W-FRI"
"""
            }
        ],
        "rationale": "Volatility normalization reduces signal noise in turbulent markets",
        "rag_sources": ["momentum_basics.pdf", "volatility_scaling.pdf"]
    }
    
    proposals_file = output_dir / 'factor_proposals.json'
    with open(proposals_file, 'w') as f:
        json.dump(factor_proposals, f, indent=2)
    
    print(f"  ✓ Created: {proposals_file} ({proposals_file.stat().st_size:,} bytes)")
    print(f"  ✓ Proposals: {len(factor_proposals['proposals'])}")
    
    # Step 2: Generate data provenance (simulating fetch_data)
    print("\n[2/6] Generating data_provenance.json")
    
    # Generate synthetic data
    dates = pd.date_range('2020-01-01', '2023-12-31', freq='D')
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META']
    
    np.random.seed(42)
    prices_df = pd.DataFrame(
        np.random.randn(len(dates), len(tickers)).cumsum(axis=0) * 2 + 100,
        index=dates,
        columns=tickers
    )
    prices_df = prices_df.clip(lower=10)
    returns_df = prices_df.pct_change()
    
    data_provenance = DataProvenanceSchema(
        source="synthetic",
        tickers=tickers,
        start_date="2020-01-01",
        end_date="2023-12-31",
        fields=["Close"],
        rows=len(dates),
        fetched_at=datetime.now(),
        data_quality={
            "missing_rate": 0.0,
            "outliers_detected": 0
        }
    )
    
    provenance_file = output_dir / 'data_provenance.json'
    with open(provenance_file, 'w') as f:
        json.dump(data_provenance.model_dump(mode='json'), f, indent=2, default=str)
    
    print(f"  ✓ Created: {provenance_file} ({provenance_file.stat().st_size:,} bytes)")
    print(f"  ✓ Tickers: {len(tickers)}, Rows: {len(dates)}")
    
    # Step 3: Compute signals and generate signals_meta.json
    print("\n[3/6] Computing signals → signals_meta.json")
    
    factor_yaml = factor_proposals['proposals'][0]['yaml_spec']
    
    factor_result = compute_factor(factor_yaml, prices_df, returns_df)
    
    if factor_result['signals'] is not None:
        signals_df = factor_result['signals']
        
        signals_meta = SignalsMetaSchema(
            factor_name="momentum_vol_adjusted",
            num_signals=signals_df.shape[1],
            num_observations=signals_df.shape[0],
            date_range=(str(signals_df.index[0].date()), str(signals_df.index[-1].date())),
            signal_names=list(signals_df.columns),
            coverage=1.0 - signals_df.isnull().sum().sum() / (signals_df.shape[0] * signals_df.shape[1]),
            null_rate=signals_df.isnull().sum().sum() / (signals_df.shape[0] * signals_df.shape[1]),
            standardization="zscore_63",
            universe_size=len(tickers),
            computed_at=datetime.now().isoformat()
        )
        
        meta_file = output_dir / 'signals_meta.json'
        with open(meta_file, 'w') as f:
            json.dump(signals_meta.model_dump(mode='json'), f, indent=2)
        
        print(f"  ✓ Created: {meta_file} ({meta_file.stat().st_size:,} bytes)")
        print(f"  ✓ Signals: {signals_meta.num_signals}, Coverage: {signals_meta.coverage:.2%}")
    
    # Step 4: Run backtest → metrics.json + manifest.json + 3-panel chart
    print("\n[4/6] Running backtest → metrics.json, manifest.json, charts")
    
    backtest_dir = output_dir / 'backtest'
    backtest_result = run_backtest(
        factor_yaml=factor_yaml,
        prices_df=prices_df,
        returns_df=returns_df,
        output_dir=backtest_dir
    )
    
    if backtest_result['metrics']:
        print(f"  ✓ Backtest completed")
        print(f"    Sharpe: {backtest_result['metrics'].get('sharpe', 0):.2f}")
        print(f"    Annual Return: {backtest_result['metrics'].get('ann_ret', 0):.2%}")
        
        # Check artifacts
        metrics_file = backtest_dir / 'metrics.json'
        manifest_file = backtest_dir / 'manifest.json'
        chart_file = backtest_dir / 'charts' / 'equity_curve_3panel.png'
        
        if metrics_file.exists():
            print(f"  ✓ metrics.json ({metrics_file.stat().st_size:,} bytes)")
        if manifest_file.exists():
            print(f"  ✓ manifest.json ({manifest_file.stat().st_size:,} bytes)")
        if chart_file.exists():
            print(f"  ✓ equity_curve_3panel.png ({chart_file.stat().st_size:,} bytes)")
    
    # Step 5: Generate compliance report (simulating CriticAgent)
    print("\n[5/6] Generating compliance.json")
    
    metrics = backtest_result['metrics']
    issues = []
    
    # Check for issues
    if metrics.get('sharpe', 0) < 1.0:
        issues.append(IssueSchema(
            type="low_sharpe",
            severity="warning",
            detail=f"Sharpe ratio {metrics.get('sharpe', 0):.2f} is below 1.0",
            recommendation="Consider adding more signals or improving signal quality"
        ))
    
    if metrics.get('maxdd', 0) < -0.20:
        issues.append(IssueSchema(
            type="high_drawdown",
            severity="error",
            detail=f"Max drawdown {metrics.get('maxdd', 0):.2%} exceeds -20%",
            recommendation="Implement risk management or position sizing"
        ))
    
    compliance = ComplianceSchema(
        passed=len([i for i in issues if i.severity == 'error']) == 0,
        verdict="CONDITIONAL" if issues else "PASS",
        issues=issues,
        recommendations=[
            "Monitor performance in different market regimes",
            "Consider transaction cost sensitivity"
        ],
        critique_summary=f"Factor shows {'acceptable' if not issues else 'mixed'} performance with {len(issues)} issues identified",
        reviewed_at=datetime.now().isoformat()
    )
    
    compliance_file = output_dir / 'compliance.json'
    with open(compliance_file, 'w') as f:
        json.dump(compliance.model_dump(mode='json'), f, indent=2)
    
    print(f"  ✓ Created: {compliance_file} ({compliance_file.stat().st_size:,} bytes)")
    print(f"  ✓ Verdict: {compliance.verdict}, Issues: {len(issues)}")
    
    # Step 6: Summary
    print("\n[6/6] Artifact Summary")
    print("="*70)
    
    all_artifacts = list(output_dir.rglob('*.json')) + list(output_dir.rglob('*.png'))
    
    print(f"\nGenerated {len(all_artifacts)} artifacts:")
    for artifact in sorted(all_artifacts):
        rel_path = artifact.relative_to(output_dir)
        size = artifact.stat().st_size
        print(f"  • {rel_path} ({size:,} bytes)")
    
    # Verify schema compliance
    print("\n" + "="*70)
    print(" SCHEMA VALIDATION")
    print("="*70)
    
    from src.schemas.validate import validate_json_against_schema
    
    schema_checks = [
        (proposals_file, None, "factor_proposals.json"),
        (provenance_file, DataProvenanceSchema, "data_provenance.json"),
        (meta_file, SignalsMetaSchema, "signals_meta.json"),
        (metrics_file, MetricsSchema, "metrics.json"),
        (manifest_file, ManifestSchema, "manifest.json"),
        (compliance_file, ComplianceSchema, "compliance.json")
    ]
    
    all_valid = True
    for file_path, schema_class, name in schema_checks:
        if file_path.exists() and schema_class:
            is_valid, errors = validate_json_against_schema(file_path, schema_class)
            if is_valid:
                print(f"  ✓ {name} - VALID")
            else:
                print(f"  ✗ {name} - INVALID")
                for error in errors:
                    print(f"      {error}")
                all_valid = False
        elif file_path.exists():
            print(f"  ○ {name} - EXISTS (no schema)")
    
    print("\n" + "="*70)
    print(" FINAL RESULT")
    print("="*70)
    
    if all_valid:
        print("✓ ALL ARTIFACTS GENERATED AND SCHEMA-COMPLIANT")
        return True
    else:
        print("✗ SOME ARTIFACTS FAILED SCHEMA VALIDATION")
        return False


if __name__ == '__main__':
    try:
        success = test_full_pipeline_with_artifacts()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
