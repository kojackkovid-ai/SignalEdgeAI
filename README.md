# SignalEdge AI

An industry-leading sports prediction platform powered by sophisticated ML ensemble models with Cyber-Tactical HUD interface.

## Features

- **Multi-Sport Coverage**: Soccer, NHL, Basketball, NFL
- **Prediction Types**: Player Props, Over/Under, Team Props
- **ML Ensemble Models**: Multiple sophisticated models for accuracy
- **Real-time Reasoning**: Shows prediction logic and confidence scores
- **Auto-Training Pipeline**: Continuous model improvement
- **Tier-based Monetization**: Free, Basic, Pro tiers
- **Cyber-Tactical UI**: Military HUD-inspired dark-mode interface

## Architecture

```
sports-prediction-platform/
├── frontend/          # React + Cyber-Tactical HUD
├── backend/           # FastAPI + Authentication
├── ml-models/         # Ensemble ML models
└── database/          # PostgreSQL schemas
```

## Quick Start

```bash
# Install dependencies
npm install

# Start development environment
npm run dev
```

## Technology Stack

- **Frontend**: React, TypeScript, TailwindCSS
- **Backend**: FastAPI, Python 3.11
- **ML**: scikit-learn, XGBoost, LightGBM, TensorFlow
- **Database**: PostgreSQL
- **Auth**: JWT + OAuth2
- **Deployment**: Docker, Kubernetes ready

## Project Structure

### Frontend
- React SPA with Cyber-Tactical HUD design
- Real-time predictions dashboard
- User authentication & tier management
- Responsive design with accessibility

### Backend
- RESTful API with FastAPI
- PostgreSQL database integration
- JWT authentication
- Tier-based access control
- Model serving infrastructure

### ML Models
- Ensemble prediction models
- Auto-training pipeline
- Backtesting framework
- Feature engineering pipeline

## Getting Started

1. Clone the repository
2. Install dependencies: `npm install`
3. Configure environment variables
4. Run migrations: `npm run migrate`
5. Start development: `npm run dev`

## License

Proprietary
