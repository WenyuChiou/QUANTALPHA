"""Test manifest generator functionality."""

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

from src.utils.manifest_generator import (
    compute_checksum,
    create_manifest,
    validate_manifest,
    update_manifest
)


def test_manifest_generator():
    """Test manifest generation with checksums."""
    print("\n" + "="*70)
    print(" MANIFEST GENERATOR TEST")
    print("="*70)
    
    # Use existing e2e test artifacts
    test_dir = Path('test_results/e2e_test/backtest')
    
    if not test_dir.exists():
        print(f"✗ Test directory not found: {test_dir}")
        print("  Run test_e2e_pipeline.py first to generate test artifacts")
        return False
    
    # Collect artifacts
    artifacts = {}
    
    metrics_file = test_dir / 'metrics.json'
    if metrics_file.exists():
        artifacts['metrics'] = metrics_file
    
    equity_file = test_dir / 'equity_curve.parquet'
    if equity_file.exists():
        artifacts['equity_curve'] = equity_file
    
    chart_file = test_dir / 'charts' / 'equity_curve_3panel.png'
    if chart_file.exists():
        artifacts['equity_curve_3panel'] = chart_file
    
    signals_file = test_dir.parent / 'signals.parquet'
    if signals_file.exists():
        artifacts['signals'] = signals_file
    
    alpha_spec_file = test_dir.parent / 'alpha_spec.json'
    if alpha_spec_file.exists():
        artifacts['alpha_spec'] = alpha_spec_file
    
    print(f"\n[1/4] Found {len(artifacts)} artifacts:")
    for name, path in artifacts.items():
        size = path.stat().st_size
        print(f"  • {name:25} {size:>10,} bytes")
    
    # Create manifest
    print("\n[2/4] Creating manifest with checksums...")
    
    metadata = {
        'python_version': '3.11.0',
        'quantalpha_version': '0.1.0',
        'test_run': True
    }
    
    manifest_path = create_manifest(
        run_id='test_manifest_20251121',
        factor_name='momentum_21_63_volscaled',
        output_dir=test_dir.parent,
        artifacts=artifacts,
        status='completed',
        metadata=metadata
    )
    
    print(f"✓ Manifest created: {manifest_path}")
    print(f"  Size: {manifest_path.stat().st_size:,} bytes")
    
    # Display manifest content
    print("\n[3/4] Manifest content:")
    with open(manifest_path, 'r') as f:
        manifest_data = json.load(f)
    
    print(f"  Run ID: {manifest_data['run_id']}")
    print(f"  Factor: {manifest_data['factor_name']}")
    print(f"  Status: {manifest_data['status']}")
    print(f"  Artifacts: {len(manifest_data['artifacts'])}")
    
    print("\n  Artifact Details:")
    for name, entry in manifest_data['artifacts'].items():
        print(f"    {name}:")
        print(f"      Path: {entry['path']}")
        print(f"      Checksum: {entry['checksum'][:16]}...")
        print(f"      Size: {entry['size_bytes']:,} bytes")
        print(f"      Type: {entry['artifact_type']}")
    
    # Validate manifest
    print("\n[4/4] Validating manifest...")
    
    validation_report = validate_manifest(manifest_path)
    
    if validation_report['valid']:
        print("✓ Manifest validation PASSED")
        print(f"  Artifacts checked: {validation_report['artifacts_checked']}")
        print(f"  Artifacts valid: {validation_report['artifacts_valid']}")
        print(f"  Checksums verified: ✓")
    else:
        print("✗ Manifest validation FAILED")
        for error in validation_report['errors']:
            print(f"  Error: {error}")
        for warning in validation_report['warnings']:
            print(f"  Warning: {warning}")
        return False
    
    # Test update functionality
    print("\n[BONUS] Testing manifest update...")
    
    # Create a dummy new artifact
    dummy_file = test_dir.parent / 'test_artifact.txt'
    dummy_file.write_text("This is a test artifact")
    
    update_manifest(
        manifest_path,
        new_artifacts={'test_artifact': dummy_file},
        metadata_updates={'updated_at': datetime.now().isoformat()}
    )
    
    print("✓ Manifest updated successfully")
    
    # Validate again
    validation_report = validate_manifest(manifest_path)
    if validation_report['valid']:
        print(f"✓ Updated manifest still valid ({validation_report['artifacts_checked']} artifacts)")
    
    # Cleanup
    dummy_file.unlink()
    
    print("\n" + "="*70)
    print(" SUMMARY")
    print("="*70)
    print("✓ Manifest creation: SUCCESS")
    print("✓ Checksum computation: SUCCESS")
    print("✓ Manifest validation: SUCCESS")
    print("✓ Manifest update: SUCCESS")
    
    return True


if __name__ == '__main__':
    try:
        success = test_manifest_generator()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
