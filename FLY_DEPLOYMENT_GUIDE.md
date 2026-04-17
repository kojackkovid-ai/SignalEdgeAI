# Fly.io Deployment Setup Guide

## Prerequisites
1. Install Fly CLI: https://fly.io/docs/getting-started/installing-flyctl/
2. Create Fly.io account: https://fly.io/app/sign-up
3. Run `flyctl auth login` to authenticate

## Quick Start (Copy-Paste Commands)

### 1. Create App (if not exists)
```bash
cd c:\Users\bigba\Desktop\New folder\sports-prediction-platform
flyctl auth login
flyctl launch --name sports-predictions-ai --region ord --builder docker
```

### 2. Create PostgreSQL Database
```bash
flyctl postgres create --name sports-predictions-db --region ord --initial-cluster-size 1 --vm-size shared-cpu-1x
flyctl postgres attach sports-predictions-db --app sports-predictions-ai
```

### 3. Create Redis Database
```bash
flyctl redis create --name sports-predictions-redis --region ord --eviction-policy allkeys-lru
flyctl redis attach sports-predictions-redis --app sports-predictions-ai
```

### 4. Set Environment Secrets
```bash
# Set production secrets
flyctl secrets set \
  SECRET_KEY="$(openssl rand -hex 32)" \
  ENVIRONMENT="production" \
  ENABLE_ANALYTICS="true" \
  SLOT_BASED_RECOMMENDATIONS="true" \
  LOG_LEVEL="INFO" \
  --app sports-predictions-ai
```

### 5. Deploy
```bash
flyctl deploy --app sports-predictions-ai
```

### 6. Check Deployment
```bash
flyctl status --app sports-predictions-ai
flyctl logs --app sports-predictions-ai
```

### 7. Test Endpoints
```bash
# Get app URL
flyctl info --app sports-predictions-ai

# Test health endpoint
curl https://sports-predictions-ai.fly.dev/health

# Get external IP for custom domain
flyctl ips list --app sports-predictions-ai
```

## Environment Variables Reference

| Variable | Value | Notes |
|----------|-------|-------|
| `DATABASE_URL` | Auto-set by Postgres attachment | Don't set manually |
| `REDIS_URL` | Auto-set by Redis attachment | Don't set manually |
| `SECRET_KEY` | Generate with: `openssl rand -hex 32` | Must be kept secret |
| `ENVIRONMENT` | `production` | Changes app behavior |
| `API_HOST` | `0.0.0.0` | Already in fly.toml |
| `API_PORT` | `8080` | Already in fly.toml |
| `LOG_LEVEL` | `INFO` | Can be DEBUG for troubleshooting |
| `ENABLE_ANALYTICS` | `true` | Enable analytics features |
| `SLOT_BASED_RECOMMENDATIONS` | `true` | Enable recommendation engine |

## Custom Domain Setup (Optional)

1. **Point domain to Fly app**:
   ```bash
   flyctl certs create your-domain.com --app sports-predictions-ai
   ```

2. **Add DNS records** (from `flyctl certs check your-domain.com`):
   - Type A: `your-domain.com` → Fly IP
   - Type CNAME: `www.your-domain.com` → `your-domain.com.fly.dev`

3. **Verify SSL certificate**:
   ```bash
   flyctl certs list --app sports-predictions-ai
   ```

## Monitoring & Troubleshooting

```bash
# View real-time logs
flyctl logs --app sports-predictions-ai -f

# View app status
flyctl status --app sports-predictions-ai

# SSH into running machine
flyctl ssh console --app sports-predictions-ai

# View metrics
flyctl metrics --app sports-predictions-ai

# Rollback to previous deployment
flyctl releases --app sports-predictions-ai
flyctl releases rollback <version> --app sports-predictions-ai
```

## Cost & Scaling

- **Base**: $5/month for shared-cpu instance
- **Storage**: Postgres (shared tier), Redis (shared tier) included in free tier
- **Scale up**: `flyctl machine update <id> --memory 1024 --app sports-predictions-ai`

## Manual Steps

If the commands above fail, do these step-by-step:

1. Login to [fly.io](https://fly.io)
2. Create new app from dashboard
3. Create PostgreSQL from "Databases" section
4. Create Redis from "Databases" section
5. Add secrets from "Variables and Secrets" section
6. Deploy with: `flyctl deploy`

---

**Current Status**: ✅ Configuration files created (fly.toml, Dockerfile.fly)  
**Next Step**: Run the commands above to deploy
