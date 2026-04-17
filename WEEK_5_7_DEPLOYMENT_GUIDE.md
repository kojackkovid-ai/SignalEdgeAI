# WEEK 5-7 DEPLOYMENT GUIDE
## Step-by-Step Production Deployment Instructions

**Last Updated:** March 22, 2026  
**Deployment Target:** PostgreSQL DB + FastAPI Backend + Docker  
**Estimated Deployment Time:** 45 minutes (including validation)

---

## PRE-DEPLOYMENT CHECKLIST

### 1. Local Testing (Run These First)
```bash
# Verify all tests pass
cd sports-prediction-platform
pytest backend/tests/test_week_5_7_enhancements.py -v --cov

# Verify linting
black . --check
pylint backend/app/services/

# Build Docker image locally
docker build -t prediction-platform:week5-7-latest -f Dockerfile .

# Run smoke tests
docker-compose -f docker-compose.yml up -d
pytest backend/tests/smoke_tests.py -v
docker-compose down
```

### 2. Environment Variables Check
```bash
# Copy .env.example to .env
cp .env.example .env

# Verify these are set:
DATABASE_URL=postgresql://user:password@db:5432/predictions
REDIS_URL=redis://cache:6379
ENVIRONMENT=production
LOG_LEVEL=INFO
SECRET_KEY=[your-secret-key]

# Add new Week 5-7 variables:
ODDS_SYNC_INTERVAL=10  # seconds
ENSEMBLE_RETRAIN_HOUR=3  # UTC hour (3 AM)
SYNTHETIC_DATA_SIZE=5000  # samples for augmentation
```

### 3. Database Backup
```bash
# Create backup before deployment
BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
pg_dump $DATABASE_URL -Fc -f "backups/$BACKUP_FILE"

# Verify backup
pg_restore --list "backups/$BACKUP_FILE" | head -20
```

---

## STEP 1: DATABASE MIGRATION

### 1.1 Apply Alembic Migration
```bash
# Check current schema version
alembic current

# Create new migration (if not already created)
alembic revision --autogenerate -m "add_odds_and_ensemble_tables"

# Verify migration content
cat alembic/versions/006_add_odds_and_ensemble.py

# Apply migration
alembic upgrade head

# Verify migration applied
alembic current
```

### 1.2 Migration SQL Manual Check
```sql
-- Verify new tables created
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('odds_records', 'odds_movement', 'ensemble_weights', 'synthetic_datasets');

-- Should return 4 rows ✓

-- Check odds_records schema
\d odds_records

-- Check indexes created
SELECT indexname FROM pg_indexes 
WHERE tablename IN ('odds_records', 'odds_movement', 'ensemble_weights');

-- Should show indexes on event_id, provider, timestamp, etc.
```

### 1.3 Create Initial Data
```python
# Run this script to initialize ensemble_weights table
python scripts/initialize_ensemble_weights.py

# Expected output:
# Created 7 ensemble weight records
# ✓ XGBoost: 0.28
# ✓ Neural Network: 0.22
# ✓ Random Forest: 0.18
# ✓ Bayesian: 0.15
# ✓ ARIMA: 0.08
# ✓ Decision Trees: 0.06
# ✓ Linear Regression: 0.03
```

---

## STEP 2: BACKEND SERVICE DEPLOYMENT

### 2.1 Update Docker Images
```bash
# Build backend with Week 5-7 code
docker build \
  --build-arg ENVIRONMENT=production \
  -t prediction-backend:week5-7-latest \
  -f Dockerfile .

# Tag for registry
docker tag prediction-backend:week5-7-latest \
  your-registry/prediction-backend:week5-7-latest

# Push to registry (if using cloud)
docker push your-registry/prediction-backend:week5-7-latest
```

### 2.2 Update Docker Compose
```yaml
# In docker-compose.prod.yml
services:
  backend:
    image: prediction-backend:week5-7-latest
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/predictions
      REDIS_URL: redis://cache:6379
      ODDS_SYNC_INTERVAL: 10
      ENSEMBLE_RETRAIN_HOUR: 3
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    depends_on:
      db:
        condition: service_healthy
      cache:
        condition: service_healthy
    ports:
      - "8000:8000"
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
```

### 2.3 Launch Updated Backend
```bash
# Stop current backend
docker-compose -f docker-compose.prod.yml down backend

# Start updated backend
docker-compose -f docker-compose.prod.yml up -d backend

# Verify startup (wait 10 seconds)
sleep 10

# Check logs
docker logs -f backend --tail=50

# Expected log output:
# INFO: Started server process [1]
# INFO: Waiting for application startup.
# INFO: Application startup complete.
# INFO: Uvicorn running on http://0.0.0.0:8000
```

