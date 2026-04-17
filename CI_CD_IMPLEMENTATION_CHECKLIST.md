# CI/CD Implementation Checklist

## Phase 1: GitHub Secrets Setup ✓

- [ ] Go to your GitHub repo → Settings → Secrets and variables → Actions
- [ ] Click "New repository secret" and add:

### Required Secrets

- [ ] `DEPLOY_HOST` - Your production server IP
- [ ] `DEPLOY_USER` - SSH username (e.g., ubuntu)
- [ ] `DEPLOY_SSH_KEY` - Private SSH key content
- [ ] `DEPLOY_PORT` - SSH port (default: 22)
- [ ] `DEPLOY_PATH` - Server deployment path

### Optional Secrets

- [ ] `VITE_STRIPE_PUBLISHABLE_KEY` - Stripe key for frontend build

## Phase 2: SSH Key Generation

- [ ] Generate SSH key pair:
  ```bash
  ssh-keygen -t ed25519 -C "deployment@example.com" -f deploy_key -N ""
  ```
- [ ] Copy public key to server:
  ```bash
  cat deploy_key.pub | ssh user@your-server "cat >> ~/.ssh/authorized_keys"
  ```
- [ ] Add private key content to GitHub secret `DEPLOY_SSH_KEY`
- [ ] Store deploy_key safely (backup)

## Phase 3: Prepare Production Server

- [ ] SSH into production server
- [ ] Create deployment directory:
  ```bash
  mkdir -p /home/ubuntu/sports-prediction-platform
  cd /home/ubuntu/sports-prediction-platform
  ```

- [ ] Copy docker-compose files to server:
  ```bash
  scp docker-compose.prod.yml user@server:/home/ubuntu/sports-prediction-platform/
  scp .env.example user@server:/home/ubuntu/sports-prediction-platform/.env
  ```

- [ ] Edit .env with production values:
  ```bash
  ssh user@server
  cd /home/ubuntu/sports-prediction-platform
  vim .env
  # Add: DB_PASSWORD, STRIPE_KEYS, SECRET_KEY, etc.
  ```

- [ ] Login to GitHub Container Registry:
  ```bash
  docker login ghcr.io -u YOUR_GITHUB_USERNAME -p YOUR_GITHUB_TOKEN
  ```
  
  Create a Personal Access Token:
  - GitHub → Settings → Developer settings → Personal access tokens
  - Generate new token with `read:packages` scope
  - Use token as password

## Phase 4: Test Workflow Manually

- [ ] Check GitHub Actions tab in your repo
- [ ] Click "Build and Push Docker Images"
- [ ] Click "Run workflow" → "Run workflow"
- [ ] Wait for workflow to complete
- [ ] Verify images appear in Packages section

## Phase 5: Test Deployment

- [ ] In GitHub Actions, find "Deploy to Production" workflow
- [ ] Click "Run workflow"
- [ ] Select environment: `staging` (for first test)
- [ ] Click "Run workflow"
- [ ] Monitor deployment in workflow logs
- [ ] SSH to server and verify containers:
  ```bash
  docker compose ps
  curl http://localhost/health
  ```

## Phase 6: Enable Auto-Deployment (Optional)

The workflow currently:
- ✅ Auto-triggers on push to `production` branch
- ✅ Auto-triggers on git tags (v1.0.0, etc.)
- ✅ Can be manually triggered anytime

To enable:
- Simply push to `production` branch or create a git tag
- Workflow automatically runs tests → builds → pushes → deploys

## Phase 7: Monitoring & Maintenance

- [ ] Set up alerts for GitHub Actions failures
- [ ] Monitor container health:
  ```bash
  # SSH to server
  docker compose logs -f backend
  ```
- [ ] Set up log aggregation (optional)
- [ ] Create rollback procedure (documented)

## Troubleshooting

### Build Fails
- Check GitHub Actions logs for specific error
- Common: Dockerfile issues, missing dependencies
- Fix locally, push to branch, CI/CD will retry

### Push to Registry Fails
- Verify GITHUB_TOKEN has `packages:write` permission
- Check if you're on correct branch (main/production)
- Check repository visibility (must be public or private with paid plan)

### Deployment Fails (SSH)
- Test SSH manually: `ssh -i deploy_key user@server`
- Check DEPLOY_SSH_KEY secret is correct (no line breaks)
- Verify DEPLOY_PATH exists on server
- Check server can pull from ghcr.io (run `docker login` on server)

### Containers Crash After Deployment
- Check environment variables in .env
- Verify database credentials
- Check container logs: `docker compose logs backend`
- Rollback to previous version if needed

## Next Workflow: Test → Push → Deploy

```
1. Developer: Push code to production branch
                        ↓
2. GitHub Actions: Run automated tests
                        ↓
3. If tests pass: Build Docker images
                        ↓
4. Push to ghcr.io
                        ↓
5. SSH to production server
                        ↓
6. Deploy new images
                        ↓
7. Run health checks
                        ↓
8. Success! New version live
```

## Files Changed

✅ Created `.github/workflows/build-and-push.yml` - Builds and pushes Docker images
✅ Created `.github/workflows/deploy-production.yml` - Deploys to production
✅ Created `GITHUB_CICD_SETUP.md` - Complete setup guide
✅ Created `CI_CD_ENV_VARS.md` - Environment variables reference
✅ Updated `docker-compose.prod.yml` - Supports environment variables

## Support Resources

- GitHub Actions Docs: https://docs.github.com/en/actions
- Docker Build Action: https://github.com/docker/build-push-action
- GitHub Container Registry: https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry
