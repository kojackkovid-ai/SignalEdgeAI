#!/usr/bin/env python3
"""
Detailed test of model loading to diagnose why models aren't loading
"""
import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

def test_model_loading():
    """Test model loading step by step"""
    from app.config import settings
    
    print(f"Working directory: {Path.cwd()}")
    print(f"Script directory: {Path(__file__).parent}")
    print(f"ML_MODELS_DIR from settings: {settings.ml_models_dir}")
    
    models_dir = Path(settings.ml_models_dir)
    print(f"Models directory (absolute): {models_dir.absolute()}")
    print(f"Models directory exists: {models_dir.exists()}")
    
    if models_dir.exists():
        print(f"\nContents of {models_dir}:")
        for item in models_dir.iterdir():
            print(f"  {item.name} ({'dir' if item.is_dir() else 'file'})")
        
        # Check for joblib files
        joblib_files = list(models_dir.rglob("*.joblib"))
        print(f"\nFound {len(joblib_files)} .joblib files:")
        for f in joblib_files[:10]:
            print(f"  {f.relative_to(models_dir)}")
        
        # Check for specific model files
        print("\nChecking specific model paths:")
        test_paths = [
            "basketball/nba/basketball_nba_moneyline_xgboost.joblib",
            "americanfootball/nfl/americanfootball_nfl_moneyline_xgboost.joblib",
            "icehockey/nhl/icehockey_nhl_moneyline_xgboost.joblib",
        ]
        for path in test_paths:
            full_path = models_dir / path
            print(f"  {path}: exists={full_path.exists()}")
    
    # Now test the actual loading
    print("\n" + "="*60)
    print("Testing EnhancedMLService._load_all_models()...")
    print("="*60)
    
    from app.services.enhanced_ml_service import EnhancedMLService
    
    ml_service = EnhancedMLService()
    
    print(f"\nModels loaded: {len(ml_service.models)}")
    print(f"Model keys: {list(ml_service.models.keys())}")
    
    # Check individual model data
    for key, data in ml_service.models.items():
        print(f"\n  {key}:")
        print(f"    Has ensemble: {'ensemble' in data}")
        print(f"    Has individual_models: {'individual_models' in data}")
        if 'individual_models' in data:
            print(f"    Individual models: {list(data['individual_models'].keys())}")

if __name__ == "__main__":
    test_model_loading()
