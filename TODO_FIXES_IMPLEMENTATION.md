# Implementation TODO for Prediction Platform Fixes

## Tasks:

### 1. Fix Font Colors in PredictionCard.tsx
- [ ] Change `getPredictionColor` function to use dark colors
- [ ] Replace bright neon colors with dark readable colors
- [ ] Update ConfidenceGauge colors if needed

### 2. Fix AI Prediction Display Logic in espn_prediction_service.py
- [ ] Update `convert_prediction_to_string` function
- [ ] Map probability arrays to readable text like "Lakers to Win"
- [ ] Handle different prediction types (moneyline, spread, total)

### 3. Fix Player Props API Endpoint in predictions.py
- [ ] Check `/predictions/player-props` endpoint
- [ ] Ensure proper data structure and error handling
- [ ] Add logging for debugging

### 4. Improve Prediction Flow in Dashboard.tsx
- [ ] Restructure detail view to show game prediction first
- [ ] Make unlock mechanism clearer
- [ ] Show predicted winner prominently

### 5. Add Clear Winner Display
- [ ] Add visual indicator for predicted winner
- [ ] Show prediction type clearly
- [ ] Display confidence score prominently

## Files to Edit:
1. `frontend/src/components/PredictionCard.tsx`
2. `backend/app/services/espn_prediction_service.py`
3. `frontend/src/pages/Dashboard.tsx`
4. `backend/app/routes/predictions.py`
