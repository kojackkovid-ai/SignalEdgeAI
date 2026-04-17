import joblib
import os
from pathlib import Path

# Test what models are available
models_dir = Path("ml-models/trained")

print("Available models:")
for file in models_dir.glob("*"):
    print(f"  {file.name}")

# Try to load the existing models
print("\nTrying to load existing models:")
try:
    linear_model = joblib.load(models_dir / "linear_model.pkl")
    print(f"Linear model loaded: {type(linear_model)}")
except Exception as e:
    print(f"Error loading linear model: {e}")

try:
    lgb_model = joblib.load(models_dir / "lightgbm_model.pkl")
    print(f"LightGBM model loaded: {type(lgb_model)}")
except Exception as e:
    print(f"Error loading LightGBM model: {e}")

try:
    xgb_model = joblib.load(models_dir / "xgboost_model.pkl")
    print(f"XGBoost model loaded: {type(xgb_model)}")
except Exception as e:
    print(f"Error loading XGBoost model: {e}")