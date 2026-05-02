# SignalEdge AI - Sports Prediction Platform

## Overview
AI-powered sports prediction platform with ML ensemble models (XGBoost, LightGBM, TensorFlow, scikit-learn) providing real-time predictions for Soccer, NHL, Basketball, NFL, and MLB with a "Cyber-Tactical HUD" military-inspired interface.

## Architecture

### Frontend
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite (port 5000)
- **Styling**: TailwindCSS + custom CSS
- **State**: Zustand
- **HTTP**: Axios with retry interceptor (analytics excluded from retry)
- **Charts**: Chart.js, Recharts
- **Animation**: Framer Motion

### Backend
- **Framework**: FastAPI (Python 3.12)
- **Server**: Uvicorn (port 8000)
- **ORM**: SQLAlchemy (async)
- **Database**: PostgreSQL (Replit-managed, via DATABASE_URL env var)
- **Auth**: JWT (python-jose, passlib/bcrypt)
- **ML**: XGBoost, LightGBM, scikit-learn, TensorFlow (lazy-loaded, requires libgomp)

### Key Directories
- `frontend/` - React application
  - `src/utils/api.ts` - Axios client with auth interceptor and token refresh
  - `src/utils/retry.ts` - Retry interceptor with URL exclusion support
  - `src/utils/tokenManager.ts` - JWT lifecycle monitoring
  - `src/utils/analytics.ts` - Frontend analytics tracker
  - `src/pages/Dashboard.tsx` - Main prediction dashboard
- `backend/app/` - FastAPI application
  - `routes/` - API endpoints (auth, predictions, users, payment, analytics, etc.)
  - `services/` - Business logic and ML services
  - `models/` - SQLAlchemy database models and response schemas
  - `utils/` - Utilities (caching, rate limiting, health checks, logging)
- `ml-models/` - ML model definitions and training pipeline
- `database/` - Database schemas and backups

## Workflows
- **Start application** - Frontend (Vite dev server on port 5000, webview)
- **Backend API** - FastAPI server (Uvicorn on localhost:8000, console)
  - Sets `LD_LIBRARY_PATH` to `/nix/store/055bzdrski1dwqa4km1gxpcjhpn73mng-gcc-10.3.0-lib/lib` for libgomp (XGBoost/LightGBM OpenMP support)

## Environment Configuration

### Backend (.env in backend/)
- `USE_SQLITE=true` (overridden by DATABASE_URL env var from Replit PostgreSQL)
- `SECRET_KEY` - JWT signing key (real hex key, not dev placeholder)
- `ALGORITHM=HS256`
- `ACCESS_TOKEN_EXPIRE_MINUTES=30`

### Frontend (.env in frontend/)
- `VITE_API_URL=/api` - proxied to backend
- `VITE_APP_NAME=SignalEdge AI`

### Replit Environment Variables
- `DATABASE_URL` - PostgreSQL connection string (auto-set by Replit)
- `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE` - PostgreSQL credentials

## CORS & Host Configuration
- CORS: `allow_origins=["*"]` with `allow_credentials=False`
- Trusted host middleware: disabled to allow all Replit proxy hosts
- Vite: `allowedHosts: true`, `host: '0.0.0.0'`, `port: 5000`
- Backend proxy: `/api` → `http://localhost:8000`

## API Endpoints
- `GET /health` - Health check
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login (returns JWT)
- `POST /api/auth/refresh` - Refresh token (requires valid Bearer token, returns 401 on invalid)
- `POST /api/auth/logout` - Logout
- `GET /api/predictions/` - Get predictions (requires auth)
- `GET /api/users/me` - Current user
- `GET /api/users/tier` - User subscription tier and daily limit
- `POST /api/analytics/event` - Track analytics event (field: `event_type`)
- `GET /api/analytics/` - Analytics data

## Production Fixes Applied
1. **Auth `/refresh` and `/logout` endpoints** - Fixed broken `Depends(lambda: ...)` pattern; now uses `Depends(get_auth_service().get_current_user)` — returns proper 401 for invalid tokens instead of 500.
2. **Database migration startup error** - Fixed `InFailedSQLTransactionError` by detecting SQLite from the URL string instead of executing `SELECT sqlite_version()` which was aborting PostgreSQL transactions.
3. **libgomp for XGBoost/LightGBM** - Backend workflow sets `LD_LIBRARY_PATH` to the 64-bit gcc-10 lib path; EnhancedMLService loads correctly.
4. **Verbose console logging removed** - `api.ts` no longer logs every request/token; `Dashboard.tsx` removed all debug `console.log` statements; `tokenManager.ts` removed all monitoring noise; `App.tsx` removed startup debug logs.
5. **Analytics retry storm fixed** - Retry interceptor now excludes `/analytics/event` URL via `excludeUrls` config; analytics failures are silently dropped as intended.
6. **Retry stats logging removed** - Removed `logRetryStats` from `retry.ts` (was logging to console every minute).
7. **React Router future flags** - Added `v7_startTransition` and `v7_relativeSplatPath` flags to `BrowserRouter` to silence upgrade warnings.
8. **Secret key** - Backend `.env` updated with a real cryptographic hex key.

## Optional Integrations (not required for basic functionality)
- **OddsAPI** - Real-time sports odds (ODDS_API_KEY env var)
- **Stripe** - Payment processing (STRIPE_SECRET_KEY, STRIPE_PUBLIC_KEY)
- **Mailgun** - Email (MAILGUN_API_KEY, MAILGUN_DOMAIN)
- **Redis** - Caching (REDIS_URL, falls back to in-memory)
- **OpenWeather** - Weather data (OPENWEATHER_API_KEY)