---

## STEP 3: SERVICE HEALTH VERIFICATION

### 3.1 API Endpoint Verification
```bash
# Test basic health endpoint
curl -X GET http://localhost:8000/health
# Expected: {"status": "healthy", "timestamp": "..."}

# Test odds endpoint
curl -X GET "http://localhost:8000/api/v1/odds/event/nba_2024_03_22_lal_gsw" \
  -H "Authorization: Bearer $AUTH_TOKEN"
# Expected: {"success": true, "data": {...event odds...}, "timestamp": "..."}

# Test ensemble prediction endpoint
curl -X POST "http://localhost:8000/api/v1/ensemble/prediction/nba_2024_03_22_lal_gsw" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sport": "nba", "include_probabilities": true}'
# Expected: {"success": true, "data": {"ensemble_prediction": 0.623, ...}, ...}

# Test analytics endpoint
curl -X GET "http://localhost:8000/api/v1/analytics/arima-forecast/nba_scoring" \
  -H "Authorization: Bearer $AUTH_TOKEN"
# Expected: {"success": true, "data": {"forecast": [...], "confidence_intervals": [...]}, ...}
```

### 3.2 Database Connectivity Check
```python
# Run verification script
python scripts/verify_db_connection.py

# Expected output:
# ✓ Connected to PostgreSQL
# ✓ Found 4 new tables (odds_records, odds_movement, ensemble_weights, synthetic_datasets)
# ✓ ensemble_weights table has 7 records
# ✓ Able to execute queries
# ✓ All tables have proper indexes
```

### 3.3 Service Integration Check
```python
# Run integration test script
python scripts/verify_service_integration.py

# Expected output:
# ✓ OddsAggregatorService initialized
# ✓ AdvancedModelEnsemble loaded (7 models)
# ✓ SyntheticDataGenerator ready
# ✓ MultiModelEnsemble service ready
# ✓ All services communicating correctly
# ✓ Redis cache working
# ✓ Database models initialized
```

---

## STEP 4: LOAD TESTING & PERFORMANCE VALIDATION

### 4.1 Load Test Script
```bash
# Run load test (uses locust)
pip install locust

# Run 100 concurrent users for 60 seconds
locust -f backend/tests/load_tests.py \
  -u 100 \
  -r 10 \
  -t 60s \
  --headless \
  -H http://localhost:8000 \
  --csv=load_test_results

# Expected results:
# Average response time: < 300ms
# 95th percentile: < 500ms
# Error rate: < 1%
# Requests/second: 1000+
```

### 4.2 Calculate Performance Baseline
```python
# Run performance benchmarking
python scripts/performance_benchmark.py

# Expected output:
# Benchmark Results:
# ✓ GET /odds/event: avg 45ms, p95 75ms
# ✓ GET /ensemble/prediction: avg 180ms, p95 280ms
# ✓ GET /analytics/arima: avg 250ms, p95 400ms
# ✓ GET /odds/comparison: avg 60ms, p95 100ms
# 
# System Throughput: 1200+ requests/sec ✓
# Concurrent Users Supported: 1000+ ✓
```

---

## STEP 5: MODEL INITIALIZATION & TRAINING

### 5.1 Initialize ML Models
```python
# Generate initial model files
python scripts/initialize_ml_models.py

# Expected output:
# Loading model checkpoints...
# ✓ XGBoost model loaded (2.1 MB)
# ✓ Neural Network model loaded (5.3 MB)
# ✓ Random Forest model loaded (1.8 MB)
# ✓ Bayesian prior loaded (0.1 MB)
# ✓ ARIMA parameters loaded (0.02 MB)
# 
# Models initialized successfully
```

### 5.2 Retrain Ensemble Weights
```bash
# Manually trigger ensemble weight retraining
curl -X POST "http://localhost:8000/api/v1/ensemble/retrain-weights" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sport_key": "nba", "force_retrain": true}'

# Expected response:
# {
#   "success": true,
#   "data": {
#     "weights_updated": 7,
#     "xgboost_weight": 0.285,
#     "neural_network_weight": 0.218,
#     ...
#     "retraining_time_ms": 1250
#   },
#   "timestamp": "2026-03-22T15:30:00Z"
# }
```

---

## STEP 6: ODDS INTEGRATION SETUP

