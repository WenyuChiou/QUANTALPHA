"""Factor registry for loading and validating Factor DSL YAML specs."""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from pydantic import BaseModel, Field, validator


class SignalSpec(BaseModel):
    """Signal specification within a factor."""
    id: str
    expr: str
    normalize: Optional[str] = None


class PortfolioSpec(BaseModel):
    """Portfolio construction specification."""
    scheme: str = Field(default="long_short_deciles")
    weight: str = Field(default="equal")
    notional: float = Field(default=1.0)
    costs: Optional[Dict[str, float]] = None


class ValidationSpec(BaseModel):
    """Validation constraints."""
    min_history_days: int = Field(default=800)
    purge_gap_days: int = Field(default=21)
    max_turnover_monthly: float = Field(default=250.0)


class TargetsSpec(BaseModel):
    """Performance targets."""
    min_sharpe: float = Field(default=1.8)  # Updated requirement: minimum Sharpe 1.8
    max_maxdd: float = Field(default=0.25)  # Updated requirement: maximum drawdown -25%
    min_avg_ic: float = Field(default=0.05)


class FactorSpec(BaseModel):
    """Complete Factor DSL specification."""
    name: str
    universe: str
    frequency: str = Field(default="D")
    signals: List[SignalSpec]
    portfolio: PortfolioSpec = Field(default_factory=PortfolioSpec)
    validation: ValidationSpec = Field(default_factory=ValidationSpec)
    targets: TargetsSpec = Field(default_factory=TargetsSpec)
    
    @validator('frequency')
    def validate_frequency(cls, v):
        if v not in ['D', 'W', 'M']:
            raise ValueError("Frequency must be D (daily), W (weekly), or M (monthly)")
        return v
    
    @classmethod
    def from_yaml(cls, yaml_str: str) -> 'FactorSpec':
        """Load factor spec from YAML string."""
        data = yaml.safe_load(yaml_str)
        return cls(**data)
    
    @classmethod
    def from_file(cls, file_path: Path) -> 'FactorSpec':
        """Load factor spec from YAML file."""
        with open(file_path, 'r') as f:
            return cls.from_yaml(f.read())
    
    def to_yaml(self) -> str:
        """Convert factor spec to YAML string."""
        return yaml.dump(self.dict(), default_flow_style=False, sort_keys=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.dict()


class FactorRegistry:
    """Registry for managing factor specifications."""
    
    def __init__(self, registry_dir: Optional[Path] = None):
        self.registry_dir = registry_dir or Path("experiments/factors")
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        self._factors: Dict[str, FactorSpec] = {}
    
    def register(self, spec: FactorSpec) -> Path:
        """Register a factor spec and save to file."""
        self._factors[spec.name] = spec
        file_path = self.registry_dir / f"{spec.name}.yml"
        file_path.write_text(spec.to_yaml())
        return file_path
    
    def load(self, name: str) -> Optional[FactorSpec]:
        """Load a factor spec by name."""
        if name in self._factors:
            return self._factors[name]
        
        file_path = self.registry_dir / f"{name}.yml"
        if file_path.exists():
            spec = FactorSpec.from_file(file_path)
            self._factors[name] = spec
            return spec
        
        return None
    
    def list_factors(self) -> List[str]:
        """List all registered factor names."""
        if self.registry_dir.exists():
            return [f.stem for f in self.registry_dir.glob("*.yml")]
        return []
    
    def validate_no_lookahead(self, spec: FactorSpec) -> List[str]:
        """Validate that the factor spec has no lookahead issues.
        
        Returns list of warnings/errors.
        """
        warnings = []
        
        # Check signal expressions for common lookahead patterns
        for signal in spec.signals:
            expr = signal.expr.lower()
            
            # Check for future-looking functions (simplified check)
            if "future" in expr or "forward" in expr:
                warnings.append(f"Signal '{signal.id}' may contain lookahead: {signal.expr}")
            
            # Check normalization
            if signal.normalize:
                norm = signal.normalize.lower()
                if "future" in norm or "forward" in norm:
                    warnings.append(f"Normalization '{signal.normalize}' may contain lookahead")
        
        return warnings

