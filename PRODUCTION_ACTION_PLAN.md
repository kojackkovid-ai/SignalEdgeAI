# Production Readiness Action Plan

**Start Date**: May 3, 2026  
**Target Launch**: May 31, 2026 (4 weeks)  
**Status**: IN PROGRESS

---

## Phase 1: CRITICAL FIXES (Week 1-2)

### Task 1.1: Remove Debug Code and Print Statements
**Priority**: CRITICAL  
**Assigned**: [Backend Lead]  
**Deadline**: May 10, 2026  
**Estimated Effort**: 2-3 hours

**Files to Fix**:
- [ ] `backend/app/database.py` - Replace 15+ print() calls with logger
- [ ] `backend/app/main.py` - Remove commented debug blocks
- [ ] `backend/app/services/advanced_statistical_models.py` - Line 536
- [ ] `backend/app/routes/users.py` - Remove debug log statements

**Acceptance Criteria**:
- [ ] Zero print() statements in production code
- [ ] All logging uses proper logger instance
- [ ] No commented-out code blocks remain
- [ ] LOG_LEVEL=INFO in production .env

```bash
# Command to find remaining print statements:
grep -r "print(" backend/app --include="*.py" | grep -v test | grep -v debug
```

---

### Task 1.2: Secure All Hardcoded Credentials
**Priority**: CRITICAL  
**Assigned**: [DevOps/Security]  
**Deadline**: May 10, 2026  
**Estimated Effort**: 3-4 hours

**Files to Fix**:
- [ ] `docker-compose.prod.yml` - Replace hardcoded passwords with env vars
- [ ] `backend/app/config.py` - Add production validation
- [ ] `.gitignore` - Ensure `.env.production` is ignored
- [ ] CI/CD secrets - Configure in Fly.io/deployment platform

**Implementation**:

```yaml
# ❌ CURRENT (docker-compose.prod.yml)
environment:
  POSTGRES_PASSWORD: sports_predictions_password

# ✅ FIXED
environment:
  POSTGRES_PASSWORD: ${DB_PASSWORD}
  POSTGRES_USER: ${DB_USER}
  POSTGRES_DB: ${DB_NAME}
```

```python
# ✅ ADD TO config.py
def validate_production_config(self):
    """Validate critical production settings"""
    if self.environment == "production":
        required_vars = {
            "secret_key": "SECRET_KEY",
            "stripe_secret_key": "STRIPE_SECRET_KEY", 
            "odds_api_key": "ODDS_API_KEY",
            "db_pass": "DB_PASS",
            "mailgun_api_key": "MAILGUN_API_KEY",
        }
        
        missing = []
        for attr, name in required_vars.items():
            if not getattr(self, attr):
                missing.append(name)
        
        if missing:
            raise ValueError(
                f"Missing required production secrets: {missing}. "
                f"Set in environment or Fly.io secrets: flyctl secrets set {' '.join(missing)}"
            )
```

**Acceptance Criteria**:
- [ ] No passwords/keys in version control
- [ ] All secrets use environment variables
- [ ] Git history cleaned: `git log --all -S 'password'` returns nothing
- [ ] `.env.production` explicitly in `.gitignore`

---

### Task 1.3: Configure HTTPS Enforcement
**Priority**: CRITICAL  
**Assigned**: [Backend Lead]  
**Deadline**: May 12, 2026  
**Estimated Effort**: 2-3 hours

**Implementation**:

```python
# backend/app/main.py - Add after CORS middleware setup

# Middleware 1: HTTPS Redirect (for self-hosted deployments)
@app.middleware("http")
async def https_redirect_middleware(request: Request, call_next):
    """Redirect HTTP to HTTPS in production"""
    if settings.environment == "production" and settings.enable_https_redirect:
        if request.url.scheme != "https":
            url = request.url.replace(scheme="https")
            return RedirectResponse(url=url, status_code=301)
    return await call_next(request)

# Middleware 2: Security Headers (already partially implemented)
# ✅ Already good - review for completeness
```

