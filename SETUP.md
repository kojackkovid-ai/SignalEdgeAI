# Installation & Setup Guide

## Prerequisites

- Node.js 20+
- Python 3.11+
- Docker & Docker Compose (optional)
- PostgreSQL 16+ (or use Docker)
- Redis (or use Docker)

## Quick Start with Docker

```bash
# Clone repository
git clone <repo-url>
cd sports-prediction-platform

# Build and start all services
docker-compose up -d

# Run migrations
docker-compose exec backend python -m alembic upgrade head

# Access the platform
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# PgAdmin: http://localhost:5050
```

## Local Development Setup

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp ../.env.example .env
# Edit .env with your settings

# Start database
# Make sure PostgreSQL is running

# Run migrations
python -m alembic upgrade head

# Start server
python -m uvicorn app.main:app --reload
```

Backend API will be available at `http://localhost:8000`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at `http://localhost:5173`

## Configuration

### Environment Variables

See `.env.example` for all available options:

```bash
cp .env.example .env
```

Key variables:
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT secret key (change in production!)
- `STRIPE_*`: Payment processing credentials
- `REACT_APP_API_URL`: Backend API URL for frontend

### Database Setup

```bash
# Create database
createdb sports_predictions

# Run migrations
python -m alembic upgrade head

# Seed initial data (optional)
python scripts/seed_db.py
```

## Project Structure

```
sports-prediction-platform/
├── frontend/              # React SPA
│   ├── src/
│   │   ├── components/   # Reusable UI components
│   │   ├── pages/        # Page components
│   │   ├── hooks/        # Custom React hooks
│   │   ├── utils/        # Utility functions & API
│   │   └── styles/       # CSS & theme
│   └── package.json
│
├── backend/              # FastAPI server
│   ├── app/
│   │   ├── routes/       # API endpoints
│   │   ├── models/       # Database & data models
│   │   ├── services/     # Business logic
│   │   ├── auth/         # Authentication
│   │   └── main.py       # FastAPI app
│   ├── requirements.txt
│   └── Dockerfile
│
├── ml-models/            # Machine Learning
│   ├── models/          # Model implementations
│   ├── training/        # Auto-training pipeline
│   └── data/            # Training data
│
└── database/            # Database schemas
```

## Running Tests

### Backend Tests
```bash
cd backend
pytest tests/ -v
```

### Frontend Tests
```bash
cd frontend
npm test
```

## Deployment

### Production Build

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
npm run build
```

### Docker Production

```bash
docker-compose -f docker-compose.yml up -d
```

### Environment Checklist

- [ ] Update `SECRET_KEY` to a strong random value
- [ ] Set `DATABASE_URL` to production PostgreSQL
- [ ] Configure Stripe API keys if using payments
- [ ] Set CORS origins to production domain
- [ ] Enable HTTPS
- [ ] Set up logging and monitoring
- [ ] Configure automated backups
- [ ] Set up CI/CD pipeline

## Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL is running
psql -U postgres -d sports_predictions

# Verify connection string in .env
# Format: postgresql://user:password@host:port/database
```

### ML Model Issues
```bash
# Verify all ML dependencies are installed
pip install -r ml-models/requirements.txt

# Check model files exist
ls ml-models/models/*.py
```

### API Not Responding
```bash
# Check backend is running
curl http://localhost:8000/health

# View backend logs
docker-compose logs -f backend
```

### Frontend Not Loading
```bash
# Check frontend build
npm run build

# Clear cache
rm -rf node_modules
npm install
npm run dev
```

## Next Steps

1. Configure authentication (OAuth2, JWT)
2. Set up payment processing (Stripe)
3. Create sports data pipeline
4. Train initial ML models
5. Deploy to production
6. Set up monitoring & alerts

## Support

For issues and questions:
- GitHub Issues: [Project Issues]
- Documentation: [Wiki]
- Email: support@example.com
