# ML Sports Prediction System

## 🎯 Overview

This ML system provides advanced sports predictions using an ensemble of machine learning models with sophisticated confidence scoring and data-driven reasoning.

## 🔧 Key Features

- **Ensemble ML Models**: XGBoost, LightGBM, Neural Network, and Linear Regression
- **Advanced Confidence Scoring**: Multi-factor confidence calculation with calibration
- **Data-Driven Reasoning**: Unique, detailed reasoning for each prediction
- **Automated Daily Training**: Models retrain daily at 2 AM with fresh data
- **Multi-Sport Support**: NBA, NFL, MLB, NHL, and player props
- **Market Integration**: Combines ML predictions with market odds

## 🚀 Quick Start

### 1. Setup the System

**Windows:**
```batch
setup.bat
```

**Linux/Mac:**
```bash
python setup_ml_system.py
```

### 2. Start Daily Training

**Windows:**
```batch
start_ml_system.bat
```

**Linux/Mac:**
```bash
bash ml-models/start_ml_system.sh
```

## 📊 System Architecture

### Model Ensemble
- **XGBoost** (35% weight): Gradient boosting for complex feature interactions
- **LightGBM** (30% weight): Efficient gradient boosting for large datasets
- **Neural Network** (25% weight): Deep learning for non-linear patterns
- **Linear Regression** (10% weight): Baseline model for calibration

### Confidence Scoring Factors
1. **Model Consensus** (25%): Agreement between different models
2. **Prediction Strength** (20%): Feature difference magnitude
3. **Data Quality** (15%): Completeness and reliability of input data
4. **Market Alignment** (15%): Consistency with market odds
5. **Historical Accuracy** (10%): Recent model performance
6. **Feature Stability** (10%): Data consistency and reasonable ranges
7. **Temporal Factors** (5%): Time-based considerations

### Reasoning Engine
The system generates unique reasoning for each prediction based on:
- ELO rating advantages
- Recent form trends
- Injury impact analysis
- Head-to-head history
- Model consensus analysis
- Market sentiment alignment
- Situational factors

## 📁 Directory Structure

```
ml-models/
├── trained/                    # Trained model files
│   ├── xgboost_model.pkl
│   ├── lightgbm_model.pkl
│   ├── neural_net_model.h5
│   ├── linear_model.pkl
│   └── ensemble_weights.json
├── data/                      # Training data
│   ├── nba_training_data.csv
│   ├── nfl_training_data.csv
│   └── player_props_training_data.csv
├── logs/                      # Training and prediction logs
│   ├── daily_training.log
│   ├── training_history.json
│   └── daily_reports/
├── training/                  # Training scripts
│   ├── initial_training.py
│   ├── daily_scheduler.py
│   ├── data_generator.py
│   └── auto_training.py
├── reasoning/                 # Reasoning engine
│   └── advanced_reasoning.py
└── confidence/                # Confidence scoring
    └── advanced_confidence.py
```

## 🔍 Prediction Process

1. **Data Collection**: Gather team stats, market odds, injury reports
2. **Feature Engineering**: Extract 20+ predictive features
3. **Model Prediction**: Run ensemble of 4 ML models
4. **Confidence Calculation**: Multi-factor confidence scoring
5. **Reasoning Generation**: Data-driven explanation
6. **Market Integration**: Combine with market consensus
7. **Result Output**: Prediction with confidence and reasoning

## ⚙️ Configuration

Edit `ml-models/config.json` to customize:
- Model weights and parameters
- Training schedules
- Confidence thresholds
- Data source preferences
- Logging levels

## 📈 Performance Monitoring

### Key Metrics Tracked
- **Accuracy**: Percentage of correct predictions
- **Precision**: True positives / (True positives + False positives)
- **Recall**: True positives / (True positives + False negatives)
- **F1 Score**: Harmonic mean of precision and recall
- **ROI**: Return on investment for betting strategies
- **Calibration**: Prediction confidence vs actual accuracy

### Monitoring Commands
```bash
# Check training history
cat ml-models/logs/training_history.json

# Monitor daily training logs
tail -f ml-models/logs/daily_training.log

# View latest training report
cat ml-models/logs/daily_report_*.json
```

## 🔧 Troubleshooting

### Common Issues

**1. Low Confidence Scores**
- Check data quality and completeness
- Verify model training status
- Review feature engineering pipeline

**2. Identical Reasoning**
- Ensure models are properly trained
- Check data source variety
- Verify reasoning engine configuration

**3. Training Failures**
- Check available system resources
- Verify data file integrity
- Review training logs for errors

**4. Poor Model Performance**
- Increase training data volume
- Adjust model hyperparameters
- Consider feature selection optimization

### Debug Mode
Enable debug logging by setting:
```python
logging.basicConfig(level=logging.DEBUG)
```

## 📊 Sample Prediction Output

```json
{
  "prediction": "Lakers Win",
  "confidence": 78.5,
  "confidence_level": "High",
  "prediction_type": "moneyline",
  "reasoning": [
    {
      "factor": "ELO Rating Advantage (Home)",
      "impact": "Positive",
      "weight": 0.25,
      "explanation": "Significant ELO rating advantage indicates superior team strength. ELO difference: 145 points.",
      "data_points": {
        "home_elo": 1650,
        "away_elo": 1505,
        "elo_difference": 145
      }
    },
    {
      "factor": "Recent Form (Home)",
      "impact": "Positive",
      "weight": 0.22,
      "explanation": "Exceptional recent form demonstrates current momentum. Recent form: 80% vs 45%.",
      "data_points": {
        "home_form": 0.8,
        "away_form": 0.45,
        "form_difference": 0.35
      }
    }
  ],
  "models": [
    {
      "name": "XGBoost",
      "weight": 0.35,
      "confidence": 82.1,
      "prediction": "Lakers Win"
    },
    {
      "name": "LightGBM",
      "weight": 0.30,
      "confidence": 76.8,
      "prediction": "Lakers Win"
    }
  ]
}
```

## 🔄 Daily Training Process

### Automated Schedule
- **2:00 AM**: Generate fresh training data
- **2:05 AM**: Train all models with new data
- **2:15 AM**: Evaluate model performance
- **2:20 AM**: Update model weights
- **2:25 AM**: Generate training report
- **2:30 AM**: Save updated models

### Training Data Sources
1. **Synthetic Data**: Realistic simulated games
2. **Historical Data**: Past game results and statistics
3. **Market Data**: Betting odds and line movements
4. **Performance Data**: Team and player statistics

## 📋 API Integration

### Backend Service Integration
```python
from backend.app.services.ml_service import MLService

ml_service = MLService()
await ml_service.initialize()

prediction = await ml_service.predict_from_odds(game_data)
```

### Frontend Integration
```typescript
const prediction = await fetch('/api/predictions', {
  method: 'POST',
  body: JSON.stringify(gameData)
});
```

## 🔮 Future Enhancements

- **Real-time Data Integration**: Live odds and injury updates
- **Advanced Feature Engineering**: Weather, travel, rest days
- **Model Explainability**: SHAP values and feature importance
- **A/B Testing Framework**: Compare model configurations
- **Performance Dashboard**: Real-time monitoring and alerts
- **Mobile App Integration**: Push notifications for high-confidence picks

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review training logs in `ml-models/logs/`
3. Examine configuration in `ml-models/config.json`
4. Check system requirements and dependencies

## 📄 License

This ML system is part of the sports prediction platform and follows the project's licensing terms.