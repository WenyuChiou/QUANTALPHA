"""Schema validation script for CI/CD integration."""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.schemas.manifest import ManifestSchema
from src.schemas.metrics import MetricsSchema
from src.schemas.compliance import ComplianceSchema
from src.schemas.signals_meta import SignalsMetaSchema
from src.schemas.data_provenance import DataProvenanceSchema
from src.schemas.validate import validate_json_against_schema, validate_run_artifacts
from src.utils.manifest_generator import validate_manifest


def validate_single_run(run_dir: Path) -> Dict[str, Any]:
    """Validate all artifacts in a single run directory.
    
    Args:
        run_dir: Path to run directory
    
    Returns:
        Validation report
    """
    report = {
        'run_dir': str(run_dir),
        'passed': True,
        'errors': [],
        'warnings': [],
        'artifacts_validated': []
    }
    
    # Check for manifest.json
    manifest_path = run_dir / 'manifest.json'
    if not manifest_path.exists():
        report['passed'] = False
        report['errors'].append("manifest.json not found")
        return report
    
    # Validate manifest schema
    is_valid, errors = validate_json_against_schema(manifest_path, ManifestSchema)
    if not is_valid:
        report['passed'] = False
        report['errors'].extend([f"manifest.json: {e}" for e in errors])
        return report
    
    report['artifacts_validated'].append('manifest.json')
    
    # Validate manifest checksums
    checksum_report = validate_manifest(manifest_path)
    if not checksum_report['valid']:
        report['passed'] = False
        report['errors'].extend(checksum_report['errors'])
        report['warnings'].extend(checksum_report.get('warnings', []))
    
    # Validate individual artifacts
    schema_map = {
        'metrics': MetricsSchema,
        'metrics_oos': MetricsSchema,
        'compliance': ComplianceSchema,
        'signals_meta': SignalsMetaSchema,
        'data_provenance': DataProvenanceSchema
    }
    
    for artifact_name, schema_class in schema_map.items():
        artifact_path = run_dir / f"{artifact_name}.json"
        
        if artifact_path.exists():
            is_valid, errors = validate_json_against_schema(artifact_path, schema_class)
            
            if is_valid:
                report['artifacts_validated'].append(f"{artifact_name}.json")
            else:
                report['passed'] = False
                report['errors'].extend([f"{artifact_name}.json: {e}" for e in errors])
    
    return report


def validate_all_runs(runs_dir: Path) -> Dict[str, Any]:
    """Validate all run directories.
    
    Args:
        runs_dir: Path to directory containing run directories
    
    Returns:
        Overall validation report
    """
    overall_report = {
        'runs_dir': str(runs_dir),
        'total_runs': 0,
        'passed_runs': 0,
        'failed_runs': 0,
        'run_reports': []
    }
    
    if not runs_dir.exists():
        print(f"✗ Runs directory not found: {runs_dir}")
        return overall_report
    
    # Find all run directories (those containing manifest.json)
    run_dirs = []
    for path in runs_dir.rglob('manifest.json'):
        run_dirs.append(path.parent)
    
    overall_report['total_runs'] = len(run_dirs)
    
    if len(run_dirs) == 0:
        print(f"⚠ No runs found in {runs_dir}")
        return overall_report
    
    # Validate each run
    for run_dir in run_dirs:
        report = validate_single_run(run_dir)
        overall_report['run_reports'].append(report)
        
        if report['passed']:
            overall_report['passed_runs'] += 1
        else:
            overall_report['failed_runs'] += 1
    
    return overall_report


def print_validation_report(report: Dict[str, Any]) -> None:
    """Print validation report in a readable format.
    
    Args:
        report: Validation report
    """
    print("\n" + "="*70)
    print(" SCHEMA VALIDATION REPORT")
    print("="*70)
    
    print(f"\nRuns Directory: {report['runs_dir']}")
    print(f"Total Runs: {report['total_runs']}")
    print(f"Passed: {report['passed_runs']}")
    print(f"Failed: {report['failed_runs']}")
    
    if report['total_runs'] > 0:
        pass_rate = (report['passed_runs'] / report['total_runs']) * 100
        print(f"Pass Rate: {pass_rate:.1f}%")
    
    # Show details for each run
    for run_report in report['run_reports']:
        status = "✓ PASS" if run_report['passed'] else "✗ FAIL"
        run_name = Path(run_report['run_dir']).name
        
        print(f"\n{status} {run_name}")
        print(f"  Artifacts validated: {len(run_report['artifacts_validated'])}")
        
        if run_report['artifacts_validated']:
            for artifact in run_report['artifacts_validated']:
                print(f"    ✓ {artifact}")
        
        if run_report['errors']:
            print(f"  Errors: {len(run_report['errors'])}")
            for error in run_report['errors']:
                print(f"    ✗ {error}")
        
        if run_report['warnings']:
            print(f"  Warnings: {len(run_report['warnings'])}")
            for warning in run_report['warnings']:
                print(f"    ⚠ {warning}")
    
    print("\n" + "="*70)


def main():
    """Main validation function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate QuantAlpha run artifacts against schemas')
    parser.add_argument(
        'runs_dir',
        type=Path,
        nargs='?',
        default=Path('test_results'),
        help='Directory containing run directories (default: test_results)'
    )
    parser.add_argument(
        '--run',
        type=Path,
        help='Validate a single run directory'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output report as JSON'
    )
    
    args = parser.parse_args()
    
    if args.run:
        # Validate single run
        report = validate_single_run(args.run)
        
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            status = "✓ PASS" if report['passed'] else "✗ FAIL"
            print(f"\n{status} {args.run}")
            print(f"Artifacts validated: {len(report['artifacts_validated'])}")
            
            for artifact in report['artifacts_validated']:
                print(f"  ✓ {artifact}")
            
            if report['errors']:
                print(f"\nErrors:")
                for error in report['errors']:
                    print(f"  ✗ {error}")
        
        sys.exit(0 if report['passed'] else 1)
    
    else:
        # Validate all runs
        report = validate_all_runs(args.runs_dir)
        
        if args.json:
            print(json.dumps(report, indent=2, default=str))
        else:
            print_validation_report(report)
        
        sys.exit(0 if report['failed_runs'] == 0 else 1)


if __name__ == '__main__':
    main()
