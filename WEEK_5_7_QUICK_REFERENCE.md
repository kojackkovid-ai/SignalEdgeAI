# WEEK 5-7 QUICK REFERENCE GUIDE
## API Endpoints, Services, and Common Operations

**Purpose:** Developer and operations quick reference for Week 5-7 services  
**Audience:** Backend developers, API consumers, DevOps engineers  
**Last Updated:** March 22, 2026

---

## NEW API ENDPOINTS SUMMARY

### 🎲 ODDS INTEGRATION ENDPOINTS (Base: `/api/v1/odds/`)

| Endpoint | Method | Purpose | Response Time |
|----------|--------|---------|----------------|
| `/event/{event_id}` | GET | Get consensus odds from all providers | 45-75ms |
| `/comparison/{event_id}` | GET | Compare odds across sportsbooks | 60-100ms |
| `/implied-probability/{event_id}` | GET | Extract true probability from odds | 20-30ms |
| `/movement-history/{event_id}` | GET | View odds movement over time | 80-120ms |
| `/sharp-movement` | GET | Detect steam/sharp money moves | 50-90ms |
| `/market-discord/{event_id}` | GET | Find model vs market disagreements | 70-110ms |

**Query Parameters:**
```
?sport=nba,mlb,nhl
?market=moneyline,spread,total
?limit=10
?offset=0
?since=2024-03-20T10:00:00Z
```

**Example Request:**
```bash
curl -X GET "http://api.example.com/api/v1/odds/event/nba_2024_03_22_lal_gsw?sport=nba" \
  -H "Authorization: Bearer $TOKEN"
```

**Example Response:**
```json
{
  "success": true,
  "data": {
    "event_id": "nba_2024_03_22_lal_gsw",
    "sport": "nba",
    "timestamp": "2024-03-22T14:30:00Z",
    "consensus_moneyline": -215,
    "consensus_spread": -7.5,
    "consensus_total": 213.5,
    "odds_by_provider": {
      "draftkings": {
        "moneyline": [-220, 180],
        "spread": [-7.5, -110],
        "total": [213.5, -110]
      },
      "fanduel": {
        "moneyline": [-210, 175],
        "spread": [-7.5, -110],
        "total": [213.5, -110]
      }
    },
    "implied_probability_consensus": 0.682,
    "market_consensus": "strong_consensus"
  },
  "timestamp": "2024-03-22T14:30:00.123Z"
}
```

---

### 📊 ANALYTICS ENDPOINTS (Base: `/api/v1/analytics/`)

| Endpoint | Method | Purpose | Response Time |
|----------|--------|---------|----------------|
| `/bayesian-update/{entity_key}` | GET | Get Bayesian posterior for entity | 80-120ms |
| `/arima-forecast/{entity_key}` | GET | ARIMA time series forecast | 200-300ms |
| `/generate-synthetic/{sport}` | POST | Generate synthetic training data | 500-1500ms |
| `/cross-validation-results` | GET | Model CV performance metrics | 100-150ms |
| `/market-discord` | GET | Global market vs model analysis | 90-140ms |

**Query Parameters:**
```
?horizon=7      # days ahead for forecasting
?samples=1000   # synthetic data samples
?method=smote   # generation method (smote, gmm, copula)
?confidence=0.95 # confidence level for intervals
?limit=100      # max results
```

**Example Request - Bayesian Update:**
```bash
curl -X GET "http://api.example.com/api/v1/analytics/bayesian-update/nba_team_lakers" \
  -H "Authorization: Bearer $TOKEN"
```

**Example Response - Bayesian:**
```json
{
  "success": true,
  "data": {
    "entity_key": "nba_team_lakers",
    "prior": {
      "mean": 0.550,
      "std": 0.08,
      "confidence": 500
    },
    "posterior": {
      "mean": 0.563,
      "std": 0.072,
      "confidence": 680
    },
    "credible_interval_95": [0.422, 0.704],
    "evidence_weight": 180,
    "update_ratio": 1.36,
    "recent_results": [1, 1, 0, 1, 1],
    "last_updated": "2024-03-22T14:30:00Z"
  }
}
```

**Example Request - ARIMA Forecast:**
```bash
curl -X GET "http://api.example.com/api/v1/analytics/arima-forecast/nba_scoring?horizon=7&confidence=0.95"
```

