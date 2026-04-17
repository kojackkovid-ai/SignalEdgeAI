JIU# Accuracy Audit & Confidence Fix Plan

## Executive Summary
Your platform has systematic issues with confidence score calculation that prevent monetization:
1. **Hash-based confidence**: Uses MD5 hashes of team names instead of real statistics
2. **Deterministic pseudo-randomness**: Same matchup always produces identical scores
3. **Model fallbacks**: When ML models unavailable, uses basic heuristics
4. **No validation**: Predictions never compared to actual outcomes for calibration

**Status:** CRITICAL - Blocks paid user acquisition

---

## PART 1: AUDIT FINDINGS

### Issue #1: Hash-Based Confidence (HIGH PRIORITY)

**Location:** `backend/app/services/enhanced_ml_service.py` line 1178

```python
# PROBLEMATIC CODE:
import hashlib
seed = int(hashlib.md5(f"{game_id}_{sport_key}_{market_type}".encode()).hexdigest(), 16) % 10000
# Generates confidence from MD5 hash - completely disconnected from team performance!
```

**Impact:**
- Same team matchup always produces identical confidence
- No learning from historical outcomes
- Predictions are **deterministic, not probabilistic**
- Users betting on "52% confidence" get random outcomes
- Violates basic ML principle of calibration

**Example:**
- Game: Lakers vs Celtics
- Confidence: 67.3% (determined by hash of "lakers_celtics")
- Tomorrow: Lakers vs Celtics rematch
- Confidence: SAME 67.3% (same hash!)
- But actual outcomes may differ significantly

### Issue #2: Model Fallback Strategy (MEDIUM PRIORITY)

**Location:** Multiple - when ML models fail to load

**Current behavior:**
- If XGBoost model missing → use LightGBM
- If LightGBM missing → use linear regression
- If all models missing → use heuristics based on team metadata
- If all else fails → return 50% confidence

**Problem:**
- No prediction accuracy tracking when fallback used
- Can't calibrate confidence based on historical accuracy
- Users don't know predictions are degraded

### Issue #3: Prediction Accuracy Tracking (CRITICAL)

**Location:** Database schema - missing fields

**Problem:**
- Predictions stored WITHOUT actual outcomes
- No `result` field populated in most predictions
- Can't calculate: win rate, precision, ROI
- Can't verify platform works before monetizing

**Current Database State:**
```
Prediction record:
{
  id: "pred-123",
  sport: "basketball_nba",
  prediction: "Lakers over Celtics",
  confidence: 67.3,
  odds: "+110",
  created_at: "2026-04-06 15:30:00",
  resolved_at: null,           # ← PROBLEM: Never filled in
  result: null,                # ← PROBLEM: Never filled in  
  actual_value: null           # ← PROBLEM: Never filled in
}
```

---

## PART 2: TECHNICAL SPECIFICATION FOR FIXES

### FIX #1: Replace Hash-Based Confidence (24 hours)

**Current Code:** `enhanced_ml_service.py` line 1178
```python
# CURRENT (BROKEN):
import hashlib
seed = int(hashlib.md5(f"{game_id}_{sport_key}_{market_type}".encode()).hexdigest(), 16) % 10000
```

**Replacement Strategy:**
Use Bayesian confidence from `bayesian_confidence.py` (already implemented!)

```python
# NEW (CORRECT):
from app.services.bayesian_confidence import BayesianConfidenceCalculator

calculator = BayesianConfidenceCalculator()
confidence, metadata = calculator.calculate_confidence(
    home_team_data={
        'wins': home_team.recent_wins,
        'losses': home_team.recent_losses
    },
    away_team_data={
        'wins': away_team.recent_wins,
        'losses': away_team.recent_losses
    },
    historical_results=h2h_games,
    recent_games=home_team.recent_games
)
```

**Benefits:**
- ✅ Real statistical inference
- ✅ Based on historical performance
- ✅ Calibrated to actual outcomes
- ✅ Tracks uncertainty properly

**Testing:**
```python
# Verify: Same game always produces different confidence when team stats differ
game1 = predict(home_wins=50, away_wins=40)  # confidence: X
game1_next_day = predict(home_wins=51, away_wins=40)  # confidence: Y (different!)
assert game1 != game1_next_day  # Different stats = different confidence
```

---

### FIX #2: Implement Outcome Tracking (16 hours)

**New Database Fields:**

```sql
ALTER TABLE predictions ADD COLUMN IF NOT EXISTS:
- scheduled_time TIMESTAMP         -- When game starts
- resolved_at TIMESTAMP            -- When game ends and result known
- result VARCHAR(10)               -- 'win', 'loss', 'push', 'no_result'
- actual_value FLOAT               -- Actual game outcome (e.g., final score)
- line_beaten BOOLEAN              -- Did actual beat the line?
- resolution_method VARCHAR(20)    -- 'api', 'manual', 'auto'
```

