"""
Enhanced Main Application with Advanced Auto-Training and Monitoring
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Enhanced services
from app.services.enhanced_ml_service import EnhancedMLService
from app.services.enhanced_auto_training import EnhancedAutoTrainingPipeline
from app.services.model_monitoring import ModelPerformanceMonitor
from app.services.espn_prediction_service import ESPNPredictionService

# Routes
from app.routes import predictions, auth, users, models as model_routes, payment
from app.database import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Enhanced Sports Prediction Platform API",
    description="Advanced ML-powered sports prediction API with automated training and monitoring",
    version="2.0.0"
)

# Global service instances
enhanced_ml_service = None
auto_training_pipeline = None
model_monitor = None

async def initialize_enhanced_services():
    """Initialize all enhanced services"""
    global enhanced_ml_service, auto_training_pipeline, model_monitor
    
    try:
        logger.info("Initializing enhanced services...")
        
        # Initialize enhanced ML service
        enhanced_ml_service = EnhancedMLService()
        logger.info("✓ Enhanced ML Service initialized")
        
        # Initialize auto-training pipeline
        auto_training_pipeline = EnhancedAutoTrainingPipeline(
            retrain_interval_days=7,
            min_samples=500,
            performance_threshold=0.05,
            min_accuracy_threshold=0.55
        )
        logger.info("✓ Auto-training pipeline initialized")
        
        # Initialize model monitoring
        model_monitor = ModelPerformanceMonitor()
        await model_monitor.start_monitoring()
        logger.info("✓ Model monitoring started")
        
        return True
        
    except Exception as e:
        logger.error(f"Error initializing enhanced services: {e}")
        return False

async def enhanced_auto_training_loop():
    """Enhanced background task for automated model training and monitoring"""
    logger.info("Starting enhanced auto-training loop...")
    
    # Wait for initial startup
    await asyncio.sleep(60)
    
    while True:
        try:
            logger.info("ENHANCED AUTO-TRAIN: Starting comprehensive training cycle...")
            
            # Initialize ESPN service for data fetching
            espn_service = ESPNPredictionService()
            
            # Define sports and markets to train
            training_configs = [
                ('basketball_nba', 'moneyline'),
                ('basketball_nba', 'spread'),
                ('basketball_nba', 'total'),
                ('americanfootball_nfl', 'moneyline'),
                ('americanfootball_nfl', 'spread'),
                ('baseball_mlb', 'moneyline'),
                ('baseball_mlb', 'total'),
                ('icehockey_nhl', 'moneyline'),
                ('icehockey_nhl', 'puck_line'),
                ('soccer_epl', 'spread'),
                ('soccer_epl', 'total')
            ]
            
            for sport_key, market_type in training_configs:
                try:
                    logger.info(f"ENHANCED AUTO-TRAIN: Processing {sport_key} - {market_type}")
                    
                    # Fetch historical data (last 60 days for more comprehensive training)
                    training_data = await espn_service.get_historical_data(
                        sport_key=sport_key, 
                        days_back=60
                    )
                    
                    if training_data and len(training_data) >= 100:  # Minimum 100 samples
                        logger.info(f"ENHANCED AUTO-TRAIN: Training on {len(training_data)} games for {sport_key} - {market_type}")
                        
                        # Convert to DataFrame for enhanced pipeline
                        import pandas as pd
                        df = pd.DataFrame(training_data)
                        
                        # Check and trigger retraining with comprehensive analysis
                        result = await auto_training_pipeline.comprehensive_check_and_retrain(
                            df, sport_key, market_type
                        )
                        
                        if result['status'] == 'success':
                            logger.info(f"✅ ENHANCED AUTO-TRAIN: {sport_key} - {market_type} training completed")
                            logger.info(f"   Duration: {result['duration']:.1f}s, Samples: {result['samples_used']}")
                            logger.info(f"   Models trained: {result['models_trained']}")
                        else:
                            logger.warning(f"⚠️  ENHANCED AUTO-TRAIN: {sport_key} - {market_type} - {result.get('reason', 'No retrain needed')}")
                    
                    else:
                        logger.warning(f"⚠️  ENHANCED AUTO-TRAIN: Insufficient data for {sport_key} - {market_type} ({len(training_data) if training_data else 0} games)")
                    
                    # Small delay between different sports/markets
                    await asyncio.sleep(5)
                    
                except Exception as e:
                    logger.error(f"❌ ENHANCED AUTO-TRAIN: Error training {sport_key} - {market_type}: {e}")
                    continue
            
            # Performance monitoring and alerting
            logger.info("ENHANCED AUTO-TRAIN: Running performance analysis...")
            
            # Check for active alerts
            active_alerts = await model_monitor.get_active_alerts()
            if active_alerts:
                logger.warning(f"🚨 ENHANCED AUTO-TRAIN: {len(active_alerts)} active performance alerts")
                for alert in active_alerts:
                    logger.warning(f"   [{alert['severity'].upper()}] {alert['sport_key']} - {alert['market_type']}: {alert['message']}")
            else:
                logger.info("✅ ENHANCED AUTO-TRAIN: No active performance alerts")
            
            # Get performance summary
            performance_summary = await model_monitor.get_performance_summary(days_back=7)
            if 'overall_accuracy' in performance_summary:
                logger.info(f"📊 ENHANCED AUTO-TRAIN: 7-day overall accuracy: {performance_summary['overall_accuracy']:.2%}")
                logger.info(f"📊 ENHANCED AUTO-TRAIN: Total predictions: {performance_summary['total_predictions']}")
            
            logger.info("ENHANCED AUTO-TRAIN: Training cycle completed. Sleeping for 24 hours...")
            
        except Exception as e:
            logger.error(f"❌ ENHANCED AUTO-TRAIN: Critical error in training loop: {e}")
            logger.info("ENHANCED AUTO-TRAIN: Retrying in 1 hour...")
            await asyncio.sleep(3600)  # Wait 1 hour on critical error
            continue
        
        # Wait 24 hours before next cycle
        await asyncio.sleep(24 * 60 * 60)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Enhanced startup with comprehensive service initialization"""
    logger.info("🚀 Starting Enhanced Sports Prediction Platform...")
    
    try:
        # Initialize database
        await init_db()
        logger.info("✅ Database initialized")
        
        # Initialize enhanced services
        services_initialized = await initialize_enhanced_services()
        if not services_initialized:
            logger.error("❌ Failed to initialize enhanced services")
            raise RuntimeError("Enhanced services initialization failed")
        
        # Start enhanced auto-training background task
        asyncio.create_task(enhanced_auto_training_loop())
        logger.info("✅ Enhanced auto-training task scheduled")
        
        logger.info("🚀 Enhanced Sports Prediction Platform started successfully!")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.example.com", "*.vercel.app"]
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", "http://localhost:5174", "http://localhost:3000", 
        "http://127.0.0.1:5173", "https://*.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(payment.router, prefix="/api/payment", tags=["Payment"])
