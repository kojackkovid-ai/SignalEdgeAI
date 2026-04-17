# HASH-BASED CONFIDENCE: CODE LOCATIONS & FIX BLUEPRINT

## Issue Overview
Your platform generates confidence scores using MD5 hashes of team names/IDs instead of real statistical inference. This creates **deterministic pseudo-randomness** that:
- Always produces the same confidence for identical teams
- Is unrelated to actual prediction accuracy
- Cannot be calibrated to real outcomes
- Violates basic ML principles

---

## CRITICAL LOCATIONS TO FIX

### Location #1: backend/app/services/enhanced_ml_service.py (Line 1178)

**PROBLEMATIC CODE:**
```python
def _generate_prediction_with_seed(
    self, 
    game_id: str, 
    sport_key: str, 
    market_type: str
) -> float:
    """
    Generate confidence based on hash-based seed.
    PROBLEM: This is completely disconnected from team performance!
    """
    import hashlib
    
    # THIS IS THE BUG:
    seed = int(
        hashlib.md5(f"{game_id}_{sport_key}_{market_type}".encode()).hexdigest(), 
        16
    ) % 10000
    
    # Generate "random" confidence using the hash seed
    base_confidence = 50.0
    variance = (seed % 25) + (seed % 20) + (seed % 15)  # 0-60 range
    return min(base_confidence + variance / 2, 95)
```

**WHY THIS IS BROKEN:**
```
Example:
Game ID: "game_abc123" → MD5 hash → Always produces same seed
Lakers vs Celtics on April 1 → confidence = 67.3%
Lakers vs Celtics on April 15 → confidence = 67.3% (SAME!)

But actual game outcomes can be completely different.
This is essentially random number generation with no basis in reality.
```

**FIX:**
Replace with Bayesian confidence calculation:

```python
async def _generate_prediction_with_confidence(
    self,
    game_id: str,
    sport_key: str,
    home_team_data: Dict,
    away_team_data: Dict,
    recent_games: Dict
) -> Tuple[float, Dict]:
    """
    Generate confidence based on Bayesian statistical inference.
    FIXED: Now based on actual team performance!
    """
    from app.services.bayesian_confidence import BayesianConfidenceCalculator
    
    calculator = BayesianConfidenceCalculator()
    
    confidence, metadata = calculator.calculate_confidence(
        home_team_data=home_team_data,
        away_team_data=away_team_data,
        recent_games=recent_games.get('home', [])
    )
    
    return confidence, metadata
```

**Verification Test:**
```python
# After fix, same game with different team records should produce different confidence
game1 = get_prediction(       # Lakers 50-20, Celtics 45-25
    home_team={'wins': 50, 'losses': 20},
    away_team={'wins': 45, 'losses': 25}
)  # confidence = 61.2%

game2 = get_prediction(       # Lakers 48-22, Celtics 45-25 (Lakers dropped 2 games)
    home_team={'wins': 48, 'losses': 22},
    away_team={'wins': 45, 'losses': 25}
)  # confidence = 59.8% (DIFFERENT!)

assert game1['confidence'] != game2['confidence']
```

---

### Location #2: backend/app/services/ml_service.py

**STATUS:** Need to check if using hash-based approach or already using Bayesian

Search for:
```python
grep -n "hashlib\|hashing\|MD5\|seed" backend/app/services/ml_service.py
```

If found, same fix as Location #1.

---

### Location #3: backend/app/services/espn_prediction_service.py

**CURRENT CODE (Line 539):**
```python
def _get_cache_key(self, prefix: str, *args) -> str:
    """Generate a cache key from prefix and arguments"""
    key_data = f"{prefix}:{':'.join(str(a) for a in args)}"
    return hashlib.md5(key_data.encode()).hexdigest()
```

**STATUS:** ✅ OK TO KEEP (this is just for cache key generation, not prediction logic)

**BUT CHECK:** Line 920 - "DO NOT use hash-based fallback"
- This indicates someone already fixed the fallback
- May have residual hash-based code to clean up

---

## WHERE HASH-BASED CODE IS CALLED

### Call Chain:
```
User requests prediction
    ↓
GET /api/predictions/[game_id]
    ↓
PredictionService.get_prediction()
    ↓
EnhancedMLService.generate_prediction()
    ↓
_generate_prediction_with_seed()  ← PROBLEM HERE
    ↓
confidence = MD5 hash-based value
    ↓
Returns to user with fake confidence
```

---

## INTEGRATION: USING BAYESIAN CALCULATOR (ALREADY IMPLEMENTED)

The good news: **Bayesian calculator already exists** at `backend/app/services/bayesian_confidence.py`

You just need to:
1. ✅ Import it in `enhanced_ml_service.py`
2. ✅ Use it instead of hash-based calculation
3. ✅ Pass real team data to it
4. ✅ Test on historical data