**Configuration**:
```python
# backend/app/config.py
class Settings(BaseSettings):
    environment: str = "development"  # Set to "production" for prod
    enable_https_redirect: bool = False  # Enable in production
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.environment == "production":
            self.enable_https_redirect = True
```

**Deployment**:
- For Fly.io: Already configured in `fly.toml` (force_https = true)
- For self-hosted: Configure nginx or reverse proxy to force HTTPS

**Acceptance Criteria**:
- [ ] HTTP requests redirect to HTTPS (test: `curl -I http://localhost:8000`)
- [ ] HSTS header present: `Strict-Transport-Security: max-age=31536000`
- [ ] CSP header enforces HTTPS: `upgrade-insecure-requests` (if needed)

---

### Task 1.4: Fix CORS Configuration
**Priority**: CRITICAL  
**Assigned**: [Backend Lead]  
**Deadline**: May 12, 2026  
**Estimated Effort**: 1-2 hours

**Current Issue**:
```python
# ❌ BAD - hardcoded localhost in production string
cors_origins: str = "http://localhost,http://127.0.0.1,..."
```

**Fix**:
```python
# backend/app/config.py

@property
def allowed_origins(self) -> list[str]:
    """Get allowed CORS origins based on environment"""
    if self.environment == "production":
        return [
            "https://yourdomain.com",
            "https://www.yourdomain.com",
            # Add production URLs only
        ]
    else:
        return [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://localhost:8000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
        ]

@property
def cors_allow_methods(self) -> list[str]:
    """Restrict HTTP methods in production"""
    if self.environment == "production":
        return ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    else:
        return ["*"]

# backend/app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=settings.cors_allow_methods,
    allow_headers=["Content-Type", "Authorization"],
    max_age=600,
)
```

**Acceptance Criteria**:
- [ ] CORS origin list is environment-specific
- [ ] No development URLs in production config
- [ ] Methods are restricted (not `["*"]`)
- [ ] Test: Requests from unauthorized domain return 403

---

### Task 1.5: Re-enable and Fix Rate Limiting
**Priority**: CRITICAL  
**Assigned**: [Backend Lead]  
**Deadline**: May 15, 2026  
**Estimated Effort**: 4-5 hours

**Current Issue**:
```python
# Currently disabled - TEMPORARILY DISABLED FOR DEBUGGING
```

**Implementation**:
```python
# backend/app/utils/enhanced_rate_limiter.py

from fastapi_limiter import FastAPILimiter
from fastapi_limiter.backends.redis import RedisBackend
from aioredis import from_url

async def setup_rate_limiting(app: FastAPI):
    """Initialize rate limiting"""
    redis = await from_url(settings.redis_url, encoding="utf8", decode_responses=True)
    await FastAPILimiter.init(RedisBackend(redis), key_func=get_client_ip)

# backend/app/main.py
@app.on_event("startup")
async def startup():
    await setup_rate_limiting(app)

# In routes
from fastapi_limiter.depends import RateLimiter

@app.post("/api/auth/login")
@limiter.limit("5/minute")  # 5 attempts per minute
async def login(credentials: LoginRequest):
    ...

@app.post("/api/predictions")
@limiter.limit("30/minute")  # 30 predictions per minute
async def get_predictions(request: PredictionRequest):
    ...

@app.post("/api/payment/create-intent")
@limiter.limit("10/minute")  # 10 payment attempts per minute
async def create_payment(payment: PaymentRequest):
    ...
```

**Testing**:
```bash
# Test rate limiting
for i in {1..6}; do curl -X POST http://localhost:8000/api/auth/login; done
# Should return 429 on 6th request
```

**Acceptance Criteria**:
- [ ] Auth endpoints: 5 requests/minute per IP
- [ ] Prediction endpoints: 30 requests/minute per user
- [ ] Payment endpoints: 10 requests/minute per user
- [ ] Returns HTTP 429 when limit exceeded
- [ ] No timeout errors in production

---

## Phase 2: HIGH PRIORITY FIXES (Week 2-3)

