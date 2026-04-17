# ESPN-Only Cleanup Plan
## Steps to Complete

### 1. Remove fake fallback methods from espn_prediction_service.py
- Remove `_get_default_player_stats_for_sport()`
- Remove `_get_position_based_stats()` if exists
- Update `_get_player_stat_averages()` to return None when no ESPN data (no stats_dict fallback)
- Update prop generation to skip players without ESPN stats (already mostly done)
- Clean up comments/references to removed methods

### 2. Delete or update test files
- DELETE test_fallback.py (tests position-based fake stats)
- DELETE test_stats_quick.py (tests default stats methods)
- Ensure no new test files created

### 3. Update fallback logic in production code
- In `_calculate_dynamic_line()` - ensure None when no stats
- In `_get_player_stat_averages()` - no fake estimation
- Prop generation: skip if no real ESPN data

### 4. Verification
- Run existing ESPN API tests
- Check production predictions show fewer props (only real data)
- Verify no errors from missing fallbacks

### Status: Pending User Approval

