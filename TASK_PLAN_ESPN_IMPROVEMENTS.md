# Task Plan: ESPN API Improvements

## Information Gathered:
Based on analysis of the codebase:
- `espn_prediction_service.py`: Main service with ESPN API integration (1300+ lines)
- `espn_player_stats_service.py`: Player stats extraction service
- `bayesian_confidence.py`: Bayesian confidence calculation
- Current endpoints: scoreboard, teams, roster, athlete/gamelog, athlete/stats
- Current line calculation uses 85% multiplier for all sports

## Plan:

### 1. Add More ESPN API Endpoints as Fallbacks
- **Add alternative endpoints**:
  - Player profile endpoint
  - Leaders/ rankings endpoint  
  - Season stats endpoint
  - Game logs endpoint
- **Create fallback chain** with graceful degradation
- **Add retry logic** with exponential backoff

### 2. Add Data Validation
- **Validate stat types**: Ensure numeric values
- **Validate ranges**: Check stats are within expected bounds
- **Validate required fields**: Ensure critical data present
- **Add validation errors**: Proper error messages

### 3. Handle Different Response Formats
- **Sport-specific parsing**: Different JSON structures for NBA/NHL/MLB
- **Format detection**: Auto-detect response format
- **Normalize data**: Convert to unified internal format

### 4. Improve Dynamic Line Calculation
- **Sport-specific multipliers**:
  - NBA: 85%
  - NHL: 75%
  - MLB: 80%
  - NFL: 80%
  - Soccer: 75%
- **Opponent defense adjustments**: Factor in opponent defensive rankings
- **Home/away splits**: Apply different lines based on venue

## Dependent Files to be Edited:
1. `sports-prediction-platform/backend/app/services/espn_prediction_service.py` - Main service
2. `sports-prediction-platform/backend/app/services/espn_player_stats_service.py` - Player stats
3. `sports-prediction-platform/backend/app/services/bayesian_confidence.py` - Confidence calculation

## Followup Steps:
1. Test API endpoints with fallbacks
2. Validate data format for all sports
3. Test dynamic line calculation with multipliers
4. Verify confidence scores remain in expected range (52-80%)

