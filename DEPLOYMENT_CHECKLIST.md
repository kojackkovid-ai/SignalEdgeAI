# Pre-Production Deployment Checklist

Complete this checklist before deploying to production.

## Security & Credentials

- [ ] **SECRET_KEY**
  - Generate: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
  - Add to `.env.production`
  - ⚠️ **Do NOT commit real keys to git** - use environment variables

- [ ] **Database Password**
  - Generate strong password: `python -c "import secrets; print(secrets.token_urlsafe(16))"`
  - Use in DB_PASS environment variable
  - Store safely in deployment platform's secrets manager

- [ ] **Stripe Keys**
  - [ ] Get LIVE keys from Stripe Dashboard (not test keys)
  - [ ] Add `STRIPE_PUBLIC_KEY` (starts with `pk_live_`)
  - [ ] Add `STRIPE_SECRET_KEY` (starts with `sk_live_`) - keep secret!

- [ ] **Odds API Key**
  - [ ] Verify key is valid
  - [ ] Check API rate limits
  - [ ] Monitor usage

- [ ] **Remove Debug Mode**
  - [ ] Set `LOG_LEVEL=info` (not debug)
  - [ ] Remove all `print()` statements in production code
  - [ ] Disable source maps in frontend build (if not needed)

## Backend Configuration

- [ ] **Database**
  - [ ] Update `DB_HOST` to proper hostname
  - [ ] Update `DB_USER` and `DB_PASS`
  - [ ] Update `DB_NAME` (use `sports_predictions_prod` or similar)
  - [ ] Test connection: `python -c "import psycopg2; ..."`

- [ ] **API Settings**
  - [ ] `API_HOST=0.0.0.0` (listen on all interfaces)
  - [ ] `API_PORT=8000` (or your chosen port)
  - [ ] CORS settings configured for your domain

- [ ] **ML Models**
  - [ ] Models are uploaded/built
  - [ ] `MODEL_UPDATE_INTERVAL` set appropriately (3600 seconds = 1 hour)
  - [ ] `MODEL_RETRAIN_DAYS=7` is reasonable
  - [ ] Check available disk space for models

- [ ] **Redis/Cache**
  - [ ] `REDIS_URL` properly configured
  - [ ] Redis is running (check docker-compose)
  - [ ] No memory limits that would evict data

- [ ] **Dependencies**
  - [ ] `requirements.txt` is up to date
  - [ ] All versions are pinned (no floating `~=`)
  - [ ] Run: `pip install -r requirements.txt` in Docker build

## Frontend Configuration

- [ ] **API URL**
  - [ ] `VITE_API_URL` points to production backend
  - [ ] Example: `https://your-domain.com/api`
  - [ ] Not hardcoded localhost

- [ ] **Build**
  - [ ] `npm run build` completes successfully
  - [ ] No console warnings
  - [ ] Source maps excluded if sensitive (optional)
  - [ ] Production bundle size is reasonable

- [ ] **Stripe Integration**
  - [ ] Stripe keys are for LIVE environment
  - [ ] Test payment flow locally first
  - [ ] Webhook endpoint configured in Stripe Dashboard

## Docker & Deployment

- [ ] **Docker Images**
  - [ ] Backend Dockerfile: `FROM python:3.12-slim`
  - [ ] Frontend Dockerfile: Multi-stage build (node → nginx)
  - [ ] Build test: `docker-compose -f docker-compose.prod.yml build`

- [ ] **Environment**
  - [ ] `.env.production` exists and is complete
  - [ ] `.env.production` is in `.gitignore` (never commit secrets)
  - [ ] All required variables are set

- [ ] **Health Checks**
  - [ ] Backend has `/health` endpoint
  - [ ] Frontend returns 200 on `/`
  - [ ] Docker healthchecks configured

## SSL/HTTPS & Networking

