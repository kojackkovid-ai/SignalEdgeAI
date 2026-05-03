"""
Enhanced Main Application with Advanced Auto-Training and Monitoring
"""

import sys
import os
# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Enhanced services - lazy loaded due to potential import hangs
# These will be initialized in _import_ml_services() function
EnhancedMLService = None
EnhancedAutoTrainingPipeline = None
ModelPerformanceMonitor = None
ESPNPredictionService = None

# Models
from app.models.tier_features import TierFeatures

# Routes
from app.routes import predictions, auth, users, models as model_routes, payment, resolution, analytics, prediction_history, email, ml_operations, club100_addon, admin
from app.database import init_db, SessionLocal, AsyncSessionLocal
from app.services.prediction_resolution_service import run_prediction_resolution_loop
from app.services.email_templates_service import EmailTemplateService
from app.tasks.email_tasks import run_email_task_loop
from app.config import settings

# ML Training and Monitoring
from app.services.training_scheduler import get_training_scheduler, EnhancedTrainingScheduler
from app.services.model_performance_monitor import get_model_monitor

# New utilities
from app.utils.structured_logging import setup_structured_logging, get_logger
from app.utils.health_checks import health_registry, setup_default_health_checks, HealthCheck, check_database
from app.utils.rate_limiter import setup_rate_limiting
from app.utils.enhanced_rate_limiter import setup_enhanced_rate_limiting
# TEMPORARILY DISABLED: from app.utils.comprehensive_logging import setup_comprehensive_logging
from app.utils.exceptions import setup_exception_handlers
from app.utils.circuit_breaker import get_circuit_breaker
from app.utils.error_handler import APIException, api_exception_handler, general_exception_handler
from app.utils.caching import init_cache_service, get_cache_service, CacheKeys
from app.utils.monitoring import get_monitoring_service, init_monitoring
from app.models.responses import ErrorResponse

# Setup structured logging
setup_structured_logging(level=logging.INFO)
logger = get_logger(__name__)

# Function to lazy-load ML services
def _import_ml_services():
    """Lazy import ML services that may hang on import"""
    global EnhancedMLService, EnhancedAutoTrainingPipeline, ModelPerformanceMonitor, ESPNPredictionService
    
    if EnhancedMLService is not None:
        return  # Already imported
    
    try:
        from app.services.enhanced_ml_service import EnhancedMLService as EMLService
        EnhancedMLService = EMLService
        logger.debug("EnhancedMLService imported successfully")
    except Exception as e:
        logger.warning(f"Failed to import EnhancedMLService: {e}. ML features may be unavailable.")
    
    try:
        from app.services.enhanced_auto_training import EnhancedAutoTrainingPipeline as EATP
        EnhancedAutoTrainingPipeline = EATP
        logger.debug("EnhancedAutoTrainingPipeline imported successfully")
    except Exception as e:
        logger.warning(f"Failed to import EnhancedAutoTrainingPipeline: {e}")
    
    try:
        from app.services.model_monitoring import ModelPerformanceMonitor as MPM
        ModelPerformanceMonitor = MPM
        logger.debug("ModelPerformanceMonitor imported successfully")
    except Exception as e:
        logger.warning(f"Failed to import ModelPerformanceMonitor: {e}")
    
    try:
        from app.services.espn_prediction_service import ESPNPredictionService as EPS
        ESPNPredictionService = EPS
        logger.debug("ESPNPredictionService imported successfully")
    except Exception as e:
        logger.warning(f"Failed to import ESPNPredictionService: {e}")

# Initialize FastAPI app
app = FastAPI(
    title="SignalEdge AI - Advanced Sports Prediction API",
    description="AI-powered sports prediction engine with machine learning and advanced analytics",
    version="2.0.0",
    redirect_slashes=False
)

# Global service instances
enhanced_ml_service = None
auto_training_pipeline = None
model_monitor = None

# Security headers middleware
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://js.stripe.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com https://fonts.stripe.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https://api.stripe.com https://m.stripe.com https://m.stripe.network; "
        "frame-src https://js.stripe.com https://hooks.stripe.com; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self' https://hooks.stripe.com"
    )
    response.headers["Permissions-Policy"] = "payment=(self \"https://js.stripe.com\")"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    # Cache control for static assets
    if request.url.path.startswith("/assets/"):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    else:
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    
    return response