**Example Response - ARIMA:**
```json
{
  "success": true,
  "data": {
    "entity_key": "nba_scoring",
    "model_params": "ARIMA(2,1,2)",
    "forecast_days": 7,
    "forecast": [105.2, 106.1, 104.8, 107.3, 105.9, 106.5, 105.1],
    "confidence_lower": [98.5, 97.2, 94.1, 91.2, 88.3, 85.1, 82.0],
    "confidence_upper": [111.9, 114.8, 115.5, 123.4, 123.5, 127.9, 128.2],
    "trend": "slightly_increasing",
    "seasonality_detected": true,
    "model_rmse": 2.35,
    "last_training": "2024-03-21T03:00:00Z"
  }
}
```

**Example Request - Generate Synthetic Data:**
```bash
curl -X POST "http://api.example.com/api/v1/analytics/generate-synthetic/nba" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "samples": 1000,
    "method": "smote",
    "include_augmentation": true
  }'
```

**Example Response - Synthetic Data:**
```json
{
  "success": true,
  "data": {
    "sport": "nba",
    "method": "smote",
    "samples_generated": 1000,
    "base_dataset_size": 5000,
    "quality_metrics": {
      "distribution_match": 0.92,
      "correlation_preservation": 0.88,
      "mean_preservation": 0.95,
      "std_preservation": 0.91,
      "overall_score": 0.915
    },
    "augmentation_techniques": [
      "noise_injection",
      "time_shifting",
      "feature_scaling_variations",
      "opponent_swaps"
    ],
    "dataset_id": "synth_nba_20240322_smote_001",
    "ready_for_training": true,
    "generation_time_ms": 1250,
    "estimated_accuracy_boost": "2.3%"
  }
}
```

---

### 🤖 ENSEMBLE ENDPOINTS (Base: `/api/v1/ensemble/`)

| Endpoint | Method | Purpose | Response Time |
|----------|--------|---------|----------------|
| `/prediction/{event_id}` | POST | Get ensemble prediction | 150-250ms |
| `/model-weights/{sport_key}` | GET | Current model weights | 30-50ms |
| `/individual-predictions/{event_id}` | GET | See all 7 model predictions | 120-180ms |
| `/retrain-weights` | POST | Manually retrain weights | 5000-15000ms |
| `/performance/{period}` | GET | Ensemble accuracy metrics | 100-150ms |

**Example Request - Ensemble Prediction:**
```bash
curl -X POST "http://api.example.com/api/v1/ensemble/prediction/nba_2024_03_22_lal_gsw" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sport": "nba",
    "include_probabilities": true,
    "include_confidence": true,
    "include_individual_models": true
  }'
```

**Example Response - Ensemble Prediction:**
```json
{
  "success": true,
  "data": {
    "event_id": "nba_2024_03_22_lal_gsw",
    "ensemble_prediction": 0.623,
    "ensemble_confidence": 0.78,
    "market_odds": -215,
    "market_implied_probability": 0.682,
    "edge": -0.059,
    "recommended_action": "none",
    "model_agreement": 0.82,
    "voting_method": "weighted",
    "individual_predictions": {
      "xgboost": {"prediction": 0.618, "weight": 0.28, "confidence": 0.82},
      "neural_network": {"prediction": 0.635, "weight": 0.22, "confidence": 0.79},
      "random_forest": {"prediction": 0.605, "weight": 0.18, "confidence": 0.75},
      "bayesian": {"prediction": 0.627, "weight": 0.15, "confidence": 0.81},
      "arima": {"prediction": 0.632, "weight": 0.08, "confidence": 0.68},
      "decision_trees": {"prediction": 0.614, "weight": 0.06, "confidence": 0.72},
      "linear_regression": {"prediction": 0.621, "weight": 0.03, "confidence": 0.65}
    },
    "generation_time_ms": 185,
    "timestamp": "2024-03-22T14:30:00.185Z"
  }
}
```

**Example Request - Model Weights:**
```bash
curl -X GET "http://api.example.com/api/v1/ensemble/model-weights/nba" \
  -H "Authorization: Bearer $TOKEN"
```

**Example Response - Model Weights:**
```json
{
  "success": true,
  "data": {
    "sport": "nba",
    "weights": {
      "xgboost": 0.285,
      "neural_network": 0.218,
      "random_forest": 0.175,
      "bayesian": 0.152,
      "arima": 0.082,
      "decision_trees": 0.062,
      "linear_regression": 0.026
    },
    "last_updated": "2024-03-22T03:00:00Z",
    "next_update": "2024-03-23T03:00:00Z",
    "models_included": 7,
    "accuracy_improvement_since_last_update": 0.015
  }
}
```

