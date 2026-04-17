# Integration Testing Guide

## Services Status

### ✅ Backend Server
- **Status**: Running on http://127.0.0.1:8000
- **Database**: Connected to sports_predictions (PostgreSQL)
- **API Documentation**: http://127.0.0.1:8000/docs

### 🔄 Frontend Server  
- **Status**: Starting on http://localhost:5173
- **Development Mode**: Hot reload enabled
- **Proxy**: /api routes to http://localhost:8000

---

## Manual Testing Steps

### Step 1: Access Frontend
1. Open browser to **http://localhost:5173**
2. You should see the landing page with:
   - Header with "Sign In", "Register", "Get Started" buttons
   - Pricing section with 4 tiers (Starter, Basic, Pro, Elite)
   - Features and comparison table
   - CTA buttons for each plan

### Step 2: Test Navigation
- Click "Sign In" → Navigate to sign-in page
- Click "Register" → Navigate to register page
- Click "Get Started" → Navigate to dashboard
- Click pricing plan CTA buttons → Should navigate to sign-up/login

### Step 3: Test User Registration
1. Go to Registration page
2. Fill in:
   - Email: `test@example.com`
   - Username: `testuser`
   - Password: `TestPass123`
3. Click Register
4. Should get JWT token in response
5. Redirected to Dashboard (if logged in)

### Step 4: Test Starter Tier (Free)
1. Log in as user (registered above)
2. Dashboard shows:
   - ✅ "1 Pick Today" (pick limit)
   - ✅ Only basic confidence scores
   - ❌ No odds showing
   - ❌ No reasoning/strategy showing
   - ❌ No ML models showing
3. After 1 pick, button should disable
4. Pricing page shows Starter features highlighted

### Step 5: Test Basic Tier  
1. Via database/admin, upgrade user to "basic" tier
2. Refresh Dashboard
3. Shows:
   - ✅ "10 Picks Today" (pick limit)
   - ✅ Confidence scores
   - ✅ Odds displayed
   - ✅ Basic reasoning
   - ❌ No ML models
4. After 10 picks, button disables

### Step 6: Test Pro Tier
1. Upgrade user to "pro"
2. Refresh Dashboard
3. Shows:
   - ✅ "25 Picks Today"
   - ✅ All features: confidence, odds, reasoning
   - ✅ ML models displayed
   - ✅ Extended reasoning
4. After 25 picks, button disables

### Step 7: Test Elite Tier
1. Upgrade user to "elite"
2. Refresh Dashboard  
3. Shows:
   - ✅ "∞ Picks" or no limit message
   - ✅ All features
   - ✅ Pick button never disables

### Step 8: Test API Endpoints

**Register User:**
```powershell
$body = @{
    email="newuser@test.com"
    password="Pass123"
    username="newuser"
} | ConvertTo-Json

$response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/auth/register" `
  -Method POST -ContentType "application/json" -Body $body -UseBasicParsing
  
$response.Content | ConvertFrom-Json
```

**Expected Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "tier": "free"
}
```

**Login User:**
```powershell
$body = @{
    email="test@example.com"
    password="TestPass123"
} | ConvertTo-Json

$response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/auth/login" `
  -Method POST -ContentType "application/json" -Body $body -UseBasicParsing

$response.Content | ConvertFrom-Json
```

**Get Predictions (requires token):**
```powershell
$token = "<JWT_TOKEN_FROM_LOGIN>"

Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/predictions" `
  -Headers @{"Authorization" = "Bearer $token"} `
  -UseBasicParsing | Select-Object -ExpandProperty Content | ConvertFrom-Json
```

---

## Expected Behavior Summary

| Tier | Picks/Day | Confidence | Odds | Reasoning | Models | Price |
|------|-----------|-----------|------|-----------|--------|-------|
| Starter | 1 | ✅ | ❌ | ❌ | ❌ | Free |
| Basic | 10 | ✅ | ✅ | ✅ | ❌ | $9/mo |
| Pro | 25 | ✅ | ✅ | ✅ | ✅ | $29/mo |
| Elite | ∞ | ✅ | ✅ | ✅ | ✅ | $99/mo |

---

## Troubleshooting

### Frontend won't start
```powershell
cd frontend
npm install
npm run dev
```

### Backend won't start
```powershell
cd backend
venv\Scripts\activate
venv\Scripts\python.exe -m pip install -r requirements.txt
venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Can't connect to API
- Check backend is running: http://127.0.0.1:8000/docs
- Check database is running: pgAdmin at localhost:5050
- Check environment variables in backend/.env

### Database errors
- Verify database exists: `psql -U postgres -l | grep sports_predictions`
- Recreate if needed via pgAdmin

---

## Next Actions

1. ✅ Start both servers
2. ✅ Test UI navigation and rendering
3. ✅ Test user registration
4. ✅ Test each subscription tier
5. ✅ Verify pick limits and feature gating
6. ✅ Test API endpoints
7. Fix any bugs found
8. Deploy!

---

**Last Updated**: January 26, 2026
**Status**: Ready for testing
