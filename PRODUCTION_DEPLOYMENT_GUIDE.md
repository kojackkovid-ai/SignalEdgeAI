# Production Deployment Guide

Complete guide to deploy your Sports Prediction Platform for remote access and production use.

## Quick Start (Recommended: Railway.app)

### Step 1: Prepare Your Repository

1. **Initialize Git** (if not already done):
   ```bash
   cd sports-prediction-platform
   git init
   git add .
   git commit -m "Initial commit"
   ```

2. **Push to GitHub**:
   - Create a new repo on GitHub
   - Push your code:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/sports-prediction-platform.git
   git branch -M main
   git push -u origin main
   ```

### Step 2: Deploy on Railway.app (FREE)

**Why Railway?** Simple setup, free tier, automatic HTTPS, easy environment variables.

1. **Go to [railway.app](https://railway.app)**
2. **Sign up with GitHub**
3. **Create a new project** → "Deploy from GitHub repo"
4. **Select your repository**
5. **Railway will auto-detect services** and create a docker-compose setup
6. **Add Environment Variables**:
   - Go to Project Settings → Variables
   - Add all variables from `.env.production`:
   ```
   DB_USER=postgres
   DB_PASS=YOUR_SECURE_PASSWORD_HERE
   DB_HOST=${{ Postgres.RAILWAY_PRIVATE_URL }}
   REDIS_URL=${{ Redis.RAILWAY_PRIVATE_URL }}
   SECRET_KEY=GENERATE_A_SECURE_32_CHAR_KEY
   ODDS_API_KEY=YOUR_KEY
   STRIPE_SECRET_KEY=sk_live_YOUR_KEY
   VITE_API_URL=https://your-railway-domain.railway.app/api
   ```

7. **Add Postgres and Redis Services**:
   - Click "Add Service" → Select "Database" → PostgreSQL
   - Click "Add Service" → Select "Database" → Redis

8. **Deploy**:
   - Click "Deploy" - Railway builds and deploys automatically
   - Get your public URL and share it!

**You'll get a URL like**: `https://sports-prediction-railway.up.railway.app`

---

## Alternative: Deploy on Fly.io

### Step 1: Install Fly CLI
```bash
# Windows
choco install flyctl

# Or download from https://fly.io/docs/getting-started/installing-flyctl/
```

### Step 2: Initialize Project
```bash
cd sports-prediction-platform
fly auth login
fly launch --no-deploy
```

### Step 3: Create fly.toml
```toml
app = "sports-prediction-platform"
primary_region = "ord"

[env]
  ENVIRONMENT = "production"
  LOG_LEVEL = "info"

[build]
  dockerfile = "Dockerfile.prod"

[[services]]
  protocol = "tcp"
  internal_port = 8000
  processes = ["app"]
  
  [services.http_checks]
    enabled = true
    grace_period = "5s"
    interval = "10s"
    timeout = "5s"
    path = "/health"

[[services]]
  protocol = "tcp"
  internal_port = 80
  processes = ["web"]
  
  [[services.ports]]
    port = 80
    handlers = ["http"]
  
  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]
```

### Step 4: Set Secrets
```bash
fly secrets set DB_PASS=YOUR_PASSWORD
fly secrets set SECRET_KEY=YOUR_SECRET_KEY
fly secrets set STRIPE_SECRET_KEY=sk_live_YOUR_KEY
```

### Step 5: Deploy
```bash
fly deploy
```

---

## Docker Deployment (Any Server)

For deploying to your own server (AWS, DigitalOcean, Linode, etc.):

### Step 1: Prepare Server
```bash
# SSH into your server
ssh user@your-server-ip

# Install Docker & Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo apt-get install docker-compose -y
```

### Step 2: Clone and Setup
```bash
git clone https://github.com/YOUR_USERNAME/sports-prediction-platform.git
cd sports-prediction-platform

# Create production .env file
cp .env.production .env
nano .env  # Edit with your values
```

### Step 3: Deploy with Docker Compose
```bash
# Build and start all services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Check status
docker-compose -f docker-compose.prod.yml ps
```

### Step 4: Setup SSL with Nginx Reverse Proxy
```bash
# Install Nginx
sudo apt-get install nginx certbot python3-certbot-nginx -y

# Create nginx config
sudo nano /etc/nginx/sites-available/sports-prediction
```

Add this config:
```nginx
upstream backend {
    server localhost:8000;
}

upstream frontend {
    server localhost:3000;
}

server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;
    
    # SSL certificates (certbot will add these)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Proxy to frontend
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Proxy to backend API
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }
}
```

Enable and setup SSL:
```bash
sudo ln -s /etc/nginx/sites-available/sports-prediction /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
sudo certbot --nginx -d your-domain.com
```

---

## Environment Variables Checklist

**CRITICAL - Change these before deploying:**
- [ ] `DB_PASS` - Strong, unique password
- [ ] `SECRET_KEY` - Generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- [ ] `STRIPE_SECRET_KEY` - Get from Stripe Dashboard
- [ ] `VITE_API_URL` - Your actual domain

**Optional - Get your keys:**
- [ ] `ODDS_API_KEY` - Get free at https://the-odds-api.com
- [ ] `STRIPE_PUBLIC_KEY` - From Stripe Dashboard

---

## Testing Remote Access

Once deployed:

1. **Get your URL**:
   - Railway: Check your deployment dashboard
   - Fly.io: `fly status`
   - Self-hosted: `https://your-domain.com`

2. **Share with testers**:
   ```
   Frontend: https://your-deployed-url.com
   Backend API: https://your-deployed-url.com/api
   ```

3. **Test from anywhere**:
   - Use your phone's cellular (not WiFi your computer is on)
   - Have friends test
   - Use this command to test:
   ```bash
   curl https://your-deployed-url.com/health
   ```

---

## Troubleshooting

### Backend Connection Refused
```bash
# Check container status
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs backend

# Restart services
docker-compose -f docker-compose.prod.yml restart
```

### Database Issues
```bash
# Connect to DB
docker-compose -f docker-compose.prod.yml exec db psql -U postgres -d sports_predictions_prod

# Check tables
\dt

# Run migrations if needed
docker-compose -f docker-compose.prod.yml exec backend python -m alembic upgrade head
```

### Frontend Shows 404
- Ensure frontend Dockerfile builds correctly
- Check nginx.conf paths
- Verify SPA routing: all routes should serve index.html

### SSL Certificate Errors
```bash
# Renew cert
sudo certbot renew

# Manual renewal
sudo certbot renew --force-renewal
```

---

## Performance Tips

1. **Enable Caching**:
   - Cache predictions for 10-15 minutes
   - Cache models for 1 hour

2. **Database Optimization**:
   - Add indexes on frequently queried columns
   - Use connection pooling (PgBouncer)

3. **CDN for Frontend**:
   - Use Cloudflare (free tier)
   - Cache static assets aggressively

4. **Monitoring**:
   - Set up error tracking: Sentry, LogRocket
   - Monitor performance: Datadog, New Relic free tier

---

## Security Checklist

- [ ] Change all default credentials
- [ ] Use HTTPS only (not HTTP)
- [ ] Enable CORS only for your domain
- [ ] Remove debug mode from production
- [ ] Use strong database passwords
- [ ] Keep dependencies updated: `pip install --upgrade -r requirements.txt`
- [ ] Enable rate limiting on API
- [ ] Setup firewall rules
- [ ] Regular backups of database

---

## Need Help?

1. **Railway Support**: railway.app/support
2. **Fly.io Support**: fly.io/docs
3. **Docker Issues**: Check service logs and healthchecks
4. **API Issues**: Check backend logs for detailed errors
