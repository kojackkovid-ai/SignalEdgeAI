# Phase 5: Verification & Deployment - Complete Implementation Guide

## Overview
Phase 5 executes the final verification of all improvements and deploys the enhanced prediction system to production with monitoring and rollback strategies.

**Timeline**: 21 hours  
**Status**: NOW STARTING  
**Prerequisite**: Phases 2, 3, 4 completion (Dashboard, Confidence Fixes, Outcome Tracking)

---

## Phase 5 Execution Plan

### Part 1: Pre-Deployment Verification (4 hours)

#### 1.1 Run Comprehensive Verification Suite
```bash
cd sports-prediction-platform
python phase5_verification_suite.py
```

**What It Checks**:
- ✓ Confidence fixes properly integrated
- ✓ Analytics endpoints implemented  
- ✓ Database schema ready for production
- ✓ Outcome tracking fields populated
- ✓ Accuracy metrics calculable

**Expected Output**:
- Deployment readiness status (GREEN/YELLOW/RED)
- Comparison: baseline vs current accuracy metrics
- Risk assessment
- Detailed deployment steps & rollback plan

#### 1.2 Staging Deployment
**Duration**: 2 hours

**Steps**:
```bash
# 1. Create deployment branch
git checkout -b feature/phase5-production-deployment
git tag v1.0-pre-deployment

# 2. Build staging container
docker build -t sports-prediction:staging -f Dockerfile.backend .
docker-compose -f docker-compose.staging.yml up -d

# 3. Run staging smoke tests
python test_staging_deployment.py --endpoint=staging

# 4. Verify analytics dashboard loads
curl http://staging:8000/api/analytics/accuracy

# 5. Test confidence calculations with sample game
curl -X POST http://staging:8000/api/test/prediction \
  -H "Content-Type: application/json" \
  -d '{"sport_key": "nba", "event_id": "test123"}'
```

**Success Criteria**:
- All endpoints respond with <100ms latency
- Analytics dashboard renders without errors
- Sample prediction generates with new Bayesian confidence
- Database queries return results within 2 seconds
- No error logs in application output

**If Issues Found**:
1. Check analytics endpoint query performance (database indexes)
2. Verify bayesian_confidence.py is imported correctly
3. Confirm outcome tracking fields are populated
4. Review error logs for import/configuration issues

#### 1.3 Accuracy Metrics Validation
**Duration**: 1 hour

**Steps**:
```bash
# Run pre-deployment audit
python audit_accuracy_simple.py --days=30 --environment=staging

# Compare to baseline
python phase5_verification_suite.py --compare-baseline

# Generate comparison report
python generate_comparison_report.py --output=phase5_accuracy_report.json
```

**Expected Results**:
- Win rate: ≥ baseline (or explain why calibration improves)
- Calibration error: < baseline (confidence closer to actual results)
- ROI: ≥ baseline
- No anomalies detected

**If Metrics Degraded**:
1. Check if confidence field is properly populated
2. Run `python explain_confidence_calculation.py` to trace specific predictions
3. Compare old vs new confidence for same predictions
4. Verify ML models are loaded correctly

---

### Part 2: Database Backup & Safety (2 hours)

#### 2.1 Create Production Backup
```bash
# Backup current database
sqlite3 backend/sports.db ".backup 'backups/sports_pre_phase5_$(date +%Y%m%d_%H%M%S).db'"

# Backup PostgreSQL (if in production)
pg_dump sports_db > backups/sports_pre_phase5_$(date +%Y%m%d_%H%M%S).sql

# Verify backup integrity
python verify_backup_integrity.py --backup-file=latest
```

#### 2.2 Create Archive of Old Predictions
```sql
-- Create archive table for old confidence scores
INSERT INTO prediction_archive 
SELECT * FROM prediction 
WHERE created_at < datetime('now', '-30 days');

-- Keep all prediction data intact with old confidence marked
ALTER TABLE prediction ADD COLUMN confidence_version TEXT DEFAULT 'hash-based';

-- After deployment, update new predictions
UPDATE prediction 
SET confidence_version = 'bayesian'
WHERE created_at >= datetime('now', '-1 day');
```