**Required Team Data:**
```python
home_team_data = {
    'wins': 50,              # Wins this season
    'losses': 25,            # Losses this season
    'recent_wins': 8,        # Last 10 games
    'recent_losses': 2,
    'pf': 2850,              # Points for (season total)
    'pa': 2750,              # Points against
    'home_wins': 28,         # Home record
    'away_losses': 12
}

away_team_data = {
    'wins': 48,
    'losses': 27,
    'recent_wins': 7,
    'recent_losses': 3,
    'pf': 2800,
    'pa': 2900,
    'away_wins': 22,
    'home_losses': 15
}

# Call Bayesian calculator
calculator = BayesianConfidenceCalculator()
confidence, metadata = calculator.calculate_confidence(
    home_team_data=home_team_data,
    away_team_data=away_team_data,
    historical_results=head_to_head_games,
    recent_games=home_team['recent_games']
)
```

---

## STEP-BY-STEP FIX IMPLEMENTATION

### Step 1: Create Confidence Fix File (1 hour)

Create: `backend/app/services/confidence_fix.py`

```python
"""
Replaces hash-based confidence with Bayesian calculation.
"""

from typing import Dict, Tuple, Optional, List
from app.services.bayesian_confidence import BayesianConfidenceCalculator
import logging

logger = logging.getLogger(__name__)


class ConfidenceCalculator:
    """
    Centralized confidence calculation using Bayesian inference.
    Replaces all hash-based calculations throughout the codebase.
    """
    
    def __init__(self):
        self.bayesian = BayesianConfidenceCalculator()
        self._cache = {}  # Cache calculations for same game
    
    async def calculate_confidence(
        self,
        game_id: str,
        home_team_data: Dict,
        away_team_data: Dict,
        recent_games: Optional[List[Dict]] = None,
        head_to_head: Optional[List[Dict]] = None
    ) -> Tuple[float, Dict]:
        """
        Calculate confidence for a prediction.
        
        Args:
            game_id: Unique game identifier
            home_team_data: Home team statistics
            away_team_data: Away team statistics
            recent_games: Recent games for both teams
            head_to_head: Historical head-to-head results
            
        Returns:
            Tuple of (confidence_score, metadata)
        """
        
        # Check cache
        if game_id in self._cache:
            logger.debug(f"Cache hit for game {game_id}")
            return self._cache[game_id]
        
        try:
            # Call Bayesian calculator
            confidence, metadata = self.bayesian.calculate_confidence(
                home_team_data=home_team_data,
                away_team_data=away_team_data,
                recent_games=recent_games,
                historical_results=head_to_head
            )
            
            # Ensure confidence is between 0-100
            confidence = max(0, min(100, confidence))
            
            result = (confidence, metadata)
            
            # Cache result
            self._cache[game_id] = result
            
            logger.info(f"Calculated confidence for {game_id}: {confidence}%")
            return result
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            # Fallback: return neutral confidence
            return (50.0, {'error': str(e), 'method': 'fallback'})
    
    def clear_cache(self):
        """Clear the cache"""
        self._cache.clear()
```

### Step 2: Update enhanced_ml_service.py (2 hours)

Find the function `_generate_prediction_with_seed()` and replace it:

**BEFORE:**
```python
def _generate_prediction_with_seed(self, game_id, sport_key, market_type) -> float:
    import hashlib
    seed = int(hashlib.md5(...).hexdigest(), 16) % 10000
    variance = (seed % 25) + ...
    return min(base_confidence + variance / 2, 95)
```

**AFTER:**
```python
async def _get_prediction_confidence(
    self, 
    game_id: str,
    home_team: Dict,
    away_team: Dict,
    recent_games: Optional[List[Dict]] = None
) -> Tuple[float, Dict]:
    """
    Get prediction confidence using Bayesian inference.
    REPLACES hash-based calculation.
    """
    from app.services.confidence_fix import ConfidenceCalculator
    
    calc = ConfidenceCalculator()
    confidence, metadata = await asyncio.to_thread(
        calc.calculate_confidence,
        game_id=game_id,
        home_team_data=home_team,
        away_team_data=away_team,
        recent_games=recent_games
    )
    
    return confidence, metadata
```

### Step 3: Update Prediction Generation Flow (3 hours)

In `enhanced_ml_service.py`, find `generate_prediction()`:

**BEFORE:**
```python
prediction = {
    'confidence': self._generate_prediction_with_seed(...),  # BUG: hash-based
    'reasoning': [...]
}
```

