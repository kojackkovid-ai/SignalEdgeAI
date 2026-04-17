# Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Client Layer                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │         React SPA (Cyber-Tactical HUD)           │   │
│  │  • Dashboard • Predictions • Pricing • Profile   │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                   API Gateway Layer                      │
│  ┌──────────────────────────────────────────────────┐   │
│  │           FastAPI with CORS & Auth               │   │
│  │  • REST API • JWT Auth • Rate Limiting           │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
         ↓                          ↓                    ↓
    ┌─────────┐          ┌──────────────┐        ┌──────────────┐
    │  ML     │          │  Database    │        │  Cache       │
    │ Service │          │  PostgreSQL  │        │  Redis       │
    │ (Async) │          │  (Async)     │        │              │
    └─────────┘          └──────────────┘        └──────────────┘
         ↓
┌─────────────────────────────────────────────────────────┐
│               ML Model Ensemble Layer                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │ XGBoost  │ │LightGBM  │ │  Neural  │ │ Linear   │   │
│  │ (35%)    │ │ (30%)    │ │  Net(25%)│ │ Reg(10%) │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
│         └─────────────── Weighted Ensemble ────────────┘ │
│  ┌──────────────────────────────────────────────────┐   │
│  │         Auto-Training Pipeline                   │   │
│  │  • Feature Engineering • Model Retraining        │   │
│  │  • Performance Tracking • Backtesting            │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Data Flow

### Prediction Pipeline

```
User Request
    ↓
API Endpoint (/api/predictions)
    ↓
Authentication & Authorization
    ↓
Prediction Service
    ↓
ML Service (Request)
    ↓
Ensemble Models (Parallel)
    ├── XGBoost Prediction (35%)
    ├── LightGBM Prediction (30%)
    ├── Neural Network Prediction (25%)
    └── Linear Regression Prediction (10%)
    ↓
Weighted Average Ensemble
    ↓
Confidence Score Calculation
    ↓
Reasoning Generation
    ↓
Response Formatting
    ↓
Cache Storage
    ↓
API Response to Client
    ↓
UI Rendering (Cyber-Tactical HUD)
```

### Training Pipeline

```
Sports Data Collection
    ↓
Data Validation & Cleaning
    ↓
Feature Engineering
    ↓
Train/Test Split
    ↓
Model Training (Async)
    ├── Train XGBoost
    ├── Train LightGBM
    ├── Train Neural Network
    └── Train Linear Regression
    ↓
Model Evaluation
    ├── Accuracy
    ├── Precision/Recall
    ├── F1-Score
    └── AUC-ROC
    ↓
Weight Optimization
    ↓
Model Persistence
    ↓
Performance Logging
    ↓
Alert if Performance Degraded
```

## Technology Stack

### Frontend
- **Framework**: React 18+ with TypeScript
- **Build Tool**: Vite
- **State Management**: Zustand
- **HTTP Client**: Axios
- **Styling**: TailwindCSS + Custom CSS
- **Charting**: Recharts, Chart.js
- **Animations**: Framer Motion

### Backend
- **Framework**: FastAPI
- **Language**: Python 3.11+
- **ORM**: SQLAlchemy (Async)
- **Auth**: JWT + OAuth2
- **Async**: AsyncIO
- **Task Queue**: Celery (optional)

### ML & Data
- **XGBoost**: Gradient boosting
- **LightGBM**: Fast tree boosting
- **TensorFlow**: Deep learning models
- **scikit-learn**: Classical ML
- **Pandas/NumPy**: Data processing
- **joblib**: Model persistence

### Database & Caching
- **Database**: PostgreSQL 16
- **Cache**: Redis
- **Migrations**: Alembic

### DevOps & Deployment
- **Containerization**: Docker
- **Orchestration**: Docker Compose
- **Web Server**: Nginx
- **CI/CD**: GitHub Actions (ready)
- **Monitoring**: Sentry (optional)

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/logout` - Logout
- `POST /api/auth/refresh` - Refresh token

### Users
- `GET /api/users/me` - Get current user
- `GET /api/users/profile/{id}` - Get user profile
- `PUT /api/users/me` - Update profile

### Predictions
- `GET /api/predictions` - Get predictions (with filters)
- `GET /api/predictions/{id}` - Get specific prediction
- `POST /api/predictions/{id}/follow` - Follow prediction
- `POST /api/predictions/{id}/unfollow` - Unfollow prediction
- `GET /api/predictions/stats/user-stats` - User statistics

### Models
- `GET /api/models/status` - Get model status
- `GET /api/models/performance/{name}` - Model performance
- `POST /api/models/retrain/{name}` - Trigger retraining
- `GET /api/models/backtest/{name}` - Backtest results

## Database Schema

### Users Table
- `id`: UUID (Primary Key)
- `email`: Email (Unique, Indexed)
- `username`: Username (Unique, Indexed)
- `password_hash`: Hashed password
- `subscription_tier`: free/basic/pro
- `subscription_start/end`: Dates
- `stats`: win_rate, roi, profit_loss, total_predictions
- `created_at`: Timestamp
- `is_active`: Boolean

### Predictions Table
- `id`: UUID (Primary Key)
- `sport`: Soccer/NHL/Basketball/NFL
- `league`: League name
- `matchup`: Match details
- `prediction`: Prediction value
- `confidence`: 0-1 confidence score
- `odds`: Optional odds
- `type`: player_prop/team_prop/over_under
- `reasoning`: JSON array of reasoning
- `model_weights`: JSON ensemble details
- `result`: win/loss/push
- `created_at`: Timestamp
- `resolved_at`: Timestamp

### ModelPerformance Table
- `id`: UUID
- `model_name`: Model identifier
- `accuracy/precision/recall/f1`: Metrics
- `period_start/end`: Period covered
- `created_at`: Timestamp

### TrainingLog Table
- `id`: UUID
- `timestamp`: Training timestamp
- `duration`: Training duration (seconds)
- `samples_used`: Number of samples
- `status`: success/failed
- `results`: JSON training results
- `new_weights`: Updated ensemble weights

## Scalability Considerations

### Horizontal Scaling
- Stateless API servers
- Database read replicas
- Redis cluster for caching
- Kubernetes-ready architecture

### Performance
- Async database operations
- Model caching
- Request pagination
- Response compression

### Monitoring
- API performance metrics
- Model accuracy tracking
- System health checks
- Error logging & alerts

## Security

- **Authentication**: JWT tokens with expiration
- **Authorization**: Tier-based access control
- **Password**: Bcrypt hashing with salt
- **Data**: Encrypted at rest and in transit
- **Rate Limiting**: Per-user API limits
- **CORS**: Configurable origins
- **HTTPS**: Required in production