### Task 2.1: Add Sentry Error Tracking
**Priority**: HIGH  
**Assigned**: [Backend Lead]  
**Deadline**: May 18, 2026  
**Estimated Effort**: 2 hours

```python
# backend/app/main.py - Add at very start of file

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

if settings.environment == "production":
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=0.1,
        environment=settings.environment,
        release=settings.app_version,
        before_send=lambda event, hint: event,  # Filter sensitive data if needed
    )
```

**Configuration**:
```python
# backend/app/config.py
sentry_dsn: Optional[str] = None  # Get from https://sentry.io

# Validate in production
if self.environment == "production" and not self.sentry_dsn:
    warnings.warn("SENTRY_DSN not configured - error tracking disabled")
```

**Deployment**:
```bash
# Set in Fly.io
flyctl secrets set SENTRY_DSN=your-sentry-dsn
```

**Acceptance Criteria**:
- [ ] Sentry initialized in production
- [ ] Errors automatically captured
- [ ] Alerts configured for critical errors
- [ ] Test: Trigger an error and verify in Sentry dashboard

---

### Task 2.2: Setup Structured Logging & Audit Trail
**Priority**: HIGH  
**Assigned**: [Backend Lead]  
**Deadline**: May 18, 2026  
**Estimated Effort**: 3-4 hours

```python
# backend/app/middleware/logging_middleware.py

import json
import time
from uuid import uuid4
from datetime import datetime

@app.middleware("http")
async def structured_logging_middleware(request: Request, call_next):
    """Log all requests/responses for audit trail"""
    request_id = str(uuid4())
    start_time = time.time()
    
    # Extract user info if authenticated
    user_id = None
    if hasattr(request.state, "user"):
        user_id = request.state.user.id
    
    # Log request
    request.state.request_id = request_id
    logger.info("request.started", extra={
        "request_id": request_id,
        "timestamp": datetime.utcnow().isoformat(),
        "method": request.method,
        "path": request.url.path,
        "user_id": user_id,
        "ip": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent"),
    })
    
    response = await call_next(request)
    
    # Log response
    duration_ms = (time.time() - start_time) * 1000
    logger.info("request.completed", extra={
        "request_id": request_id,
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "duration_ms": int(duration_ms),
        "user_id": user_id,
    })
    
    response.headers["X-Request-ID"] = request_id
    return response
```

**Log Format (JSON)**:
```json
{
  "timestamp": "2026-05-03T10:30:45.123Z",
  "level": "INFO",
  "event": "request.completed",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "method": "POST",
  "path": "/api/predictions",
  "status": 200,
  "duration_ms": 250,
  "user_id": "user-123",
  "ip": "192.168.1.1"
}
```

**Acceptance Criteria**:
- [ ] All requests logged with request_id
- [ ] Payment requests include transaction details
- [ ] Auth requests log attempt (not password)
- [ ] Logs are structured JSON (parseable)
- [ ] Log storage configured (CloudWatch/ELK)

---

### Task 2.3: Database Backup & Recovery
**Priority**: HIGH  
**Assigned**: [DevOps/DBA]  
**Deadline**: May 20, 2026  
**Estimated Effort**: 3-4 hours

**Implementation**:
```yaml
# docker-compose.prod.yml - Add backup service

services:
  postgres:
    # ... existing config ...
    volumes:
      - postgres_data_prod:/var/lib/postgresql/data
      - ./database/backups:/backups

  # Add backup container
  postgres-backup:
    image: postgres:16-alpine
    depends_on:
      - postgres
    environment:
      PGPASSWORD: ${DB_PASSWORD}
    volumes:
      - ./database/backups:/backups
    command: |
      bash -c "
        while true; do
          pg_dump -h postgres -U ${DB_USER} ${DB_NAME} > /backups/backup_\$(date +%Y%m%d_%H%M%S).sql
          # Keep only last 30 days
          find /backups -name 'backup_*.sql' -mtime +30 -delete
          sleep 86400  # Run daily
        done
      "
    networks:
      - backend-network
    restart: unless-stopped
```

