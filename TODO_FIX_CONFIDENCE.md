# TODO: Fix Confidence Level Issue - All Sports Showing 51%

## Problem
All predictions across all sports show 51% confidence level, which is incorrect. The ML models should produce varied confidence levels based on real data.

## Root Cause
1. Data mapping issue between `espn_prediction_service.py` and `enhanced_ml_service.py`
2. Game data uses keys like `home_wins`, `home_losses` but ML service looks for `home_win_pct`, `away_win_pct`
3. Missing keys cause fallback to defaults producing similar confidence values

## Tasks

### Phase 1: Fix Data Mapping in enhanced_ml_service.py
- [ ] 1.1 Update `predict()` method to calculate win percentages from wins/losses when keys don't exist
- [ ] 1.2 Fix confidence calculation to use real ESPN data

### Phase 2: Fix espn_prediction_service.py
- [ ] 2.1 Add proper data fields (win_pct) to game_data before passing to ML service

### Phase 3: Retrain ML Models with Real Data
- [ ] 3.1 Collect fresh real data from ESPN API
- [ ] 3.2 Train ML models for all sports
- [ ] 3.3 Verify varied confidence output

### Phase 4: Testing
- [ ] 4.1 Run tests to verify varied confidence levels
- [ ] 4.2 Check all sports produce different confidence values
