"""Signals metadata schema for feature agent outputs."""

from typing import List, Tuple, Optional
from pydantic import BaseModel, Field, field_validator


class SignalsMetaSchema(BaseModel):
    """Schema for signals_meta.json file from FeatureAgent.
    
    Contains metadata about computed factor signals.
    """
    
    factor_name: str = Field(..., description="Name of the factor")
    num_signals: int = Field(..., description="Number of signal columns")
    num_observations: int = Field(..., description="Number of time periods")
    
    date_range: Tuple[str, str] = Field(
        ..., 
        description="Date range as (start, end) in ISO format"
    )
    
    signal_names: List[str] = Field(..., description="List of signal column names")
    
    coverage: float = Field(
        ..., 
        description="Data coverage ratio (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )
    
    null_rate: float = Field(
        ..., 
        description="Proportion of null values (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )
    
    standardization: Optional[str] = Field(
        None, 
        description="Standardization method applied (zscore, rank, etc.)"
    )
    
    universe_size: Optional[int] = Field(
        None, 
        description="Number of assets in universe"
    )
    
    computed_at: str = Field(..., description="Computation timestamp (ISO format)")
    
    @field_validator('num_signals', 'num_observations')
    @classmethod
    def validate_positive(cls, v):
        """Ensure counts are positive."""
        if v <= 0:
            raise ValueError(f"Value must be positive, got {v}")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "factor_name": "momentum_21_63",
                "num_signals": 2,
                "num_observations": 1461,
                "date_range": ["2020-01-01", "2023-12-31"],
                "signal_names": ["mom_21", "mom_63"],
                "coverage": 0.98,
                "null_rate": 0.02,
                "standardization": "zscore_63",
                "universe_size": 500,
                "computed_at": "2023-11-20T12:30:15"
            }
        }
