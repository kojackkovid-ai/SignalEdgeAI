from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import logging
import asyncio
from app.services.ml_service import MLService
from app.services.espn_prediction_service import ESPNPredictionService

from app.routes import predictions, auth, users, models as model_routes, payment
from app.database import init_db

# Logging
logging.basicConfig(level=logging.INFO)
# Trigger reload for API key update
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Sports Prediction Platform API",
    description="Industry-leading ML-powered sports prediction API",
    version="1.0.0"
)

async def run_auto_training():
    """Background task to retrain models daily"""
    # Initial delay to let server start up
    await asyncio.sleep(60) 
    
    while True:
        try:
            logger.info("AUTO-TRAIN: Starting daily training sequence...")
            
            espn_service = ESPNPredictionService()
            ml_service = MLService()
            await ml_service.initialize()
            
            # Fetch data (last 30 days)
            logger.info("AUTO-TRAIN: Fetching historical data...")
            training_data = await espn_service.get_historical_data(days_back=30)
            
            if training_data:
                logger.info(f"AUTO-TRAIN: Training on {len(training_data)} games...")
                success = await ml_service.train_models(training_data)
                if success:
                    logger.info("AUTO-TRAIN: ✅ Training completed successfully")
                else:
                    logger.error("AUTO-TRAIN: ❌ Training failed")
            else:
                logger.warning("AUTO-TRAIN: No data found")
                
        except Exception as e:
            logger.error(f"AUTO-TRAIN Error: {e}")
            
        # Wait 24 hours
        logger.info("AUTO-TRAIN: Sleeping for 24 hours...")
        await asyncio.sleep(24 * 60 * 60)

# Initialize database tables on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    from app.config import settings
    logger.info(f"Starting up... API Key: {settings.odds_api_key[:5]}...")
    try:
        await init_db()
        logger.info("✓ Database tables initialized")
        
        # Start Auto-Train Background Task
        asyncio.create_task(run_auto_training())
        logger.info("✓ Auto-Training task scheduled")
        
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

# Security - add before CORS
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.example.com"]
)

# CORS - add last so it's processed first
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(payment.router, prefix="/api/payment", tags=["Payment"])
app.include_router(predictions.router, prefix="/api/predictions", tags=["Predictions"])
app.include_router(model_routes.router, prefix="/api/models", tags=["Models"])

@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "online",
        "service": "Sports Prediction Platform",
        "version": "1.0.0",
        "timestamp": __import__("datetime").datetime.utcnow().isoformat()
    }

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "db": "connected"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
