"""
Database Optimization Guide
Includes indexes, query optimization strategies, and migration scripts
"""

# Database Indexes to Add
# These are the recommended indexes for frequently queried columns

RECOMMENDED_INDEXES = {
    "users": [
        {
            "name": "idx_users_email",
            "columns": ["email"],
            "unique": True,
            "reason": "Email lookups during login/registration"
        },
        {
            "name": "idx_users_subscription_tier",
            "columns": ["subscription_tier"],
            "unique": False,
            "reason": "Filtering users by subscription tier (platform metrics)"
        },
        {
            "name": "idx_users_created_at",
            "columns": ["created_at"],
            "unique": False,
            "reason": "Time-based user queries and reports"
        },
        {
            "name": "idx_users_club_100_unlocked",
            "columns": ["club_100_unlocked"],
            "unique": False,
            "reason": "Filtering Club 100 enabled users"
        },
    ],
    "predictions": [
        {
            "name": "idx_predictions_sport_league",
            "columns": ["sport", "league"],
            "unique": False,
            "reason": "Most common filter combination for predictions"
        },
        {
            "name": "idx_predictions_sport_key",
            "columns": ["sport_key"],
            "unique": False,
            "reason": "Sport-specific prediction queries"
        },
        {
            "name": "idx_predictions_created_at",
            "columns": ["created_at"],
            "unique": False,
            "reason": "Latest predictions, time-based queries"
        },
        {
            "name": "idx_predictions_event_id",
            "columns": ["event_id"],
            "unique": False,
            "reason": "Looking up predictions by ESPN event ID"
        },
        {
            "name": "idx_predictions_resolved_at",
            "columns": ["resolved_at"],
            "unique": False,
            "reason": "Active predictions (WHERE resolved_at IS NULL)"
        },
        {
            "name": "idx_predictions_player_market",
            "columns": ["player", "market_key"],
            "unique": False,
            "reason": "Player prop queries by market"
        },
        {
            "name": "idx_predictions_is_club_100",
            "columns": ["is_club_100_pick"],
            "unique": False,
            "reason": "Filtering Club 100 picks"
        },
    ],
    "user_predictions": [
        {
            "name": "idx_user_predictions_user_id",
            "columns": ["user_id"],
            "unique": False,
            "reason": "User prediction history queries"
        },
        {
            "name": "idx_user_predictions_created_at",
            "columns": ["created_at"],
            "unique": False,
            "reason": "Time-based prediction ordering"
        },
    ],
    "training_sessions": [
        {
            "name": "idx_training_sessions_sport_market",
            "columns": ["sport_key", "market_type"],
            "unique": False,
            "reason": "Sport/market-specific training history"
        },
        {
            "name": "idx_training_sessions_started_at",
            "columns": ["started_at"],
            "unique": False,
            "reason": "Recent training session queries"
        },
        {
            "name": "idx_training_sessions_status",
            "columns": ["status"],
            "unique": False,
            "reason": "Finding in-progress or failed trainings"
        },
    ],
    "model_performance_metrics": [
        {
            "name": "idx_model_perf_sport_market_date",
            "columns": ["sport_key", "market_type", "measurement_date"],
            "unique": False,
            "reason": "Performance trending queries"
        },
        {
            "name": "idx_model_perf_drift",
            "columns": ["has_drift"],
            "unique": False,
            "reason": "Finding anomalies/drift detection"
        },
    ],
    "prediction_records": [
        {
            "name": "idx_prediction_records_user_id",
            "columns": ["user_id"],
            "unique": False,
            "reason": "User accuracy tracking"
        },
        {
            "name": "idx_prediction_records_created_at",
            "columns": ["created_at"],
            "unique": False,
            "reason": "Recent record queries"
        },
        {
            "name": "idx_prediction_records_outcome",
            "columns": ["outcome"],
            "unique": False,
            "reason": "Hit/miss filtering"
        },
    ],
}

# SQL Migration Script
# Execute this in your database to add recommended indexes

SQL_MIGRATION_UP = """
-- Users Table Indexes
CREATE INDEX IF NOT EXISTS idx_users_subscription_tier ON users(subscription_tier);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
CREATE INDEX IF NOT EXISTS idx_users_club_100_unlocked ON users(club_100_unlocked);

-- Predictions Table Indexes (Most Important!)
CREATE INDEX IF NOT EXISTS idx_predictions_sport_league ON predictions(sport, league);
CREATE INDEX IF NOT EXISTS idx_predictions_sport_key ON predictions(sport_key);
CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON predictions(created_at);
CREATE INDEX IF NOT EXISTS idx_predictions_event_id ON predictions(event_id);
CREATE INDEX IF NOT EXISTS idx_predictions_resolved_at ON predictions(resolved_at);
CREATE INDEX IF NOT EXISTS idx_predictions_player_market ON predictions(player, market_key);
CREATE INDEX IF NOT EXISTS idx_predictions_is_club_100 ON predictions(is_club_100_pick);

-- User Predictions Junction Table
CREATE INDEX IF NOT EXISTS idx_user_predictions_user_id ON user_predictions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_predictions_created_at ON user_predictions(created_at);

-- Training Sessions
CREATE INDEX IF NOT EXISTS idx_training_sessions_sport_market ON training_sessions(sport_key, market_type);
CREATE INDEX IF NOT EXISTS idx_training_sessions_started_at ON training_sessions(started_at);
CREATE INDEX IF NOT EXISTS idx_training_sessions_status ON training_sessions(status);

-- Model Performance Metrics
CREATE INDEX IF NOT EXISTS idx_model_perf_sport_market_date ON model_performance_metrics(sport_key, market_type, measurement_date);
CREATE INDEX IF NOT EXISTS idx_model_perf_drift ON model_performance_metrics(has_drift);

-- Prediction Records (if exists)
CREATE INDEX IF NOT EXISTS idx_prediction_records_user_id ON prediction_records(user_id);
CREATE INDEX IF NOT EXISTS idx_prediction_records_created_at ON prediction_records(created_at);
CREATE INDEX IF NOT EXISTS idx_prediction_records_outcome ON prediction_records(outcome);
"""

# Rollback Script (Remove indexes if needed)
SQL_MIGRATION_DOWN = """
-- Remove all created indexes
DROP INDEX IF EXISTS idx_users_subscription_tier;
DROP INDEX IF EXISTS idx_users_created_at;
DROP INDEX IF EXISTS idx_users_club_100_unlocked;

DROP INDEX IF EXISTS idx_predictions_sport_league;
DROP INDEX IF EXISTS idx_predictions_sport_key;
DROP INDEX IF EXISTS idx_predictions_created_at;
DROP INDEX IF EXISTS idx_predictions_event_id;
DROP INDEX IF EXISTS idx_predictions_resolved_at;
DROP INDEX IF EXISTS idx_predictions_player_market;
DROP INDEX IF EXISTS idx_predictions_is_club_100;

DROP INDEX IF EXISTS idx_user_predictions_user_id;
DROP INDEX IF EXISTS idx_user_predictions_created_at;

DROP INDEX IF EXISTS idx_training_sessions_sport_market;
DROP INDEX IF EXISTS idx_training_sessions_started_at;
DROP INDEX IF EXISTS idx_training_sessions_status;

DROP INDEX IF EXISTS idx_model_perf_sport_market_date;
DROP INDEX IF EXISTS idx_model_perf_drift;

DROP INDEX IF EXISTS idx_prediction_records_user_id;
DROP INDEX IF EXISTS idx_prediction_records_created_at;
DROP INDEX IF EXISTS idx_prediction_records_outcome;
"""

# Query Optimization Strategies

QUERY_OPTIMIZATION_GUIDE = """
# Database Query Optimization Guide

## 1. Predictions Queries (Most Critical - High Volume)

### Current Issue:
- Predictions table likely has millions of rows
- Frequent queries: "Get all predictions for sport X"
- Without indexes: Full table scan takes seconds

### Solution:
- ✅ ADDED: idx_predictions_sport_league (sport, league)
- ✅ ADDED: idx_predictions_created_at for ordering
- ✅ ADDED: idx_predictions_event_id for ESPN lookups

### Optimized Query Pattern:
```sql
SELECT * FROM predictions 
WHERE sport_key = 'basketball_nba' 
  AND created_at > NOW() - INTERVAL '24 hours'
  AND resolved_at IS NULL
ORDER BY created_at DESC
LIMIT 50;
```

## 2. User Prediction History (Common Query)

### Current Issue:
- Joining user_predictions + predictions tables repeatedly
- Without indexes: Slow for users with many predictions

### Solution:
- ✅ ADDED: idx_user_predictions_user_id
- ✅ ADDED: idx_user_predictions_created_at

### Optimized Query Pattern:
```sql
SELECT p.* FROM predictions p
JOIN user_predictions up ON p.id = up.prediction_id
WHERE up.user_id = '123' 
ORDER BY up.created_at DESC
LIMIT 100;
```

## 3. Platform Metrics Queries

### Current Issue:
- Scanning all predictions to count hits/misses by sport
- Without indexes: Very slow aggregation

### Solution:
- ✅ ADDED: idx_predictions_sport_key (quick sport filtering)
- ✅ ADDED: idx_predictions_resolved_at (only resolved predictions)

### Optimized Query:
```sql
SELECT 
    sport_key,
    COUNT(*) AS total,
    SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) AS wins
FROM predictions
WHERE resolved_at IS NOT NULL
GROUP BY sport_key;
```

## 4. Model Training & Performance Queries

### Current Issue:
- Querying training history by sport/market is slow
- Performance drift detection requires scanning many records

### Solution:
- ✅ ADDED: idx_training_sessions_sport_market
- ✅ ADDED: idx_model_perf_sport_market_date

## 5. Caching Strategy

### Implement Redis Caching for:
1. **User Tier Lookups** - Cache for 5 minutes
2. **Prediction Counts** - Cache by sport for 2 minutes
3. **Model Performance** - Cache for 10 minutes
4. **Platform Metrics** - Cache for 5 minutes

### Pattern:
```python
async def get_predictions(sport_key: str, limit: int = 50):
    cache_key = f"predictions:{sport_key}:limit{limit}"
    
    # Try cache
    cached = await cache_service.get(cache_key)
    if cached:
        return cached
    
    # Query DB
    result = await session.execute(
        select(Prediction)
        .where(Prediction.sport_key == sport_key)
        .limit(limit)
    )
    
    # Cache for 2 minutes
    await cache_service.setex(cache_key, 120, result)
    return result
```

## 6. Connection Pooling

### Current Configuration (backend/app/database.py):
- pool_size=20 (connections ready)
- max_overflow=40 (additional connections under load)
- pool_pre_ping=True (validates connection health)

### Monitor with:
```python
# In monitoring service
pool_status = engine.pool.checkedout()
logger.info(f"Database connections: {pool_status} active")
```

## 7. Slow Query Logging

### Enable PostgreSQL Slow Query Log:
```sql
-- In PostgreSQL
SET log_min_duration_statement = 1000;  -- Log queries > 1 second
```

### Monitor in app logs:
- Queries > 1 second are logged with WARN level
- Queries > 5 seconds cause alerts

## 8. Query Analysis Using EXPLAIN

### Before optimization:
```sql
EXPLAIN ANALYZE 
SELECT * FROM predictions WHERE sport = 'soccer' ORDER BY created_at DESC;
```

### Should see index scan after optimization:
```
Index Scan Backward using idx_predictions_sport_key on predictions...
```

## Performance Targets

- Prediction fetches: < 500ms
- User history queries: < 2s
- Platform metrics: < 5s
- Model training queries: < 1s
"""