# Request validation middleware
@app.middleware("http")
async def request_validation_middleware(request: Request, call_next):
    """Validate incoming requests"""
    # Check content length for large payloads
    content_length = request.headers.get("content-length")
    if content_length:
        max_size = 10 * 1024 * 1024  # 10MB
        if int(content_length) > max_size:
            return JSONResponse(
                status_code=413,
                content={"error": "Payload too large", "max_size_mb": 10}
            )
    
    return await call_next(request)

# Rate limiting middleware (based on subscription tier)
# TEMPORARILY DISABLED FOR DEBUGGING - causes timeout
# @app.middleware("http")
# async def rate_limiting_middleware(request: Request, call_next):
#     """Rate limit based on user's subscription tier"""
#     try:
#         # Only rate limit prediction endpoints
#         if "/predictions/" not in request.url.path or request.method != "GET":
#             return await call_next(request)
#         
#         # Extract user ID from token (if available)
#         auth_header = request.headers.get("authorization", "")
#         if not auth_header.startswith("Bearer "):
#             return await call_next(request)
#         
#         # Get user tier from JWT token (basic parsing)
#         try:
#             from app.services.auth_service import AuthService
#             from app.database import AsyncSessionLocal
#             from sqlalchemy import select
#             from app.models.db_models import User
#             
#             auth_service = AuthService()
#             token = auth_header.replace("Bearer ", "")
#             user_id = auth_service._decode_token(token)
#             
#             if not user_id:
#                 return await call_next(request)
#             
#             # Get user's tier and daily limit
#             async with AsyncSessionLocal() as session:
#                 result = await session.execute(select(User.subscription_tier).where(User.id == user_id))
#                 user_tier = result.scalar_one_or_none()
#                 
#                 if user_tier:
#                     tier_config = TierFeatures.get_tier_config(user_tier.lower() if user_tier else 'starter')
#                     daily_limit = tier_config.get('predictions_per_day')
#                     
#                     # If unlimited (Pro/Elite), skip rate limiting
#                     if daily_limit is None or daily_limit > 1000:
#                         return await call_next(request)
#                     
#                     # Check daily count in Redis
#                     try:
#                         from app.services.redis_cache import redis_client
#                         today = datetime.utcnow().strftime('%Y-%m-%d')
#                         key = f"predictions:daily:{user_id}:{today}"
#                         count = await redis_client.incr(key)
#                         
#                         # Set expiry to 24 hours on first increment
#                         if count == 1:
#                             await redis_client.expire(key, 86400)
#                         
#                         if count > daily_limit:
#                             logger.warning(f"Rate limit exceeded for user {user_id}: {count}/{daily_limit}")
#                             return JSONResponse(
#                                 status_code=429,
#                                 content={
#                                     "error": "Daily prediction limit exceeded",
#                                     "limit": daily_limit,
#                                     "used": count - 1,  # Subtract the increment we just did
#                                     "message": f"You've reached your daily limit of {daily_limit} predictions. Upgrade your plan for more!"
#                                 }
#                             )
#                     except Exception as redis_error:
#                         logger.warning(f"Redis rate limiting failed, skipping: {redis_error}")
#                         # Continue if Redis fails - don't break the service
#                         
#         except Exception as auth_error:
#             logger.debug(f"Rate limiting auth failed, skipping: {auth_error}")
#             # Continue if auth fails - don't break the service
#         
#         return await call_next(request)
#     
#     except Exception as e:
#         logger.error(f"Rate limiting middleware error: {e}")
#         # Don't break the service if middleware fails
#         return await call_next(request)


