"""
Standalone ML Model Training Script
Trains models with enhanced features (weather, rest, travel)
Run from: cd sports-prediction-platform/ml-models/training && python train_standalone.py
"""

import numpy as np
import pandas as pd
import json
import logging
import os
from pathlib import Path
from datetime import datetime

# Setup
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent
MODELS_DIR = SCRIPT_DIR / "trained"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_training_data(sport_key: str, n_samples: int = 500) -> pd.DataFrame:
    """
    Generate realistic training data with enhanced features.
    
    Features include:
    - Team win percentages
    - Recent form
    - Rest days
    - Weather (for outdoor sports)
    - Travel distance
    """
    np.random.seed(42)
    
    records = []
    
    for i in range(n_samples):
        # Team win percentages (beta distribution centered at 0.5)
        home_win_pct = np.clip(np.random.beta(5, 5), 0.2, 0.8)
        away_win_pct = np.clip(np.random.beta(5, 5), 0.2, 0.8)
        
        # Recent form (last 5 games)
        home_recent_form = np.clip(np.random.beta(4, 3), 0.2, 0.9)
        away_recent_form = np.clip(np.random.beta(4, 3), 0.2, 0.9)
        
        # Strength of schedule
        home_sos = np.clip(np.random.beta(5, 5), 0.3, 0.7)
        away_sos = np.clip(np.random.beta(5, 5), 0.3, 0.7)
        
        # Rest days (exponential, typical 1-5 days)
        home_rest = max(1, int(np.random.exponential(2.5)))
        away_rest = max(1, int(np.random.exponential(2.5)))
        rest_diff = home_rest - away_rest
        
        # Back-to-back games (tired team)
        home_b2b = 1 if home_rest == 1 else 0
        away_b2b = 1 if away_rest == 1 else 0
        
        # Weather features (for outdoor sports)
        if sport_key in ['americanfootball_nfl', 'baseball_mlb', 'soccer_epl']:
            temperature = np.random.normal(65, 15)  # 50-80F
            wind_speed = max(0, np.random.exponential(5))
            humidity = np.random.uniform(30, 90)
            
            # Weather impact flags
            temp_extreme = 1 if (temperature < 35 or temperature > 95) else 0
            strong_wind = 1 if wind_speed > 15 else 0
            bad_weather = temp_extreme or strong_wind
        else:
            temperature = 72
            wind_speed = 0
            humidity = 50
            temp_extreme = 0
            strong_wind = 0
            bad_weather = 0
        
        # Travel (miles)
        home_travel = np.random.exponential(200) if np.random.random() > 0.7 else 0
        away_travel = np.random.exponential(200) if np.random.random() > 0.7 else 0
        travel_impact = (away_travel - home_travel) / 1000  # Normalize
        
        # Home advantage (historically ~3-5%)
        home_advantage = 0.04
        
        # Calculate win probability using logistic model
        strength_diff = (home_win_pct + home_recent_form) / 2 - (away_win_pct + away_recent_form) / 2
        rest_impact = -0.02 * home_b2b + 0.02 * away_b2b  # B2B disadvantage
        weather_impact = -0.01 * bad_weather if sport_key in ['americanfootball_nfl', 'soccer_epl'] else 0
        travel_impact_factor = -0.01 * travel_impact
        
        logit = home_advantage + strength_diff * 0.5 + rest_impact + weather_impact + travel_impact_factor
        home_win_prob = 1 / (1 + np.exp(-logit))
        
        # Generate outcome
        target = 1 if np.random.random() < home_win_prob else 0
        
        record = {
            'target': target,
            # Core 7 features (required by models)
            'home_win_pct': round(home_win_pct, 4),
            'away_win_pct': round(away_win_pct, 4),
            'home_recent_form': round(home_recent_form, 4),
            'away_recent_form': round(away_recent_form, 4),
            'home_sos': round(home_sos, 4),
            'away_sos': round(away_sos, 4),
            'rest_days_diff': rest_diff,
            
            # Additional features for better predictions
            'home_rest_days': home_rest,
            'away_rest_days': away_rest,
            'home_back_to_back': home_b2b,
            'away_back_to_back': away_b2b,
            'temperature': round(temperature, 1),
            'wind_speed': round(wind_speed, 1),
            'humidity': round(humidity, 1),
            'temp_extreme': temp_extreme,
            'strong_wind': strong_wind,
            'bad_weather': bad_weather,
            'home_travel_miles': round(home_travel, 0),
            'away_travel_miles': round(away_travel, 0),
            'travel_impact': round(travel_impact, 3),
            
            # Derived features
            'home_strength': round((home_win_pct + home_recent_form) / 2, 4),
            'away_strength': round((away_win_pct + away_recent_form) / 2, 4),
            'strength_diff': round(strength_diff, 4),
        }
        
        records.append(record)
    
    return pd.DataFrame(records)