**Or use managed backups** (recommended):
```bash
# Fly.io with Supabase PostgreSQL
flyctl postgres create --name signaledge-db --region ams
flyctl postgres attach signaledge-db --app signaledge-ai

# Backups are automatic
```

**Acceptance Criteria**:
- [ ] Daily backups configured and running
- [ ] Backup retention policy: 30 days
- [ ] Tested restore procedure (monthly)
- [ ] Backups stored off-site (S3/GCS)
- [ ] Documentation updated

---

### Task 2.4: Add Health Check Endpoints
**Priority**: HIGH  
**Assigned**: [Backend Lead]  
**Deadline**: May 18, 2026  
**Estimated Effort**: 2-3 hours

```python
# backend/app/routes/health.py

from typing import Dict, Any
from enum import Enum

class ComponentStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Comprehensive health check for monitoring"""
    checks: Dict[str, bool] = {}
    
    # Database health
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            checks["database"] = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        checks["database"] = False
    
    # Redis health
    try:
        cache = await get_cache_service()
        await cache.get("health_check_key")
        checks["cache"] = True
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        checks["cache"] = False
    
    # ML models health
    try:
        # Quick validation that models are loaded
        checks["ml_models"] = EnhancedMLService is not None
    except Exception as e:
        checks["ml_models"] = False
    
    # Overall status
    all_healthy = all(checks.values())
    status = ComponentStatus.HEALTHY if all_healthy else ComponentStatus.DEGRADED
    
    return {
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks,
    }

@app.get("/health/ready")
async def readiness_check():
    """Kubernetes-style readiness probe"""
    checks = await health_check()
    if checks["status"] == ComponentStatus.HEALTHY:
        return {"ready": True}
    else:
        return JSONResponse(
            status_code=503,
            content={"ready": False, "reason": str(checks)}
        )
```

**Deployment Configuration**:
```yaml
# docker-compose.prod.yml
services:
  backend:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/ready"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
```

**Acceptance Criteria**:
- [ ] `/health` endpoint returns component status
- [ ] `/health/ready` returns 200 only if fully ready
- [ ] Health checks include database and cache
- [ ] All checks complete in < 5 seconds
- [ ] Used by load balancer/orchestrator for routing

---

### Task 2.5: Input Validation & SQL Injection Prevention
**Priority**: HIGH  
**Assigned**: [Security/Backend]  
**Deadline**: May 20, 2026  
**Estimated Effort**: 4-5 hours

**Current Status**: ✅ SQLAlchemy ORM provides some protection

**Additional Hardening**:
```python
# backend/app/schemas/validation.py

from pydantic import BaseModel, Field, validator

class PredictionRequest(BaseModel):
    """Validated prediction request"""
    sport: str = Field(..., min_length=2, max_length=50, regex="^[a-z_]+$")
    market_type: str = Field(..., min_length=2, max_length=50)
    confidence: float = Field(..., ge=0.0, le=1.0)
    wager_amount: float = Field(..., gt=0, le=10000)
    
    @validator("sport")
    def validate_sport(cls, v):
        allowed = {"nfl", "nba", "nhl", "mlb", "soccer"}
        if v not in allowed:
            raise ValueError(f"Invalid sport. Allowed: {allowed}")
        return v

class PaymentRequest(BaseModel):
    """Validated payment request"""
    amount: float = Field(..., gt=0, le=100000)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    description: str = Field(..., max_length=500)
    
    @validator("currency")
    def validate_currency(cls, v):
        allowed = {"USD", "EUR", "GBP", "CAD"}
        if v not in allowed:
            raise ValueError(f"Currency not supported: {v}")
        return v
```

**Acceptance Criteria**:
- [ ] All POST/PUT endpoints have Pydantic validation
- [ ] No string concatenation in SQL (use parameters)
- [ ] Range validation on numeric inputs
- [ ] Pattern validation on enums (regex where applicable)
- [ ] Test: Invalid inputs return 422

---

### Task 2.6: Stripe Integration Security Hardening
**Priority**: HIGH  
**Assigned**: [Payment/Backend]  
**Deadline**: May 20, 2026  
**Estimated Effort**: 3-4 hours