# Python Utility Functions for DB Optimization

PYTHON_MONITORING_CODE = """
# Add to app/utils/db_monitoring.py

import logging
from datetime import datetime, timedelta
from sqlalchemy import text, func
from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

async def check_slow_queries():
    '''Monitor for slow queries in PostgreSQL'''
    try:
        async with AsyncSessionLocal() as session:
            # Query execution statistics (PostgreSQL specific)
            result = await session.execute(text('''
                SELECT query, calls, total_time, mean_time
                FROM pg_stat_statements
                WHERE mean_time > 1000
                ORDER BY mean_time DESC
                LIMIT 10;
            '''))
            
            slow_queries = result.fetchall()
            if slow_queries:
                for query in slow_queries:
                    logger.warning(
                        f"Slow query detected",
                        extra={
                            "query": query[0][:100],
                            "calls": query[1],
                            "total_time_ms": float(query[2]),
                            "mean_time_ms": float(query[3]),
                        }
                    )
    except Exception as e:
        logger.debug(f"Could not retrieve slow query stats: {e}")

async def check_index_usage():
    '''Check if indexes are being used effectively'''
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text('''
                SELECT schemaname, tablename, indexname, idx_scan
                FROM pg_stat_user_indexes
                WHERE idx_scan = 0
                ORDER BY tablename;
            '''))
            
            unused_indexes = result.fetchall()
            if unused_indexes:
                logger.info(f"Found {len(unused_indexes)} unused indexes")
                for idx in unused_indexes:
                    logger.debug(f"Unused index: {idx[2]} on {idx[1]}")
    except Exception as e:
        logger.debug(f"Could not retrieve index stats: {e}")

async def check_table_sizes():
    '''Monitor table and index sizes'''
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text('''
                SELECT tablename, 
                       pg_size_pretty(pg_total_relation_size(tablename::regclass)) AS size
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(tablename::regclass) DESC;
            '''))
            
            tables = result.fetchall()
            for table_name, size in tables:
                logger.debug(f"Table {table_name}: {size}")
    except Exception as e:
        logger.debug(f"Could not retrieve table sizes: {e}")

async def run_optimization_checks():
    '''Run all optimization checks periodically'''
    logger.info("Starting database optimization checks")
    await check_slow_queries()
    await check_index_usage()
    await check_table_sizes()
    logger.info("Database optimization checks complete")
"""

# API Endpoint to Trigger Optimization Analysis

OPTIMIZATION_ENDPOINT = """
# Add to app/routes/admin.py (admin only)

from fastapi import APIRouter, Depends
from app.utils.db_monitoring import run_optimization_checks

router = APIRouter(prefix="/api/admin", tags=["Admin"])

@router.post("/db-optimization-check")
async def run_db_optimization_check(current_user: User = Depends(get_admin_user)):
    '''
    Admin endpoint to trigger database optimization analysis
    '''
    try:
        await run_optimization_checks()
        return {
            "status": "success",
            "message": "Optimization checks completed. Check logs for details."
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
"""


if __name__ == "__main__":
    print("Database Optimization Guide")
    print("=" * 50)
    print(f"\nRecommended Indexes: {len(RECOMMENDED_INDEXES)}")
    for table, indexes in RECOMMENDED_INDEXES.items():
        print(f"\n{table}: {len(indexes)} indexes")
        for idx in indexes:
            print(f"  - {idx['name']}: {idx['reason']}")
    
    print("\n" + "=" * 50)
    print("To apply migrations, run:")
    print("psql -U postgres -d sports_prediction < migration_up.sql")
