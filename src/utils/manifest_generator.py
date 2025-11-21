"""Manifest generator for run artifacts with checksums."""

import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

from ..schemas.manifest import ManifestSchema, ArtifactEntry


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


def create_artifact_entry(
    file_path: Path,
    artifact_type: str,
    base_dir: Optional[Path] = None
) -> ArtifactEntry:
    """Create an artifact entry with checksum.
    
    Args:
        file_path: Path to artifact file
        artifact_type: Type of artifact
        base_dir: Base directory for relative path calculation
    
    Returns:
        ArtifactEntry instance
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Artifact file not found: {file_path}")
    
    # Compute relative path
    if base_dir:
        try:
            relative_path = file_path.relative_to(base_dir)
        except ValueError:
            relative_path = file_path
    else:
        relative_path = file_path
    
    # Get file stats
    stat = file_path.stat()
    
    return ArtifactEntry(
        path=str(relative_path),
        checksum=compute_checksum(file_path),
        size_bytes=stat.st_size,
        created_at=datetime.fromtimestamp(stat.st_mtime),
        artifact_type=artifact_type
    )


def create_manifest(
    run_id: str,
    factor_name: str,
    output_dir: Path,
    artifacts: Dict[str, Path],
    status: str = 'completed',
    metadata: Optional[Dict[str, Any]] = None
) -> Path:
    """Create manifest.json with checksums for all artifacts.
    
    Args:
        run_id: Unique run identifier
        factor_name: Name of the factor
        output_dir: Output directory for manifest
        artifacts: Dictionary mapping artifact name to file path
        status: Run status ('running', 'completed', 'failed')
        metadata: Additional metadata
    
    Returns:
        Path to created manifest.json
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create artifact entries
    artifact_entries = {}
    for name, path in artifacts.items():
        if path and Path(path).exists():
            # Infer artifact type from name
            artifact_type = _infer_artifact_type(name)
            artifact_entries[name] = create_artifact_entry(
                Path(path),
                artifact_type,
                base_dir=output_dir
            )
    
    # Create manifest
    manifest = ManifestSchema(
        run_id=run_id,
        factor_name=factor_name,
        created_at=datetime.now(),
        completed_at=datetime.now() if status == 'completed' else None,
        status=status,
        artifacts=artifact_entries,
        metadata=metadata or {}
    )
    
    # Save to file
    manifest_path = output_dir / 'manifest.json'
    with open(manifest_path, 'w') as f:
        json.dump(manifest.model_dump(mode='json'), f, indent=2, default=str)
    
    return manifest_path


def update_manifest(
    manifest_path: Path,
    new_artifacts: Optional[Dict[str, Path]] = None,
    status: Optional[str] = None,
    metadata_updates: Optional[Dict[str, Any]] = None
) -> Path:
    """Update an existing manifest with new artifacts or status.
    
    Args:
        manifest_path: Path to existing manifest.json
        new_artifacts: New artifacts to add
        status: Updated status
        metadata_updates: Metadata updates
    
    Returns:
        Path to updated manifest.json
    """
    # Load existing manifest
    with open(manifest_path, 'r') as f:
        manifest_data = json.load(f)
    
    manifest = ManifestSchema(**manifest_data)
    
    # Update artifacts
    if new_artifacts:
        base_dir = manifest_path.parent
        for name, path in new_artifacts.items():
            if path and Path(path).exists():
                artifact_type = _infer_artifact_type(name)
                manifest.artifacts[name] = create_artifact_entry(
                    Path(path),
                    artifact_type,
                    base_dir=base_dir
                )
    
    # Update status
    if status:
        manifest.status = status
        if status == 'completed':
            manifest.completed_at = datetime.now()
    
    # Update metadata
    if metadata_updates:
        manifest.metadata.update(metadata_updates)
    
    # Save updated manifest
    with open(manifest_path, 'w') as f:
        json.dump(manifest.model_dump(mode='json'), f, indent=2, default=str)
    
    return manifest_path


def validate_manifest(manifest_path: Path) -> Dict[str, Any]:
    """Validate manifest and verify all checksums.
    
    Args:
        manifest_path: Path to manifest.json
    
    Returns:
        Validation report dictionary
    """
    report = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'artifacts_checked': 0,
        'artifacts_valid': 0,
        'artifacts_invalid': 0
    }
    
    try:
        # Load and validate schema
        with open(manifest_path, 'r') as f:
            manifest_data = json.load(f)
        
        manifest = ManifestSchema(**manifest_data)
        
        # Verify checksums
        base_dir = manifest_path.parent
        for name, entry in manifest.artifacts.items():
            report['artifacts_checked'] += 1
            
            artifact_path = base_dir / entry.path
            
            if not artifact_path.exists():
                report['errors'].append(f"{name}: File not found at {entry.path}")
                report['artifacts_invalid'] += 1
                report['valid'] = False
                continue
            
            # Verify checksum
            actual_checksum = compute_checksum(artifact_path)
            if actual_checksum != entry.checksum:
                report['errors'].append(
                    f"{name}: Checksum mismatch (expected {entry.checksum[:8]}..., "
                    f"got {actual_checksum[:8]}...)"
                )
                report['artifacts_invalid'] += 1
                report['valid'] = False
            else:
                report['artifacts_valid'] += 1
            
            # Check file size
            actual_size = artifact_path.stat().st_size
            if actual_size != entry.size_bytes:
                report['warnings'].append(
                    f"{name}: Size mismatch (expected {entry.size_bytes}, got {actual_size})"
                )
    
    except Exception as e:
        report['valid'] = False
        report['errors'].append(f"Validation error: {str(e)}")
    
    return report


def _infer_artifact_type(artifact_name: str) -> str:
    """Infer artifact type from name.
    
    Args:
        artifact_name: Name of artifact
    
    Returns:
        Artifact type string
    """
    name_lower = artifact_name.lower()
    
    if 'metric' in name_lower:
        return 'metrics'
    elif 'signal' in name_lower:
        return 'signals'
    elif 'chart' in name_lower or 'png' in name_lower:
        return 'chart'
    elif 'equity' in name_lower:
        return 'equity_curve'
    elif 'compliance' in name_lower:
        return 'compliance'
    elif 'alpha_spec' in name_lower:
        return 'alpha_spec'
    elif 'provenance' in name_lower:
        return 'data_provenance'
    else:
        return 'other'
