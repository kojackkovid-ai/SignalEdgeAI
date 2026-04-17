# Week 1 Implementation Guide

## ✅ Completed Implementations

### 1. Data Validation Service
**File:** `/backend/app/services/data_validation_service.py`

**What it does:**
- Validates all ESPN API responses for data integrity
- Detects invalid, NaN, and infinity values
- Checks stats against realistic sport-specific ranges
- Identifies statistical anomalies
- Logs all validation issues for monitoring

**Key Features:**
- Sport-specific stat ranges (actual ESPN maximums, not guesses)
- Handles multiple validation types: player stats, game data, stat values
- Anomaly detection for suspicious data patterns
- Comprehensive logging for debugging

**How to use:**
```python
from app.services.data_validation_service import get_data_validation_service

service = get_data_validation_service()

# Validate player stats
is_valid, errors, cleaned = service.validate_player_stats(
    stats={'ppg': 24.5, 'rpg': 8.2},
    sport_key='basketball_nba'
)

# Validate game data
is_valid, errors = service.validate_game_data(game_dict, 'basketball_nba')

# Check individual stat values
is_valid, value, error = service.validate_stat_value(24.5, 'points')
```

**Testing:**
Run unit tests:
```bash
pytest backend/tests/unit/test_data_validation.py -v
```

All tests validate against real ESPN data structures and ranges.

---

### 2. Audit Logging Service
**File:** `/backend/app/services/audit_service.py`

**What it does:**
- Logs all sensitive operations (payments, tier changes, data exports)
- Persists to database for compliance (GDPR, CCPA)
- Tracks user actions with IP address and timestamp
- Enables data retrieval for regulatory requirements

**Database Model:**
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY,
    user_id VARCHAR,
    action VARCHAR,                 -- login, payment_completed, tier_upgrade
    resource VARCHAR,               -- user, payment, subscription
    resource_id VARCHAR,
    details JSONB,                 -- Real action details (no mock data)
    ip_address VARCHAR,
    user_agent VARCHAR,
    status VARCHAR,                -- success, failure, error
    error_message VARCHAR,
    created_at TIMESTAMP,
    month INTEGER
);
```

**Audited Actions:**
- Authentication: login, logout, password_change, password_reset
- Payments: payment_completed, payment_failed, payment_refunded
- Subscriptions: tier_upgrade, tier_downgrade, subscription_cancelled
- Data: data_export_requested, account_delete
- Admin: user_suspended, fraud_flagged

**How to use:**
```python
from app.services.audit_service import get_audit_service

audit_service = await get_audit_service(db_session)

# Log a payment
await audit_service.log_payment(
    user_id='user123',
    payment_intent_id='pi_real_stripe_id',
    amount_cents=2900,              # REAL amount from Stripe
    tier='pro',
    status='completed'
)

# Log tier upgrade
await audit_service.log_tier_change(
    user_id='user123',
    from_tier='free',
    to_tier='pro',
    ip_address=request.client.host
)

# Get user's audit history
logs = await audit_service.get_user_audit_logs(user_id='user123')
```

**Testing:**
```bash
pytest backend/tests/unit/test_audit_service.py -v
```

---

### 3. Tier Features Configuration
**File:** `/backend/app/models/tier_features.py`

**What it does:**
- Defines subscription tier features and limits
- Provides tier-based access control
- Manages pricing and tier comparison
- Supports feature flags and tier upgrades

**Tier Structure:**
```python
# FREE: $0/month
- 5 predictions/day
- 2 sports only (NBA, EPL)
- Moneyline only
- No reasoning, no model breakdown
- Ad-enabled

# BASIC: $9/month
- 50 predictions/day
- 8 sports
- Moneyline + Over/Under
- Shows reasoning (no model breakdown)
- Ad-enabled

# PRO: $29/month (Most popular)
- Unlimited predictions
- All 11 sports
- All prediction types (props, combos)
- Shows reasoning + model breakdown
- Ad-free
- API coming soon

# ELITE: $99/month (Power users)
- Everything in Pro +
- Custom models training
- White-label API (coming)
- Early access features
- Dedicated support
```

**How to use:**
```python
from app.models.tier_features import TierFeatures

# Get tier configuration
config = TierFeatures.get_tier_config('pro')

# Check feature access
can_see_props = TierFeatures.is_feature_enabled('pro', 'player_props')

# Check sport access
can_access = TierFeatures.can_access_sport('basic', 'baseball_mlb')

# Get pricing
price = TierFeatures.get_tier_price('pro', 'monthly')  # Returns: 2900 (cents)

# Compare tiers
is_upgrade = TierFeatures.compare_tiers('pro', 'basic')  # Returns: 1 (upgrade)
```

**Testing:**
```bash
pytest backend/tests/unit/test_tier_features.py -v
```

---

### 4. ESPN Integration with Validation
**File:** `/backend/app/services/espn_integration.py`

**What it does:**
- Extends ESPN service with automatic validation
- Applies tier-based filtering to predictions
- Validates all data before returning to users
- Tracks validation statistics

**How to use:**
```python
from app.services.espn_integration import get_validated_espn_service

service = get_validated_espn_service()

# Get games with validation
games = await service.get_upcoming_games_validated('basketball_nba')

# Get prediction for user tier
prediction = await service.get_prediction_validated(
    sport_key='basketball_nba',
    event_id='game123',
    user_tier='pro'  # Only returns if user tier can access
)