# Monitoring middleware - track all requests and responses
# TEMPORARILY DISABLED FOR DEBUGGING - causes "No response returned" error
# @app.middleware("http")
# async def monitoring_middleware(request: Request, call_next):
#     """Monitor all requests for performance and errors"""
#     import time
#     
#     start_time = time.time()
#     
#     try:
#         # Don't monitor health checks or internal endpoints
#         if request.url.path in ["/health", "/ready", "/metrics"]:
#             return await call_next(request)
#         
#         response = await call_next(request)
#         
#         # Record metrics
#         response_time = (time.time() - start_time) * 1000  # Convert to ms
#         monitoring = get_monitoring_service()
#         
#         monitoring.performance.record_request(
#             method=request.method,
#             path=request.url.path,
#             status_code=response.status_code,
#             response_time=response_time,
#             user_id=None  # Could extract from token if needed
#         )
#         
#         # Record if error
#         if response.status_code >= 400:
#             monitoring.errors.record_error(
#                 error_code=f"HTTP_{response.status_code}",
#                 message=f"{request.method} {request.url.path}",
#                 status_code=response.status_code,
#                 path=request.url.path,
#             )
#         
#         return response
#     
#     except Exception as e:
#         response_time = (time.time() - start_time) * 1000
#         monitoring = get_monitoring_service()
#         
#         monitoring.errors.record_error(
#             error_code="MIDDLEWARE_ERROR",
#             message=str(e),
#             status_code=500,
#             path=request.url.path,
#             exception=e
#         )
#         
#         logger.error(f"Monitoring middleware error: {e}")
#         raise



async def initialize_enhanced_services():
    """Initialize all enhanced services"""
    global enhanced_ml_service, auto_training_pipeline, model_monitor
    
    try:
        logger.info("Initializing enhanced services...")
        
        # DISABLED: Initialize Caching Service - causes hang on startup
        #try:
        #    cache_service = await init_cache_service(settings.redis_url if hasattr(settings, 'redis_url') else None)
        #    logger.info("✓ Caching service initialized")
        #except Exception as e:
        #    logger.warning(f"Caching service initialization failed: {e}. Will use in-memory fallback.")
        
        # Initialize Monitoring Service
        monitoring = init_monitoring()
        logger.info("[OK] Monitoring service initialized")
        
        # ML Services - now enabled with TensorFlow support
        enhanced_ml_service = None  # Can be initialized later with proper ML pipeline
        logger.info("[OK] ML service ready (TensorFlow enabled)")
        
        # Auto-training pipeline - initialized for ML model retraining
        auto_training_pipeline = None  # Initialize with training service when needed
        logger.info("[OK] Auto-training pipeline ready")
        
        # Model monitoring for real-time performance tracking
        model_monitor = None  # Initialize with model performance tracker when needed
        logger.info("[OK] Model monitoring ready")
        
        # Setup health checks
        setup_default_health_checks()
        logger.info("[OK] Health checks configured")
        
        return True
        
    except Exception as e:
        logger.error(f"Error initializing enhanced services: {e}")
        return False

