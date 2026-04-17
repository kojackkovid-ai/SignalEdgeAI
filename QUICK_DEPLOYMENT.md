# Quick Start - Deploy to Production in 5 Minutes

## Option A: Railway.app (EASIEST - Recommended)

1. **Sign up at [railway.app](https://railway.app)** with GitHub
2. **Click "New Project" → "Deploy from GitHub repo"**
3. **Select this repository**
4. **Add these services** (click "Add Service"):
   - PostgreSQL (database)
   - Redis (cache)

5. **Add Environment Variables** (Project → Variables):
```
DB_USER=postgres
DB_PASS=YourSecurePassword123!
DB_HOST=${{ Postgres.RAILWAY_PRIVATE_URL }}
DB_PORT=5432
DB_NAME=sports_predictions_prod
SECRET_KEY=GenerateUsingPython-32CharsMin
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
API_HOST=0.0.0.0
API_PORT=8000
MODEL_UPDATE_INTERVAL=3600
MODEL_RETRAIN_DAYS=7
MIN_TRAINING_SAMPLES=1000
REDIS_URL=${{ Redis.RAILWAY_PRIVATE_URL }}
ODDS_API_KEY=YOUR_ODDS_API_KEY
STRIPE_PUBLIC_KEY=pk_test_YOUR_KEY
STRIPE_SECRET_KEY=sk_test_YOUR_KEY
VITE_API_URL=${{ Railway_URL }}/api
```

6. **Click Deploy** - Done! Railway handles everything

**Your app will be live at: `https://sports-prediction-[random].up.railway.app`**

---

## Option B: Docker (Self-Hosted)

### Quick Setup:

```bash
# 1. Edit environment file
cp .env.production .env.prod
nano .env.prod  # Fill in your values

# 2. Start everything
docker-compose -f docker-compose.prod.yml up -d

# 3. Check it's running
docker-compose -f docker-compose.prod.yml ps

# 4. View logs
docker-compose -f docker-compose.prod.yml logs -f backend
```

**Your app will be at: `http://localhost:3000`**

---

## Generate Critical Security Keys

Run this in Python:
```python
import secrets

# Generate SECRET_KEY
secret_key = secrets.token_urlsafe(32)
print(f"SECRET_KEY: {secret_key}")

# Generate a secure DB password
db_pass = secrets.token_urlsafe(16)
print(f"DB_PASS: {db_pass}")
```

---

## Share with Testers

Once deployed, send them:
```
🎯 Frontend: https://your-app-url.com
🔌 API: https://your-app-url.com/api
📝 Documentation: See PRODUCTION_DEPLOYMENT_GUIDE.md for full details
```

---

## More Options

- **Fly.io**: Similar to Railway, good performance
- **AWS/DigitalOcean**: More complex but powerful
- **See PRODUCTION_DEPLOYMENT_GUIDE.md for complete setup instructions**
