# SignalEdge AI - Sports Prediction Platform

## Overview
AI-powered sports prediction platform with ML ensemble models (XGBoost, LightGBM, TensorFlow, scikit-learn) providing real-time predictions for Soccer, NHL, Basketball, NFL, and MLB with a "Cyber-Tactical HUD" military-inspired interface.

## Architecture

### Frontend
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite (port 5000)
- **Styling**: TailwindCSS + custom CSS
- **State**: Zustand
- **HTTP**: Axios
- **Charts**: Chart.js, Recharts
- **Animation**: Framer Motion

### Backend
- **Framework**: FastAPI (Python 3.12)
- **Server**: Uvicorn (port 8000)
- **ORM**: SQLAlchemy (async)
- **Database**: PostgreSQL (Replit-managed, via DATABASE_URL env var)
- **Auth**: JWT (python-jose, passlib)
- **ML**: XGBoost, LightGBM, scikit-learn, TensorFlow (lazy-loaded)

### Key Directories
- `frontend/` - React application
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

## Environment Configuration

### Backend (.env in backend/)
- `USE_SQLITE=true` (overridden by DATABASE_URL env var from Replit PostgreSQL)
- `SECRET_KEY` - JWT signing key
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
- `POST /api/auth/login` - User login
- `GET /api/predictions/` - Get predictions
- `GET /api/users/me` - Current user
- `GET /api/analytics/` - Analytics data

## Optional Integrations (not required for basic functionality)
- **OddsAPI** - Real-time sports odds (ODDS_API_KEY env var)
- **Stripe** - Payment processing (STRIPE_SECRET_KEY, STRIPE_PUBLIC_KEY)
- **Mailgun** - Email (MAILGUN_API_KEY, MAILGUN_DOMAIN)
- **Redis** - Caching (REDIS_URL, falls back to in-memory)
- **OpenWeather** - Weather data (OPENWEATHER_API_KEY)
