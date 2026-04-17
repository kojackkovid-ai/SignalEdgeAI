import pytest
import numpy as np
import pandas as pd
from unittest.mock import MagicMock, patch
from app.services.enhanced_ml_service import EnhancedMLService

@pytest.fixture
def ml_service():
    return EnhancedMLService(models_dir="tests/mock_models")

@pytest.fixture
def sample_features():
    # Create sample features matching the expected input shape
    return pd.DataFrame({
        'feature1': np.random.rand(10),
        'feature2': np.random.rand(10),
        'feature3': np.random.rand(10)
    })

@pytest.mark.asyncio
async def test_predict_ensemble(ml_service, sample_features):
    # Mock the individual models
    mock_xgb = MagicMock()
    mock_xgb.predict_proba.return_value = np.array([[0.3, 0.7]] * 10)
    
    mock_lgb = MagicMock()
    mock_lgb.predict_proba.return_value = np.array([[0.4, 0.6]] * 10)
    
    mock_rf = MagicMock()
    mock_rf.predict_proba.return_value = np.array([[0.2, 0.8]] * 10)
    
    # Patch the loaded models
    with patch.object(ml_service, 'models', {
        'basketball_nba_moneyline_xgboost': mock_xgb,
        'basketball_nba_moneyline_lightgbm': mock_lgb,
        'basketball_nba_moneyline_random_forest': mock_rf
    }):
        # Test prediction
        prediction = await ml_service.predict('basketball_nba', 'moneyline', sample_features)
        
        assert 'probability' in prediction
        assert 'confidence' in prediction
        assert 'model_contributions' in prediction
        assert 0 <= prediction['probability'] <= 1
        assert 0 <= prediction['confidence'] <= 1

@pytest.mark.asyncio
async def test_train_ensemble(ml_service, sample_features):
    # Mock the training process
    labels = np.random.randint(0, 2, 10)
    
    with patch('xgboost.XGBClassifier') as mock_xgb_cls, \
         patch('lightgbm.LGBMClassifier') as mock_lgb_cls, \
         patch('sklearn.ensemble.RandomForestClassifier') as mock_rf_cls:
             
        mock_xgb_instance = mock_xgb_cls.return_value
        mock_lgb_instance = mock_lgb_cls.return_value
        mock_rf_instance = mock_rf_cls.return_value
        
        metrics = await ml_service.train_ensemble('basketball_nba', 'moneyline', sample_features, labels)
        
        assert 'xgboost' in metrics
        assert 'lightgbm' in metrics
        assert 'random_forest' in metrics
        
        mock_xgb_instance.fit.assert_called()
        mock_lgb_instance.fit.assert_called()
        mock_rf_instance.fit.assert_called()

def test_feature_importance(ml_service):
    # Mock model with feature importances
    mock_model = MagicMock()
    mock_model.feature_importances_ = np.array([0.1, 0.2, 0.7])
    
    with patch.object(ml_service, 'models', {'basketball_nba_moneyline_xgboost': mock_model}):
        importance = ml_service.get_feature_importance('basketball_nba', 'moneyline')
        
        assert 'xgboost' in importance
        assert len(importance['xgboost']) == 3