def train_xgboost(X_train, y_train, X_val=None, y_val=None):
    """Train XGBoost model"""
    try:
        import xgboost as xgb
        
        model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            use_label_encoder=False,
            eval_metric='logloss'
        )
        
        model.fit(X_train, y_train)
        
        train_acc = model.score(X_train, y_train)
        logger.info(f"XGBoost training accuracy: {train_acc:.4f}")
        
        return model, 'xgboost'
    except ImportError:
        logger.warning("XGBoost not available")
        return None, 'xgboost'


def train_lightgbm(X_train, y_train):
    """Train LightGBM model"""
    try:
        import lightgbm as lgb
        
        model = lgb.LGBMClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            verbose=-1
        )
        
        model.fit(X_train, y_train)
        
        train_acc = model.score(X_train, y_train)
        logger.info(f"LightGBM training accuracy: {train_acc:.4f}")
        
        return model, 'lightgbm'
    except ImportError:
        logger.warning("LightGBM not available")
        return None, 'lightgbm'


def train_random_forest(X_train, y_train):
    """Train Random Forest model"""
    try:
        from sklearn.ensemble import RandomForestClassifier
        
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=42,
            n_jobs=-1
        )
        
        model.fit(X_train, y_train)
        
        train_acc = model.score(X_train, y_train)
        logger.info(f"Random Forest training accuracy: {train_acc:.4f}")
        
        return model, 'random_forest'
    except ImportError:
        logger.warning("Random Forest not available")
        return None, 'random_forest'


def train_sklearn_models(X_train, y_train):
    """Train basic sklearn models"""
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_train)
    
    # Logistic Regression
    lr = LogisticRegression(random_state=42, max_iter=1000)
    lr.fit(X_scaled, y_train)
    lr_acc = lr.score(X_scaled, y_train)
    logger.info(f"Logistic Regression training accuracy: {lr_acc:.4f}")
    
    return {
        'scaler': scaler,
        'logistic_regression': lr,
        'accuracy': lr_acc
    }


def save_model(model, model_name: str, sport_key: str):
    """Save model to disk"""
    try:
        import joblib
        
        filepath = MODELS_DIR / f"{model_name}_{sport_key}.pkl"
        joblib.dump(model, filepath)
        logger.info(f"Saved {model_name} model to {filepath}")
    except Exception as e:
        logger.error(f"Error saving model: {e}")


def save_weights(weights: dict, sport_key: str):
    """Save ensemble weights"""
    filepath = MODELS_DIR / f"weights_{sport_key}.json"
    with open(filepath, 'w') as f:
        json.dump(weights, f, indent=2)
    logger.info(f"Saved weights to {filepath}")


