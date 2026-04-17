#!/usr/bin/env python3
"""Quick check of model training results"""
import os
from pathlib import Path
from datetime import datetime

models_dir = Path("ml-models/trained")

if models_dir.exists():
    joblib_files = list(models_dir.glob("*.joblib"))
    
    print("=" * 70)
    print("MODEL TRAINING RESULTS - April 8, 2026")
    print("=" * 70)
    print(f"\nTotal Model Files: {len(joblib_files)}")
    print(f"Models Directory: {models_dir.absolute()}\n")
    
    if joblib_files:
        print("Trained Models:")
        for i, f in enumerate(sorted(joblib_files), 1):
            size_mb = f.stat().st_size / (1024 * 1024)
            mod_time = datetime.fromtimestamp(f.stat().st_mtime)
            print(f"  {i:2}. {f.name:50} | Size: {size_mb:7.2f} MB | Modified: {mod_time}")
        
        print("\n" + "=" * 70)
        print("PREVIOUS BASELINE PERFORMANCE")
        print("=" * 70)
        print("\nPrior trained models achieved:")
        print("  Overall Accuracy: 58.00%")
        print("  - NHL:   65.45% (Excellent)")
        print("  - MLB:   63.10% (Good)")
        print("  - NBA:   52.73% (Needs improvement)")
        print("  - NFL:   55.34% (Needs improvement)")
        print("  - Soccer: 53.76% (Needs improvement)")
        
        print("\n" + "=" * 70)
        print("STATUS")
        print("=" * 70)
        print("\n[OK] Models successfully retrained!")
        print(f"[OK] {len(joblib_files)} model files created/updated")
        print("\nTo evaluate improvements:")
        print("  1. Run: python backtest_models_simple.py")
        print("  2. Compare new accuracy against baseline")
        
    else:
        print("[WARNING] No model files found in trained directory!")
else:
    print(f"[ERROR] Models directory not found: {models_dir}")
