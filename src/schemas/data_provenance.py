"""Data provenance schema for tracking data sources."""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class DataProvenanceSchema(BaseModel):
    """Schema for data_provenance.json file.
    
    Tracks the source and characteristics of market data.
    """
    
    source: str = Field(..., description="Data source (yfinance, csv, database, etc.)")
    
    tickers: List[str] = Field(..., description="List of ticker symbols")
    
    start_date: str = Field(..., description="Data start date (ISO format)")
    end_date: str = Field(..., description="Data end date (ISO format)")
    
    fields: List[str] = Field(..., description="Data fields (Close, Open, Volume, etc.)")
    
    rows: int = Field(..., description="Number of data rows")
    
    fetched_at: datetime = Field(..., description="Data fetch timestamp")
    
    cache_path: Optional[str] = Field(
        None, 
        description="Path to cached data file"
    )
    
    data_quality: Optional[dict] = Field(
        None,
        description="Data quality metrics (missing_rate, outliers, etc.)"
    )
    
    adjustments: Optional[List[str]] = Field(
        None,
        description="List of adjustments applied (split, dividend, etc.)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "source": "yfinance",
                "tickers": ["AAPL", "MSFT", "GOOGL"],
                "start_date": "2020-01-01",
                "end_date": "2023-12-31",
                "fields": ["Close", "Open", "High", "Low", "Volume"],
                "rows": 1461,
                "fetched_at": "2023-11-20T12:00:00",
                "cache_path": "data/cache/sp500_20200101_20231231.parquet",
                "data_quality": {
                    "missing_rate": 0.001,
                    "outliers_detected": 5
                },
                "adjustments": ["split_adjusted", "dividend_adjusted"]
            }
        }
