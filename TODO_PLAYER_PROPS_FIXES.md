# Player Props Fixes TODO

## Issues to Fix:
1. **All player props show 50% confidence** - When ESPN data unavailable, default is 50% (random)
2. **Same line for Over/Under** - Both use identical point value instead of different lines
3. **Missing team name** - Team name not displayed with player props

## Implementation Plan:

### 1. Fix Confidence Calculation (espn_prediction_service.py)
- Change fallback confidence from 50% to 55-65% range
- Add logic to use available data to calculate a more accurate confidence
- Ensure confidence varies based on available stats

### 2. Fix Over/Under Lines (espn_prediction_service.py)
- Modify `_determine_over_under` to return both over_line and under_line
- OVER line = 85% of player's average
- UNDER line = 115% of player's average
- Generate separate props for Over and Under with different lines

### 3. Fix Team Name Display (espn_prediction_service.py)
- Ensure team_name is properly passed to each player prop
- Add team_name to the prop dictionary for all sports

## Files to Modify:
- sports-prediction-platform/backend/app/services/espn_prediction_service.py

## Testing:
- Test with NBA player props
- Test with NHL player props
- Test with MLB player props
- Verify confidence varies between props
- Verify different lines for Over vs Under
- Verify team name is displayed