---

## 🔧 NEW SERVICES & CLASSES

### OddsAggregatorService
```python
from backend.app.services.odds_aggregator_service import OddsAggregatorService

# Initialization
odds_service = OddsAggregatorService(session=db_session)

# Get consensus odds
consensus = await odds_service.get_event_odds('nba_2024_03_22_lal_gsw')

# Compare providers
comparison = await odds_service.get_odds_comparison('nba_2024_03_22_lal_gsw')

# Detect sharp money
sharp_moves = await odds_service.detect_sharp_movement()

# Calculate market discord
discord = await odds_service.calculate_market_discord('nba_2024_03_22_lal_gsw', 0.623)

# Get implied probabilities
implied = await odds_service.get_implied_probabilities('nba_2024_03_22_lal_gsw')
```

### AdvancedModelEnsemble
```python
from backend.app.services.advanced_statistical_models import (
    BayesianPredictor, ARIMAForecaster, DecisionTreeEnsemble, AdvancedModelEnsemble
)

# Bayesian prediction
bayesian = BayesianPredictor()
bayesian.set_prior(mean=0.55, std=0.08)
posterior = bayesian.update_with_evidence([1, 1, 0, 1, 1])
interval = bayesian.predict_credible_interval()

# ARIMA forecasting
arima = ARIMAForecaster(p=2, d=1, q=2)
arima.fit(historical_data)
forecast = arima.forecast(days=7)

# Decision trees
trees = DecisionTreeEnsemble(n_trees=10)
trees.fit(features, labels)
importance = trees.get_feature_importance()

# Ensemble voting
ensemble = AdvancedModelEnsemble()
ensemble.fit(features, labels)
prediction = ensemble.make_prediction(features)
```

### MultiModelEnsemble
```python
from backend.app.services.multi_model_ensemble import MultiModelEnsemble, EnsembleConfig

# Initialize
config = EnsembleConfig(
    voting_method='weighted',
    min_agreement_threshold=0.5,
    confidence_buckets=5
)
ensemble = MultiModelEnsemble(config=config, session=db_session)

# Register models
ensemble.register_model(name='xgboost', model=xgb_model, weight=0.28)
ensemble.register_model(name='neural_network', model=nn_model, weight=0.22)
# ... register other 5 models

# Make ensemble prediction
prediction = await ensemble.make_ensemble_prediction(event_data)
# Returns: {'probability': 0.623, 'confidence': 0.78, 'agreement': 0.82, ...}

# Update weights based on recent performance
await ensemble.update_weights()

# Get individual model predictions
individual = await ensemble.get_individual_predictions(event_data)
# Returns: {'xgboost': 0.618, 'neural_network': 0.635, ...}
```

### SyntheticDataGenerator
```python
from backend.app.services.synthetic_data_generation import (
    SyntheticDataGenerator, DataAugmentationPipeline
)

# Generate synthetic data
generator = SyntheticDataGenerator(method='smote')
synthetic = generator.generate_from_realdata(
    real_data=historical_games,
    samples=1000
)

# Augment data
augmenter = DataAugmentationPipeline()
augmented = augmenter.apply_noise_injection(
    data=synthetic,
    noise_std=0.05
)

# Validate quality
quality_metrics = generator.validate_synthetic_data(
    synthetic_data=augmented,
    original_data=historical_games
)
# Returns: {'dist_match': 0.92, 'corr_preserve': 0.88, 'mean_preserve': 0.95, ...}
```

---

## 📦 DEPENDENCY INJECTION PATTERNS

### FastAPI Dependencies

```python
# In route handlers
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

async def get_db() -> AsyncSession:
    """Database session dependency"""
    async with async_session_maker() as session:
        yield session

async def get_odds_service(db: AsyncSession = Depends(get_db)) -> OddsAggregatorService:
    """Odds service dependency"""
    return OddsAggregatorService(session=db)

async def get_ensemble_service(db: AsyncSession = Depends(get_db)) -> MultiModelEnsemble:
    """Ensemble service dependency"""
    config = EnsembleConfig(voting_method='weighted')
    return MultiModelEnsemble(config=config, session=db)

# In route
@router.get("/odds/event/{event_id}")
async def get_event_odds(
    event_id: str,
    odds_service: OddsAggregatorService = Depends(get_odds_service)
):
    result = await odds_service.get_event_odds(event_id)
    return result
```