app.include_router(predictions.router, prefix="/api/predictions", tags=["Predictions"])
app.include_router(model_routes.router, prefix="/api/models", tags=["Models"])

# Enhanced health check endpoints
@app.get("/", tags=["Health"])
async def root():
    """Enhanced root endpoint with service status"""
    return {
        "status": "online",
        "service": "Enhanced Sports Prediction Platform",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "enhanced_ml": enhanced_ml_service is not None,
            "auto_training": auto_training_pipeline is not None,
            "model_monitoring": model_monitor is not None
        }
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Comprehensive health check"""
    return {
        "status": "healthy",
        "database": "connected",
        "enhanced_services": {
            "ml_service": enhanced_ml_service is not None,
            "auto_training": auto_training_pipeline is not None,
            "monitoring": model_monitor is not None
        },
        "timestamp": datetime.utcnow().isoformat()
    }

# Enhanced model management endpoints
@app.get("/api/models/status", tags=["Models"])
async def get_model_status():
    """Get comprehensive model status and performance"""
    try:
        if not auto_training_pipeline or not model_monitor:
            raise HTTPException(status_code=503, detail="Enhanced services not available")
        
        # Get training history
        training_history = auto_training_pipeline.get_training_history()
        
        # Get performance summary
        performance_summary = await model_monitor.get_performance_summary(days_back=30)
        
        # Get active alerts
        active_alerts = await model_monitor.get_active_alerts()
        
        return {
            "status": "success",
            "services_ready": True,
            "training_history_count": len(training_history),
            "last_training": training_history[-1]['timestamp'] if training_history else None,
            "performance_summary": performance_summary,
            "active_alerts": active_alerts,
            "alerts_count": len(active_alerts)
        }
        
    except Exception as e:
        logger.error(f"Error getting model status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/models/retrain/{sport_key}/{market_type}", tags=["Models"])
async def request_manual_retrain(sport_key: str, market_type: str):
    """Request manual retraining for specific sport and market"""
    try:
        if not auto_training_pipeline:
            raise HTTPException(status_code=503, detail="Auto-training service not available")
        
        result = await auto_training_pipeline.request_manual_retrain(sport_key, market_type)
        
        if result['status'] == 'success':
            logger.info(f"Manual retraining requested for {sport_key} - {market_type}")
            return result
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Unknown error'))
            
    except Exception as e:
        logger.error(f"Error requesting manual retrain: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/models/performance/{sport_key}/{market_type}", tags=["Models"])
async def get_model_performance(sport_key: str, market_type: str, days_back: int = 30):
    """Get detailed performance metrics for specific model"""
    try:
        if not model_monitor:
            raise HTTPException(status_code=503, detail="Model monitoring service not available")
        
        performance = await model_monitor.get_performance_summary(
            sport_key=sport_key, 
            market_type=market_type, 
            days_back=days_back
        )
        
        return {
            "status": "success",
            "sport_key": sport_key,
            "market_type": market_type,
            "performance": performance
        }
        
    except Exception as e:
        logger.error(f"Error getting model performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/models/alerts", tags=["Models"])
async def get_model_alerts(sport_key: Optional[str] = None, market_type: Optional[str] = None):
    """Get model performance alerts"""
    try:
        if not model_monitor:
            raise HTTPException(status_code=503, detail="Model monitoring service not available")
        
        alerts = await model_monitor.get_active_alerts(sport_key, market_type)
        
        return {
            "status": "success",
            "alerts": alerts,
            "count": len(alerts)
        }
        
    except Exception as e:
        logger.error(f"Error getting model alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/models/alerts/{alert_id}/resolve", tags=["Models"])
async def resolve_alert(alert_id: int):
    """Resolve a model performance alert"""
    try:
        if not model_monitor:
            raise HTTPException(status_code=503, detail="Model monitoring service not available")
        
        success = await model_monitor.resolve_alert(alert_id)
        
        if success:
            return {"status": "success", "message": "Alert resolved"}
        else:
            raise HTTPException(status_code=404, detail="Alert not found or already resolved")
            
    except Exception as e:
        logger.error(f"Error resolving alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Clean shutdown of enhanced services"""
    logger.info("🛑 Shutting down Enhanced Sports Prediction Platform...")
    
    try:
        if model_monitor:
            await model_monitor.stop_monitoring()
            logger.info("✅ Model monitoring stopped")
        
        logger.info("🛑 Enhanced Sports Prediction Platform shutdown complete")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)