# Get all accessible predictions by tier
predictions = await service.get_all_predictions_validated(
    user_tier='free',
    sport='basketball_nba'
)

# Check data quality
report = service.get_validation_report()
# Returns: {
#   'total_api_responses_processed': 150,
#   'failed_validations': 2,
#   'anomalies_detected': 3,
#   'validation_success_rate': 0.9867
# }
```

---

## 📝 Database Migration

To add the audit_logs table, create a migration:

```bash
cd backend
alembic revision --autogenerate -m "Add audit logs table"
alembic upgrade head
```

Or manually run (if not using Alembic):
```sql
CREATE TABLE audit_logs (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR,
    action VARCHAR NOT NULL,
    resource VARCHAR,
    resource_id VARCHAR,
    details JSONB,
    ip_address VARCHAR,
    user_agent VARCHAR,
    status VARCHAR DEFAULT 'success',
    error_message VARCHAR,
    created_at TIMESTAMP DEFAULT NOW(),
    month INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_action (user_id, action),
    INDEX idx_created (created_at),
    INDEX idx_resource (resource, resource_id)
);
```

---

## 🧪 Running Tests

### All validation tests:
```bash
pytest backend/tests/unit/test_data_validation.py -v
```

### All tier tests:
```bash
pytest backend/tests/unit/test_tier_features.py -v
```

### Watch test details:
```bash
pytest backend/tests/unit/ -v -s --tb=short
```

### With coverage:
```bash
pytest backend/tests/unit/ --cov=app.services --cov=app.models --cov-report=html
```

---

## 🔧 Integration with Existing Routes

### In your prediction routes:

```python
from fastapi import Depends, HTTPException
from app.models.tier_features import TierFeatures
from app.services.espn_integration import get_validated_espn_service

@app.get("/api/predictions/{sport}")
async def get_predictions(
    sport: str,
    current_user: User = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db)
):
    """Get predictions with validation and tier filtering"""
    
    # Check tier access to sport
    if not TierFeatures.can_access_sport(current_user.subscription_tier, sport):
        raise HTTPException(
            status_code=403,
            detail=f"Your {current_user.subscription_tier} tier doesn't include {sport}. Upgrade to Pro to access all sports."
        )
    
    # Get validated predictions
    service = get_validated_espn_service()
    predictions = await service.get_all_predictions_validated(
        user_tier=current_user.subscription_tier,
        sport=sport
    )
    
    return {
        'predictions': predictions,
        'count': len(predictions),
        'tier': current_user.subscription_tier
    }
```

### In your payment routes:

```python
from app.services.audit_service import get_audit_service

@app.post("/api/payment/complete")
async def complete_payment(
    request: PaymentRequest,
    current_user: User = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db)
):
    """Complete payment and log"""
    
    # Process with Stripe (real data only)
    result = await stripe_service.process_payment(request)
    
    # Log the audit event
    audit = await get_audit_service(db_session)
    await audit.log_payment(
        user_id=current_user.id,
        payment_intent_id=result['id'],  # REAL Stripe ID
        amount_cents=result['amount'],    # REAL amount
        tier=request.tier,
        status='completed'
    )
    
    # Update user
    current_user.subscription_tier = request.tier
    await db_session.commit()
    
    return result
```

---

## 🚀 Next Steps (Week 2)

1. **Update ESPN Prediction Service**
   - Integrate data validation into `espn_prediction_service.py`
   - Add tier checking before returning predictions
   - Implement confidence filtering

2. **Create Migration Scripts**
   - Add audit_logs table
   - Add data export table for GDPR

3. **Testing**
   - Run full test suite
   - Manual testing with real ESPN API data
   - Load test with 100+ concurrent predictions

4. **Documentation**
   - Add API docs for new endpoints
   - Create migration guide for users

---

## 📊 Monitoring & Logs

### View validation issues:
```bash
grep "VALIDATION" backend.log
```

### View audit trail for user:
```python
# In Python
audit = await get_audit_service(db_session)
logs = await audit.get_user_audit_logs('user_id')
print(logs)
```

### Monitor validation stats:
```python
service = get_validated_espn_service()
report = service.get_validation_report()
print(f"Success rate: {report['validation_success_rate']:.1%}")
```

---

## ✅ Validation Checklist

- [x] Data validation service created
- [x] Audit logging service created
- [x] Tier features configuration created
- [x] ESPN integration with validation created
- [x] Unit tests for validation (50+ test cases)
- [x] Unit tests for tier features (40+ test cases)
- [x] Real ESPN data ranges used (no fake data)
- [ ] Database migration created
- [ ] Integration tests written
- [ ] Deployed to staging

---

## 🎯 Success Metrics

After implementation, measure:

1. **Data Quality**
   - Validation success rate (target: >99%)
   - Anomalies detected per 1000 predictions (monitor for spikes)
   - Failed validations trending down

2. **Tier Compliance**
   - Free tier users seeing only 5 predictions/day
   - Basic tier users blocked from player props
   - Pro tier users unlimited access

3. **Audit Trail**
   - All payments logged with real Stripe IDs
   - All tier changes logged
   - GDPR data exports available

---

## 📞 Questions?

If tests fail:

1. Check ESPN API responses match expected structure
2. Verify stat ranges are realistic (check ESPN records)
3. Ensure no hardcoded values in tier features
4. Validate database foreign key relationships

All code uses ONLY real data - no mocks or fakes!
