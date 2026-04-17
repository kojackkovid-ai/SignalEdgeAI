"""
Enhanced Auto-Training Pipeline with comprehensive monitoring and triggers
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, timedelta
import asyncio
import json
from pathlib import Path
import joblib
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.model_selection import train_test_split

logger = logging.getLogger(__name__)

class EnhancedAutoTrainingPipeline:
    """
    Advanced automated model retraining pipeline with performance monitoring
    """
    
    def __init__(self, 
                 retrain_interval_days: int = 7, 
                 min_samples: int = 50,
                 performance_threshold: float = 0.05,
                 min_accuracy_threshold: float = 0.55):
        self.retrain_interval = timedelta(days=retrain_interval_days)
        self.min_samples = min_samples
        self.performance_threshold = performance_threshold
        self.min_accuracy_threshold = min_accuracy_threshold
        self.last_training = None
        self.training_history = []
        self.performance_history = []
        self.models_dir = Path("ml-models/trained")
        self.models_dir.mkdir(exist_ok=True)
        
        # Performance tracking
        self.model_performance = {}
        self.data_drift_threshold = 0.1
        
    async def comprehensive_check_and_retrain(self, 
                                            new_data: pd.DataFrame,
                                            sport_key: str,
                                            market_type: str) -> Dict[str, Any]:
        """
        Comprehensive check for retraining needs with multiple triggers
        """
        should_retrain = False
        reasons = []
        
        # 1. Time-based trigger
        if self.last_training is None:
            should_retrain = True
            reasons.append("Initial training required")
        elif datetime.utcnow() - self.last_training >= self.retrain_interval:
            should_retrain = True
            reasons.append(f"Scheduled retraining (interval: {self.retrain_interval.days} days)")
        
        # 2. Data volume trigger
        if len(new_data) >= self.min_samples:
            should_retrain = True
            reasons.append(f"Sufficient new data ({len(new_data)} samples)")
        
        # 3. Performance degradation trigger
        if await self._check_performance_degradation(sport_key, market_type):
            should_retrain = True
            reasons.append("Model performance degradation detected")
        
        # 4. Data drift trigger
        if await self._detect_data_drift(new_data, sport_key, market_type):
            should_retrain = True
            reasons.append("Data drift detected")
        
        # 5. Manual override trigger (check for retrain flag)
        if await self._check_manual_retrain_flag(sport_key, market_type):
            should_retrain = True
            reasons.append("Manual retraining requested")
        
        if should_retrain:
            return await self.trigger_enhanced_retraining(new_data, sport_key, market_type, reasons)
        else:
            return {
                "status": "no_retrain_needed",
                "reason": "Conditions not met for retraining",
                "next_check": (self.last_training + self.retrain_interval).isoformat() if self.last_training else "N/A",
                "current_performance": await self._get_current_performance_summary(sport_key, market_type)
            }
    
    async def _check_performance_degradation(self, sport_key: str, market_type: str) -> bool:
        """Check if model performance has degraded significantly"""
        try:
            performance_file = self.models_dir / f"{sport_key}_{market_type}_performance.json"
            if not performance_file.exists():
                return False
            
            with open(performance_file, 'r') as f:
                performance_data = json.load(f)
            
            recent_performance = performance_data.get('recent_metrics', {})
            baseline_performance = performance_data.get('baseline_metrics', {})
            
            if not recent_performance or not baseline_performance:
                return False
            
            # Check accuracy degradation
            recent_acc = recent_performance.get('accuracy', 0)
            baseline_acc = baseline_performance.get('accuracy', 0)
            
            accuracy_drop = baseline_acc - recent_acc
            
            return accuracy_drop > self.performance_threshold or recent_acc < self.min_accuracy_threshold
            
        except Exception as e:
            logger.error(f"Error checking performance degradation: {e}")
            return False
    
    async def _detect_data_drift(self, new_data: pd.DataFrame, sport_key: str, market_type: str) -> bool:
        """Detect significant data drift using statistical methods"""
        try:
            # Load historical data statistics
            stats_file = self.models_dir / f"{sport_key}_{market_type}_data_stats.json"
            if not stats_file.exists():
                return False
            
            with open(stats_file, 'r') as f:
                historical_stats = json.load(f)
            
            # Calculate current data statistics
            current_stats = {}
            for column in new_data.select_dtypes(include=[np.number]).columns:
                current_stats[column] = {
                    'mean': float(new_data[column].mean()),
                    'std': float(new_data[column].std()),
                    'min': float(new_data[column].min()),
                    'max': float(new_data[column].max())
                }
            
            # Check for significant drift in key features
            drift_detected = False
            for feature, hist_data in historical_stats.items():
                if feature in current_stats:
                    current_mean = current_stats[feature]['mean']
                    historical_mean = hist_data['mean']
                    historical_std = hist_data['std']
                    
                    # Z-score test for mean drift
                    if historical_std > 0:
                        z_score = abs(current_mean - historical_mean) / historical_std
                        if z_score > 3.0:  # 3-sigma rule
                            drift_detected = True
                            logger.warning(f"Data drift detected in {feature}: z-score = {z_score:.2f}")
                            break
            
            return drift_detected
            
        except Exception as e:
            logger.error(f"Error detecting data drift: {e}")
            return False
    
    async def _check_manual_retrain_flag(self, sport_key: str, market_type: str) -> bool:
        """Check if manual retraining has been requested"""
        try:
            flag_file = self.models_dir / f"{sport_key}_{market_type}_retrain.flag"
            if flag_file.exists():
                flag_file.unlink()  # Remove flag after reading
                return True
            return False
        except Exception as e:
            logger.error(f"Error checking manual retrain flag: {e}")
            return False
    
    async def _get_current_performance_summary(self, sport_key: str, market_type: str) -> Dict[str, Any]:
        """Get current performance summary for the model"""
        try:
            performance_file = self.models_dir / f"{sport_key}_{market_type}_performance.json"
            if performance_file.exists():
                with open(performance_file, 'r') as f:
                    return json.load(f)
            return {"message": "No performance data available"}
        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return {"error": str(e)}
    
    async def trigger_enhanced_retraining(self, 
                                        training_data: pd.DataFrame,
                                        sport_key: str,
                                        market_type: str,
                                        reasons: List[str]) -> Dict[str, Any]:
        """
        Execute enhanced model retraining with comprehensive monitoring
        """
        logger.info(f"Starting enhanced retraining for {sport_key} - {market_type}: {'; '.join(reasons)}")
        start_time = datetime.utcnow()
        
        try:
            # Validate data
            validation_result = await self._comprehensive_data_validation(training_data)
            if not validation_result['valid']:
                raise ValueError(f"Data validation failed: {validation_result['errors']}")
            
            # Store data statistics for future drift detection
            await self._save_data_statistics(training_data, sport_key, market_type)
            
            # Prepare training data with advanced preprocessing
            X, y = await self._advanced_data_preparation(training_data)
            
            # Split data chronologically for time-series validation
            train_size = int(len(X) * 0.8)
            X_train, X_test = X[:train_size], X[train_size:]
            y_train, y_test = y[:train_size], y[train_size:]
            
            # Train multiple model types
            model_results = await self._train_model_ensemble(X_train, X_test, y_train, y_test, market_type)
            
            # Comprehensive evaluation
            evaluation_results = await self._comprehensive_model_evaluation(model_results, X_test, y_test, market_type)
            
            # Update model weights based on performance
            optimized_weights = await self._optimize_ensemble_weights(evaluation_results)
            
            # Save training artifacts
            await self._save_training_artifacts(sport_key, market_type, model_results, evaluation_results, optimized_weights)
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            training_record = {
                'timestamp': start_time.isoformat(),
                'sport_key': sport_key,
                'market_type': market_type,
                'duration': duration,
                'samples_used': len(training_data),
                'reasons': reasons,
                'validation_results': validation_result,
                'model_results': model_results,
                'evaluation_results': evaluation_results,
                'optimized_weights': optimized_weights,
                'status': 'success'
            }
            
            self.training_history.append(training_record)
            self.last_training = start_time
            
            logger.info(f"Enhanced retraining completed in {duration}s for {sport_key} - {market_type}")
            
            return {
                'status': 'success',
                'timestamp': start_time.isoformat(),
                'sport_key': sport_key,
                'market_type': market_type,
                'duration': duration,
                'samples_used': len(training_data),
                'reasons': reasons,
                'models_trained': list(model_results.keys()),
                'evaluation_metrics': evaluation_results,
                'optimized_weights': optimized_weights
            }
            
        except Exception as e:
            logger.error(f"Enhanced retraining failed for {sport_key} - {market_type}: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat(),
                'sport_key': sport_key,
                'market_type': market_type
            }
    
    async def _comprehensive_data_validation(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Comprehensive data validation"""
        errors = []
        
        if data.empty:
            errors.append("Training data is empty")
        
        if len(data) < self.min_samples:
            errors.append(f"Insufficient data: {len(data)} < {self.min_samples}")
        
        # Check for missing values
        missing_pct = (data.isnull().sum() / len(data)) * 100
        high_missing = missing_pct[missing_pct > 50]
        if not high_missing.empty:
            errors.append(f"High missing values in columns: {high_missing.to_dict()}")
        
        # Check for duplicates
        duplicates = data.duplicated().sum()
        if duplicates > len(data) * 0.1:  # More than 10% duplicates
            errors.append(f"Too many duplicate rows: {duplicates}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'data_quality_metrics': {
                'total_samples': len(data),
                'missing_values_pct': missing_pct.to_dict(),
                'duplicate_rows': int(duplicates),
                'numeric_columns': len(data.select_dtypes(include=[np.number]).columns),
                'categorical_columns': len(data.select_dtypes(include=['object']).columns)
            }
        }
    
    async def _save_data_statistics(self, data: pd.DataFrame, sport_key: str, market_type: str) -> None:
        """Save data statistics for drift detection"""
        try:
            stats = {}
            for column in data.select_dtypes(include=[np.number]).columns:
                stats[column] = {
                    'mean': float(data[column].mean()),
                    'std': float(data[column].std()),
                    'min': float(data[column].min()),
                    'max': float(data[column].max()),
                    'median': float(data[column].median()),
                    'timestamp': datetime.utcnow().isoformat()
                }
            
            stats_file = self.models_dir / f"{sport_key}_{market_type}_data_stats.json"
            with open(stats_file, 'w') as f:
                json.dump(stats, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving data statistics: {e}")
    
    async def _advanced_data_preparation(self, data: pd.DataFrame) -> tuple:
        """Advanced data preparation with feature engineering"""
        try:
            # Handle missing values
            data = data.copy()
            
            # Fill numeric columns with median
            numeric_cols = data.select_dtypes(include=[np.number]).columns
            data[numeric_cols] = data[numeric_cols].fillna(data[numeric_cols].median())
            
            # Fill categorical columns with mode
            categorical_cols = data.select_dtypes(include=['object']).columns
            for col in categorical_cols:
                data[col] = data[col].fillna(data[col].mode()[0] if not data[col].mode().empty else 'unknown')
            
            # Separate features and target
            if 'target' not in data.columns:
                raise ValueError("Target column not found in training data")
            
            X = data.drop('target', axis=1)
            y = data['target']
            
            # Convert categorical variables
            for col in X.select_dtypes(include=['object']).columns:
                X[col] = pd.Categorical(X[col]).codes
            
            return X.values, y.values
            
        except Exception as e:
            logger.error(f"Error in advanced data preparation: {e}")
            raise
    
    async def _train_model_ensemble(self, X_train: np.ndarray, X_test: np.ndarray, 
                                  y_train: np.ndarray, y_test: np.ndarray, market_type: str) -> Dict[str, Any]:
        """Train ensemble of models"""
        model_results = {}
        
        # XGBoost
        try:
            import xgboost as xgb
            if market_type in ['moneyline', 'spread']:  # Classification
                model = xgb.XGBClassifier(n_estimators=200, max_depth=6, learning_rate=0.1, random_state=42)
            else:  # Regression
                model = xgb.XGBRegressor(n_estimators=200, max_depth=6, learning_rate=0.1, random_state=42)
            
            model.fit(X_train, y_train)
            model_results['xgboost'] = {'status': 'success', 'model': model}
        except Exception as e:
            logger.error(f"XGBoost training failed: {e}")
            model_results['xgboost'] = {'status': 'failed', 'error': str(e)}
        
        # LightGBM
        try:
            import lightgbm as lgb
            if market_type in ['moneyline', 'spread']:
                model = lgb.LGBMClassifier(n_estimators=200, max_depth=6, learning_rate=0.1, random_state=42, verbose=-1)
            else:
                model = lgb.LGBMRegressor(n_estimators=200, max_depth=6, learning_rate=0.1, random_state=42, verbose=-1)
            
            model.fit(X_train, y_train)
            model_results['lightgbm'] = {'status': 'success', 'model': model}
        except Exception as e:
            logger.error(f"LightGBM training failed: {e}")
            model_results['lightgbm'] = {'status': 'failed', 'error': str(e)}
        
        # Random Forest
        try:
            from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
            if market_type in ['moneyline', 'spread']:
                model = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42)
            else:
                model = RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42)
            
            model.fit(X_train, y_train)
            model_results['random_forest'] = {'status': 'success', 'model': model}
        except Exception as e:
            logger.error(f"Random Forest training failed: {e}")
            model_results['random_forest'] = {'status': 'failed', 'error': str(e)}
        
        return model_results
    
    async def _comprehensive_model_evaluation(self, model_results: Dict, X_test: np.ndarray, 
                                            y_test: np.ndarray, market_type: str) -> Dict[str, Any]:
        """Comprehensive model evaluation"""
        evaluations = {}
        
        for model_name, result in model_results.items():
            if result['status'] == 'success':
                try:
                    model = result['model']
                    y_pred = model.predict(X_test)
                    
                    if market_type in ['moneyline', 'spread']:  # Classification
                        evaluations[model_name] = {
                            'accuracy': float(accuracy_score(y_test, y_pred)),
                            'precision': float(precision_score(y_test, y_pred, average='weighted', zero_division=0)),
                            'recall': float(recall_score(y_test, y_pred, average='weighted', zero_division=0)),
                            'f1': float(f1_score(y_test, y_pred, average='weighted', zero_division=0))
                        }
                    else:  # Regression
                        from sklearn.metrics import mean_absolute_error, mean_squared_error
                        evaluations[model_name] = {
                            'mae': float(mean_absolute_error(y_test, y_pred)),
                            'rmse': float(np.sqrt(mean_squared_error(y_test, y_pred))),
                            'mape': float(np.mean(np.abs((y_test - y_pred) / y_test)) * 100) if np.all(y_test != 0) else float('inf')
                        }
                except Exception as e:
                    logger.error(f"Error evaluating {model_name}: {e}")
                    evaluations[model_name] = {'error': str(e)}
            else:
                evaluations[model_name] = {'error': result.get('error', 'Training failed')}
        
        return evaluations
    
    async def _optimize_ensemble_weights(self, evaluations: Dict[str, Any]) -> Dict[str, float]:
        """Optimize ensemble weights based on comprehensive evaluation"""
        weights = {}
        total_score = 0
        
        for model_name, metrics in evaluations.items():
            if 'error' not in metrics:
                # Use F1 score for classification, negative MAE for regression
                if 'f1' in metrics:
                    score = metrics['f1'] + metrics.get('accuracy', 0) * 0.5
                elif 'mae' in metrics:
                    score = 1 / (1 + metrics['mae'])  # Convert MAE to score
                else:
                    score = 0.5  # Default score
                
                weights[model_name] = score
                total_score += score
        
        # Normalize weights
        if total_score > 0:
            weights = {k: v / total_score for k, v in weights.items()}
        else:
            # Equal weights if no valid scores
            valid_models = [k for k, v in evaluations.items() if 'error' not in v]
            if valid_models:
                weights = {k: 1/len(valid_models) for k in valid_models}
        
        return weights
    
    async def _save_training_artifacts(self, sport_key: str, market_type: str, 
                                      model_results: Dict, evaluation_results: Dict, 
                                      optimized_weights: Dict) -> None:
        """Save all training artifacts"""
        try:
            model_key = f"{sport_key}_{market_type}"
            
            # Save models
            models_data = {
                'models': {},
                'evaluations': evaluation_results,
                'weights': optimized_weights,
                'training_timestamp': datetime.utcnow().isoformat()
            }
            
            for model_name, result in model_results.items():
                if result['status'] == 'success':
                    models_data['models'][model_name] = result['model']
            
            # Save to joblib
            joblib.dump(models_data, self.models_dir / f"{model_key}_ensemble.joblib")
            
            # Save performance metrics
            performance_data = {
                'recent_metrics': evaluation_results,
                'baseline_metrics': evaluation_results,  # Update baseline if this is first training
                'last_updated': datetime.utcnow().isoformat()
            }
            
            with open(self.models_dir / f"{model_key}_performance.json", 'w') as f:
                json.dump(performance_data, f, indent=2)
            
            logger.info(f"Training artifacts saved for {model_key}")
            
        except Exception as e:
            logger.error(f"Error saving training artifacts: {e}")
    
    def get_training_history(self, sport_key: Optional[str] = None, 
                           market_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get training history with optional filtering"""
        history = self.training_history
        
        if sport_key:
            history = [h for h in history if h.get('sport_key') == sport_key]
        
        if market_type:
            history = [h for h in history if h.get('market_type') == market_type]
        
        return history[-50:]  # Return last 50 training sessions
    
    async def request_manual_retrain(self, sport_key: str, market_type: str) -> Dict[str, Any]:
        """Request manual retraining by creating a flag file"""
        try:
            flag_file = self.models_dir / f"{sport_key}_{market_type}_retrain.flag"
            flag_file.touch()
            
            return {
                'status': 'success',
                'message': f'Manual retraining requested for {sport_key} - {market_type}',
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

    async def check_and_trigger_retraining(self) -> Dict[str, Any]:
        """
        Check all models and trigger retraining if needed.
        This is the main entry point called by the auto-training loop.
        """
        results = []
        
        # Define all sport/market combinations to check
        sport_market_combinations = [
            ('basketball_nba', 'moneyline'),
            ('basketball_nba', 'spread'),
            ('basketball_nba', 'total'),
            ('americanfootball_nfl', 'moneyline'),
            ('americanfootball_nfl', 'spread'),
            ('americanfootball_nfl', 'total'),
            ('icehockey_nhl', 'moneyline'),
            ('icehockey_nhl', 'spread'),
            ('icehockey_nhl', 'total'),
            ('baseball_mlb', 'moneyline'),
            ('baseball_mlb', 'spread'),
            ('baseball_mlb', 'total'),
        ]
        
        for sport_key, market_type in sport_market_combinations:
            try:
                # Check if we have enough data to retrain
                # For now, just check time-based and manual triggers
                should_retrain = False
                reasons = []
                
                # Time-based trigger
                if self.last_training is None:
                    should_retrain = True
                    reasons.append("Initial training required")
                elif datetime.utcnow() - self.last_training >= self.retrain_interval:
                    should_retrain = True
                    reasons.append(f"Scheduled retraining (interval: {self.retrain_interval.days} days)")
                
                # Performance degradation trigger
                if await self._check_performance_degradation(sport_key, market_type):
                    should_retrain = True
                    reasons.append("Model performance degradation detected")
                
                # Manual override trigger
                if await self._check_manual_retrain_flag(sport_key, market_type):
                    should_retrain = True
                    reasons.append("Manual retraining requested")
                
                if should_retrain:
                    # Create dummy training data for now - in production this would come from database
                    # This is a placeholder that will trigger the retraining logic
                    logger.info(f"Retraining needed for {sport_key} - {market_type}: {'; '.join(reasons)}")
                    
                    result = {
                        'sport_key': sport_key,
                        'market_type': market_type,
                        'status': 'retrain_needed',
                        'reasons': reasons,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    results.append(result)
                else:
                    results.append({
                        'sport_key': sport_key,
                        'market_type': market_type,
                        'status': 'no_retrain_needed',
                        'timestamp': datetime.utcnow().isoformat()
                    })
                    
            except Exception as e:
                logger.error(f"Error checking retraining for {sport_key} - {market_type}: {e}")
                results.append({
                    'sport_key': sport_key,
                    'market_type': market_type,
                    'status': 'error',
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                })
        
        # Update last training time to prevent continuous retraining attempts
        if any(r['status'] == 'retrain_needed' for r in results):
            self.last_training = datetime.utcnow()
        
        return {
            'status': 'completed',
            'checks_performed': len(sport_market_combinations),
            'results': results,
            'timestamp': datetime.utcnow().isoformat()
        }
