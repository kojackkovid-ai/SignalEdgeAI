#!/usr/bin/env python
"""
Example: Using the Sports Prediction Platform API
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

async def example_prediction_workflow():
    """Example workflow for making predictions"""
    
    from backend.app.services.ml_service import MLService
    from ml_models.models.ensemble import extract_features, generate_reasoning
    
    # Initialize ML service
    ml_service = MLService()
    await ml_service.initialize()
    
    # Example: Premier League match
    match_data = {
        'sport': 'Soccer',
        'league': 'Premier League',
        'matchup': 'Man City vs Liverpool',
        'home_team': 'Man City',
        'away_team': 'Liverpool',
        'home_elo': 1750,
        'away_elo': 1720,
        'home_form': 0.75,
        'away_form': 0.68,
        'home_advantage': 0.15,
        'h2h_home_winrate': 0.55,
        'h2h_away_winrate': 0.35,
        'home_injury_impact': 0.05,
        'away_injury_impact': 0.12,
        'day_of_week': 5,  # Friday
        'season_progress': 0.45
    }
    
    # Extract features
    features = extract_features(match_data)
    
    # Make prediction
    prediction_result = await ml_service.make_prediction(match_data)
    
    print("\n" + "="*60)
    print("PREDICTION RESULT")
    print("="*60)
    print(f"Match: {match_data['matchup']}")
    print(f"Prediction: Over 2.5 Goals")
    print(f"Confidence: {prediction_result['confidence']:.2%}")
    print(f"\nIndividual Model Predictions:")
    for model_name, pred in prediction_result['individual_predictions'].items():
        conf = prediction_result['individual_confidences'][model_name]
        print(f"  {model_name}: {pred:.3f} (conf: {conf:.2%})")
    
    # Generate reasoning
    reasoning = generate_reasoning(
        prediction_result['confidence'],
        prediction_result['confidence'],
        match_data
    )
    
    print(f"\nReasoning:")
    for point in reasoning['reasoning_points']:
        print(f"  • {point['factor']} ({point['impact']})")
    
    await ml_service.shutdown()

async def example_training_workflow():
    """Example workflow for model retraining"""
    
    import pandas as pd
    from ml_models.training.auto_training import AutoTrainingPipeline
    
    # Initialize training pipeline
    pipeline = AutoTrainingPipeline(
        retrain_interval_days=7,
        min_samples=1000
    )
    
    # Simulate loading training data
    training_data = pd.DataFrame({
        'feature_1': [1, 2, 3, 4, 5] * 200,
        'feature_2': [0.5, 0.6, 0.7, 0.8, 0.9] * 200,
        'target': [0, 1, 1, 0, 1] * 200
    })
    
    print("\n" + "="*60)
    print("TRAINING PIPELINE")
    print("="*60)
    print(f"Training samples: {len(training_data)}")
    
    # Check and trigger retraining
    result = await pipeline.check_and_retrain(training_data)
    
    if result['status'] == 'success':
        print(f"Status: ✓ Training successful")
        print(f"Duration: {result['duration']:.2f}s")
        print(f"New weights: {result['new_weights']}")
    else:
        print(f"Status: ✗ {result.get('reason', 'Training failed')}")

async def main():
    """Run examples"""
    
    print("\n" + "╔" + "="*58 + "╗")
    print("║" + " "*16 + "SPORTS PREDICTION PLATFORM" + " "*16 + "║")
    print("║" + " "*20 + "API Usage Examples" + " "*20 + "║")
    print("╚" + "="*58 + "╝")
    
    try:
        await example_prediction_workflow()
        print("\n" + "-"*60)
        await example_training_workflow()
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    asyncio.run(main())
