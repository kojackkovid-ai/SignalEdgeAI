# Production Deployment Guide

## Overview

This guide covers deploying the Sports Prediction Platform to production with proper security, monitoring, and high availability.

## Prerequisites

- Docker 24.0+
- Docker Compose 2.20+
- 8GB+ RAM available
- 50GB+ disk space
- SSL certificates (for HTTPS)

## Quick Start

```bash
# 1. Clone and navigate to project
cd sports-prediction-platform

# 2. Create environment file
cp backend/.env.example .env
# Edit .env with production values

# 3. Start production stack
docker-compose -f docker-compose.prod.yml up -d

# 4. Verify deployment
curl http://localhost/health
```

## Environment Configuration

Create a `.env` file with production values:

```bash
# Database
DB_USER=postgres
DB_PASSWORD=your_secure_password_here
DB_NAME=sports_predictions

# Security
SECRET_KEY=your_256_bit_secret_key_here
ODDS_API_KEY=your_odds_api_key
STRIPE_SECRET_KEY=sk_live_your_stripe_key
STRIPE_PUBLIC_KEY=pk_live_your_stripe_key

# Monitoring
GRAFANA_PASSWORD=your_grafana_admin_password

# API URL
API_URL=https://your-domain.com/api
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Nginx Load Balancer                   │
│              (SSL Termination, Rate Limiting)            │
└─────────────────────────────────────────────────────────┘
                           │
           ┌───────────────┴───────────────┐
           ▼                               ▼
┌─────────────────────┐         ┌─────────────────────┐
│   Frontend (x2)     │         │   Backend API (x2)  │
│   React + Nginx     │         │   FastAPI + Gunicorn│
│   Port: 3000        │         │   Port: 8000        │
└─────────────────────┘         └─────────────────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    ▼                    ▼                    ▼
            ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
            │  PostgreSQL  │   │    Redis     │   │  ML Worker   │
            │   (Primary)  │   │    Cache     │   │  (Training)  │
            └──────────────┘   └──────────────┘   └──────────────┘
```

## Security Checklist

- [ ] Change all default passwords
- [ ] Generate strong SECRET_KEY (256+ bits)
- [ ] Configure SSL certificates
- [ ] Set up firewall rules (ports 80, 443 only)
- [ ] Enable automatic security updates
- [ ] Configure log aggregation
- [ ] Set up backup encryption

## Monitoring

### Health Endpoints

- `GET /health` - Comprehensive health check
- `GET /ready` - Kubernetes readiness probe
- `GET /live` - Kubernetes liveness probe

### Metrics

- `GET /api/system/metrics` - System metrics (CPU, memory, disk)
- `GET /api/system/circuit-breakers` - Circuit breaker status

### Dashboards

Access monitoring dashboards:
- Grafana: http://localhost:3001 (admin/admin)
- Prometheus: http://localhost:9090

## Backup Strategy

### Automated Backups

Database backups run automatically every 24 hours:
- Location: `./database/backups/`
- Retention: 7 days
- Format: Compressed SQL dumps

### Manual Backup

```bash
# Create manual backup
docker-compose -f docker-compose.prod.yml exec postgres \
  pg_dump -U postgres sports_predictions | gzip > backup_manual.sql.gz

# Restore from backup
gunzip < backup_manual.sql.gz | docker-compose -f docker-compose.prod.yml exec -T postgres \
  psql -U postgres sports_predictions
```

## Scaling

### Horizontal Scaling

```bash
# Scale backend API to 4 instances
docker-compose -f docker-compose.prod.yml up -d --scale backend=4

# Scale frontend to 3 instances
docker-compose -f docker-compose.prod.yml up -d --scale frontend=3
```

### Vertical Scaling

Edit `docker-compose.prod.yml` resource limits:

```yaml
deploy:
  resources:
    limits:
      cpus: '4'      # Increase CPU
      memory: 8G     # Increase memory
```

## Troubleshooting

### Check Service Status

```bash
# View all services
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f backend

# View specific service logs
docker-compose -f docker-compose.prod.yml logs -f --tail=100 ml-worker
```

### Common Issues

**Database Connection Failed**
```bash
# Check database health
docker-compose -f docker-compose.prod.yml exec postgres pg_isready

# Restart database
docker-compose -f docker-compose.prod.yml restart postgres
```

**Redis Connection Failed**
```bash
# Check Redis
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping

# Restart Redis
docker-compose -f docker-compose.prod.yml restart redis
```

**ML Models Not Loading**
```bash
# Check model files exist
docker-compose -f docker-compose.prod.yml exec backend ls -la ml-models/trained/

# Retrain models manually
docker-compose -f docker-compose.prod.yml exec backend python -c "
from app.services.enhanced_ml_service import EnhancedMLService
import asyncio
service = EnhancedMLService()
# Add training code here
"
```

## SSL Configuration

Place SSL certificates in `nginx/ssl/`:
- `certificate.crt` - Server certificate
- `private.key` - Private key

Update `nginx/nginx.conf` to enable HTTPS.

## Maintenance

### Updates

```bash
# Pull latest images
docker-compose -f docker-compose.prod.yml pull

# Restart with new images
docker-compose -f docker-compose.prod.yml up -d

# Clean up old images
docker image prune -f
```

### Database Migrations

```bash
# Run migrations
docker-compose -f docker-compose.prod.yml exec backend \
  alembic upgrade head

# Check migration status
docker-compose -f docker-compose.prod.yml exec backend \
  alembic current
```

## Support

For issues and questions:
- Check logs: `docker-compose -f docker-compose.prod.yml logs`
- Health check: `curl http://localhost/health`
- Review documentation in `ARCHITECTURE.md`
