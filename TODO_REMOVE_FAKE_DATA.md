# TODO: Remove Fake/Hardcoded Data from Sports Prediction Platform

## Issues Found:
1. Hardcoded default values in prop generation (NBA, NHL, MLB, NFL, Soccer)
2. Fake confidence values (50%, 55%) when ESPN data unavailable
3. _calculate_dynamic_line returns fake defaults instead of None

## Fix Plan:

### Phase 1: Fix espn_prediction_service.py
- [ ] 1.1 Fix _get_sport_default_line - already returns None (verified)
- [ ] 1.2 Fix _calculate_dynamic_line to return None when no ESPN data
- [ ] 1.3 Fix NBA props generation - skip props when no ESPN data
- [ ] 1.4 Fix NHL props generation - skip props when no ESPN data  
- [ ] 1.5 Fix MLB props generation - skip props when no ESPN data
- [ ] 1.6 Fix NFL props generation - skip props when no ESPN data
- [ ] 1.7 Fix Soccer props generation - skip props when no ESPN data

### Phase 2: Fix frontend Dashboard
- [ ] 2.1 Remove fallback mock data in Dashboard.tsx
- [ ] 2.2 Show proper loading/error states

### Phase 3: Fix confidence calculations
- [ ] 3.1 Ensure confidence returns None when no real data
- [ ] 3.2 Remove hash-based seeding in reasoning

</content>