#### 2.3 Implement Monitoring Setup
```python
# Set up alerts for Phase 5 success metrics

PHASE5_MONITORING = {
    "metrics_to_track": [
        "prediction_win_rate_by_sport",  # Alert if drops >10%
        "confidence_calibration_error",   # Alert if increases >5%
        "analytics_api_response_time",    # Alert if >500ms p95
        "prediction_generation_time",     # Alert if >10s
        "database_query_latency",         # Alert if >2s for analytics queries
        "new_predictions_count",          # Track daily volume
        "resolved_predictions_count"      # Verify outcome tracking is working
    ],
    "alert_thresholds": {
        "win_rate_degradation": -10,           # percent
        "calibration_error_increase": 5,       # percentage points
        "api_error_rate": 5,                   # percent
        "api_timeout_rate": 2                  # percent
    },
    "alert_recipients": ["dev-team@company.com", "ops@company.com"]
}
```

---

### Part 3: Production Deployment (8 hours)

#### 3.1 Blue-Green Deployment Setup
```bash
# Current production = BLUE (old confidence)
# New deployment = GREEN (Bayesian confidence)

# 1. Verify BLUE is stable
curl http://production:8000/health

# 2. Start GREEN environment with new code
docker pull sports-prediction:latest
docker tag sports-prediction:latest sports-prediction:v1.0-bayesian
docker run -d --name prediction-green \
  -e CONFIDENCE_METHOD=bayesian \
  -e DB_BACKUP_ON_STARTUP=true \
  sports-prediction:v1.0-bayesian

# 3. Run health checks on GREEN
python test_green_deployment.py --wait=60s

# 4. Verify GREEN analytics endpoints work
curl http://production-green:8000/api/analytics/accuracy
```

#### 3.2 Traffic Routing & Canary Deployment
```bash
# Stage 1: Route 5% of traffic to GREEN (monitor for 2 hours)
# Stage 2: Route 25% of traffic to GREEN (monitor for 2 hours)
# Stage 3: Route 50% of traffic to GREEN (monitor for 1 hour)
# Stage 4: Route 100% of traffic to GREEN (go live)

# Using nginx load balancer
# upstream production_blue { server prod-blue:8000; }
# upstream production_green { server prod-green:8000; }
# 
# location / {
#     if ($random < 0.05) {
#         proxy_pass http://production_green;
#     } else {
#         proxy_pass http://production_blue;
#     }
# }
```

#### 3.3 Monitoring During Deployment (4 hours)
```python
# Real-time metrics to monitor
DEPLOYMENT_MONITORING = {
    "check_interval": 60,  # seconds
    "duration": 4 * 3600,  # 4 hours
    "metrics": [
        ("win_rate_by_sport", "compare_blue_vs_green"),
        ("prediction_confidence_distribution", "check_bayesian_coverage"),
        ("api_response_times", "p50_p95_p99"),
        ("error_rates", "by_endpoint"),
        ("database_connection_pool", "utilization"),
        ("memory_usage", "per_container"),
        ("requests_per_second", "traffic_volume")
    ]
}

# Alert conditions
if win_rate_degradation > 10%:
    send_alert("CRITICAL: Win rate degraded >10%, initiating rollback")
    initiate_rollback()

if confidence_calibration_worse:
    send_alert("WARNING: Calibration error increased, check bayesian_confidence.py")
    review_logs()
```

#### 3.4 Complete Switchover
```bash
# After 4+ hours of successful canary deployment:

# 1. Route 100% to GREEN
# 2. Update BLUE config for debugging/rollback
# 3. Keep BLUE running for 24 hours as backup
# 4. Enable automatic failover on errors

# Test complete switchover
python verify_production_switchover.py --wait=300s
```

---

### Part 4: Post-Deployment Validation (5 hours)

#### 4.1 Comprehensive Accuracy Audit
```bash
# After Phase 5 completion, run full audit on production
python audit_accuracy_simple.py --days=30 --environment=production --output=post_phase5_audit.json

# Compare against baseline
python generate_comparison_report.py \
  --baseline=pre_phase5_audit.json \
  --current=post_phase5_audit.json \
  --output=phase5_results_final.json
```

**Expected Metrics** (minimum acceptable):
- Win Rate: ≥ 50% (baseline was 50%)
- Calibration Error: < 0.16 (baseline was 0.1625)
- ROI: ≥ +5% (baseline was +5%)
- Error Rate: < 2%
- P95 Response Time: < 5 seconds