---

## 🗄️ DATABASE MODELS

### OddsRecord Table
```
Column Name         | Type      | Index | Nullable | Notes
event_id           | VARCHAR   | ✓     | NO       | Foreign key to events
provider           | VARCHAR   | ✓     | NO       | DraftKings, FanDuel, etc.
moneyline_home     | DECIMAL   | -     | YES      | Home team moneyline
moneyline_away     | DECIMAL   | -     | YES      | Away team moneyline
spread_value       | DECIMAL   | -     | YES      | Spread line
spread_home        | DECIMAL   | -     | YES      | Home spread odds
spread_away        | DECIMAL   | -     | YES      | Away spread odds
total_line         | DECIMAL   | -     | YES      | Total points
total_over         | DECIMAL   | -     | YES      | Over odds
total_under        | DECIMAL   | -     | YES      | Under odds
implied_prob_home  | DECIMAL   | -     | YES      | Extracted probability
implied_prob_away  | DECIMAL   | -     | YES      | Extracted probability
timestamp          | TIMESTAMP | ✓     | NO       | Record creation time
confidence_score   | DECIMAL   | -     | YES      | Data quality (0-1)
```

### OddsMovement Table
```
Column Name         | Type      | Index | Nullable | Notes
event_id           | VARCHAR   | ✓     | NO       | Which event
market_type        | VARCHAR   | ✓     | NO       | moneyline/spread/total
movement_type      | VARCHAR   | ✓     | NO       | reversal/consensus/steam
opening_line       | DECIMAL   | -     | NO       | Original line
current_line       | DECIMAL   | -     | NO       | Latest line
move_amount        | DECIMAL   | -     | NO       | Change from opening
provider_count     | INTEGER   | -     | NO       | Providers agreeing
speed_index        | DECIMAL   | -     | NO       | Urgency of move
smart_money        | BOOLEAN   | ✓     | NO       | Coordinated movement
arbitrage          | BOOLEAN   | ✓     | NO       | Guaranteed profit opp
detected_reason    | VARCHAR   | -     | YES      | Why movement detected
market_consensus   | VARCHAR   | -     | YES      | strong/weak/neutral
timestamp          | TIMESTAMP | ✓     | NO       | Detection time
```

### EnsembleWeights Table
```
Column Name         | Type      | Index | Nullable | Notes
model_name         | VARCHAR   | ✓     | NO       | xgboost, neural_net, etc.
sport_key          | VARCHAR   | ✓     | NO       | nba, mlb, nhl
weight             | DECIMAL   | -     | NO       | Current weight (0-1)
recent_accuracy    | DECIMAL   | -     | NO       | Last 30 days accuracy
calibration_score  | DECIMAL   | -     | NO       | Confidence calibration
model_agreement    | DECIMAL   | -     | YES      | Avg agreement with ensemble
predictions_count  | INTEGER   | -     | NO       | Total predictions made
last_updated       | TIMESTAMP | ✓     | NO       | Weight update time
```

---

## 🔌 COMMON INTEGRATIONS

### Using Ensemble in Prediction Pipeline
```python
async def predict_game(event_id: str, db: AsyncSession):
    # Get odds context
    odds_service = OddsAggregatorService(session=db)
    odds = await odds_service.get_event_odds(event_id)
    
    # Get ensemble prediction
    ensemble_service = MultiModelEnsemble(session=db)
    ensemble_pred = await ensemble_service.make_ensemble_prediction(event_data)
    
    # Check for edge/discord
    discord = odds['implied_prob'] - ensemble_pred['probability']
    
    # Make decision
    if abs(discord) > 0.05:
        logger.info(f"Market discord detected: {discord:.3f}")
    
    return {
        'ensemble': ensemble_pred,
        'odds': odds,
        'edge': discord
    }
```

### Using Bayesian Updates
```python
async def update_player_model(player_id: str, recent_games: List[Game]):
    # Get historical prior
    bayesian = BayesianPredictor()
    prior = get_player_prior(player_id)  # Load from DB
    bayesian.set_prior(mean=prior['mean'], std=prior['std'])
    
    # Update with recent evidence
    recent_results = [g.player_stats[player_id] for g in recent_games]
    posterior = bayesian.update_with_evidence(recent_results)
    
    # Save updated prior for next time
    save_player_prior(player_id, posterior)
    
    return posterior
```