**Autoresolution Service:**
```python
# Create: backend/app/services/prediction_resolution_service.py

class PredictionResolutionService:
    async def resolve_predictions_for_sport(self, sport_key: str):
        """
        Fetch final game results and update predictions:
        1. Get all unresolved predictions for sport
        2. Fetch final scores from ESPN API
        3. Compare actual vs predicted
        4. Update result field (win/loss/push)
        5. Log resolution method
        """
        
        # Get unclosed predictions
        predictions = await db.query(Prediction).filter(
            Prediction.sport == sport_key,
            Prediction.resolved_at == null,
            Prediction.created_at < (now - 6 hours)  # Game should be done by now
        )
        
        for pred in predictions:
            # Fetch actual result from ESPN
            actual = await espn_service.get_final_score(pred.event_id)
            
            if actual:
                # Compare prediction vs actual
                correct = compare_prediction(pred, actual)
                
                # Update database
                await db.update(Prediction, id=pred.id, {
                    resolved_at: datetime.now(),
                    result: 'win' if correct else 'loss',
                    actual_value: actual.final_score,
                    resolution_method: 'api'
                })
                
                # Update user stats
                await update_user_stats(pred.user_id, correct)
```

**User Stats Calculation:**
```python
async def calculate_user_stats(user_id: str):
    """Recalculate user win rate, ROI, etc"""
    
    resolved = await db.query(Prediction).filter(
        Prediction.user_id == user_id,
        Prediction.resolved_at != null
    )
    
    win_count = sum(1 for p in resolved if p.result == 'win')
    total = len(resolved)
    
    # Calculate ROI (based on odds and stake)
    total_wagered = total * 100  # Assume $100 per prediction
    winnings = sum(calculate_payout(p) for p in resolved if p.result == 'win')
    
    return {
        win_rate: win_count / total if total > 0 else 0,
        total_predictions: total,
        roi: (winnings - total_wagered) / total_wagered if total_wagered > 0 else 0
    }
```

---

### FIX #3: Accuracy Dashboard (12 hours)

**New API Endpoint:**

```python
# routes/analytics.py

@router.get("/api/analytics/prediction-accuracy")
async def get_prediction_accuracy(
    sport: Optional[str] = None,
    days: int = 30,
    min_predictions: int = 10
):
    """
    Return accuracy metrics for predictions.
    
    Response:
    {
      "overall": {
        "win_rate": 0.55,           # Percentage of correct predictions
        "precision": 0.58,          # True positives / (true pos + false pos)
        "recall": 0.52,             # True positives / (true pos + false neg)
        "roi": 0.12,                # Return on investment (12% profit)
        "sample_size": 523,         # Number of resolved predictions
        "confidence_calibration": 0.94  # How well confidence matches actual accuracy
      },
      "by_sport": {
        "basketball_nba": { ... },
        "americanfootball_nfl": { ... }
      },
      "by_confidence_bucket": {
        "50-55%": { "accuracy": 0.51, "count": 12 },
        "55-60%": { "accuracy": 0.54, "count": 45 },
        "60-65%": { "accuracy": 0.61, "count": 89 },
        ...
      },
      "by_model": {
        "xgboost": { "accuracy": 0.56, "count": 120 },
        "lightgbm": { "accuracy": 0.54, "count": 130 },
        ...
      }
    }
    """
```

**Confidence Calibration Plot:**
```python
# If predictions are well-calibrated:
# - Predictions at 60% confidence should be right ~60% of the time
# - Predictions at 75% confidence should be right ~75% of the time

def calculate_calibration_error(predictions):
    """Calculate how far confidence is from actual accuracy"""
    
    buckets = {
        (0.50, 0.55): [],
        (0.55, 0.60): [],
        (0.60, 0.65): [],
        ...
    }
    
    # Sort predictions into buckets by confidence
    for pred in predictions:
        for bucket in buckets:
            if bucket[0] <= pred.confidence < bucket[1]:
                buckets[bucket].append(pred.result == 'win')
    
    # Compare confidence vs actual accuracy per bucket
    errors = []
    for (conf_min, conf_max), results in buckets.items():
        if not results:
            continue
        expected = (conf_min + conf_max) / 2
        actual = sum(results) / len(results)
        error = abs(expected - actual)
        errors.append(error)
    
    return np.mean(errors)  # Lower is better (0 = perfect calibration)
```

---

### FIX #4: Model Performance Dashboard (8 hours)

**New Metrics to Track:**

```python
# Per-model accuracy over time

model_performance = {
    "xgboost": {
        "accuracy_7d": 0.554,
        "accuracy_30d": 0.542,
        "trend": -1.2,  # Declining
        "sample_size_30d": 248,
        "roi_30d": -0.08  # Negative ROI - needs retraining
    },
    "lightgbm": {
        "accuracy_7d": 0.538,
        "accuracy_30d": 0.559,
        "trend": +2.1,  # Improving  
        "sample_size_30d": 267,
        "roi_30d": +0.15  # Positive ROI
    }
}
```

