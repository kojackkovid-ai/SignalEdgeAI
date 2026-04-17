#!/usr/bin/env python3
"""
Verify NCAAB ML Models
"""
import joblib
import numpy as np
from pathlib import Path

models_dir = Path(__file__).parent.parent / "ml-models" / "trained"

print("=" * 60)
print("VERIFYING NCAAB ML MODELS")
print("=" * 60)

all_good = True

for market in ['moneyline', 'spread', 'total']:
    model_path = models_dir / f'basketball_ncaa_{market}_models.joblib'
    print(f"\n{market.upper()}:")
    
    if model_path.exists():
        try:
            data = joblib.load(model_path)
            print(f"  ✓ Models: {list(data['models'].keys())}")
            print(f"  ✓ Features: {len(data['feature_names'])} features")
            print(f"  ✓ Training samples: {data['training_samples']}")
            print(f"  ✓ RF Accuracy: {data['accuracy']['random_forest']:.3f}")
            print(f"  ✓ GB Accuracy: {data['accuracy']['gradient_boosting']:.3f}")
            
            # Test prediction
            rf = data['models']['random_forest']
            scaler = data['scaler']
            
            # Create test input
            test_input = np.random.randn(1, len(data['feature_names']))
            test_scaled = scaler.transform(test_input)
            pred = rf.predict_proba(test_scaled)[0]
            print(f"  ✓ Test prediction: Home Win {pred[1]*100:.1f}% confidence")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            all_good = False
    else:
        print(f"  ✗ NOT FOUND")
        all_good = False

print("\n" + "=" * 60)
if all_good:
    print("✓ ALL NCAAB MODELS READY FOR REAL ML PREDICTIONS!")
else:
    print("✗ Some models missing or corrupted")
print("=" * 60)
