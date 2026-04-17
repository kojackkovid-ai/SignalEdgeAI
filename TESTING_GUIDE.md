# 📋 Project Status & Testing Guide

## Current State - January 29, 2026

### ✅ What's Working
1. **Backend API**
   - FastAPI server with async SQLite database
   - JWT authentication
   - Real predictions from OddsAPI
   - Tier-based access control
   - CORS properly configured

2. **Frontend**
   - React + TypeScript + Vite
   - Zustand store for auth state
   - Protected routes requiring login
   - Responsive design with Tailwind CSS

3. **Real Predictions**
   - OddsAPI integration
   - Fetches real sports events (NFL, NBA, NHL, Soccer, MLB)
   - Transforms events to predictions with confidence scores
   - Model ensemble data included
   - Reasoning points generated

### 🔧 What Was Just Fixed

#### **1. Login Flow - Token Storage Race Condition**
**Issue**: Token wasn't being persisted correctly
```
Before:
  1. Login API call ✓
  2. Store updates setToken() (reads localStorage)
  3. But localStorage.setItem() never called!

After:
  1. Login API call ✓
  2. localStorage.setItem('access_token', token)
  3. Then store setToken() 
  4. Both in sync ✓
```

#### **2. Database Initialization**
**Issue**: Tables weren't created on startup
```
Before: Tables only created if create_tables.py explicitly run
After:  Tables auto-created via @app.on_event("startup")
```

---

## 🧪 How to Test Everything

### **Quick Start (5 min)**

```bash
# Terminal 1: Backend
cd backend
python -m uvicorn app.main:app --reload

# Terminal 2: Frontend (in separate terminal)
cd frontend
npm run dev

# Terminal 3: Run tests (in another terminal)
cd sports-prediction-platform
python test_login_and_predictions.py
```

### **Manual Testing Steps**

#### **1. Register**
- Navigate to `http://localhost:5173`
- Click "Register"
- Fill in email, password, username
- Click "Register"
- Should see success and redirect to dashboard

#### **2. Login**
- Navigate to `http://localhost:5173/login`
- Use credentials from registration
- Click "Sign In"
- Should see dashboard with predictions

#### **3. Verify Token Storage**
```javascript
// Open browser DevTools (F12) → Console → type:
localStorage.getItem('access_token')
// Should return a long JWT token starting with "eyJ..."
```

#### **4. Check Predictions**
- Dashboard should show real sports predictions
- Each prediction has: matchup, confidence, odds
- Click prediction to see details (reasoning, models)
- Filter by sport (NFL, NBA, NHL, Soccer)

#### **5. Test API Directly**
```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email":"testuser@test.com",
    "password":"Password123!",
    "username":"testuser"
  }'

# Get token from response, then use it:
curl -X GET http://localhost:8000/api/predictions/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Should return JSON array of predictions
```

---

## 🔍 Debugging Tips

### **If Login Fails**

**Check browser console** (F12):
```javascript
// You should see these debug messages:
[Login] Response: {...token...}
[Login] Token saved to localStorage and store
```

**Check backend logs**:
```
INFO: Fetching predictions endpoint called - User ID: xxx
INFO: User tier: basic
```

**Common issues**:
- ❌ Token not in localStorage → Check the fix in Login.tsx was applied
- ❌ 401 Unauthorized → Backend not getting Bearer token
- ❌ 500 Server Error → Check backend logs for database issues

### **If Predictions Not Showing**

**Check**:
1. User is authenticated (has token)
2. Backend logs show "Calling odds_api_service.get_predictions()"
3. OddsAPI might be rate limited or down

**Test public endpoint** (no auth needed):
```bash
curl http://localhost:8000/api/predictions/public
```

If this works but authenticated endpoint doesn't, it's an auth issue.

---

## 📊 Architecture Overview

```
User Login Flow:
┌─────────────┐
│   Frontend  │
│  (React)    │
└─────────────┘
      ↓
  LoginForm.tsx
      ↓
  api.login(email, password)
      ↓
  POST /api/auth/login
      ↓
┌─────────────────────────────┐
│    Backend (FastAPI)        │
│  - Validates credentials    │
│  - Queries database         │
│  - Creates JWT token        │
└─────────────────────────────┘
      ↓
  Returns: {access_token, user_id, tier}
      ↓
  localStorage.setItem('access_token', token)
      ↓
  useAuthStore.setToken(token)
      ↓
  Navigate to /dashboard
      ↓
  API calls include: Authorization: Bearer {token}
      ↓
  Backend validates JWT
      ↓
  Returns tier-filtered predictions
```

---

## 📁 Key Files Modified

1. **frontend/src/pages/Login.tsx**
   - Fixed token storage order
   - Added debug logging

2. **backend/app/main.py**
   - Added startup event
   - Calls init_db() to create tables

---

## 🚀 Next Steps After Testing

1. ✅ Verify login works
2. ✅ Verify predictions appear
3. ✅ Test filtering by sport
4. ⏭️  Test tier differences (register with different tiers)
5. ⏭️  Test prediction details modal
6. ⏭️  Change JWT secret key to production value
7. ⏭️  Set up proper environment variables (.env file)

---

## 🔐 Security Reminders

⚠️ **For Development Only**:
- JWT secret: `"your-secret-key-change-in-production"`
- Allow all CORS origins
- Logging debug info enabled

✅ **Before Production**:
- Generate strong JWT secret: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- Restrict CORS to specific domains
- Disable debug logging
- Use environment variables for secrets
- Enable HTTPS
- Add rate limiting
- Add input validation

---

## 📞 Support Commands

```bash
# Kill any running Python/Node processes
taskkill /IM python.exe /F
taskkill /IM node.exe /F

# Start fresh backend
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload

# Start fresh frontend
cd frontend
npm install
npm run dev

# Clean database (delete old data)
rm sports_predictions.db
# Database will recreate on next backend start
```

---

**Status**: 🟢 Ready for testing
**Last Updated**: 2026-01-29