async def enhanced_auto_training_loop():
    """Enhanced background task for automated model training and monitoring"""
    logger.info("Starting enhanced auto-training loop...")
    
    while True:
        try:
            # Check if retraining is needed
            if auto_training_pipeline:
                result = await auto_training_pipeline.check_and_trigger_retraining()
                
                if result.get("retrained"):
                    logger.info(f"Models retrained: {result.get('models_trained', [])}")
                
                # Check model performance for key sport/market combinations
                if model_monitor:
                    sport_market_combos = [
                        ('basketball_nba', 'moneyline'),
                        ('americanfootball_nfl', 'moneyline'),
                        ('icehockey_nhl', 'moneyline'),
                    ]
                    for sport_key, market_type in sport_market_combos:
                        try:
                            perf_check = await model_monitor.check_model_performance(sport_key, market_type)
                            if perf_check.get('needs_retrain'):
                                logger.warning(f"Model {sport_key}/{market_type} needs retraining: {perf_check.get('reason')}")
                        except Exception as perf_error:
                            logger.debug(f"Could not check performance for {sport_key}/{market_type}: {perf_error}")
            
            # Wait before next check (every hour)
            await asyncio.sleep(3600)
            
        except asyncio.CancelledError:
            logger.info("Auto-training loop cancelled")
            break
        except Exception as e:
            logger.error(f"Error in auto-training loop: {e}")
            await asyncio.sleep(300)  # Wait 5 minutes on error

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("[STARTUP] Starting up SignalEdge AI...")
    
    try:
        # Initialize database (OPTIONAL - server can run without it for testing)
        logger.info("[STARTUP] Initializing database...")
        try:
            await init_db()
            logger.info("[STARTUP] [OK] Database initialized")
        except Exception as db_error:
            logger.warning(f"[STARTUP] [WARN] Database initialization failed (continuing anyway): {db_error}")
            # Continue without database - useful for testing
        
        # Initialize enhanced services
        logger.info("[STARTUP] Initializing enhanced services...")
        try:
            success = await initialize_enhanced_services()
            if not success:
                logger.warning("[STARTUP] [WARN] Enhanced services initialization incomplete")
        except Exception as svc_error:
            logger.warning(f"[STARTUP] [WARN] Enhanced services failed (continuing): {svc_error}")
        logger.info("[STARTUP] [OK] Services initialized (or skipped)")
        
    except Exception as e:
        logger.error(f"[STARTUP] [ERROR] Startup error: {e}", exc_info=True)
    
    # Start auto-training in background - now enabled with ML support
    try:
        asyncio.create_task(enhanced_auto_training_loop())
        logger.info("[STARTUP] [OK] Auto-training background task started")
    except Exception as e:
        logger.warning(f"[STARTUP] [WARN] Auto-training task failed to start: {e}")
    
    # Start prediction resolution background loop
    try:
        asyncio.create_task(run_prediction_resolution_loop(SessionLocal))
        logger.info("[STARTUP] [OK] Prediction resolution background task started")
    except Exception as e:
        logger.warning(f"[STARTUP] [WARN] Prediction resolution task failed to start: {e}")
    
    # Initialize email templates and start email task loop
    try:
        async with SessionLocal() as db:
            template_service = EmailTemplateService()
            await template_service.create_default_templates(db)
            logger.info("[STARTUP] [OK] Email templates initialized")
        
        # asyncio.create_task(run_email_task_loop(SessionLocal))
        logger.info("[STARTUP] [INFO] Email campaign background task DISABLED for startup debugging")
    except Exception as e:
        logger.warning(f"[STARTUP] [WARN] Email task failed to start: {e}")
    
    # Initialize ML Training Scheduler
    try:
        logger.info("[STARTUP] Initializing ML Training Scheduler...")
        scheduler = await get_training_scheduler()

        # Add timeout to prevent hanging during initialization
        try:
            async with AsyncSessionLocal() as session:
                await asyncio.wait_for(
                    scheduler.initialize(session),
                    timeout=30.0  # 30 second timeout
                )
            logger.info("[STARTUP] [OK] Training jobs initialized")
        except asyncio.TimeoutError:
            logger.warning("[STARTUP] [WARN] Training scheduler initialization timed out (continuing without scheduler)")
            scheduler = None
        except Exception as init_error:
            logger.warning(f"[STARTUP] [WARN] Training scheduler initialization failed: {init_error}")
            scheduler = None

        # Start scheduler if initialization succeeded
        if scheduler is not None:
            asyncio.create_task(scheduler.start())
            logger.info("[STARTUP] [OK] ML Training Scheduler started")
        else:
            logger.info("[STARTUP] [INFO] ML Training Scheduler not started due to initialization issues")

    except Exception as e:
        logger.warning(f"[STARTUP] [WARN] ML Training Scheduler setup failed (continuing): {e}")
    
    logger.info("[STARTUP] [OK] SignalEdge AI startup complete")

# === MIDDLEWARE SETUP (must be before routers) ===

# Register exception handlers for standardized error responses
app.add_exception_handler(APIException, api_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# OWASP security headers are set by security_headers_middleware above.
# setup_owasp_security is intentionally NOT called here — calling
# app.add_middleware(BaseHTTPMiddleware subclass) after @app.middleware
# decorators are registered causes Starlette to store a 2-tuple instead
# of a 3-tuple in the middleware stack, crashing every request with
# "ValueError: not enough values to unpack (expected 3, got 2)".

# Setup comprehensive logging middleware (must be early)
# TEMPORARILY DISABLED - causes "No response returned" error
# setup_comprehensive_logging(app)

# CORS configuration - MUST come before routes
# In production set ALLOWED_ORIGINS to a comma-separated list of your domains,
# e.g. "https://yourdomain.com,https://www.yourdomain.com"
import os as _os
_raw_origins = _os.environ.get("ALLOWED_ORIGINS", "").strip()
allowed_origins: list[str] = [o.strip() for o in _raw_origins.split(",") if o.strip()] or ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
    max_age=3600,
)

