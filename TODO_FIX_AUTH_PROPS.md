# TODO: Fix NBA Player Props and Predictions Issues

## Issues to Fix:
1. **401 Unauthorized** - API calls failing due to authentication issues
2. **Player prop unlock not showing data** - User picks are used but prop info doesn't display
3. **No sports predictions showing** - All predictions not rendering in the frontend

## Root Cause Analysis:
- Backend predictions API works (verified by test)
- Frontend-auth connection has issues causing 401 errors
- Player prop unlock flow has UI handling issues

## Fix Plan:
- [ ] 1. Investigate authentication issue in frontend API client
- [ ] 2. Fix player prop unlock data display in Dashboard.tsx
- [ ] 3. Ensure predictions endpoint returns proper data
- [ ] 4. Verify all sports predictions display correctly
