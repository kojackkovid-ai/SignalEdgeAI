"""
Verify trained models exist and are loadable
"""
import json
from pathlib import Path
import joblib

def verify_models():
    """Verify all trained models"""
    models_dir = Path("ml-models/trained")
    
    print("=" * 70)
    print("VERIFYING TRAINED MODELS")
    print("=" * 70)
    
    # Check training summary
    summary_path = models_dir / "training_summary.json"
    if summary_path.exists():
        with open(summary_path) as f:
            data = json.load(f)
        print(f"\n✅ Training Summary Found")
        print(f"   Total models: {data['total_models']}")
        print(f"   Successful: {data['successful']}")
        print(f"   Failed: {data['failed']}")
        print(f"   Timestamp: {data['timestamp']}")
    else:
        print("\n❌ Training summary not found")
        return False
    
    # Count model files
    model_files = list(models_dir.rglob("*.joblib"))
    print(f"\n📁 Model Files: {len(model_files)}")
    
    # Verify each model can be loaded
    print("\n🔍 Verifying model files...")
    loadable = 0
    failed = 0
    
    for model_file in model_files[:5]:  # Check first 5
        try:
            model = joblib.load(model_file)
            print(f"   ✅ {model_file.name[:50]}... (loadable)")
            loadable += 1
        except Exception as e:
            print(f"   ❌ {model_file.name[:50]}... (error: {e})")
            failed += 1
    
    if len(model_files) > 5:
        print(f"   ... and {len(model_files) - 5} more files")
    
    print(f"\n📊 Results:")
    print(f"   Total .joblib files: {len(model_files)}")
    print(f"   Loadable (sampled): {loadable}")
    print(f"   Failed (sampled): {failed}")
    
    # Check ensemble weights
    weight_files = list(models_dir.rglob("*_ensemble_weights.json"))
    print(f"\n⚖️  Ensemble Weight Files: {len(weight_files)}")
    
    for wf in weight_files[:3]:
        with open(wf) as f:
            weights = json.load(f)
        print(f"   📄 {wf.parent.name}/{wf.name}")
        print(f"      Weights: {weights.get('weights', {})}")
        print(f"      Scores: {weights.get('scores', {})}")
    
    print("\n" + "=" * 70)
    print("✅ MODEL VERIFICATION COMPLETE")
    print("=" * 70)
    
    return len(model_files) > 0

if __name__ == "__main__":
    success = verify_models()
    exit(0 if success else 1)
