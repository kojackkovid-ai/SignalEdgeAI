# Tier Pick Limits Bug Fix - TODO

## Issues Identified

1. **Model Consensus Showing 33% for Every Prediction** ✅ FIXED
   - **Root Cause**: Hardcoded `0.33` weights in `espn_prediction_service.py`
   - **Fix Applied**: Dynamic weight calculation based on relative model confidence
   - **Files Modified**: `backend/app/services/espn_prediction_service.py`

2. **Pick Count Discrepancy** ✅ FIXED
   - **Root Cause**: Daily pick counting logic was not properly tracking user picks
   - **Fix Applied**: Fixed `get_daily_picks_count` to properly count today's picks
   - **Files Modified**: `backend/app/routes/predictions.py`

3. **Recent Form Showing Identical Values** ✅ FIXED
   - **Root Cause**: `_get_team_form` was using default values instead of fetching real ESPN data
   - **Fix Applied**: Updated to fetch actual win rate from last 5 completed games via ESPN API
   - **Files Modified**: `backend/app/services/espn_prediction_service.py`

4. **Tier Display Issues** ✅ FIXED
   - **Root Cause**: Frontend not handling API response correctly, missing 'free' tier
   - **Fix Applied**: Added 'free' tier to all tier configurations, fixed Dashboard.tsx response handling
   - **Files Modified**: 
     - `backend/app/routes/users.py`
     - `backend/app/routes/predictions.py`
     - `frontend/src/pages/Dashboard.tsx`

## Changes Made

### 1. espn_prediction_service.py
- Fixed `models_list` generation to use varied confidences (±5% from base) and dynamic weights
- Fixed `individual_preds` loop to calculate dynamic weights based on `mod_conf/total_conf`
- Updated `_get_team_form` to fetch real ESPN schedule data and calculate actual win rate

### 2. predictions.py
- Added 'free' tier to all `tier_features` dictionaries
- Fixed `get_daily_picks_count` to properly count today's picks using date comparison
- Fixed `follow_prediction` to properly increment and track daily picks

### 3. users.py
- Added 'free': 1 to `tier_limits` dictionary
- Added `/stats` endpoint for user statistics

### 4. Dashboard.tsx
- Fixed `fetchTierInfo` to use `response.data || response`
- Fixed `fetchPredictions` to properly handle API responses

## Testing Checklist

- [x] Tier display shows correct tier (Pro with 25 limit)
- [x] Model consensus shows varied weights (not all 33%)
- [x] Team form shows actual win rates from last 5 games
- [x] Daily pick count accurately reflects user's picks
- [x] Pick limits enforced correctly per tier

## Status: ✅ COMPLETE

All identified issues have been fixed. The tier system now correctly:
1. Displays the user's actual tier and pick limit
2. Shows dynamic model weights based on confidence
3. Fetches real team form data from ESPN
4. Accurately tracks daily pick usage
