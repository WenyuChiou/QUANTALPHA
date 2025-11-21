"""Metrics schema for backtest results."""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


class MetricsSchema(BaseModel):
    """Schema for backtest metrics.json file.
    
    Contains all performance metrics from a backtest run.
    """
    
    # Core performance metrics
    sharpe: float = Field(..., description="Sharpe ratio")
    ann_ret: float = Field(..., description="Annualized return")
    ann_vol: float = Field(..., description="Annualized volatility")
    maxdd: float = Field(..., description="Maximum drawdown (negative value)")
    
    # Information coefficient metrics
    avg_ic: Optional[float] = Field(None, description="Average information coefficient")
    ir: Optional[float] = Field(None, description="Information ratio")
    
    # Advanced risk metrics
    psr: Optional[float] = Field(None, description="Probabilistic Sharpe ratio")
    sortino: Optional[float] = Field(None, description="Sortino ratio")
    calmar: Optional[float] = Field(None, description="Calmar ratio")
    var_95: Optional[float] = Field(None, description="Value at Risk (95%)")
    cvar: Optional[float] = Field(None, description="Conditional VaR")
    
    # Strategy characteristics
    linearity: Optional[float] = Field(None, description="Equity curve linearity (R²)")
    turnover_monthly: Optional[float] = Field(None, description="Average monthly turnover")
    hit_rate: Optional[float] = Field(None, description="Hit rate (% profitable periods)")
    
    # Additional metrics
    num_trades: Optional[int] = Field(None, description="Total number of trades")
    avg_holding_period: Optional[float] = Field(None, description="Average holding period (days)")
    
    @field_validator('maxdd')
    @classmethod
    def validate_maxdd(cls, v):
        """Ensure maxdd is negative or zero."""
        if v > 0:
            raise ValueError("maxdd must be negative or zero")
        return v
    
    @field_validator('sharpe', 'ir', 'sortino', 'calmar')
    @classmethod
    def validate_ratios(cls, v):
        """Validate ratio values are reasonable."""
        if v is not None and abs(v) > 100:
            raise ValueError(f"Ratio value {v} seems unreasonable (|v| > 100)")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "sharpe": 1.85,
                "ann_ret": 0.12,
                "ann_vol": 0.065,
                "maxdd": -0.18,
                "avg_ic": 0.06,
                "ir": 0.55,
                "psr": 0.92,
                "sortino": 2.15,
                "calmar": 1.42,
                "var_95": -0.021,
                "cvar": -0.032,
                "linearity": 0.88,
                "turnover_monthly": 85.3,
                "hit_rate": 0.54
            }
        }


class MetricsOOSSchema(MetricsSchema):
    """Schema for out-of-sample metrics.
    
    Inherits from MetricsSchema but adds OOS-specific fields.
    """
    
    oos_start_date: str = Field(..., description="OOS period start date (ISO format)")
    oos_end_date: str = Field(..., description="OOS period end date (ISO format)")
    is_start_date: Optional[str] = Field(None, description="In-sample period start date")
    is_end_date: Optional[str] = Field(None, description="In-sample period end date")
