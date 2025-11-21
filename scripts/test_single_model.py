"""
Single model validation test - Test gemma2:9b before full production run.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.data.real_data_loader import load_real_data
import subprocess
import json
from datetime import datetime

def test_single_model():
    """Test a single model to verify the system works."""
    
    print("\n" + "="*70)
    print("  SINGLE MODEL VALIDATION TEST")
    print("  Model: gemma2:9b (Google Gemini Architecture)")
    print("="*70 + "\n")
    
    # Step 1: Load real data
    print("Step 1/4: Loading real market data...")
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
    
    # Step 2: Verify model is available
    print(f"\nStep 2/4: Verifying gemma2:9b model...")
    result = subprocess.run(
        ["ollama", "list"],
        capture_output=True,
        text=True
    )
    
    if "gemma2:9b" in result.stdout:
        print("✅ gemma2:9b model is available")
    else:
        print("❌ gemma2:9b model not found!")
        print("   Please run: ollama pull gemma2:9b")
        return False
    
    # Step 3: Test model with simple prompt
    print(f"\nStep 3/4: Testing model with simple prompt...")
    test_prompt = "Generate a simple momentum-based alpha factor for stock trading. Keep it brief."
    
    result = subprocess.run(
        ["ollama", "run", "gemma2:9b", test_prompt],
        capture_output=True,
        text=True,
        timeout=60
    )
    
    if result.returncode == 0 and len(result.stdout) > 50:
        print("✅ Model responds correctly")
        print(f"   Response length: {len(result.stdout)} characters")
    else:
        print("❌ Model test failed")
        return False
    
    # Step 4: Save test results
    print(f"\nStep 4/4: Saving test results...")
    output_dir = Path("validation_test_results")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save data provenance
    with open(output_dir / "data_provenance.json", 'w') as f:
        json.dump(data['provenance'], f, indent=2)
    
    # Save test summary
    test_summary = {
        "test_date": datetime.now().isoformat(),
        "model": "gemma2:9b",
        "data_source": data['source'],
        "is_real_data": data['is_real'],
        "tickers": len(data['provenance']['tickers']),
        "trading_days": data['provenance']['total_days'],
        "model_test": "passed",
        "status": "ready_for_production"
    }
    
    with open(output_dir / "test_summary.json", 'w') as f:
        json.dump(test_summary, f, indent=2)
    
    print(f"✅ Test results saved to: {output_dir}")
    
    print("\n" + "="*70)
    print("  ✅ VALIDATION TEST PASSED")
    print("  System is ready for production testing!")
    print("="*70 + "\n")
    
    print("📋 Next Steps:")
    print("   1. Review test results in validation_test_results/")
    print("   2. Run full production test:")
    print("      python scripts/production_model_comparison.py")
    print()
    
    return True


if __name__ == "__main__":
    success = test_single_model()
    if success:
        print("✅ Single model validation: PASSED")
    else:
        print("❌ Single model validation: FAILED")
        sys.exit(1)