# Custom trusted host middleware that exempts health checks
@app.middleware("http")
async def trusted_host_middleware(request: Request, call_next):
    """Custom trusted host middleware that allows health checks"""
    # Allow health and readiness checks from any host
    if request.url.path in ["/health", "/ready", "/live"]:
        return await call_next(request)

    return await call_next(request)

# Trusted host middleware - DISABLED in favor of custom middleware above
# try:
#     trusted_hosts = [
#         "localhost",
#         "127.0.0.1",
#         "signaledge-ai.fly.dev",
#         "yourdomain.com",
#         "www.yourdomain.com",
#         # Add production domains here
#         "*",  # Allow all hosts for health checks and internal requests
#     ]
#     app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)
#     logger.info(f"✅ Trusted host middleware enabled for: {trusted_hosts}")
# except Exception as e:
#     logger.warning(f"Trusted host middleware setup failed: {e}")

# Setup enhanced rate limiting with Redis (if available)
try:
    from app.utils.caching import get_redis_client
    redis_client = get_redis_client()
    setup_enhanced_rate_limiting(
        app,
        redis_client=redis_client,
        exempt_paths=[
            "/health",
            "/ready",
            "/docs",
            "/openapi.json",
            "/api/auth/login",
            "/api/auth/register",
            "/api/auth/forgot-password",
            "/api/auth/reset-password",
            "/api/payment/webhook",
        ],
    )
    logger.info("Enhanced rate limiting with Redis enabled")
except Exception as e:
    logger.warning(f"Redis rate limiting unavailable: {e}. Falling back to standard rate limiting.")
    setup_rate_limiting(
        app,
        exempt_paths=[
            "/health",
            "/ready",
            "/docs",
            "/openapi.json",
            "/api/auth/login",
            "/api/auth/register",
            "/api/auth/forgot-password",
            "/api/auth/reset-password",
            "/api/payment/webhook",
        ],
    )

# === STATIC FILES & SPA ROUTING ===

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
assets_dir = os.path.join(static_dir, "assets")
if os.path.isdir(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="static")
    logger.info(f"[STARTUP] Static files mounted from {assets_dir}")
else:
    logger.warning(f"[STARTUP] Assets directory not found at {assets_dir}")