def train_sport(sport_key: str, n_samples: int = 500) -> dict:
    """
    Train all models for a single sport.
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Training models for {sport_key}")
    logger.info(f"{'='*60}")
    
    # Generate training data
    logger.info(f"Generating {n_samples} training samples...")
    df = generate_training_data(sport_key, n_samples)
    
    # Core features (required 7)
    core_features = [
        'home_win_pct', 'away_win_pct',
        'home_recent_form', 'away_recent_form',
        'home_sos', 'away_sos',
        'rest_days_diff'
    ]
    
    # Extended features
    extended_features = core_features + [
        'home_rest_days', 'away_rest_days',
        'home_back_to_back', 'away_back_to_back',
        'temperature', 'wind_speed', 'temp_extreme', 'strong_wind',
        'home_travel_miles', 'away_travel_miles'
    ]
    
    # Use extended features for training
    X = df[extended_features].values
    y = df['target'].values
    
    results = {
        'sport': sport_key,
        'samples': n_samples,
        'features': len(extended_features),
        'models': {}
    }
    
    # Train models
    xgb_model, xgb_name = train_xgboost(X, y)
    if xgb_model:
        save_model(xgb_model, xgb_name, sport_key)
        results['models'][xgb_name] = {'status': 'trained', 'accuracy': xgb_model.score(X, y)}
    
    lgb_model, lgb_name = train_lightgbm(X, y)
    if lgb_model:
        save_model(lgb_model, lgb_name, sport_key)
        results['models'][lgb_name] = {'status': 'trained', 'accuracy': lgb_model.score(X, y)}
    
    rf_model, rf_name = train_random_forest(X, y)
    if rf_model:
        save_model(rf_model, rf_name, sport_key)
        results['models'][rf_name] = {'status': 'trained', 'accuracy': rf_model.score(X, y)}
    
    # Train sklearn models
    sklearn_results = train_sklearn_models(X, y)
    save_model(sklearn_results['scaler'], 'scaler', sport_key)
    save_model(sklearn_results['logistic_regression'], 'logistic_regression', sport_key)
    results['models']['logistic_regression'] = {'status': 'trained', 'accuracy': sklearn_results['accuracy']}
    
    # Calculate ensemble weights based on accuracies
    weights = {}
    total_acc = sum(m['accuracy'] for m in results['models'].values())
    
    if total_acc > 0:
        for name, data in results['models'].items():
            weights[name] = round(data['accuracy'] / total_acc, 3)
    
    # Normalize weights
    weight_total = sum(weights.values())
    if weight_total > 0:
        weights = {k: round(v/weight_total, 3) for k, v in weights.items()}
    
    # Set defaults if empty
    if not weights:
        weights = {'xgboost': 0.35, 'lightgbm': 0.30, 'random_forest': 0.20, 'logistic_regression': 0.15}
    
    save_weights(weights, sport_key)
    results['weights'] = weights
    
    logger.info(f"\nEnsemble weights for {sport_key}:")
    for name, weight in weights.items():
        logger.info(f"  {name}: {weight:.1%}")
    
    return results


def main():
    """Main training function"""
    print("\n" + "="*70)
    print("SPORTS PREDICTION MODEL TRAINING")
    print("With Enhanced Features: Weather, Rest Days, Travel")
    print("="*70 + "\n")
    
    # Sports to train
    sports = [
        ('basketball_nba', 500),
        ('basketball_ncaa', 400),
        ('icehockey_nhl', 400),
        ('americanfootball_nfl', 300),
        ('baseball_mlb', 400),
        ('soccer_epl', 400),
    ]
    
    all_results = {
        'training_date': datetime.now().isoformat(),
        'sports': []
    }
    
    for sport_key, n_samples in sports:
        try:
            result = train_sport(sport_key, n_samples)
            all_results['sports'].append(result)
        except Exception as e:
            logger.error(f"Failed to train {sport_key}: {e}")
    
    # Save summary
    summary_file = MODELS_DIR / "training_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print("\n" + "="*70)
    print("TRAINING COMPLETE")
    print("="*70)
    print(f"\nModels saved to: {MODELS_DIR}")
    print(f"\nTrained sports:")
    for sport in all_results['sports']:
        print(f"  - {sport['sport']}: {len(sport['models'])} models, {sport['samples']} samples")
    
    print(f"\nEnsemble weights saved for each sport.")
    print("="*70)


if __name__ == "__main__":
    main()
