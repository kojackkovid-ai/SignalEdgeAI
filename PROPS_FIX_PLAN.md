# Player Props Fix Plan

## Issues Identified

### Issue 1: All Player Props Show 50% Confidence
- **Root Cause**: When ESPN player stats are unavailable, the code falls back to `_get_fallback_confidence()` which returns 55%+
- **Possible Issue**: There might be a code path that returns hardcoded 50% elsewhere
- **Fix Location**: `espn_prediction_service.py` - need to ensure confidence calculation never returns exactly 50%

### Issue 2: Over/Under Lines Are Same (Hardcoded)
- **Root Cause**: Both Over and Under props use the same line value
- **Fix**: Need to create DIFFERENT lines for Over vs Under:
  - Over line: player's average + 0.5 (slightly higher)
  - Under line: player's average - 0.5 (slightly lower)

### Issue 3: Missing Team Name in Player Props
- **Root Cause**: The `team_name` variable is being passed but might be None or empty
- **Fix**: Need to ensure team name is properly extracted from roster/team data and included in props

## Files to Modify

1. **sports-prediction-platform/backend/app/services/espn_prediction_service.py**
   - Fix confidence calculation to ensure NO hardcoded 50%
   - Fix line calculation to create different over/under lines
   - Fix team_name to be properly included

## Plan

### Step 1: Fix Confidence Calculation
- Search for any hardcoded 50% in confidence calculations
- Ensure minimum confidence is 55%+ when fallback is used

### Step 2: Fix Line Calculation
- Create separate logic for Over vs Under lines
- Add 0.5 to line for Over
- Subtract 0.5 from line for Under

### Step 3: Fix Team Name
- Ensure team_name is extracted from player roster data
- Include team abbreviation for compact display (e.g., "LAL" instead of "Los Angeles Lakers")
