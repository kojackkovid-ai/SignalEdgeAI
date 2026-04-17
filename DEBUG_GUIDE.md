# Debug Guide - NCAAB & Player Props Not Showing

## ✅ Backend Status: WORKING
```
✓ Found 57 NCAAB games
  1. NJIT Highlanders @ New Hampshire Wildcats
  2. UMBC Retrievers @ Maine Black Bears
  3. Bryant Bulldogs @ UMass Lowell River Hawks
```

## 🔍 Common Issues & Solutions

### Issue 1: Frontend Not Calling Backend Correctly

**Test the API directly:**
```bash
# 1. Get a test token first
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpassword"}'

# 2. Use the token to fetch NCAAB predictions
curl -X GET "http://localhost:8000/api/predictions/?sport=basketball_ncaa" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Expected Response:**
```json
[
  {
    "id": "basketball_ncaa_401705XXX",
    "matchup": "NJIT Highlanders @ New Hampshire Wildcats",
    "confidence": 66,
    "prediction": "New Hampshire Wildcats Win",
    "reasoning": [...]
  }
]
```

### Issue 2: Sport Key Mapping Not Working

**Check the browser console:**
1. Open browser dev tools (F12)
2. Go to Console tab
3. Look for logs like:
   - `[Dashboard] Fetching predictions for ncaab -> basketball_ncaa`
   - `[API] Fetching props for basketball_ncaa/401705XXX`

**If you don't see these logs, the mapping isn't working.**

### Issue 3: CORS or Network Error

**Check Network tab:**
1. Open browser dev tools (F12)
2. Go to Network tab
3. Click on "NCAAB" tab in the UI
4. Look for requests to `/api/predictions/`
5. Check if they return 200 or errors

### Issue 4: Empty Response Handling

**Check if predictions array is empty:**
In browser console, type:
```javascript
// After clicking NCAAB tab
fetch('/api/predictions/?sport=basketball_ncaa', {
  headers: { 'Authorization': 'Bearer ' + localStorage.getItem('access_token') }
})
.then(r => r.json())
.then(data => console.log('Predictions:', data.length, data))
```

## 🛠️ Quick Fixes to Try

### Fix 1: Clear Cache & Reload
```javascript
// In browser console
localStorage.clear();
location.reload();
```

### Fix 2: Check if User is Authenticated
```javascript
// In browser console
console.log('Token:', localStorage.getItem('access_token'));
console.log('User:', JSON.parse(localStorage.getItem('user') || '{}'));
```

### Fix 3: Test API Health
```bash
curl http://localhost:8000/health
```
Should return: `{"status":"healthy",...}`

### Fix 4: Restart Servers
```bash
# Stop existing servers (find PIDs)
lsof -ti:8000 | xargs kill
lsof -ti:3000 | xargs kill

# Restart backend
cd sports-prediction-platform/backend
python -m app.main

# Restart frontend (new terminal)
cd sports-prediction-platform/frontend
npx vite --port 3000
```

## 📝 Step-by-Step Verification

### Step 1: Verify Backend
```bash
curl http://localhost:8000/health
# Should show "status": "healthy"
```

### Step 2: Verify Frontend Build
```bash
cd sports-prediction-platform/frontend
npm run build
# Should show "built in XX.XXs" with 0 errors
```

### Step 3: Check Browser Console
1. Open http://localhost:3000
2. Login with test account
3. Open DevTools (F12) → Console
4. Click "NCAAB" tab
5. Look for:
   - `[Dashboard] Fetching predictions for ncaab -> basketball_ncaa`
   - `[Dashboard] Received X predictions`
   - Or any red error messages

### Step 4: Check Network Requests
1. Open DevTools → Network tab
2. Click "NCAAB" tab
3. Look for request to `predictions/?sport=basketball_ncaa`
4. Click on it → Preview tab
5. Should show array of predictions

## 🚨 If Still Not Working

### Check the PredictionCard Component
The issue might be in how PredictionCard displays data. Check:
1. Is `predictions` array populated? (Console: `console.log(predictions)`)
2. Is `PredictionCard` receiving props correctly?
3. Are there any conditional renders blocking display?

### Check for These Common Errors in Console:
- `Cannot read property 'map' of undefined` → predictions is undefined
- `401 Unauthorized` → token expired or missing
- `404 Not Found` → API endpoint wrong
- `CORS error` → backend/frontend port mismatch

## 📊 Expected Data Flow

1. User clicks "NCAAB" tab
2. Frontend sends: `GET /api/predictions/?sport=basketball_ncaa`
3. Backend fetches 57 games from ESPN
4. Backend generates predictions with 66% confidence
5. Frontend receives array of 57 predictions
6. Frontend maps through array and renders PredictionCards

## ✅ Success Indicators

- Console shows: `[Dashboard] Fetching predictions for ncaab -> basketball_ncaa`
- Console shows: `[Dashboard] Received 57 predictions`
- Network tab shows: Status 200 for predictions request
- UI shows: Grid of game cards with team names and confidence scores

## 🆘 Still Need Help?

If you've tried all above and still not working, check:

1. **Is the backend actually running?**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Is the frontend connected to the right backend?**
   Check `frontend/src/utils/api.ts` - should point to `/api` (not localhost:8000)

3. **Are there any ad blockers?**
   Some ad blockers block API calls. Try disabling them.

4. **Try incognito mode**
   Rules out extension conflicts

5. **Check if it's a specific sport issue**
   Try NBA tab - does that work?