### 6.1 Configure Sportsbook API Keys
```bash
# Add to .env or secrets manager
# DraftKings
DRAFTKINGS_API_KEY=your_dk_key
DRAFTKINGS_API_SECRET=your_dk_secret
DRAFTKINGS_ACCOUNT_ID=your_account_id

# FanDuel
FANDUEL_API_KEY=your_fd_key
FANDUEL_API_SECRET=your_fd_secret

# BetMGM
BETMGM_API_KEY=your_mgm_key
BETMGM_API_SECRET=your_mgm_secret

# Caesars
CAESARS_API_KEY=your_caesars_key
CAESARS_API_SECRET=your_caesars_secret
```

### 6.2 Start Odds Sync Service
```python
# Test odds sync service
python scripts/test_odds_sync.py

# Expected output:
# Starting odds sync service...
# [14:23:15] Syncing odds for 45 NBA events
# [14:23:20] ✓ DraftKings: 45 events synced
# [14:23:22] ✓ FanDuel: 45 events synced
# [14:23:25] ✓ BetMGM: 45 events synced
# [14:23:27] ✓ Caesars: 43 events synced (2 unavailable)
# [14:23:30] Consensus calculated for 45 events
# Total odds stored: 178 records
# Next sync in 10 seconds...
```

### 6.3 Verify Real-Time Odds Updates
```bash
# Monitor live odds updates
curl -X GET "http://localhost:8000/api/v1/odds/event/nba_2024_03_22_lal_gsw" \
  -H "Authorization: Bearer $AUTH_TOKEN" | jq '.data | {
    event_id: .event_id,
    timestamp: .timestamp,
    providers: [.draftkings_moneyline, .fanduel_moneyline, .betmgm_moneyline],
    consensus: .consensus_moneyline
}'

# Should show live updating odds
# Repeat query 2-3 times, odds should update
```

---

## STEP 7: MONITORING & ALERTING SETUP

### 7.1 Configure CloudWatch Metrics (AWS)
```python
# Deploy CloudWatch monitoring
python scripts/setup_cloudwatch_metrics.py

# Creates metrics for:
# - API response times
# - Error rates by endpoint
# - Odds sync latency
# - Ensemble model agreement
# - Database query performance
# - Cache hit rates
# - Synthetic data generation timing
```

### 7.2 Configure Alarms
```python
# Create CloudWatch alarms
python scripts/setup_cloudwatch_alarms.py

# Alarms created:
# - API response time > 500ms → Alert
# - Error rate > 5% → Alert
# - Odds sync failure → Alert
# - Database connection errors → Alert
# - Ensemble model disagreement > 30% → Warning
# - Cache hit rate < 70% → Warning
```

### 7.3 Set Up Log Aggregation
```bash
# Configure log shipping to CloudWatch
cat > /etc/logrotate.d/prediction-platform << 'EOF'
/var/log/prediction-platform/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 ubuntu ubuntu
}
EOF

# Restart log rotation
sudo systemctl restart logrotate
```

---

## STEP 8: FINAL VALIDATION (48-HOUR MONITORING)

### 8.1 Hour 0-2: Basic Functionality
```checklist
- ☐ All endpoints responding (< 500ms)
- ☐ Error rate < 1%
- ☐ Odds syncing at 10-second intervals
- ☐ Ensemble predictions generating correctly
- ☐ Database inserts working
- ☐ Redis cache active
```

### 8.2 Hour 2-24: Extended Testing
```checklist
- ☐ Monitor daily ensemble retraining (3 AM UTC)
- ☐ Verify synthetic data generation jobs
- ☐ Check Bayesian update performance
- ☐ Validate ARIMA forecasts
- ☐ Ensure odds movement detection working
- ☐ Verify market discord alerts
```

### 8.3 Hour 24-48: Production Validation
```checklist
- ☐ API response times stable (avg 205ms)
- ☐ Ensemble accuracy > 63% (on holdout test set)
- ☐ Odds consensus within 2% of manual checks
- ☐ No database integrity issues
- ☐ No memory leaks (check container memory)
- ☐ All scheduled tasks completed successfully
```

### 8.4 Run Validation Script
```bash
# Run 48-hour validation report
python scripts/generate_deployment_report.py

# Expected output:
# ========== DEPLOYMENT VALIDATION REPORT ==========
# Generated: 2026-03-24 14:30:00
# 
# API HEALTH:
# ✓ 100% endpoints operational
# ✓ Average response time: 203ms
# ✓ Error rate: 0.3% (target: < 1%)
# ✓ P95 latency: 285ms (target: < 300ms)
# 
# SERVICE HEALTH:
# ✓ OddsAggregatorService: 1245 updates processed
# ✓ Ensemble predictions: 823 generated
# ✓ Bayesian updates: 156 completed
# ✓ Synthetic data: 2340 samples generated
# 
# DATABASE:
# ✓ 4347 new odds records
# ✓ 183 movement records
# ✓ 7 ensemble weight updates
# ✓ No integrity issues
# 
# PERFORMANCE:
# ✓ Throughput: 1250 req/sec (sustained)
# ✓ Concurrent users: 850 peak
# ✓ Cache hit rate: 82%
# 
# RECOMMENDATION: ✅ PRODUCTION READY
```

