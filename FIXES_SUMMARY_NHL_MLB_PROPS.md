# NHL/MLB Player Props & Unlock Game Pick Fixes

## Issues Fixed

### 1. NHL and MLB Player Props Not Showing
**Problem**: Player props for NHL and MLB were not being generated or displayed in the dashboard.

**Root Causes**:
- Athletes without `real_stats` were being skipped without proper logging
- MLB home runs prop ID used `hr` instead of `home_runs` causing inconsistency
- Missing counters to track athletes with/without stats for debugging

**Fixes Applied**:
- Added proper `athletes_with_stats` and `athletes_without_stats` counters in `_generate_nhl_player_props()` and `_generate_mlb_player_props()`
- Fixed MLB home runs prop ID from `{event_id}_hr_{name}` to `{event_id}_home_runs_{name}` for consistency
- Added detailed logging with `[NHL_PROPS]` and `[MLB_PROPS]` prefixes
- Added debug logging when athletes are skipped due to missing stats

### 2. Unlock Game Pick Not Working for All Sports
**Problem**: The unlock/follow endpoint was not correctly identifying player props for multi-word market types.

**Root Cause**: 
- The player prop detection logic only checked if the ID had 3+ parts split by `_`
- Multi-word market types like `home_runs`, `pass_yards`, `rush_yards`, `rec_yards` were not being recognized as player props
- This caused game prediction logic to be used instead of player prop logic

**Fixes Applied**:
- Created new `is_player_prop_id()` function that properly handles multi-word market types
- The function checks all possible market key combinations by joining parts with `_`
- Supports all market types: `points`, `rebounds`, `assists`, `goals`, `hits`, `rbi`, `hr`, `home_runs`, `pass_yards`, `rush_yards`, `rec_yards`, `passing_yards`, `rushing_yards`, `receiving_yards`, etc.
- Added comprehensive `[FOLLOW_DEBUG]` logging throughout the follow endpoint
- Added try/except error handling around all service calls

## Files Modified

### 1. `backend/app/services/espn_prediction_service.py`
- Fixed `_generate_nhl_player_props()`: Added stats counters and logging
- Fixed `_generate_mlb_player_props()`: Changed `hr` to `home_runs` in prop ID, added stats counters and logging

### 2. `backend/app/routes/predictions.py`
- Added `is_player_prop_id()` function with multi-word market type support
- Added `dailyLimit` to `TIER_FEATURES` configuration
- Enhanced `follow_prediction()` endpoint with:
  - `[FOLLOW_DEBUG]` logging at every step
  - Proper player prop detection using `is_player_prop_id()`
  - Try/except error handling around all service calls
  - Fixed user tier retrieval to use database query instead of non-existent auth methods

## Test Results

### Player Prop Detection Tests
All tests pass:
- ✅ MLB home runs prop: `401672633_home_runs_Aaron_Judge` → is_player_prop=True
- ✅ MLB hits prop: `401672633_hits_Mike_Trout` → is_player_prop=True
- ✅ MLB RBI prop: `401672633_rbi_Jose_Altuve` → is_player_prop=True
- ✅ NBA points prop: `401672633_points_LeBron_James` → is_player_prop=True
- ✅ NBA rebounds prop: `401672633_rebounds_Anthony_Davis` → is_player_prop=True
- ✅ NBA assists prop: `401672633_assists_James_Harden` → is_player_prop=True
- ✅ NHL goals prop: `401672633_goals_Connor_McDavid` → is_player_prop=True
- ✅ NHL assists prop: `401672633_assists_Sidney_Crosby` → is_player_prop=True
- ✅ NFL pass yards prop: `401672633_pass_yards_Tom_Brady` → is_player_prop=True
- ✅ NFL rush yards prop: `401672633_rush_yards_Derrick_Henry` → is_player_prop=True
- ✅ NFL rec yards prop: `401672633_rec_yards_Cooper_Kupp` → is_player_prop=True
- ✅ Game prediction IDs correctly return False

### API Flow
The unlock game pick flow now works correctly:
1. Frontend calls `POST /predictions/{prediction_id}/follow` with prop data
2. Backend uses `is_player_prop_id()` to detect if it's a player prop
3. For player props: validates required fields (`player`, `market_key`, `prediction`)
4. Checks if user already following (idempotent)
5. Checks daily pick limits based on user tier
6. Saves prediction to database via `prediction_service.follow_prediction()`
7. Returns unlocked prediction data with proper tier-based feature gating

## ESPN API Compliance
All fixes maintain strict ESPN API-only data usage:
- No mock/fallback data generation
- Real athlete stats from ESPN API
- Real game data from ESPN API
- Proper timeout handling for all API calls
- Caching to reduce API load

## Next Steps
1. Test with real NHL/MLB game IDs during active season
2. Monitor logs for `[NHL_PROPS]`, `[MLB_PROPS]`, and `[FOLLOW_DEBUG]` entries
3. Verify unlock functionality works for all sports in production
