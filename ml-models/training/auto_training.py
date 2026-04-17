"""
Auto-Training Pipeline
Continuously retrains models with new data
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
import logging
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)

class AutoTrainingPipeline:
    """
    Automated model retraining pipeline
    """
    
    def __init__(self, retrain_interval_days: int = 7, min_samples: int = 1000):
        self.retrain_interval = timedelta(days=retrain_interval_days)
        self.min_samples = min_samples
        self.last_training = None+
         
        self.training_history = []

    async def check_and_retrain(self, new_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Check if retraining is needed and trigger if necessary
        """
        should_retrain = False
        reason = ""
        
        # Check time-based trigger
        if self.last_training is None:
            should_retrain = True
            reason = "Initial training"
        elif datetime.utcnow() - self.last_training >= self.retrain_interval:
            should_retrain = True
            reason = "Scheduled retraining (interval exceeded)"
        
        # Check data-based trigger
        if len(new_data) >= self.min_samples:
            should_retrain = True
            reason = f"Sufficient new data ({len(new_data)} samples)"
        
        if should_retrain:
            return await self.trigger_retraining(new_data, reason)
        else:
            return {
                "status": "no_retrain_needed",
                "reason": "Conditions not met for retraining",
                "next_check": (self.last_training + self.retrain_interval).isoformat()
            }

    async def trigger_retraining(self, training_data: pd.DataFrame, reason: str) -> Dict[str, Any]:
        """
        Execute model retraining
        """
        logger.info(f"Starting retraining: {reason}")
        start_time = datetime.utcnow()
        
        try:
            # Validate data
            if not self._validate_training_data(training_data):
                raise ValueError("Invalid training data")
            
            # Prepare features and labels
            X, y = self._prepare_training_data(training_data)
            
            # Train individual models
            results = {
                'xgboost': await self._train_xgboost(X, y),
                'lightgbm': await self._train_lightgbm(X, y),
                'neural_net': await self._train_neural_network(X, y),
                'linear': await self._train_linear_model(X, y)
            }
            
            # Evaluate models
            evaluations = await self._evaluate_models(results, X, y)
            
            # Update weights based on performance
            new_weights = self._optimize_weights(evaluations)
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            training_record = {
                'timestamp': start_time.isoformat(),
                'duration': duration,
                'samples_used': len(training_data),
                'reason': reason,
                'results': results,
                'evaluations': evaluations,
                'new_weights': new_weights
            }
            
            self.training_history.append(training_record)
            self.last_training = start_time
            
            logger.info(f"Retraining completed in {duration}s")
            
            return {
                'status': 'success',
                'timestamp': start_time.isoformat(),
                'duration': duration,
                'samples_used': len(training_data),
                'models_trained': list(results.keys()),
                'new_weights': new_weights,
                'evaluation_metrics': evaluations
            }
        
        except Exception as e:
            logger.error(f"Retraining failed: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

    def _validate_training_data(self, data: pd.DataFrame) -> bool:
        """Validate training data"""
        if data.empty:
            return False
        if len(data) < self.min_samples:
            return False
        if 'target' not in data.columns:
            return False
        return True

    def _prepare_training_data(self, data: pd.DataFrame) -> tuple:
        """Prepare features and labels with encoding"""
        # Separate features and target
        features = data.drop('target', axis=1)
        y = data['target'].values
        
        # Identify categorical columns
        categorical_cols = features.select_dtypes(include=['object', 'category']).columns
        
        # One-hot encode categorical columns
        if len(categorical_cols) > 0:
            features = pd.get_dummies(features, columns=categorical_cols)
            
        # Drop any non-numeric columns that might remain (e.g. dates)
        features = features.select_dtypes(include=['number'])
        
        X = features.values
        
        # Handle any NaN values
        X = np.nan_to_num(X, nan=0.0)
        
        return X, y

    async def _train_xgboost(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """Train XGBoost model"""
        try:
            import xgboost as xgb
            model = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8
            )
            await asyncio.to_thread(model.fit, X, y)
            return {'status': 'success', 'model': model}
        except Exception as e:
            logger.error(f"XGBoost training failed: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def _train_lightgbm(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """Train LightGBM model"""
        try:
            import lightgbm as lgb
            model = lgb.LGBMClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1
            )
            await asyncio.to_thread(model.fit, X, y)
            return {'status': 'success', 'model': model}
        except Exception as e:
            logger.error(f"LightGBM training failed: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def _train_neural_network(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """Train Neural Network"""
        try:
            import tensorflow as tf
            from tensorflow import keras
            
            model = keras.Sequential([
                keras.layers.Dense(128, activation='relu', input_shape=(X.shape[1],)),
                keras.layers.Dropout(0.2),
                keras.layers.Dense(64, activation='relu'),
                keras.layers.Dropout(0.2),
                keras.layers.Dense(1, activation='sigmoid')
            ])
            
            model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
            await asyncio.to_thread(
                model.fit, X, y, epochs=50, batch_size=32, verbose=0
            )
            return {'status': 'success', 'model': model}
        except Exception as e:
            logger.error(f"Neural Network training failed: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def _train_linear_model(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """Train Linear Regression"""
        try:
            from sklearn.linear_model import LogisticRegression
            model = LogisticRegression(max_iter=1000)
            await asyncio.to_thread(model.fit, X, y)
            return {'status': 'success', 'model': model}
        except Exception as e:
            logger.error(f"Linear model training failed: {e}")
            return {'status': 'failed', 'error': str(e)}

    async def _evaluate_models(self, models: Dict, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """Evaluate trained models"""
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
        
        evaluations = {}
        for model_name, result in models.items():
            if result['status'] == 'success':
                model = result['model']
                predictions = model.predict(X)
                
                # Convert continuous predictions to binary classes
                # Handle both single output (sigmoid) and multi-output (softmax) cases
                if len(predictions.shape) > 1 and predictions.shape[1] > 1:
                    # Multi-class: take argmax
                    predictions = np.argmax(predictions, axis=1)
                elif len(predictions.shape) > 1 and predictions.shape[1] == 1:
                    # Single output with extra dimension: squeeze and threshold
                    predictions = (predictions.squeeze() > 0.5).astype(int)
                else:
                    # Single output: threshold at 0.5
                    predictions = (predictions > 0.5).astype(int)
                
                # Ensure y is also 1D
                if len(y.shape) > 1:
                    y = y.squeeze()
                
                evaluations[model_name] = {
                    'accuracy': accuracy_score(y, predictions),
                    'precision': precision_score(y, predictions, zero_division=0),
                    'recall': recall_score(y, predictions, zero_division=0),
                    'f1': f1_score(y, predictions, zero_division=0)
                }
            else:
                evaluations[model_name] = None
        
        return evaluations


    def _optimize_weights(self, evaluations: Dict[str, Any]) -> Dict[str, float]:
        """Optimize ensemble weights based on performance"""
        weights = {}
        total_score = 0
        
        for model_name, metrics in evaluations.items():
            if metrics:
                # Use F1 score as primary metric
                score = metrics.get('f1', 0) + metrics.get('accuracy', 0) * 0.5
                weights[model_name] = score
                total_score += score
        
        # Normalize weights
        if total_score > 0:
            weights = {k: v / total_score for k, v in weights.items()}
        else:
            weights = {k: 1/len(weights) for k in weights}
        
        return weights