- [ ] **HTTPS**
  - [ ] (Railway/Fly.io handles automatically)
  - [ ] (Self-hosted: Get SSL cert from Let's Encrypt)
  - [ ] All traffic redirects HTTP → HTTPS

- [ ] **CORS**
  - [ ] Set proper origins (not `*` in production)
  - [ ] Example: `CORS_ORIGINS=https://your-domain.com`

- [ ] **Firewall**
  - [ ] Database port (5432) not exposed to internet
  - [ ] Only frontend (80/443) and API (8000) are accessible
  - [ ] Use security groups/firewall rules

## Database

- [ ] **Migrations**
  - [ ] All Alembic migrations run on startup
  - [ ] Run manually if needed: `alembic upgrade head`

- [ ] **Backups**
  - [ ] [ ] Set up automated daily backups
  - [ ] [ ] Test restore procedure
  - [ ] [ ] Store backups securely

- [ ] **Performance**
  - [ ] Database indexes created: `CREATE INDEX ON table(column);`
  - [ ] Connection pooling configured (if using)
  - [ ] Query slowlog monitored

## Performance & Monitoring

- [ ] **Caching**
  - [ ] Predictions cached (10-15 minutes)
  - [ ] Models cached (1 hour)
  - [ ] Redis memory limit set appropriately

- [ ] **Logging**
  - [ ] Structured logging configured
  - [ ] Log aggregation service (Sentry, LogRocket, etc.)
  - [ ] Error tracking enabled

- [ ] **Monitoring**
  - [ ] Uptime monitoring (UptimeRobot, Statuspage)
  - [ ] Performance monitoring (Datadog, New Relic free tier)
  - [ ] Database monitoring enabled

- [ ] **Rate Limiting**
  - [ ] API rate limits configured
  - [ ] Auth endpoint rate limited
  - [ ] DDoS protection enabled (Cloudflare)

## Testing Before Deployment

- [ ] **Functionality Tests**
  - [ ] Login/authentication works
  - [ ] Predictions load correctly
  - [ ] Payment flow works (test mode)
  - [ ] All sports supported
  - [ ] Database queries work

- [ ] **Load Testing**
  - [ ] Load test with ~10 concurrent users
  - [ ] Command: `ab -n 100 -c 10 https://your-domain.com`
  - [ ] Response times remain acceptable

- [ ] **Security Testing**
  - [ ] SQL injection prevention verified
  - [ ] CSRF tokens present
  - [ ] XSS protection enabled
  - [ ] No sensitive data in logs

## Deployment Platform Specific

### Railway.app
- [ ] GitHub repo is public (or grant access)
- [ ] Environment variables added in dashboard
- [ ] Services (Postgres, Redis) added
- [ ] Deployment triggered and succeeded
- [ ] Preview environment tested

### Self-Hosted
- [ ] Server has minimum specs: 2GB RAM, 20GB disk
- [ ] Docker & Docker Compose installed
- [ ] Firewall rules configured
- [ ] SSL certificates obtained
- [ ] Nginx or reverse proxy configured
- [ ] Logs accessible: `docker-compose logs -f`

## Post-Deployment

- [ ] **Verify Live Site**
  - [ ] Frontend loads: https://your-domain.com
  - [ ] API responds: https://your-domain.com/api/health
  - [ ] Login works
  - [ ] At least one prediction loads

- [ ] **Monitor Initial Hours**
  - [ ] Check error logs
  - [ ] Verify database is receiving data
  - [ ] Monitor resource usage

- [ ] **Share with Testers**
  - [ ] Provide frontend URL
  - [ ] Provide API documentation
  - [ ] List known limitations
  - [ ] Collect feedback

- [ ] **Set Up Alerts**
  - [ ] Email alerts for errors
  - [ ] Uptime monitoring alerts
  - [ ] Database size alerts
  - [ ] Disk space alerts

## Emergency Recovery

- [ ] **Rollback Plan**
  - [ ] Keep previous version tagged in git
  - [ ] Database migration rollback procedure documented
  - [ ] Backup restore procedure tested

- [ ] **Incident Response**
  - [ ] Status page created
  - [ ] Contact info for critical issues
  - [ ] Escalation procedure documented

---

## Sign Off

- [ ] All items checked
- [ ] No critical issues remaining
- [ ] Ready for production

**Deployment Date**: ________________
**Deployed By**: ________________
**Approval**: ________________
