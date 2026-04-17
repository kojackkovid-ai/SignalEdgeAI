
# Player Props Implementation TODO

## Task: Fix Player Props for All Sports Using Real ESPN API Data

### Current Issue
The `get_player_props` method in `espn_prediction_service.py` is a placeholder returning empty list.

### Implementation Steps

#### Step 1: Implement ESPN API Integration Methods
- [ ] Add `_get_team_roster(sport_key, team_id)` method
- [ ] Add `_fetch_athlete_stats(athlete_id, sport_key)` method
- [ ] Add `_fetch_team_stats(team_id, sport_key)` method

#### Step 2: Implement Sport-Specific Prop Generators
- [ ] `_generate_nba_player_props()` - Points, rebounds, assists
- [ ] `_generate_nhl_player_props()` - Goals, assists, saves
- [ ] `_generate_mlb_player_props()` - Home runs, hits, RBIs
- [ ] `_generate_nfl_player_props()` - Pass yards, rush yards, rec yards
- [ ] `_generate_soccer_player_props()` - Goals, shots, assists

#### Step 3: Rewrite `get_player_props()` Method
- [ ] Fetch game data from ESPN
- [ ] Get team rosters for both teams
- [ ] Fetch player stats for key players
- [ ] Generate player props using real data only
- [ ] Calculate confidence based on actual stats
- [ ] Return empty list only when no real data available

#### Step 4: Testing
- [ ] Run `python backend/test_live_props.py`
- [ ] Run `python backend/test_nhl_mlb_props.py`
- [ ] Run `python backend/test_follow_endpoint.py`
- [ ] Verify no fake/simulated/placeholder data is returned

### Files to Edit
1. `sports-prediction-platform/backend/app/services/espn_prediction_service.py` - Main implementation
2. `sports-prediction-platform/backend/app/routes/predictions.py` - Minor verification
3. `sports-prediction-platform/backend/app/services/prediction_service.py` - Minor verification