```python
# backend/app/services/stripe_service.py

import stripe
from typing import Optional

class StripeService:
    """Secure Stripe integration"""
    
    @staticmethod
    def verify_webhook(request_body: bytes, signature: str) -> dict:
        """Verify webhook signature - MUST validate before processing"""
        try:
            event = stripe.Webhook.construct_event(
                request_body,
                signature,
                settings.stripe_webhook_secret
            )
            return event
        except ValueError as e:
            # Invalid payload
            logger.error(f"Invalid webhook payload: {e}")
            raise HTTPException(status_code=400, detail="Invalid signature")
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            logger.error(f"Invalid webhook signature: {e}")
            raise HTTPException(status_code=401, detail="Signature verification failed")
    
    @staticmethod
    async def create_payment_intent(
        user_id: str,
        amount: int,  # In cents
        description: str,
        idempotency_key: Optional[str] = None
    ) -> dict:
        """Create payment intent with idempotency"""
        try:
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency="usd",
                description=description,
                metadata={"user_id": user_id},
                idempotency_key=idempotency_key or str(uuid4()),
            )
            return intent
        except stripe.error.CardError as e:
            logger.error(f"Card error: {e}")
            raise HTTPException(status_code=400, detail="Card declined")
        except stripe.error.RateLimitError as e:
            logger.error(f"Stripe rate limit: {e}")
            raise HTTPException(status_code=429, detail="Too many requests")
        except Exception as e:
            logger.error(f"Stripe error: {e}")
            raise HTTPException(status_code=500, detail="Payment processing error")
    
    @staticmethod
    async def confirm_payment_intent(intent_id: str) -> dict:
        """Confirm payment with error handling"""
        try:
            intent = stripe.PaymentIntent.retrieve(intent_id)
            
            if intent.status == "succeeded":
                return {"status": "success", "intent": intent}
            elif intent.status == "processing":
                return {"status": "processing", "intent": intent}
            else:
                return {"status": "failed", "intent": intent}
        except stripe.error.InvalidRequestError as e:
            logger.error(f"Invalid payment intent: {e}")
            raise HTTPException(status_code=404, detail="Payment intent not found")
        except Exception as e:
            logger.error(f"Error confirming payment: {e}")
            raise HTTPException(status_code=500, detail="Error confirming payment")

# In routes/payment.py
@app.post("/api/payment/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events"""
    payload = await request.body()
    signature = request.headers.get("stripe-signature")
    
    # 1. Verify signature (CRITICAL!)
    event = StripeService.verify_webhook(payload, signature)
    
    # 2. Handle event type
    if event.type == "payment_intent.succeeded":
        await handle_payment_succeeded(event.data.object)
    elif event.type == "payment_intent.payment_failed":
        await handle_payment_failed(event.data.object)
    elif event.type == "charge.refunded":
        await handle_refund(event.data.object)
    
    return {"status": "ok"}
```

**Acceptance Criteria**:
- [ ] Webhook signature verified before processing
- [ ] Idempotency keys used for payment creation
- [ ] All Stripe errors handled gracefully
- [ ] Payment status logged for audit
- [ ] PCI DSS compliant (no card data stored locally)

---

## Phase 3: MEDIUM PRIORITY (Week 3)

### Task 3.1: Enable TypeScript Strict Mode
**Priority**: MEDIUM  
**Assigned**: [Frontend Lead]  
**Deadline**: May 22, 2026  
**Estimated Effort**: 2-3 hours

```json
// frontend/tsconfig.json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "strictBindCallApply": true,
    "strictPropertyInitialization": true,
    "noImplicitThis": true,
    "alwaysStrict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true
  }
}
```

---

### Task 3.2: Add Frontend Error Boundary
**Priority**: MEDIUM  
**Assigned**: [Frontend Lead]  
**Deadline**: May 22, 2026  
**Estimated Effort**: 2-3 hours

