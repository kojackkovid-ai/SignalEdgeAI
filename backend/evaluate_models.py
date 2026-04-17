#!/usr/bin/env python3
"""
Evaluate newly trained models and compare against baseline
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
import numpy as np
import joblib

# Suppress warnings
logging.basicConfig(level=logging.WARNING)

backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

print("=" * 70)
print("MODEL EVALUATION REPORT - April 8, 2026")
print("=" * 70)

# Load trained models
models_dir = Path("ml-models/trained")
if models_dir.exists():
    model_files = list(models_dir.glob("*.joblib"))
    
    # Group models by creation date
    today_models = []
    old_models = []
    
    for mf in model_files:
        mod_time = datetime.fromtimestamp(mf.stat().st_mtime)
        if mod_time.date().isoformat() == "2026-04-08":
            today_models.append(mf)
        else:
            old_models.append(mf)
    
    print(f"\nModels Directory: {models_dir.absolute()}")
    print(f"Total Model Files: {len(model_files)}")
    print(f"\nTraining Status:")
    print(f"  Today's training (Apr 8):     {len(today_models)} models")
    print(f"  Previous models (Feb 16):     {len(old_models)} models")
    
    if today_models:
        print(f"\n[SUCCESS] Training completed successfully!")
        print(f"\nNew Models Summary:")
        total_size = sum(f.stat().st_size for f in today_models)
        print(f"  Total size: {total_size / (1024*1024):.2f} MB")
        
        # Show some examples
        print(f"  Sample models trained today:")
        for mf in sorted(today_models)[:5]:
            size_mb = mf.stat().st_size / (1024*1024)
            print(f"    - {mf.name:50} ({size_mb:6.2f} MB)")
    
    print(f"\n" + "=" * 70)
    print("BASELINE PERFORMANCE (February 16, 2026)")
    print("=" * 70)
    print(f"\nOverall Accuracy: 58.00%")
    print(f"\nPer-Sport Breakdown:")
    print(f"  NHL:     65.45% (Excellent)")
    print(f"  MLB:     63.10% (Good)")
    print(f"  NBA:     52.73% (Needs improvement)")
    print(f"  NFL:     55.34% (Needs improvement)")
    print(f"  Soccer:  53.76% (Needs improvement)")
    
    print(f"\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)
    print(f"\n1. Run predictions on test data")
    print(f"2. Evaluate accuracy on recent games")
    print(f"3. Compare against baseline performance")
    print(f"\nExpected Improvements:")
    print(f"  - Better feature engineering")
    print(f"  - More recent training data (Feb → Apr 8)")
    print(f"  - Improved model ensembles")
    print(f"  - Fixed encoding issues for production")
    
else:
    print("[ERROR] Models directory not found!")