**AFTER:**
```python
# Get team data from database/stats
home_team_data = await self._get_team_stats(home_team_id, sport_key)
away_team_data = await self._get_team_stats(away_team_id, sport_key)

# Calculate confidence using Bayesian method
confidence, metadata = await self._get_prediction_confidence(
    game_id=game_id,
    home_team=home_team_data,
    away_team=away_team_data,
    recent_games=recent_games
)

prediction = {
    'confidence': confidence,
    'reasoning': [...],
    'model_weights': metadata  # Include Bayesian metadata
}
```

### Step 4: Create Unit Tests (2 hours)

Create: `tests/unit/test_confidence_calculation.py`

```python
import pytest
from app.services.confidence_fix import ConfidenceCalculator


@pytest.mark.asyncio
async def test_confidence_differs_with_team_performance():
    """Verify confidence changes with team performance"""
    
    calc = ConfidenceCalculator()
    game_id = "test_game_123"
    
    # Strong home team, weak away team
    conf1, _ = await calc.calculate_confidence(
        game_id=game_id,
        home_team_data={'wins': 50, 'losses': 10, 'recent_wins': 9, 'recent_losses': 1},
        away_team_data={'wins': 20, 'losses': 40, 'recent_wins': 2, 'recent_losses': 8}
    )
    
    # Weak home team, strong away team
    calc.clear_cache()  # Clear cache so it recalculates
    conf2, _ = await calc.calculate_confidence(
        game_id=game_id,
        home_team_data={'wins': 20, 'losses': 40, 'recent_wins': 2, 'recent_losses': 8},
        away_team_data={'wins': 50, 'losses': 10, 'recent_wins': 9, 'recent_losses': 1}
    )
    
    # Confidence should be significantly different
    assert abs(conf1 - conf2) > 10, f"Confidence should differ by >10%, got {conf1} vs {conf2}"
    assert conf1 > conf2, "Strong home team should have higher confidence"


@pytest.mark.asyncio
async def test_confidence_in_valid_range():
    """Verify confidence is between 0-100"""
    
    calc = ConfidenceCalculator()
    
    for i in range(100):
        confidence, _ = await calc.calculate_confidence(
            game_id=f"game_{i}",
            home_team_data={'wins': 30 + (i % 50), 'losses': 25},
            away_team_data={'wins': 30, 'losses': 25 + (i % 50)}
        )
        
        assert 0 <= confidence <= 100, f"Confidence out of range: {confidence}"


@pytest.mark.asyncio  
async def test_neutral_teams_near_50_percent():
    """Verify evenly-matched teams have ~50% confidence"""
    
    calc = ConfidenceCalculator()
    
    # Identical records
    confidence, _ = await calc.calculate_confidence(
        game_id="neutral_game",
        home_team_data={'wins': 30, 'losses': 25, 'recent_wins': 5, 'recent_losses': 5},
        away_team_data={'wins': 30, 'losses': 25, 'recent_wins': 5, 'recent_losses': 5}
    )
    
    # Should be close to 50% (50-55% considering home court advantage)
    assert 48 <= confidence <= 58, f"Neutral teams should be ~50%, got {confidence}%"
```

### Step 5: Deploy & Verify (1 hour)

1. **Staging Deployment:**
```bash
# Deploy fixed code to staging
cd sports-prediction-platform/backend
python -m pytest tests/unit/test_confidence_calculation.py -v
```

2. **Verify on Historical Data:**
```bash
# Run audit on last 30 days
python audit_accuracy.py --days 30 --unresolved
```

3. **Compare Before/After:**
- Generate predictions with old code (hash-based)
- Generate predictions with new code (Bayesian)
- Verify results are different and more statistically sound

---

## TIMELINE & EFFORT

| Task | Hours | Dependencies |
|------|-------|--------------|
| Create confidence_fix.py | 1 | None |
| Update enhanced_ml_service.py | 2 | Understand current flow |
| Update prediction generation | 3 | Understanding of prediction pipeline |
| Create unit tests | 2 | Knowledge of testing framework |
| Deploy & test | 1 | All above |
| **TOTAL** | **9 hours** | None blocking |

---

## SUCCESS CRITERIA

- [ ] No MD5/hashlib usage in confidence generation
- [ ] All confidence scores use Bayesian calculator
- [ ] Unit tests pass (confidence differs with team performance)
- [ ] Confidence scores in valid range (0-100)
- [ ] Historical predictions re-scored and compared
- [ ] Documentation updated with new method
- [ ] Code review completed

---

## AFTER THIS FIX

Once hash-based confidence is eliminated:
1. ✅ Confidence scores become statistical and calibrated
2. ✅ Can measure actual accuracy
3. ✅ Can monetize with confidence (pun intended)
4. ✅ Can add real user acquisition
5. ✅ Can build investor pitch around verified accuracy

**Next Steps (see ACCURACY_AUDIT_PLAN.md):**
- Implement outcome tracking
- Create accuracy dashboard
- Calculate ROI metrics
- Publish accuracy report