```typescript
// frontend/src/components/ErrorBoundary.tsx

import React, { ReactNode } from "react";
import * as Sentry from "@sentry/react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    Sentry.captureException(error, { contexts: { react: errorInfo } });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-container">
          <h1>Something went wrong</h1>
          <p>{this.state.error?.message}</p>
          <button onClick={() => window.location.reload()}>
            Reload Page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default Sentry.withProfiler(ErrorBoundary);
```

---

### Task 3.3: Add API Versioning
**Priority**: MEDIUM  
**Assigned**: [Backend/API Lead]  
**Deadline**: May 22, 2026  
**Estimated Effort**: 2 hours

```python
# backend/app/routes/v1/predictions.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["Predictions V1"])

@router.get("/predictions")
async def get_predictions_v1():
    # Version 1 implementation
    pass

# backend/app/routes/v2/predictions.py
router_v2 = APIRouter(prefix="/api/v2", tags=["Predictions V2"])

@router_v2.get("/predictions")
async def get_predictions_v2():
    # Version 2 implementation with improvements
    pass

# backend/app/main.py
app.include_router(v1_predictions_router)
app.include_router(v2_predictions_router)
```

---

## Phase 4: VALIDATION & TESTING (Week 4)

### Task 4.1: Full Integration Testing
**Priority**: HIGH  
**Assigned**: [QA/Testing]  
**Deadline**: May 28, 2026  
**Estimated Effort**: Full week

**Test Scenarios**:
- [ ] User registration & authentication flow
- [ ] Payment processing (test & live mode)
- [ ] Prediction generation for all sports
- [ ] Model retraining pipeline
- [ ] Database backup & restore
- [ ] Error handling & error rates
- [ ] Rate limiting enforcement
- [ ] Webhook handling (Stripe)
- [ ] Load testing (100+ concurrent users)
- [ ] Security scanning (OWASP Top 10)

---

### Task 4.2: Load Testing
**Priority**: HIGH  
**Assigned**: [DevOps/Performance]  
**Deadline**: May 28, 2026  
**Estimated Effort**: 2-3 days

```python
# test_load.py using locust

from locust import HttpUser, task, between

class PredictionUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def get_predictions(self):
        self.client.get(
            "/api/v1/predictions",
            params={"sport": "nfl", "limit": 10}
        )
    
    @task(1)
    def create_prediction(self):
        self.client.post(
            "/api/v1/predictions",
            json={"sport": "nfl", "wager_amount": 100}
        )

# Run: locust -f test_load.py --host=http://localhost:8000
```

**Targets**:
- [ ] 100 concurrent users
- [ ] P95 response time: < 1 second
- [ ] P99 response time: < 2 seconds
- [ ] Error rate: < 0.1%

---

### Task 4.3: Security Audit & Scanning
**Priority**: HIGH  
**Assigned**: [Security]  
**Deadline**: May 28, 2026  
**Estimated Effort**: 1-2 days

```bash
# Backend security scanning
python -m pip install bandit safety

# Check for known vulnerabilities
bandit -r backend/app
safety check

# OWASP dependency check
npm install -g snyk
snyk test

# Frontend security audit
npm audit

# SQL injection check
grep -r "execute(" backend/app | grep -v "text("
```

**Security Checklist**:
- [ ] No hardcoded secrets found
- [ ] No SQL injection vulnerabilities
- [ ] No XSS vulnerabilities
- [ ] No CSRF vulnerabilities
- [ ] Dependency vulnerabilities addressed
- [ ] OWASP Top 10 tested

---

## Summary & Sign-off

| Phase | Status | Owner | Deadline |
|-------|--------|-------|----------|
| Phase 1: Critical Fixes | IN PROGRESS | Backend/DevOps | May 15 |
| Phase 2: High Priority | QUEUED | Backend/DevOps | May 20 |
| Phase 3: Medium Priority | QUEUED | Frontend/Backend | May 22 |
| Phase 4: Testing | QUEUED | QA/DevOps | May 28 |
| **Production Launch** | **PLANNED** | All | **May 31** |

---

**Questions?** Contact: [DevOps Lead] or [Engineering Manager]
