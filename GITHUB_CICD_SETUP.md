# CI/CD Docker Registry Setup Guide

## Overview

Your project now has automated Docker image building and pushing to GitHub Container Registry (GHCR).

## Prerequisites

- GitHub account with repository access
- Docker Hub, AWS ECR, or GitHub Container Registry account
- SSH access to your production server (for deployment)

## 1. GitHub Secrets Configuration

Add these secrets to your GitHub repository settings (`Settings > Secrets and variables > Actions`):

### For Docker Registry (Automatic via GITHUB_TOKEN)
✅ **Already provided by GitHub** - GITHUB_TOKEN is automatically available

### For Production Deployment (SSH)
Add these secrets:

```
DEPLOY_HOST         → Your production server IP (e.g., 1.2.3.4)
DEPLOY_USER         → SSH username (e.g., ubuntu)
DEPLOY_SSH_KEY      → Private SSH key for the server
DEPLOY_PORT         → SSH port (default: 22)
DEPLOY_PATH         → Server deployment path (e.g., /home/ubuntu/sports-prediction-platform)
```

### For Frontend Build (Optional)
```
VITE_STRIPE_PUBLISHABLE_KEY  → Your Stripe publishable key
```

## 2. Generate SSH Key for Deployment

If you don't have an SSH key:

```bash
# On your local machine
ssh-keygen -t ed25519 -C "deployment@example.com" -f deploy_key -N ""

# Copy public key to server
cat deploy_key.pub | ssh user@your-server "cat >> ~/.ssh/authorized_keys"

# Get the private key content (for GitHub secret)
cat deploy_key
```

Add the **private key content** to `DEPLOY_SSH_KEY` secret in GitHub.

## 3. Prepare Production Server

```bash
# SSH into your server
ssh user@your-server

# Create deployment directory
mkdir -p /home/ubuntu/sports-prediction-platform
cd /home/ubuntu/sports-prediction-platform

# Create docker-compose override file
cat > docker-compose.override.yml <<EOF
version: '3.8'
services:
  backend:
    image: ${BACKEND_IMAGE}
  frontend:
    image: ${FRONTEND_IMAGE}
EOF

# Log in to GitHub Container Registry
docker login ghcr.io -u USERNAME -p YOUR_GITHUB_TOKEN

# Create .env file with production settings
cat > .env <<EOF
# Database
DB_USER=postgres
DB_PASSWORD=your_secure_password
DB_NAME=sports_predictions

# API Keys
ODDS_API_KEY=your_odds_api_key
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLIC_KEY=pk_live_...
SECRET_KEY=your_256_bit_secret_key

# URLs
API_URL=https://your-domain.com/api
FRONTEND_URL=https://your-domain.com
EOF
```

## 4. Workflow Triggers

### Build & Push Workflow
Triggers on:
- Push to `main` branch → tags image as `:main`
- Push to `production` branch → tags image as `:production`
- Git version tags (v1.0.0) → tags image as `:v1.0.0` and `:1.0`
- Manual workflow dispatch

**Images are pushed to:**
```
ghcr.io/YOUR_GITHUB_USERNAME/sports-prediction-platform-backend:TAG
ghcr.io/YOUR_GITHUB_USERNAME/sports-prediction-platform-frontend:TAG
```

### Deploy Workflow
Triggers on:
- Push to `production` branch → auto-deploys
- Git version tags
- Manual workflow dispatch with environment selection

## 5. Deployment Flow

```
1. Push code to production branch
    ↓
2. Tests run (tests.yml)
    ↓
3. If tests pass → Build & Push images (build-and-push.yml)
    ↓
4. SSH into production server → Pull images & restart containers
    ↓
5. Health checks verify deployment
```

## 6. View Image Registry

**GitHub Container Registry:**
- Go to your repo → Packages section
- Or visit: `ghcr.io/username/sports-prediction-platform-backend`

**Pull images manually:**
```bash
docker pull ghcr.io/your-username/sports-prediction-platform-backend:main
docker pull ghcr.io/your-username/sports-prediction-platform-frontend:main
```

## 7. Monitor Deployments

**View workflow runs:**
- GitHub repo → Actions tab
- Click on workflow to see logs and deployment status

**Common issues:**

| Issue | Solution |
|-------|----------|
| "Package push access denied" | Ensure GITHUB_TOKEN has `write:packages` permission (automatic for Actions) |
| "SSH authentication failed" | Verify DEPLOY_SSH_KEY format (should be private key content) |
| "Docker pull failed" | Check if server is logged into ghcr.io with valid token |
| "Health check failed" | Check backend logs: `docker logs signaledge-api` |

## 8. Rollback to Previous Version

```bash
# SSH to server
ssh user@your-server
cd /home/ubuntu/sports-prediction-platform

# View available image tags
docker image ls | grep ghcr.io

# Rollback to previous tag
export BACKEND_IMAGE=ghcr.io/username/sports-prediction-platform-backend:main
export FRONTEND_IMAGE=ghcr.io/username/sports-prediction-platform-frontend:main

docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

## 9. Manual Deployment (Without CI/CD)

If you prefer manual control:

```bash
# On server
cd /home/ubuntu/sports-prediction-platform

# Login to registry
cat > ~/.docker/config.json <<EOF
{
  "auths": {
    "ghcr.io": {
      "auth": "$(echo -n USERNAME:GITHUB_TOKEN | base64)"
    }
  }
}
EOF

# Pull and deploy
export BACKEND_IMAGE=ghcr.io/username/sports-prediction-platform-backend:main
export FRONTEND_IMAGE=ghcr.io/username/sports-prediction-platform-frontend:main

docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

## Next Steps

1. **Add GitHub Secrets** (in Settings > Secrets and variables > Actions)
2. **Prepare SSH key** for production server
3. **Update docker-compose files** to support environment variables
4. **Test deployment workflow** with manual trigger first
5. **Monitor health checks** after first deployment

## Support

**For debugging:**
```bash
# Check workflow logs
gh workflow view build-and-push --log

# Or via GitHub UI: Actions > workflow > job logs

# SSH to server and check containers
ssh user@your-server
docker compose logs -f backend
```
