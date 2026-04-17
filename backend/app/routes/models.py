from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.auth_service import AuthService
from app.services.ml_service import MLService
from app.services.espn_prediction_service import ESPNPredictionService
from pydantic import BaseModel
from typing import List


# Lazy-initialized services to prevent import hangs
_auth_service = None

def get_auth_service():
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service


router = APIRouter()
# Lazy-loaded
auth_service = None

class ModelPerformance(BaseModel):
    name: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    last_retrain: str

class ModelStatus(BaseModel):
    models: List[ModelPerformance]
    ensemble_score: float
    last_update: str
    auto_training_enabled: bool

@router.get("/status", response_model=ModelStatus)
async def get_models_status(
    current_user_id: str = Depends(lambda: get_auth_service().get_current_user()),
    db: AsyncSession = Depends(get_db)
):
    """Get ML models status"""
    # Return placeholder data as we don't have active trained models yet
    return {
        "models": [],
        "ensemble_score": 0.0,
        "last_update": "N/A",
        "auto_training_enabled": False
    }

@router.get("/performance/{model_name}")
async def get_model_performance(
    model_name: str,
    current_user_id: str = Depends(lambda: get_auth_service().get_current_user()),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed model performance"""
    return {
        "name": model_name,
        "metrics": {
            "accuracy": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "f1_score": 0.0,
            "auc_roc": 0.0,
            "log_loss": 0.0
        },
        "recent_performance": {
            "last_7_days": 0.0,
            "last_30_days": 0.0,
            "last_90_days": 0.0
        }
    }

@router.post("/retrain/{model_name}")
async def trigger_model_retrain(
    model_name: str,
    current_user_id: str = Depends(lambda: get_auth_service().get_current_user()),
    db: AsyncSession = Depends(get_db)
):
    """Trigger manual model retraining"""
    try:
        # Check if user is admin (optional, skipping for now)
        
        # Lazy-loaded
        
        espn_service = None
        ml_service = MLService()
        await ml_service.initialize() 
        
        # Fetch historical data (last 30 days)
        # This might take a while, so in production use background tasks
        training_data = await get_espn_service().get_historical_data(days_back=30)
        
        if not training_data:
             return {
                "message": "No historical data found for training",
                "status": "failed"
            }
            
        # Train models
        success = await ml_service.train_models(training_data)
        
        if success:
            return {
                "message": f"Successfully retrained models on {len(training_data)} historical games",
                "status": "success",
                "estimated_time": "Completed"
            }
        else:
             return {
                "message": "Training failed",
                "status": "failed"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/backtest/{model_name}")
async def get_model_backtest(
    model_name: str,
    start_date: str = "2024-01-01",
    end_date: str = "2024-01-24",
    current_user_id: str = Depends(lambda: get_auth_service().get_current_user()),
    db: AsyncSession = Depends(get_db)
):
    """Get model backtest results"""
    return {
        "model": model_name,
        "period": f"{start_date} to {end_date}",
        "total_predictions": 0,
        "wins": 0,
        "losses": 0,
        "pushes": 0,
        "win_rate": 0.0,
        "roi": 0.0,
        "max_drawdown": 0.0
    }
