# Fix Plan: NBA Player Props and Predictions Issues

## Issue Summary:
1. **Predictions not showing** - API calls returning 401 Unauthorized
2. **Player prop unlock not displaying info** - Picks are used but UI doesn't show the unlocked data

## Root Causes:
1. Authentication issue - token may not be properly attached to API requests
2. Player prop unlock response handling in frontend needs verification

## Fixes to Implement:

### Fix 1: Add unauthenticated test endpoint for debugging
- Add a test endpoint to verify backend is working without auth
- Helps isolate if issue is auth or something else

### Fix 2: Ensure predictions API has proper error handling
- Add logging to help debug what's happening
- Ensure predictions are fetched even if there's an auth issue

### Fix 3: Verify player prop unlock response
- The backend should return proper data after unlock
- The frontend should display the unlocked data correctly

## Files to Check/Modify:
- backend/app/routes/predictions.py - ensure endpoints work
- frontend/src/pages/Dashboard.tsx - ensure response handling
- frontend/src/utils/api.ts - ensure auth token is sent

## Testing:
1. Run predictions API test directly (already verified working)
2. Check if frontend can authenticate properly
3. Verify player prop unlock flow works end-to-end