#### 4.2 Feature Verification
```bash
# Verify all Phase 4 features work with Phase 3 changes
python test_all_features_post_phase5.py

# Test cases:
# 1. Dashboard loads with new metrics
# 2. Confidence values are Bayesian-based
# 3. Outcome tracking is active
# 4. Real predictions are being generated
# 5. Accuracy trends are calculated correctly
```

#### 4.3 Document Deployment
```bash
# Create deployment record
cat > PHASE5_DEPLOYMENT_RECORD.md << 'EOF'
# Phase 5 Deployment Record - April 6, 2026

## Timeline
- Verification: [4 hours]
- Backup & Safety: [2 hours]
- Deployment: [8 hours]
- Validation: [5 hours]

## Results
- Upgraded confidence from MD5-hash to Bayesian calculation
- Deployed analytics dashboard for real-time metrics
- Implemented outcome tracking for accuracy verification
- Achieved [X]% win rate with [Y] confidence calibration

## Metrics Achieved
- Pre-deployment win rate: [baseline]%
- Post-deployment win rate: [current]%
- Improvement: [+/-]X%

## Issues & Resolutions
[Document any issues encountered and how they were resolved]

## Next Steps
[Document recommended follow-up actions]

## By: [Your Name]
## Date: [Date]
EOF
```

---

### Part 5: Rollback Plan (On-Demand)

#### If Critical Issues Detected:

**Immediate Rollback** (< 15 minutes):
```bash
# Revert traffic to BLUE (old system)
# nginx: route 100% to production_blue

# Disable new analytics endpoints
# Disable Bayesian confidence calculations
# Switch back to MD5-hash reasoning

# Monitor error rate drops
# Verify service stability
```

**Investigation Phase** (1-4 hours):
```bash
# Review logs to identify issue
# Check database integrity
# Verify ML models are loaded
# Review confidence score calculations
# Test with sample data

# Analysis categories:
# - Data issues (corrupted predictions, missing fields)
# - Code issues (import errors, calculation bugs)
# - Infrastructure issues (database connection, memory)
# - Performance issues (slow queries, timeouts)
```

**Root Cause & Re-Deployment** (varies):
```bash
# Fix identified issues
# Re-test in staging environment
# Re-deploy to production with fixes
# Monitor for 8+ hours before considering stable
```

---

## Success Criteria for Phase 5

✓ **Confidence fixes verified**: Bayesian confidence properly integrated  
✓ **Analytics endpoints operational**: Accuracy metrics accessible via API  
✓ **Outcome tracking active**: Predictions being resolved and tracked  
✓ **Accuracy maintained or improved**: Win rate ≥ baseline  
✓ **Performance acceptable**: P95 response time < 5 seconds  
✓ **Monitoring in place**: Alerts configured for key metrics  
✓ **Rollback plan tested**: Can revert within 15 minutes if needed  
✓ **Documentation complete**: Deployment record created

---

## Phase 5 Checklist

- [ ] Ran phase5_verification_suite.py - reviewed output
- [ ] Deployed to staging environment
- [ ] Ran accuracy audit on staging - results match expectations
- [ ] Created production database backup
- [ ] Tested analytics endpoints in staging
- [ ] Verified confidence calculations with test games
- [ ] Configured monitoring and alerts
- [ ] Set up blue-green deployment infrastructure
- [ ] Implemented canary traffic routing
- [ ] Tested rollback procedure in staging
- [ ] Deployed GREEN version to production
- [ ] Monitored canary deployment for 4+ hours
- [ ] Completed full traffic switchover
- [ ] Ran post-deployment accuracy audit
- [ ] Verified all features working (dashboard, analytics, tracking)
- [ ] Documented deployment results
- [ ] Briefed team on new metrics and system changes
- [ ] Set up ongoing monitoring and alerting

---

## Phase 5 Summary

After Phase 5 completion, the sports prediction platform will have:

1. **Real Confidence Scores**: Replaced hash-based pseudo-random values with Bayesian statistical calculations
2. **Live Analytics Dashboard**: Real-time accuracy metrics visible to users and team
3. **Outcome Tracking**: All predictions being resolved and tracked for continuous improvement
4. **Verified Accuracy**: Baseline metrics established and monitored
5. **Production Readiness**: Monitoring, alerts, rollback procedures all in place
6. **Documentation**: Complete record of deployment and performance metrics

The system is now ready for:
- Real user predictions with correct confidence
- Continuous accuracy monitoring
- Data-driven model improvements
- Future feature development based on real performance data