---

## PART 3: IMPLEMENTATION TIMELINE

### Phase 1: Outcome Tracking (Days 1-3)
**Priority: HIGHEST (blocks everything else)**

Deliverables:
- [ ] Add `resolved_at`, `result`, `actual_value` columns to predictions table
- [ ] Create migration script
- [ ] Build resolution service that fetches final scores
- [ ] Run backfill on past 30 days of predictions
- [ ] Verify data integrity

**Expected Result:** 
- 500-2000 predictions with actual outcomes populated
- Can now calculate current win rate

### Phase 2: Confidence Recalibration (Days 4-6)
**Priority: HIGH**

Deliverables:
- [ ] Remove hash-based confidence from `enhanced_ml_service.py`
- [ ] Test Bayesian calculator in isolation
- [ ] Integrate into prediction generation
- [ ] Backtest on historical predictions
- [ ] Deploy to staging

**Expected Result:**
- Confidence scores now based on real team stats
- Same matchup produces different confidence as team performance changes

### Phase 3: Analytics Dashboard (Days 7-9)
**Priority: HIGH**

Deliverables:
- [ ] Create `/api/analytics/prediction-accuracy` endpoint
- [ ] Build confidence calibration calculation
- [ ] Create model performance metrics
- [ ] Frontend: Add analytics page
- [ ] Document accuracy publicly

**Expected Result:**
- Can generate accuracy report: "Win Rate: 54%, ROI: +8%, Calibration: 0.92"
- Use for marketing / investor pitch

### Phase 4: Continuous Monitoring (Days 10+)
**Priority: MEDIUM**

Deliverables:
- [ ] Cronjob that resolves games daily
- [ ] Alert if accuracy drops below threshold
- [ ] Auto-retraining when model drift detected
- [ ] Prediction audit logs

---

## PART 4: SUCCESS METRICS

### Minimum Viable Accuracy
- [ ] Win rate > 52% (vs 50% random)
- [ ] Confidence calibration error < 0.10 (10% maximum error)
- [ ] ROI > 0% (neutral or positive)
- [ ] Sample size > 100 predictions (statistical significance)

### To Enable Monetization
- [ ] Win rate > 55% (moderate edge)
- [ ] Confidence calibration error < 0.05 (good calibration)
- [ ] ROI > +5% (real edge)
- [ ] Sample size > 1000 predictions

### Red Flags (Don't Deploy)
- ❌ Win rate < 50% (worse than random!)
- ❌ Confidence calibration error > 0.15 (badly calibrated)
- ❌ ROI < -5% (losing money consistently)
- ❌ Model drift (accuracy declining over time)

---

## PART 5: CURRENT CODE LOCATIONS

### Files with Hash-Based Code (TO FIX)
1. `backend/app/services/enhanced_ml_service.py` (line 1178)
   - Seed calculation using hashlib.md5
   - Replace with Bayesian calculator

2. `backend/app/services/espn_prediction_service.py` (line 539)
   - Cache key generation (OK to keep, it's just for cache lookup)
   - Confidence generation (check if using hash-based)

### Files with Good Code (ALREADY IMPLEMENTED)
1. `backend/app/services/bayesian_confidence.py` ✅
   - BayesianConfidenceCalculator class
   - Proper statistical framework
   - **Just need to integrate into prediction flow**

2. `backend/app/services/prediction_resolution_service.py` ✅
   - Already exists! Fetches final scores
   - Need to verify it's being called

### Files to Create
1. `backend/app/routes/analytics.py` 
   - Accuracy metrics endpoint
   - Model performance endpoint

2. `backend/app/services/accuracy_calculator.py`
   - Win rate, ROI, calibration calculations
   - Confidence bucket analysis

---

## PART 6: VALIDATION CHECKLIST

Before marking this as "Fixed":

- [ ] All MD5 hash-based confidence removedConfidence now from Bayesian calculator
- [ ] 100+ predictions resolved with actual outcomes in database
- [ ] Accuracy dashboard shows real metrics (not mock data)
- [ ] Confidence calibration measured and < 0.10
- [ ] Model-by-model accuracy tracked
- [ ] Staging deployment tested
- [ ] Confidence scores verified different for similar games with different team performance
- [ ] Resolution service runs daily without errors
- [ ] User stats (win_rate, roi) calculated correctly
- [ ] Documentation updated with accuracy claim

---

## NEXT STEPS

1. **Immediate (Next2 hours):**
   - Run audit: count predictions in DB with/without resolved outcomes
   - Identify which models are being used (XGBoost? LightGBM? Linear?)
   - Create script to backfill 30 days of actual outcomes

2. **This Week:**
   - Fix confidence calculation
   - Populate outcomes for historical predictions
   - Build accuracy dashboard

3. **Next Week:**
   - Deploy to production
   - Publish accuracy report
   - Begin user acquisition with confidence in product accuracy

---

