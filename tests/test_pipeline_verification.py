
import pytest
import pandas as pd
from datetime import datetime, timedelta
from src.backtest.pipeline import create_walk_forward_splits

def test_create_walk_forward_splits():
    """Test walk-forward split creation."""
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2023, 1, 1) # 3 years ~ 1096 days
    
    # Standard config
    splits = create_walk_forward_splits(
        start_date=start_date,
        end_date=end_date,
        n_splits=5,
        min_train_days=252,
        min_test_days=63,
        purge_gap_days=21
    )
    
    assert len(splits) == 5
    
    for i, split in enumerate(splits):
        # Check durations
        train_duration = (split['train_end'] - split['train_start']).days
        test_duration = (split['test_end'] - split['test_start']).days
        gap_duration = (split['test_start'] - split['train_end']).days
        
        assert train_duration >= 252
        assert test_duration == 63
        assert gap_duration == 21
        
        # Check continuity
        if i > 0:
            # Expanding window: start is same, end increases
            assert split['train_start'] == splits[i-1]['train_start']
            assert split['train_end'] > splits[i-1]['train_end']
            
        # Check bounds
        assert split['train_start'] >= start_date
        assert split['test_end'] <= end_date

def test_create_walk_forward_splits_insufficient_data():
    """Test error handling for insufficient data."""
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 6, 1) # ~150 days
    
    with pytest.raises(ValueError, match="Insufficient data"):
        create_walk_forward_splits(
            start_date=start_date,
            end_date=end_date,
            n_splits=5,
            min_train_days=252, # Needs at least 252
            min_test_days=63,
            purge_gap_days=21
        )
