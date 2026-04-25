# Fly.io Deployment - READY TO DEPLOY

**Status**: ✅ Configuration files updated and ready for deployment

## Prerequisites Check

Before deploying, ensure you have:
- [ ] Fly.io account (https://fly.io/app/sign-up)
- [ ] flyctl CLI installed (`flyctl --version` should work)
- [ ] Authenticated with Fly (`flyctl auth login`)

## Quick Deploy Steps

### 1. Open PowerShell in Project Root
```powershell
cd "c:\Users\bigba\Desktop\New folder\sports-prediction-platform"
```

### 2. Login to Fly.io (if not already logged in)
```powershell
flyctl auth login
```

### 3. Deploy Application
```powershell
flyctl deploy
```

The deployment will:
- Build Docker image using Dockerfile.fly
- Push to Fly.io registry
- Deploy to ams (Amsterdam) region
- Allocate 1 vCPU with 1GB RAM
- Configure HTTPS (force_https = true)

### 4. Monitor Deployment
```powershell
# Watch logs in real-time
flyctl logs -f --app signaledge-ai

# Or check status
flyctl status --app signaledge-ai
```

### 5. Verify Deployment
```powershell
# Get app URL
flyctl info --app signaledge-ai

# Test health endpoint (replace URL with actual)
curl https://signaledge-ai.fly.dev/health
```

## Database Setup (First Time Only)

If this is the first deployment, you need to create PostgreSQL:

```powershell
# Create PostgreSQL database
flyctl postgres create --name signaledge-db --region ams --vm-size shared-cpu-1x

# Attach to app (sets DATABASE_URL automatically)
flyctl postgres attach signaledge-db --app signaledge-ai

# Run migrations
flyctl ssh console --app signaledge-ai
# Inside console:
cd backend
alembic upgrade head
exit
```

## Set Required Secrets

```powershell
# Generate a secure SECRET_KEY
$SECRET_KEY = (openssl rand -hex 32 2>$null) -or "$(python -c 'import secrets; print(secrets.token_hex(32))')"

# Set secrets in Fly.io
flyctl secrets set `
  SECRET_KEY=$SECRET_KEY `
  ENVIRONMENT=production `
  LOG_LEVEL=INFO `
  --app signaledge-ai
```

## Environment Variables

**Automatically Set by Fly.io**:
- DATABASE_URL (from PostgreSQL attachment)
- API_HOST (0.0.0.0)
- API_PORT (8080)

**Set via secrets** (above):
- SECRET_KEY
- ENVIRONMENT
- LOG_LEVEL

## Configuration Files

### Updated Files:
1. **fly.toml**: 
   - Added `dockerfile = 'Dockerfile.fly'` to [build]
   - Added [env] section with API_HOST, API_PORT, PYTHONUNBUFFERED
   
2. **Dockerfile.fly**:
   - Switched to 2-stage build for smaller image size
   - Fixed COPY paths for correct directory structure
   - Uses uvicorn directly with proper HOST/PORT binding
   - Health check configured for Fly.io

## Troubleshooting

### "App not found" error
- Ensure app name is `signaledge-ai` in fly.toml
- Or create new app: `flyctl launch --name signaledge-ai`

### Port binding errors
- Check Dockerfile.fly CMD - should bind to 0.0.0.0:8080
- Verify API_HOST and API_PORT env vars in fly.toml [env]

### Build failures
- Check logs: `flyctl logs --app signaledge-ai`
- May need to update requirements.txt for production packages

### Database connection issues
- Verify DATABASE_URL set: `flyctl secrets list --app signaledge-ai`
- Check postgres attachment: `flyctl postgres list`

## Custom Domain (Optional)

After deployment working:
```powershell
flyctl certs create your-domain.com --app signaledge-ai
```

Then add DNS records as instructed by flyctl.

## Rollback

If deployment fails:
```powershell
# List recent deployments
flyctl deployments list --app signaledge-ai

# Rollback to previous version
flyctl deploy --image fly.io/signaledge-ai:deployment_version_id
```

## Next Steps

1. Run `flyctl deploy`
2. Monitor with `flyctl logs -f`
3. Test health endpoint
4. If first deployment, set up PostgreSQL as shown above
5. Run database migrations if needed

**Status**: Ready to deploy! 🚀
