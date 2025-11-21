"""Manifest schema for run artifacts with checksums."""

from typing import Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field


class ArtifactEntry(BaseModel):
    """Entry for a single artifact in the manifest."""
    
    path: str = Field(..., description="Relative path to artifact file")
    checksum: str = Field(..., description="SHA256 checksum of file")
    size_bytes: int = Field(..., description="File size in bytes")
    created_at: datetime = Field(..., description="File creation timestamp")
    artifact_type: str = Field(..., description="Type of artifact (metrics, signals, chart, etc.)")


class ManifestSchema(BaseModel):
    """Schema for run manifest.json file.
    
    The manifest tracks all artifacts produced during a run,
    including checksums for integrity verification.
    """
    
    run_id: str = Field(..., description="Unique run identifier")
    factor_name: str = Field(..., description="Name of the factor being tested")
    created_at: datetime = Field(..., description="Run creation timestamp")
    completed_at: datetime | None = Field(None, description="Run completion timestamp")
    status: Literal['running', 'completed', 'failed'] = Field(..., description="Run status")
    
    artifacts: Dict[str, ArtifactEntry] = Field(
        default_factory=dict,
        description="Dictionary of artifact name to artifact entry"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (config, environment, etc.)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "run_id": "momentum_20231120_123456",
                "factor_name": "momentum_21_63",
                "created_at": "2023-11-20T12:34:56",
                "completed_at": "2023-11-20T12:45:30",
                "status": "completed",
                "artifacts": {
                    "metrics": {
                        "path": "metrics.json",
                        "checksum": "a1b2c3d4...",
                        "size_bytes": 1024,
                        "created_at": "2023-11-20T12:45:28",
                        "artifact_type": "metrics"
                    }
                },
                "metadata": {
                    "python_version": "3.11.0",
                    "quantalpha_version": "0.1.0"
                }
            }
        }