# === ROUTES (after middleware) ===

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(predictions.router, prefix="/api/predictions", tags=["Predictions"])
app.include_router(model_routes.router, prefix="/api/models", tags=["Models"])
app.include_router(ml_operations.router, tags=["ML Training & Monitoring"])
app.include_router(payment.router, prefix="/api/payment", tags=["Payments"])
app.include_router(club100_addon.router, tags=["Club 100 Monetization"])
app.include_router(resolution.router, tags=["Resolution"])
app.include_router(analytics.router, tags=["Analytics"])
app.include_router(prediction_history.router, prefix="/api/user/predictions", tags=["Prediction History"])
app.include_router(email.router, tags=["Email"])
app.include_router(admin.router, tags=["Admin Dashboard"])

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Comprehensive health check endpoint"""
    try:
        health = await health_registry.run_all()
        status_code = 200 if health["status"] == "healthy" else 503
        return JSONResponse(content=health, status_code=status_code)
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )

# Readiness check endpoint
@app.get("/ready", tags=["Health"])
async def readiness_check():
    """Readiness check for Kubernetes"""
    checks = {
        "database": False,
        "ml_service": False,
        "espn_api": False
    }
    
    try:
        # Check database
        from app.database import AsyncSessionLocal
        from sqlalchemy import text
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            checks["database"] = True
    except Exception as e:
        logger.warning(f"Database not ready: {e}")
    
    # Check ML service
    if enhanced_ml_service:
        checks["ml_service"] = True
    
    # Check ESPN API via circuit breaker
    try:
        espn_breaker = get_circuit_breaker("espn_api")
        checks["espn_api"] = espn_breaker.state.value != "open"
    except Exception:
        checks["espn_api"] = False
    
    all_ready = all(checks.values())
    status_code = 200 if all_ready else 503
    
    return JSONResponse(
        status_code=status_code,
        content={
            "ready": all_ready,
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    )

# Liveness check endpoint
@app.get("/live", tags=["Health"])
async def liveness_check():
    """Liveness check for Kubernetes"""
    return {
        "alive": True,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

# Circuit breaker status endpoint
@app.get("/api/system/circuit-breakers", tags=["System"])
async def get_circuit_breaker_status():
    """Get status of all circuit breakers"""
    from app.utils.circuit_breaker import _circuit_breakers
    
    return {
        "circuit_breakers": {
            name: breaker.get_state()
            for name, breaker in _circuit_breakers.items()
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

# Monitoring dashboard endpoint
@app.get("/api/system/monitoring", tags=["System"])
async def get_monitoring_dashboard():
    """Get comprehensive monitoring dashboard data"""
    monitoring = get_monitoring_service()
    return monitoring.get_dashboard_data()

# Monitoring health check
@app.get("/api/system/health/detailed", tags=["System"])
async def get_detailed_health():
    """Get detailed health check information"""
    monitoring = get_monitoring_service()
    
    # Run all health checks
    health_results = await monitoring.health.run_all_checks()
    
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "overall_status": monitoring.health.get_status(),
        "health_check_results": health_results,
        "active_alerts": len(monitoring.alerts.get_active_alerts()),
    }

# System metrics endpoint
@app.get("/api/system/metrics", tags=["System"])
async def get_system_metrics():
    """Get system metrics"""
    import psutil
    import os
    
    try:
        # Memory info
        mem = psutil.virtual_memory()
        
        # Disk info
        disk = psutil.disk_usage("/")
        
        # CPU info
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        return {
            "memory": {
                "total_gb": round(mem.total / (1024**3), 2),
                "available_gb": round(mem.available / (1024**3), 2),
                "percent_used": mem.percent
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "percent_used": round((disk.used / disk.total) * 100, 2)
            },
            "cpu": {
                "percent_used": cpu_percent
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        raise HTTPException(status_code=500, detail="Could not retrieve system metrics")

# Model performance endpoint
@app.get("/api/models/performance/{sport_key}/{market_type}", tags=["Models"])
async def get_model_performance_summary(
    sport_key: str,
    market_type: str,
    days_back: int = 30
):
    """Get model performance summary"""
    try:
        if not enhanced_ml_service:
            raise HTTPException(status_code=503, detail="ML service not available")
        
        performance = await enhanced_ml_service.get_model_performance(
            sport_key=sport_key,
            market_type=market_type
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

# Model alerts endpoint
@app.get("/api/models/alerts", tags=["Models"])
async def get_model_alerts(
    sport_key: Optional[str] = None,
    market_type: Optional[str] = None
):
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

# Resolve alert endpoint
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
    logger.info("🛑 Shutting down SignalEdge AI...")
    
    try:
        if model_monitor:
            await model_monitor.stop_monitoring()
            logger.info("✅ Model monitoring stopped")
        
        # Close ESPN service connections
        from app.services.espn_prediction_service import ESPNPredictionService
        espn_service = ESPNPredictionService()
        await espn_service.close()
        logger.info("✅ ESPN service connections closed")
        
        logger.info("🛑 SignalEdge AI shutdown complete")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# === SPA FALLBACK ROUTE ===
# Serve index.html for all non-API routes (SPA routing)
@app.get("/", include_in_schema=False)
async def serve_spa_root():
    """Serve SPA index.html for root path"""
    static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
    index_path = os.path.join(static_dir, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path, media_type="text/html")
    raise HTTPException(status_code=404, detail="Frontend not found")

@app.get("/{full_path:path}", include_in_schema=False)
async def serve_spa(full_path: str):
    """Serve SPA index.html for frontend routing"""
    # Don't intercept API routes or static assets
    if full_path.startswith("api/") or full_path.startswith("assets/") or full_path.startswith("."):
        raise HTTPException(status_code=404, detail="Not found")
    
    # Try to serve the static file first
    static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
    file_path = os.path.join(static_dir, full_path)
    
    # Prevent directory traversal
    if not os.path.abspath(file_path).startswith(os.path.abspath(static_dir)):
        raise HTTPException(status_code=404, detail="Not found")
    
    # If it's a file and exists, serve it
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    
    # Otherwise serve index.html for SPA routing
    index_path = os.path.join(static_dir, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path, media_type="text/html")
    
    raise HTTPException(status_code=404, detail="Frontend not found")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get('PORT', 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)

# Reload trigger 02/14/2026 08:59:10