### Using ARIMA for Forecasts
```python
async def forecast_team_scoring(team_id: str, historical_scores: List[float]):
    arima = ARIMAForecaster(p=2, d=1, q=2)
    arima.fit(historical_scores)
    
    # Get 7-day forecast
    forecast = arima.forecast(days=7)
    intervals = arima.get_confidence_intervals()
    
    return {
        'forecast': forecast['values'],
        'lower_bound': intervals['lower_95'],
        'upper_bound': intervals['upper_95'],
        'trend': forecast.get('trend_direction')
    }
```

---

## ⚙️ CONFIGURATION & ENVIRONMENT

### Key Environment Variables
```bash
# Odds integration
ODDS_SYNC_INTERVAL=10              # seconds
ODDS_CACHE_TTL=300                 # 5 minutes

# Ensemble retraining
ENSEMBLE_RETRAIN_HOUR=3             # UTC hour to retrain daily
ENSEMBLE_RETRAIN_ENABLED=true       # Enable auto-retraining

# Synthetic data
SYNTHETIC_DATA_SIZE=5000            # Default samples to generate
SYNTHETIC_DATA_CACHE_DAYS=30        # Keep synthetic data this long

# Model paths
ML_MODELS_PATH=/app/data/models     # Where models are saved
CHECKPOINT_INTERVAL=86400           # Save health check every day
```

### Configuration Classes
```python
# In config.py
class Week5Settings(BaseSettings):
    # Odds settings
    odds_sync_interval: int = 10
    odds_providers: List[str] = ['draftkings', 'fanduel', 'betmgm', 'caesars']
    odds_cache_ttl: int = 300
    
    # Ensemble settings
    ensemble_voting_method: str = 'weighted'  # or 'majority', 'soft', 'stacking'
    ensemble_retrain_enabled: bool = True
    ensemble_retrain_hour: int = 3  # UTC
    
    # Synthetic data
    synthetic_data_size: int = 5000
    synthetic_data_method: str = 'smote'
    
    class Config:
        env_file = '.env'
```

---

## 📊 MONITORING & OBSERVABILITY

### Key Metrics to Track
```
Odds Service:
- Sync latency (ideal: < 100ms)
- Provider availability (target: 99%+)
- Consensus accuracy (vs actual results)

Ensemble Service:
- Prediction latency (target: < 250ms)
- Model agreement score (target: > 80%)
- Daily accuracy (target: > 63%)
- Weight stability (should not swing > 5% daily)

Analytics Service:
- Bayesian update accuracy (calibration)
- ARIMA forecast RMSE
- Synthetic data quality (seed distribution match)
```

### CloudWatch Metrics
```python
# Publish custom metrics
cloudwatch.put_metric_data(
    Namespace='PredictionPlatform/Week5-7',
    MetricData=[
        {
            'MetricName': 'OddsService/SyncLatency',
            'Value': sync_time_ms,
            'Unit': 'Milliseconds'
        },
        {
            'MetricName': 'Ensemble/ModelAgreement',
            'Value': agreement_score,
            'Unit': 'None'
        }
    ]
)
```

---

## 🚨 ERROR HANDLING

### Common Errors & Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `OddsProviderError: Rate limited` | Too many API requests | Wait or use different provider |
| `EnsembleError: No models registered` | Not initialized | Call register_model() for each model |
| `BayesianError: Confidence too low` | Not enough evidence | Add more data points or use wider prior |
| `DatabaseError: Connection pool exhausted` | Too many concurrent requests | Increase SQLALCHEMY_POOL_SIZE |
| `CacheError: Redis unavailable` | Cache service down | Restart Redis or bypass cache |

---

## 📚 HELPFUL DOCUMENTATION LINKS

- [Full Implementation](./WEEK_5_7_IMPLEMENTATION_COMPLETE.md)
- [Deployment Guide](./WEEK_5_7_DEPLOYMENT_GUIDE.md)
- [API OpenAPI Docs](http://api.example.com/docs)
- [Database Schema](/docs/schema.md)
- [Model Architecture](/docs/ml_architecture.md)
- [Troubleshooting](./DEBUG_GUIDE.md)

---

**Quick Reference Version:** 1.0  
**Generated:** 2026-03-22  
**Updated:** 2026-03-22  
**Audience:** Developers, API consumers, DevOps

