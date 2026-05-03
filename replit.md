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
4. **Verbose console logging removed** - `api.ts`, `Dashboard.tsx`, `tokenManager.ts`, `App.tsx`, `Payment.tsx`, `Login.tsx` — all debug `console.log` calls removed.
5. **Analytics retry storm fixed** - Retry interceptor now excludes `/analytics/event` URL; analytics failures are silently dropped.
6. **Retry stats logging removed** - Removed `logRetryStats` from `retry.ts`.
7. **React Router future flags** - Added `v7_startTransition` and `v7_relativeSplatPath` flags to `BrowserRouter`.
8. **Secret key** - Backend `.env` updated with a real cryptographic hex key.

## Platform Review Improvements (Pass 2)
9. **Security: Free tier upgrade endpoint disabled** - `POST /api/users/upgrade` had no payment verification (`# TODO: Verify payment with Stripe`). Any authenticated user could promote themselves to Elite for free. Now returns 403 directing to the proper payment flow.
10. **Security: Admin secret hardened** - `club100_addon.py` was using `"dev-admin-key"` as a fallback default for `ADMIN_SECRET_KEY`. Now refuses to serve the admin endpoint (503) if the env var is not set.
11. **Security: Hardcoded localhost URLs in emails fixed** - `email_tasks.py`, `email_integration_service.py`, `email.py` all had hardcoded `http://localhost:5173` links in email templates (verify email, dashboard links). Now all use `settings.frontend_url` (configurable via `FRONTEND_URL` env var).
12. **Performance: N+1 query eliminated** - `GET /api/predictions/props/{sport}/{event_id}` was calling `is_following_prediction()` in a per-prop loop (one DB round-trip per prop, up to 50+ queries per request). Replaced with `get_user_followed_ids()` batch method — single query fetches all followed IDs, loop uses in-memory set membership.
13. **Performance: Missing DB index added** - Added composite `Index('idx_prediction_sport_event', 'sport_key', 'event_id')` to `Prediction` model — most prop lookups filter by both fields.
14. **Data integrity: PredictionRecord.user relationship restored** - The `user = relationship("User", backref="prediction_records")` was commented out, forcing manual joins everywhere. Now uncommented.
15. **UX: Payment page debug block removed** - The checkout page was showing a developer "Debug Info" panel (`Auth ✅ / Stripe Promise ✅ / Client Secret ✅ / Loading`) to all users. Removed.
16. **UX: Analytics error state added** - Analytics page would get stuck showing "Loading analytics..." indefinitely on API failure. Now shows a proper error message with a "Try Again" button.
17. **UX: Login redirect URL preserved** - When the token monitor redirects an expired session to `/login`, it now appends `?redirect=/original/path`. The login page reads this param and navigates back after success so users don't lose their place.

## Platform Review Improvements (Pass 3)

### Critical Security
18. **ML endpoints protected** — All 8+ endpoints in `ml_operations.py` (training trigger, job enable/disable, model health, performance, dashboard) were completely unprotected — no auth at all. Added router-level `require_admin` dependency via `dependencies=[Depends(require_admin)]`; a single line locks the entire router.
19. **Resolution trigger protected** — `POST /api/resolution/trigger` was public, letting anyone spam expensive ESPN+DB calls. Added `require_admin` dependency.
20. **Analytics revenue/dashboard admin-only** — `/revenue`, `/dashboard`, `/conversion-funnel`, `/daily-active-users`, `/events`, and `/churn` were accessible to any registered user (showed MRR, churn rates, total revenue). All now require admin tier.

### Auth Lifecycle Fixes
21. **Token refresh syncs Zustand store** — `api.ts` was refreshing the token into `localStorage` and the axios default header, but never called `useAuthStore.getState().setToken()`. Any component reading from the Zustand store would hold the stale expired token for the rest of the session. Now calls `setToken(newToken)` immediately after a successful refresh.
22. **Store init skips expired tokens** — `store.ts` was initialising `isAuthenticated` from `localStorage` without checking expiry. A user with a token that expired while the tab was closed would briefly appear authenticated. Added `isTokenExpired()` helper; the store now starts with `null`/`false` for expired tokens and cleans up localStorage immediately.

### UI / UX Fixes
23. **PredictionCard default tier aligned** — `userTier` prop defaulted to `'free'` but `normalizedTier` defaulted to `'starter'`, creating a logic mismatch in feature-gating that could show the wrong locked/unlocked state. Both now default to `'starter'`.
24. **PredictionCard console.log removed** — Component was logging every render with `id`, `sport`, `league`, `matchup`, `prediction`, `confidence`, and `userTier` to the browser console.
25. **PropsTab fake model names removed** — When `prop.models` was missing the fallback rendered hardcoded "XGBoost: 65%", "RandomForest: 68%", "NeuralNet: 62%" labels, implying precision that wasn't real. Replaced with "Model breakdown not available".
26. **Header mobile button accessible** — Mobile nav toggle was missing `aria-label` and `aria-expanded`, making it invisible to screen readers. Now announces its state dynamically ("Open navigation menu" / "Close navigation menu").
27. **Club100 table headers keyboard accessible** — All four sortable column headers (Player Name, Streak, Last 4, Last 5) now have `tabIndex`, `role="button"`, `aria-label`, and `onKeyDown` Enter handlers so keyboard-only users can sort the table.

## Production Deployment (Fly.io)

App is live at: **https://signaledge-ai.fly.dev/**

- **App name**: `signaledge-ai`
- **Region**: `dfw` (Dallas)
- **Config**: `fly.toml` at repo root
- **Dockerfile**: `backend/Dockerfile` (builds backend + frontend/dist as static files)
- **Health check**: `GET /health` returns 200 with all checks passing
- **Deploy command**: `FLY_ACCESS_TOKEN="$FLY_API_TOKEN" flyctl deploy --remote-only`

### Fly.io Secrets to configure (via `flyctl secrets set`):
- `DATABASE_URL` — PostgreSQL connection string for production DB
- `SECRET_KEY` — JWT signing key
- `STRIPE_SECRET_KEY` — Stripe secret key (for payments)
- `STRIPE_PUBLIC_KEY` — Stripe publishable key
- `MAILGUN_API_KEY`, `MAILGUN_DOMAIN` — Email delivery
- `ADMIN_SECRET_KEY` — Admin endpoints protection
- `FRONTEND_URL` — Set to `https://signaledge-ai.fly.dev` for email links

### Post-deployment steps (user must perform):
1. Run `alembic upgrade head` against production DB to apply schema migrations
2. Set Stripe live keys via `flyctl secrets set STRIPE_SECRET_KEY=sk_live_...`

## Optional Integrations (not required for basic functionality)
- **OddsAPI** - Real-time sports odds (ODDS_API_KEY env var)
- **Stripe** - Payment processing (STRIPE_SECRET_KEY, STRIPE_PUBLIC_KEY)
- **Mailgun** - Email (MAILGUN_API_KEY, MAILGUN_DOMAIN)
- **Redis** - Caching (REDIS_URL, falls back to in-memory)
- **OpenWeather** - Weather data (OPENWEATHER_API_KEY)