---

## ROLLBACK PROCEDURE (If Needed)

### Complete Rollback to Previous Version
```bash
# 1. Stop current backend
docker-compose -f docker-compose.prod.yml down backend

# 2. Restore database backup
pg_restore -d predictions_db "backups/$BACKUP_FILE"

# 3. Verify backup restored
psql -U postgres -d predictions_db -c "SELECT COUNT(*) FROM odds_records;"
# Should return 0 (or previous count if Week 5-7 had been running)

# 4. Switch back to previous image
docker run -d \
  --name backend \
  -e DATABASE_URL=$DATABASE_URL \
  prediction-backend:latest  # Previous version

# 5. Verify previous version operational
curl http://localhost:8000/health

# 6. Alert team of rollback
echo "Rolled back to previous version" | slack-notify #incidents
```

---

## TROUBLESHOOTING GUIDE

### Issue: API Endpoint Returns 500 Error
```bash
# Check backend logs
docker logs -f backend --tail=100

# Common causes:
# 1. Database connection pool exhausted
#    Solution: Increase DATABASE_POOL_SIZE in .env
# 
# 2. Redis cache unavailable
#    Solution: Restart cache: docker-compose restart cache
# 
# 3. Missing environment variable
#    Solution: Add to .env and restart backend
```

### Issue: Odds Sync Failing
```bash
# Verify provider credentials
python scripts/test_provider_credentials.py

# Test individual provider
python -c "
from backend.app.services.odds_aggregator_service import DraftKingsOddsProvider
provider = DraftKingsOddsProvider()
print(provider.test_connection())
"

# Check provider API status
curl https://ak-static.cms.nba.com/referee/  # DraftKings uses ESPN data

# Solution: Verify API keys and networks
```

### Issue: High Ensemble Prediction Variance
```bash
# Check model agreement
curl http://localhost:8000/api/v1/ensemble/individual-predictions/$EVENT_ID

# Check recent model weights
curl http://localhost:8000/api/v1/ensemble/model-weights/nba

# Trigger fresh weight retraining
curl -X POST http://localhost:8000/api/v1/ensemble/retrain-weights \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Issue: Slow Response Times
```bash
# Check database performance
psql -c "SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 5;"

# Check query plans
EXPLAIN ANALYZE SELECT * FROM odds_records WHERE event_id = 'nba_2024_03_22_lal_gsw';

# Check cache hit rate
redis-cli INFO stats | grep hits

# Solution: Add indexes on frequently queried columns
```

---

## ONGOING OPERATIONS

### Daily Tasks
```
3:00 AM UTC - Automatic ensemble weight retraining
6:00 AM UTC - Synthetic data augmentation job
```

### Weekly Tasks
```
Monday 1:00 AM UTC - Model accuracy validation
Wednesday 2:00 AM UTC - Database maintenance (VACUUM/ANALYZE)
Friday 3:00 AM UTC - Performance report generation
```

### Monthly Tasks
```
1st of month - Review odds provider reliability
1st of month - Model retraining with full month of data
15th of month - Load testing (1000+ concurrent users)
```

---

## SUCCESS CRITERIA

✅ **Deployment Successful When:**
- All 16 API endpoints responding with < 500ms latency
- Database contains expected schema (4 new tables)
- Odds syncing from 4+ providers at 10-second intervals
- Ensemble making predictions with > 63% accuracy on holdout test
- Error rate < 1% across all endpoints
- Load test supporting 1000+ concurrent users
- Zero data corruption or integrity issues
- All scheduled jobs completing successfully
- Monitoring and alerting operational

---

## CONTACT & ESCALATION

```
Deployment Issues: #deployment-support Slack
Database Issues: database-team@company.com
Model Issues: ml-team@company.com
Sportsbook API Issues: open ticket with provider support

On-call: See PagerDuty rotation
Runbooks: In /docs/runbooks/
```

---

**Deployment Document Version:** 1.0  
**Last Reviewed:** 2026-03-22  
**Next Review:** 2026-04-22

