"""
Quick validation test - simplified version.

Tests 1 model with 3 iterations using REAL data.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.data.real_data_loader import load_real_data

def main():
    print("\n" + "="*70)
    print("  VALIDATION TEST")
    print("  Model: gemma2:9b (Google Gemini architecture)")
    print("  Iterations: 3")
    print("  Data: Real (Yahoo Finance, 2020-2024)")
    print("="*70 + "\n")
    
    # Load real data
    print("Step 1/3: Loading real market data...")
    data = load_real_data(
        num_tickers=20,
        start_date="2020-01-01",
        end_date="2024-01-01"
    )
    
    print(f"\n✅ Data loaded successfully!")
    print(f"   • Source: {data['source']}")
    print(f"   • Real data: {data['is_real']}")
    print(f"   • Tickers: {len(data['provenance']['tickers'])}")
    print(f"   • Days: {data['provenance']['total_days']}")
    
    # Save provenance
    output_dir = Path("validation_test_results")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    import json
    with open(output_dir / "data_provenance.json", 'w') as f:
        json.dump(data['provenance'], f, indent=2)
    
    print(f"\n✅ Data provenance saved to: {output_dir / 'data_provenance.json'}")
    
    print("\n" + "="*70)
    print("  ✅ VALIDATION TEST DATA READY")
    print(f"  Next: Implement model testing logic")
    print("="*70 + "\n")
    
    # TODO: Add model testing logic
    # For now, just verify data loading works
    
    return data


if __name__ == "__main__":
    data = main()
    print(f"\n✅ Validation test data preparation complete!")
    print(f"   Prices shape: {data['prices'].shape}")
    print(f"   Returns shape: {data['returns'].shape}")
