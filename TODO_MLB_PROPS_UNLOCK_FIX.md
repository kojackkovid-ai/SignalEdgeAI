# TODO: MLB Player Props and Unlock Issue Fix

## Issue 1: MLB Player Props Categories Not Working

### Root Cause:
The `_calculate_confidence` method in `espn_prediction_service.py` only handles specific MLB markets:
- `home_runs` - ✅ Working
- `hits` (batting average) - ✅ Working  
- `runs_batted_in` (RBI) - ❌ Missing
- `stolen_bases` - ❌ Missing
- `batting_average` (as a prop line) - ❌ Missing

For markets without specific handling, the confidence defaults to a generic calculation that may not work well.

### Fix:
Add confidence calculation logic for:
- `runs_batted_in` / `rbi`
- `stolen_bases`

---

## Issue 2: Previously Unlocked Picks Not Staying Unlocked

### Root Cause:
Backend returns `is_locked` property but frontend checks `prop.unlocked`:
- Backend: `is_locked = not is_following` (true = locked, false = unlocked)
- Frontend: Checks `prop.unlocked` which doesn't exist in the API response

### Fix:
Update frontend to check `is_locked` property instead of `unlocked`

---

## Files to Edit:

1. `sports-prediction-platform/backend/app/services/espn_prediction_service.py`
   - Add MLB confidence calculation for RBI, stolen_bases

2. `sports-prediction-platform/frontend/src/pages/Dashboard.tsx`
   - Fix prop.unlocked to prop.is_locked check

3. `sports-prediction-platform/backend/app/routes/predictions.py`  
   - Verify is_locked is being returned correctly
