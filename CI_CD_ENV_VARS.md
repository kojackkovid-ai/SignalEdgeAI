# Environment Variables for CI/CD Deployment

## Default Values (create .env file with these)

```bash
# Database Configuration
DB_USER=postgres
DB_PASSWORD=your_secure_password_here
DB_NAME=sports_predictions_prod

# API Keys
ODDS_API_KEY=your_odds_api_key
STRIPE_SECRET_KEY=sk_live_YOUR_KEY
STRIPE_PUBLIC_KEY=pk_live_YOUR_KEY
STRIPE_WEBHOOK_SECRET=whsec_YOUR_KEY

# Security
SECRET_KEY=your_256_bit_secret_key_here

# URLs
API_URL=https://your-domain.com/api
FRONTEND_URL=https://your-domain.com

# Email (Mailgun)
MAILGUN_API_KEY=key_YOUR_KEY
MAILGUN_DOMAIN=your-domain.mailgun.org

# Monitoring
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
SENTRY_ENVIRONMENT=production

# Logging
LOG_LEVEL=info

# Frontend Build Args
VITE_APP_NAME=SignalEdge AI
VITE_STRIPE_PUBLISHABLE_KEY=pk_live_YOUR_KEY
```

## CI/CD Environment Variables

These are automatically set during deployment:

```bash
# Set by GitHub Actions during build
BACKEND_IMAGE=ghcr.io/your-username/sports-prediction-platform-backend:TAG
FRONTEND_IMAGE=ghcr.io/your-username/sports-prediction-platform-frontend:TAG

# Database URLs (constructed from above)
DATABASE_URL=postgresql+asyncpg://postgres:${DB_PASSWORD}@postgres:5432/${DB_NAME}
REDIS_URL=redis://redis:6379

# Celery for ML Workers
CELERY_BROKER_URL=redis://redis:6379
CELERY_RESULT_BACKEND=redis://redis:6379

# Internal
ENVIRONMENT=production
PYTHONUNBUFFERED=1
```

## Usage Examples

### Local Development
```bash
docker compose -f docker-compose.yml up -d
```

### Staging Deployment
```bash
export BACKEND_IMAGE=ghcr.io/username/sports-prediction-platform-backend:main
export FRONTEND_IMAGE=ghcr.io/username/sports-prediction-platform-frontend:main

docker compose -f docker-compose.staging.yml pull
docker compose -f docker-compose.staging.yml up -d
```

### Production Deployment
```bash
export BACKEND_IMAGE=ghcr.io/username/sports-prediction-platform-backend:v1.0.0
export FRONTEND_IMAGE=ghcr.io/username/sports-prediction-platform-frontend:v1.0.0

docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

### With Full Configuration
```bash
export BACKEND_IMAGE=ghcr.io/username/sports-prediction-platform-backend:v1.0.0
export FRONTEND_IMAGE=ghcr.io/username/sports-prediction-platform-frontend:v1.0.0
export DB_PASSWORD=secure_password
export STRIPE_SECRET_KEY=sk_live_...

docker compose -f docker-compose.prod.yml --env-file .env up -d
```
