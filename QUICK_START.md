# Quick Start Guide - Week 1 Services

## 🚀 For Developers

### 1. Using Data Validation

```python
from app.services.data_validation_service import get_data_validation_service

# Get the service
validator = get_data_validation_service()

# Validate player stats (most common use)
is_valid, errors, cleaned_stats = validator.validate_player_stats(
    stats={'ppg': 28.5, 'rpg': 8.2, 'apg': 4.1},
    sport_key='basketball_nba',
    player_info={'position': 'SG', 'team': 'LAL'}
)

if not is_valid:
    print(f"Invalid stats: {errors}")
else:
    print(f"Cleaned stats: {cleaned_stats}")

# Validate entire game response from ESPN
is_valid, errors = validator.validate_game_data(
    game_dict=espn_game_response,
    sport_key='basketball_nba'
)

# Check individual stat value
is_valid, cleaned_value, error = validator.validate_stat_value(
    value=154.5,
    stat_name='points',
    sport_key='basketball_nba'
)

# Detect anomalies
anomalies = validator.detect_anomalies(
    player_stats={'ppg': 150.0, 'rpg': 12, 'apg': 2},  # 150 PPG is unrealistic
    sport_key='basketball_nba',
    player_info={'career_high': 69}
)
```

### 2. Using Tier Features

```python
from app.models.tier_features import TierFeatures

# Check if user tier can access a sport
user_tier = 'basic'
sport = 'basketball_nba'

can_access = TierFeatures.can_access_sport(user_tier, sport)
# True - Basic tier has 8 sports

can_access = TierFeatures.can_access_sport('free', 'baseball_mlb')
# False - Free tier only has NBA and EPL

# Check feature access
can_see_player_props = TierFeatures.is_feature_enabled('pro', 'player_props')
# True

can_see_props_free = TierFeatures.is_feature_enabled('free', 'player_props')
# False

# Get tier configuration
config = TierFeatures.get_tier_config('pro')
print(config['price'])           # 2900 (cents)
print(config['predictions_per_day'])  # None (unlimited)
print(config['sports'])          # 11 (all)

# Compare tiers
result = TierFeatures.compare_tiers('pro', 'basic')
# 1 means first tier is higher (upgrade)
# -1 means first tier is lower (downgrade)
# 0 means same tier

# Get upgrade path
upgrade = TierFeatures.get_upgrade_path('free')
print(upgrade)  # 'basic' (next tier up)
```

### 3. Using Audit Service

```python
from app.services.audit_service import get_audit_service
from sqlalchemy.ext.asyncio import AsyncSession

async def handle_login(user_id: str, db_session: AsyncSession, request):
    """Example: Log user login"""
    
    audit = await get_audit_service(db_session)
    
    # Log the login
    await audit.log_login(
        user_id=user_id,
        ip_address=request.client.host,
        user_agent=request.headers.get('user-agent'),
        status='success'
    )

async def handle_payment(user_id: str, stripe_result: dict, db_session: AsyncSession):
    """Example: Log payment completion"""
    
    audit = await get_audit_service(db_session)
    
    # Log payment with REAL Stripe data (not mocked)
    await audit.log_payment(
        user_id=user_id,
        payment_intent_id=stripe_result['id'],  # REAL Stripe ID
        amount_cents=stripe_result['amount'],   # REAL amount
        tier='pro',
        status='completed' if stripe_result['status'] == 'succeeded' else 'failed'
    )

async def handle_tier_upgrade(user_id: str, from_tier: str, to_tier: str,
                             db_session: AsyncSession, request):
    """Example: Log tier change"""
    
    audit = await get_audit_service(db_session)
    
    await audit.log_tier_change(
        user_id=user_id,
        from_tier=from_tier,
        to_tier=to_tier,
        ip_address=request.client.host,
        status='success'
    )

async def handle_data_export(user_id: str, db_session: AsyncSession):
    """Example: Log data export (GDPR Article 15)"""
    
    audit = await get_audit_service(db_session)
    
    await audit.log_data_export(
        user_id=user_id,
        exported_resources=['user_profile', 'predictions', 'audit_logs'],
        status='completed',
        size_bytes=15234  # Size of exported data
    )

async def handle_account_deletion(user_id: str, db_session: AsyncSession):
    """Example: Log account deletion (GDPR Article 17)"""
    
    audit = await get_audit_service(db_session)
    
    await audit.log_account_deletion(
        user_id=user_id,
        reason='user_requested',
        status='pending'  # Mark as pending, update to 'completed' when deletion finishes
    )

async def get_user_audit_history(user_id: str, db_session: AsyncSession):
    """Example: Retrieve user's audit history"""
    
    audit = await get_audit_service(db_session)
    
    logs = await audit.get_user_audit_logs(
        user_id=user_id,
        limit=50  # Last 50 actions
    )
    
    for log in logs:
        print(f"[{log.created_at}] {log.action} - {log.status}")
```

### 4. Using Validated ESPN Service

```python
from app.services.espn_integration import get_validated_espn_service

async def get_predictions_for_user(user_tier: str, sport: str):
    """Example: Get predictions with validation and tier filtering"""
    
    service = get_validated_espn_service()
    
    # Get all predictions for a sport, validated and filtered by tier
    predictions = await service.get_all_predictions_validated(
        user_tier=user_tier,
        sport=sport
    )
    
    return predictions

async def get_single_prediction(user_tier: str, sport: str, event_id: str):
    """Example: Get single prediction with tier enforcement"""
    
    service = get_validated_espn_service()
    
    # Returns None if user tier can't access this prediction type
    prediction = await service.get_prediction_validated(
        sport_key=sport,
        event_id=event_id,
        user_tier=user_tier
    )
    
    return prediction

def get_data_quality_report():
    """Example: Get validation statistics"""
    
    service = get_validated_espn_service()
    
    report = service.get_validation_report()
    
    print(f"Total responses: {report['total_api_responses_processed']}")
    print(f"Success rate: {report['validation_success_rate']:.1%}")
    print(f"Failures: {report['failed_validations']}")
    print(f"Anomalies: {report['anomalies_detected']}")
```

