
.....# Quick Start Guide - Sports Prediction Platform

This guide will walk you through starting the platform from scratch in both development and production modes.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Development Mode](#development-mode)
4. [Production Mode](#production-mode)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software
- **Docker Desktop** 4.25+ (includes Docker Compose)
  - [Download for Windows](https://www.docker.com/products/docker-desktop)
  - [Download for Mac](https://www.docker.com/products/docker-desktop)
  - [Linux installation](https://docs.docker.com/engine/install/)

- **Git** (for cloning)
- **Node.js** 18+ (for frontend development only)
- **Python** 3.11+ (for backend development only)

### System Requirements
- **RAM**: 8GB minimum, 16GB recommended
- **Disk**: 10GB free space
- **CPU**: 4 cores recommended

### Verify Installation
```bash
# Check Docker
docker --version
docker-compose --version

# Check resources
docker system info | grep -E "Memory|CPUs"
```

---

## Initial Setup

### Step 1: Navigate to Project Directory
```bash
cd "c:/Users/bigba/Desktop/New folder/sports-prediction-platform"
```

### Step 2: Create Environment File
```bash
# Copy the example environment file
copy backend\.env.example .env
```

### Step 3: Configure Environment Variables
Edit the `.env` file with your values:

```env
# Database (for local development, SQLite is used by default)
DB_USER=postgres
DB_PASSWORD=your_secure_password
DB_NAME=sports_predictions

# Security (generate a strong secret key)
SECRET_KEY=your-super-secret-key-min-32-chars-long

# API Keys (get from respective providers)
ODDS_API_KEY=your_odds_api_key_here
STRIPE_SECRET_KEY=sk_test_your_stripe_key
STRIPE_PUBLIC_KEY=pk_test_your_stripe_key

# For production, also set:
# REDIS_URL=redis://redis:6379
# ENVIRONMENT=production
```

**Generate a secure secret key:**
```bash
# Windows PowerShell
[Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Maximum 256 } | ForEach-Object { [byte]$_ }))

# Or use Python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Development Mode

Development mode uses SQLite (no Docker required for database) and hot-reloading.

### Option A: Quick Start (Docker - Recommended)

```bash
# Start only the database services (PostgreSQL + Redis)
docker-compose up -d postgres redis

# Wait for database to be ready (30 seconds)
timeout /t 30

# Install backend dependencies
cd backend
pip install -r requirements.txt

# Start backend (in one terminal)
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start frontend (in another terminal)
cd frontend
npm install
npm run dev
```

### Option B: Full Docker Development

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**Access points:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Database Admin: http://localhost:5050 (pgAdmin)

---

## Production Mode

Production mode uses PostgreSQL, Redis, and optimized builds.

### Step 1: Configure Production Environment

Create `.env` file with production values:

```env
# Database
DB_USER=postgres
DB_PASSWORD=your_strong_production_password
DB_NAME=sports_predictions

# Security
SECRET_KEY=your-256-bit-secret-key-here-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API Keys
ODDS_API_KEY=your_live_odds_api_key
STRIPE_SECRET_KEY=sk_live_your_stripe_key
STRIPE_PUBLIC_KEY=pk_live_your_stripe_key

# Redis
REDIS_URL=redis://redis:6379

# Environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Monitoring
GRAFANA_PASSWORD=your_grafana_admin_password
```

### Step 2: Start Production Stack

```bash
# Build and start all production services
docker-compose -f docker-compose.prod.yml up -d --build

# Verify services are running
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f backend
```

### Step 3: Initialize Database (First Time Only)

```bash
# Run database migrations
docker-compose -f docker-compose.prod.yml exec backend python -c "
from app.database import init_db
import asyncio
asyncio.run(init_db())
print('Database initialized')
"
```

**Production Access Points:**
- Application: http://localhost (via Nginx)
- API: http://localhost/api
- API Docs: http://localhost/docs
- Grafana: http://localhost:3001
- Prometheus: http://localhost:9090

---

## Verification

### 1. Health Check
```bash
# Check overall health
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2026-01-15T10:30:00Z",
  "checks": {...},
  "summary": {
    "total": 6,
    "healthy": 6,
    "degraded": 0,
    "unhealthy": 0
  }
}
```

### 2. Readiness Check
```bash
curl http://localhost:8000/ready
```

### 3. API Test
```bash
# Test predictions endpoint
curl http://localhost:8000/api/predictions?sport=nba

# Test with authentication (if you have a token)
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/api/predictions
```

### 4. System Metrics
```bash
curl http://localhost:8000/api/system/metrics
```

### 5. Circuit Breaker Status
```bash
curl http://localhost:8000/api/system/circuit-breakers
```

---

## Troubleshooting

### Issue: "Database connection failed"

**Solution:**
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# View PostgreSQL logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres

# Wait 30 seconds and check again
timeout /t 30
docker-compose exec postgres pg_isready -U postgres
```

### Issue: "Redis connection failed"

**Solution:**
```bash
# Check Redis
docker-compose ps redis

# Test Redis connection
docker-compose exec redis redis-cli ping

# Should return: PONG
```

### Issue: "Backend won't start"

**Solution:**
```bash
# Check backend logs
docker-compose logs backend

# Common fixes:
# 1. Install dependencies
cd backend
pip install -r requirements.txt

# 2. Check for port conflicts
netstat -ano | findstr :8000

# 3. Restart backend
docker-compose restart backend
```

### Issue: "Frontend won't load"

**Solution:**
```bash
# Check if frontend is running
docker-compose ps frontend

# Rebuild frontend
docker-compose up -d --build frontend

# Or run locally for debugging
cd frontend
npm install
npm run dev
```

### Issue: "ML models not found"

**Solution:**
```bash
# Check if models exist
docker-compose exec backend ls -la ml-models/trained/

# If empty, models need training (this happens on first run)
# The auto-training pipeline will start automatically
# Or trigger manually:
docker-compose exec backend python -c "
from app.services.enhanced_ml_service import EnhancedMLService
service = EnhancedMLService()
# Training will happen automatically when data is available
print('ML service initialized')
"
```

### Issue: "Port already in use"

**Solution:**
```bash
# Find what's using port 8000
netstat -ano | findstr :8000

# Kill the process (replace <PID> with actual process ID)
taskkill /PID <PID> /F

# Or use different ports in docker-compose.yml
```

### Issue: "Permission denied" (Linux/Mac)

**Solution:**
```bash
# Fix permissions
sudo chown -R $USER:$USER .

# Or run Docker without sudo (add user to docker group)
sudo usermod -aG docker $USER
# Log out and back in
```

---

## Daily Operations

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Restart Services
```bash
# Restart everything
docker-compose restart

# Restart specific service
docker-compose restart backend
```

### Update Application
```bash
# Pull latest images
docker-compose pull

# Rebuild and restart
docker-compose up -d --build
```

### Backup Database
```bash
# Manual backup
docker-compose exec postgres pg_dump -U postgres sports_predictions > backup_$(date +%Y%m%d).sql

# Automated backups happen daily at 2 AM (in production)
```

### Stop Everything
```bash
# Development
docker-compose down

# Production
docker-compose -f docker-compose.prod.yml down

# Remove all data (WARNING: deletes database)
docker-compose down -v
```

---

## Next Steps

1. **Configure SSL** - Place certificates in `nginx/ssl/` for HTTPS
2. **Set up monitoring** - Access Grafana at http://localhost:3001
3. **Configure Stripe** - Add webhook endpoints for payment processing
4. **Train ML models** - Initial training happens automatically; monitor at `/api/models/status`
5. **Read full documentation** - See `DEPLOYMENT.md` for production details

## Support

If you encounter issues:
1. Check logs: `docker-compose logs -f`
2. Run health check: `curl http://localhost:8000/health`
3. Review `DEPLOYMENT.md` for advanced configuration
4. Check `OPTIMIZATION_TODO.md` for implementation details
