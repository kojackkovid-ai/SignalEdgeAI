#!/usr/bin/env python3
"""
Verify NCAAB ML Models - Fixed version with SimpleEnsemble import
"""
import sys
import joblib
import numpy as np
from pathlib import Path

# Add paths
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent / "ml-models"))

# Import SimpleEnsemble from training module
from train_ncaab_fast import SimpleEnsemble

def verify_models():
    print("=" * 60)
    print("VERIFYING NCAAB ML MODELS")
    print("=" * 60)
    
    models_dir = Path(__file__).parent.parent / "ml-models" / "trained"
    
    market_types = ['moneyline', 'spread', 'total']
    all_good = True
    
    for market_type in market_types:
        print(f"\n{market_type.upper()}:")
        model_path = models_dir / f"basketball_ncaa_{market_type}_models.joblib"
        
        try:
            # Load model
            model_data = joblib.load(model_path)
            
            # Check structure
            required_keys = ['ensemble', 'individual_models', 'scaler', 'feature_names', 'performance']
            missing = [k for k in required_keys if k not in model_data]
            
            if missing:
                print(f"  ✗ Missing keys: {missing}")
                all_good = False
                continue
            
            # Test prediction
            ensemble = model_data['ensemble']
            scaler = model_data['scaler']
            feature_names = model_data['feature_names']
            
            # Create dummy input
            dummy_input = np.zeros((1, len(feature_names)))
            dummy_scaled = scaler.transform(dummy_input)
            
            # Test ensemble prediction
            prob = ensemble.predict_proba(dummy_scaled)[0]
            pred = ensemble.predict(dummy_scaled)[0]
            
            print(f"  ✓ Loaded successfully")
            print(f"  ✓ Features: {len(feature_names)}")
            print(f"  ✓ Test prediction: {pred} (prob: {prob[1]:.3f})")
            print(f"  ✓ RF Accuracy: {model_data['performance']['random_forest']['accuracy']:.3f}")
            print(f"  ✓ GB Accuracy: {model_data['performance']['gradient_boosting']['accuracy']:.3f}")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            all_good = False
    
    print("\n" + "=" * 60)
    if all_good:
        print("✓ All NCAAB models verified and working!")
    else:
        print("✗ Some models missing or corrupted")
    print("=" * 60)
    
    return all_good

if __name__ == "__main__":
    success = verify_models()
    sys.exit(0 if success else 1)