---

## 🔌 API Endpoint Integration Examples

### Example 1: Predictions Endpoint with Tier Filtering

```python
from fastapi import APIRouter, Depends, HTTPException
from app.models.tier_features import TierFeatures
from app.services.espn_integration import get_validated_espn_service

router = APIRouter()

@router.get("/api/predictions/{sport}")
async def get_predictions(
    sport: str,
    current_user: User = Depends(get_current_user)
):
    """Get predictions for a sport (tier-filtered)"""
    
    # Check tier access to this sport
    if not TierFeatures.can_access_sport(current_user.subscription_tier, sport):
        raise HTTPException(
            status_code=403,
            detail=f"Your {current_user.subscription_tier.upper()} tier doesn't include {sport}. "
                   f"Upgrade to {TierFeatures.get_upgrade_path(current_user.subscription_tier)} to access."
        )
    
    # Get predictions with validation
    service = get_validated_espn_service()
    predictions = await service.get_all_predictions_validated(
        user_tier=current_user.subscription_tier,
        sport=sport
    )
    
    return {
        'sport': sport,
        'predictions': predictions,
        'count': len(predictions),
        'tier': current_user.subscription_tier
    }
```

### Example 2: Payment Endpoint with Audit Logging

```python
from app.services.audit_service import get_audit_service

@router.post("/api/payment/complete-payment")
async def complete_payment(
    payment: PaymentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request
):
    """Complete payment with audit logging"""
    
    # Process with Stripe (using REAL Stripe API, not mocked)
    stripe_result = await stripe_service.create_payment_intent(
        amount_cents=payment.amount,
        tier=payment.tier
    )
    
    # Log the payment with REAL data
    audit = await get_audit_service(db)
    await audit.log_payment(
        user_id=current_user.id,
        payment_intent_id=stripe_result['id'],      # REAL Stripe ID
        amount_cents=stripe_result['amount'],       # REAL amount
        tier=payment.tier,
        status='completed' if stripe_result['status'] == 'succeeded' else 'failed'
    )
    
    if stripe_result['status'] == 'succeeded':
        # Update user subscription
        current_user.subscription_tier = payment.tier
        await db.commit()
    
    return stripe_result
```

### Example 3: Tier Upgrade Endpoint with Logging

```python
@router.post("/api/subscriptions/upgrade")
async def upgrade_subscription(
    request: UpgradeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    http_request: Request
):
    """Upgrade to higher tier with audit logging"""
    
    old_tier = current_user.subscription_tier
    new_tier = request.new_tier
    
    # Validate upgrade is valid
    if TierFeatures.compare_tiers(new_tier, old_tier) <= 0:
        raise HTTPException(400, "Can only upgrade to higher tiers")
    
    # Log the tier change
    audit = await get_audit_service(db)
    await audit.log_tier_change(
        user_id=current_user.id,
        from_tier=old_tier,
        to_tier=new_tier,
        ip_address=http_request.client.host
    )
    
    # Update database
    current_user.subscription_tier = new_tier
    await db.commit()
    
    return {
        'old_tier': old_tier,
        'new_tier': new_tier,
        'message': f'Upgraded from {old_tier} to {new_tier}!'
    }
```

---

## 🧪 Testing Quick Commands

```bash
# Run validation tests
pytest backend/tests/unit/test_data_validation.py -v

# Run tier tests
pytest backend/tests/unit/test_tier_features.py -v

# Run all new tests
pytest backend/tests/unit/test_data_validation.py \
       backend/tests/unit/test_tier_features.py -v

# With coverage
pytest backend/tests/unit/ --cov=app.services --cov=app.models

# Run with output
pytest -v -s backend/tests/unit/
```

---

## 📊 Monitoring Commands

```python
# Check validation stats
from app.services.espn_integration import get_validated_espn_service
service = get_validated_espn_service()
report = service.get_validation_report()
print(f"Validation success rate: {report['validation_success_rate']:.1%}")

# Check audit logs for a user
from app.services.audit_service import get_audit_service
audit = await get_audit_service(db_session)
logs = await audit.get_user_audit_logs('user_id')
for log in logs:
    print(f"{log.created_at} - {log.action}: {log.status}")

# Check tier features
from app.models.tier_features import TierFeatures
print(TierFeatures.get_tier_config('pro'))
print(TierFeatures.can_access_sport('basic', 'basketball_nba'))
```

---

## 🐛 Debugging

### Validation not working?
```bash
# Check if data_validation_service.py exists
find backend -name "data_validation_service.py"

# Check import
python -c "from app.services.data_validation_service import DataValidationService"
```

### Tier checking not working?
```bash
# Verify tier_features.py
python -c "from app.models.tier_features import TierFeatures; print(TierFeatures.get_tier_config('pro'))"
```

### Audit logging errors?
```bash
# Check database connection
psql -U your_user -d your_db -c "\\dt audit_logs"

# Check service import
python -c "from app.services.audit_service import AuditService"
```

---

## 📖 Full Documentation

For complete documentation, see:
- **Implementation Guide:** `WEEK_1_IMPLEMENTATION.md`
- **Progress Report:** `WEEK_1_PROGRESS.md`
- **Migration Guide:** `MIGRATION_GUIDE.md`

---

**Questions?** Refer to the implementation guide for more details!
