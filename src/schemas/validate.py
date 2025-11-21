"""Validation utilities for schema compliance."""

import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Type, List, Tuple
from pydantic import BaseModel, ValidationError


def compute_checksum(file_path: Path) -> str:
    """Compute SHA256 checksum of a file.
    
    Args:
        file_path: Path to file
    
    Returns:
        SHA256 checksum as hex string
    """
    sha256 = hashlib.sha256()
    
    with open(file_path, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    
    return sha256.hexdigest()


def validate_json_against_schema(
    json_path: Path,
    schema_class: Type[BaseModel]
) -> Tuple[bool, List[str]]:
    """Validate a JSON file against a Pydantic schema.
    
    Args:
        json_path: Path to JSON file
        schema_class: Pydantic model class
    
    Returns:
        Tuple of (is_valid, error_messages)
    """
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        # Validate against schema
        schema_class(**data)
        return True, []
    
    except ValidationError as e:
        errors = []
        for error in e.errors():
            loc = ' -> '.join(str(x) for x in error['loc'])
            msg = f"{loc}: {error['msg']}"
            errors.append(msg)
        return False, errors
    
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON: {str(e)}"]
    
    except Exception as e:
        return False, [f"Unexpected error: {str(e)}"]


def validate_run_artifacts(
    run_dir: Path,
    schema_map: Dict[str, Type[BaseModel]]
) -> Dict[str, Any]:
    """Validate all artifacts in a run directory.
    
    Args:
        run_dir: Path to run directory
        schema_map: Mapping of artifact name to schema class
    
    Returns:
        Validation report dictionary
    """
    report = {
        'run_dir': str(run_dir),
        'artifacts_checked': 0,
        'artifacts_passed': 0,
        'artifacts_failed': 0,
        'errors': {}
    }
    
    for artifact_name, schema_class in schema_map.items():
        artifact_path = run_dir / f"{artifact_name}.json"
        
        if not artifact_path.exists():
            report['errors'][artifact_name] = [f"File not found: {artifact_path}"]
            report['artifacts_failed'] += 1
            continue
        
        report['artifacts_checked'] += 1
        is_valid, errors = validate_json_against_schema(artifact_path, schema_class)
        
        if is_valid:
            report['artifacts_passed'] += 1
        else:
            report['artifacts_failed'] += 1
            report['errors'][artifact_name] = errors
    
    return report


def export_schema_to_json(
    schema_class: Type[BaseModel],
    output_path: Path
) -> None:
    """Export Pydantic schema to JSON Schema format.
    
    Args:
        schema_class: Pydantic model class
        output_path: Path to save JSON schema
    """
    schema = schema_class.model_json_schema()
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(schema, f, indent=2)


def verify_checksum(file_path: Path, expected_checksum: str) -> bool:
    """Verify file checksum matches expected value.
    
    Args:
        file_path: Path to file
        expected_checksum: Expected SHA256 checksum
    
    Returns:
        True if checksums match
    """
    actual_checksum = compute_checksum(file_path)
    return actual_checksum == expected_checksum
