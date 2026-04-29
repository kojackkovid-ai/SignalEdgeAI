                                                                            
"""
Database Models
SQLAlchemy ORM models for the platform
"""

from sqlalchemy import Column, String, Float, Integer, DateTime, Boolean, JSON, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import uuid

# Import AuditLog from audit service
from app.services.audit_service import AuditLog

# Association table for user-prediction relationships
user_predictions = Table(
    'user_predictions',
    Base.metadata,
    Column('user_id', String, ForeignKey('users.id'), primary_key=True),
    Column('prediction_id', String, ForeignKey('predictions.id'), primary_key=True),
    Column('created_at', DateTime, default=datetime.utcnow)
)

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    
    # Password Reset
    password_reset_token = Column(String, unique=True, index=True, nullable=True)
    password_reset_token_expires = Column(DateTime, nullable=True)
    
    # Subscription
    subscription_tier = Column(String, default="free")  # free, basic, pro
    subscription_start = Column(DateTime, default=datetime.utcnow)
    subscription_end = Column(DateTime, nullable=True)
    
    # Stats
    win_rate = Column(Float, default=0.0)
    total_predictions = Column(Integer, default=0)
    roi = Column(Float, default=0.0)
    profit_loss = Column(Float, default=0.0)
    
    # Club 100 Feature
    club_100_unlocked = Column(Boolean, default=False)
    club_100_unlocked_at = Column(DateTime, nullable=True)
    club_100_picks_available = Column(Integer, default=0)  # Total picks earned towards Club 100
    club_100_unlocked_picks = Column(JSON, default=list)  # List of player_ids the user has unlocked (costs 1 pick each)
    
    # Preferences
    preferences = Column(JSON, default={})
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    predictions = relationship(
        "Prediction",
        secondary=user_predictions,
        back_populates="followers"
    )

class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Match info
    sport = Column(String, index=True)  # soccer, nhl, basketball, nfl
    league = Column(String, index=True)
    matchup = Column(String)
    
    # Prediction
    prediction = Column(String)
    confidence = Column(Float)
    odds = Column(String, nullable=True)
    prediction_type = Column(String)  # player_prop, team_prop, over_under
    
    # Player props specific fields
    player = Column(String, nullable=True)  # Player name for player props
    market_key = Column(String, nullable=True)  # e.g., points, rebounds, home_runs
    point = Column(Float, nullable=True)  # The line/over-under value
    
    # Game/Event info
    event_id = Column(String, nullable=True)  # ESPN event ID
    sport_key = Column(String, nullable=True)  # Full sport key like basketball_nba
    game_time = Column(String, nullable=True)  # Formatted game time
    
    # Reasoning
    reasoning = Column(JSON)  # List of reasoning points
    model_weights = Column(JSON)  # Individual model predictions and weights
    
    # Results
    resolved_at = Column(DateTime, nullable=True)
    result = Column(String, nullable=True)  # win, loss, push
    actual_value = Column(Float, nullable=True)
    
    # Club 100 Tracking
    is_club_100_pick = Column(Boolean, default=False, index=True)  # True if this is a Club 100 prediction
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    followers = relationship(
        "User",
        secondary=user_predictions,
        back_populates="predictions"
    )

class ModelPerformance(Base):
    __tablename__ = "model_performance"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Model info
    model_name = Column(String, index=True)
    
    # Metrics
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)
    auc_roc = Column(Float)
    
    # Period
    period_start = Column(DateTime)
    period_end = Column(DateTime)
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    
class TrainingLog(Base):
    __tablename__ = "training_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Training info
    timestamp = Column(DateTime, default=datetime.utcnow)
    duration = Column(Float)  # seconds
    samples_used = Column(Integer)
    reason = Column(String)  # Reason for retraining
    
    # Results
    status = Column(String)  # success, failed
    results = Column(JSON)  # Training results
    new_weights = Column(JSON)  # Updated ensemble weights
    error = Column(String, nullable=True)


class TrainingSession(Base):
    """Track detailed ML model training sessions"""
    __tablename__ = "training_sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Session info
    sport_key = Column(String, index=True)  # e.g., basketball_nba
    market_type = Column(String, index=True)  # e.g., moneyline, spread, total
    
    # Timing
    started_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    # Data
    training_samples = Column(Integer)  # Number of samples used
    validation_samples = Column(Integer)  # Number of validation samples
    date_range_start = Column(DateTime)  # Start of historical data used
    date_range_end = Column(DateTime)  # End of historical data used
    
    # Status & Results
    status = Column(String, default="pending")  # pending, in_progress, completed, failed
    
    # Model metrics
    train_accuracy = Column(Float, nullable=True)
    validation_accuracy = Column(Float, nullable=True)
    train_loss = Column(Float, nullable=True)
    validation_loss = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    
    # Model info
    model_versions = Column(JSON, nullable=True)  # {"xgboost": "v1.0", "lightgbm": "v1.0", ...}
    hyperparameters = Column(JSON, nullable=True)  # Training hyperparameters used
    
    # Trigger
    trigger_reason = Column(String)  # "scheduled", "performance_drift", "manual"
    
    # Error handling
    error_message = Column(String, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ModelPerformanceMetrics(Base):
    """Track model performance metrics over time for drift detection"""
    __tablename__ = "model_performance_metrics"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Model identification
    sport_key = Column(String, index=True)
    market_type = Column(String, index=True)
    
    # Performance window (e.g., daily, weekly aggregates)
    measurement_date = Column(DateTime, index=True)
    window_start = Column(DateTime)  # Start of measurement window
    window_end = Column(DateTime)  # End of measurement window
    
    # Performance metrics
    predictions_count = Column(Integer)
    hit_count = Column(Integer)  # Correct predictions
    miss_count = Column(Integer)  # Incorrect predictions
    accuracy = Column(Float)  # hit_count / predictions_count
    
    # Additional metrics for drift detection
    confidence_mean = Column(Float)  # Average confidence of predictions
    confidence_std = Column(Float)  # Standard deviation
    profitable_units = Column(Float, nullable=True)  # Against the line
    roi = Column(Float, nullable=True)  # Return on investment
    
    # Anomalies
    has_drift = Column(Boolean, default=False)  # True if drift detected
    drift_severity = Column(String, nullable=True)  # low, medium, high
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)


class ScheduledTrainingJob(Base):
    """Track scheduled training jobs for weekly/recurring retraining"""
    __tablename__ = "scheduled_training_jobs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Job identification
    job_name = Column(String, unique=True, index=True)
    sport_key = Column(String, nullable=True)  # Optional: specific sport
    market_type = Column(String, nullable=True)  # Optional: specific market
    
    # Schedule
    schedule_type = Column(String)  # "weekly", "daily", "on_demand"
    day_of_week = Column(Integer, nullable=True)  # 0=Monday, 6=Sunday (for weekly)
    hour_utc = Column(Integer, nullable=True)  # Hour in UTC (0-23)
    minute_utc = Column(Integer, nullable=True)  # Minute (0-59)
    
    # Run history
    last_run_at = Column(DateTime, nullable=True)
    last_run_status = Column(String, nullable=True)  # success, failed
    last_run_error = Column(String, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    
    # Configuration
    is_enabled = Column(Boolean, default=True)
    days_of_history = Column(Integer, default=14)  # Days of data to use for training
    min_samples_required = Column(Integer, default=50)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Plan info
    name = Column(String, unique=True)
    tier = Column(String, unique=True)  # free, basic, pro
    price = Column(Float)
    
    # Limits
    predictions_per_day = Column(Integer)
    confidence_filter = Column(Float)  # Min confidence to show
    
    # Features
    features = Column(JSON)  # List of included features
    api_access = Column(Boolean)
    backtesting = Column(Boolean)
    support_level = Column(String)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class Club100Data(Base):
    """Store Club 100 elite athletes data for daily refresh"""
    __tablename__ = "club_100_data"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Sport
    sport = Column(String, index=True)  # nba, nfl, mlb, nhl, soccer
    
    # Player info
    player_id = Column(String, unique=True, index=True)
    name = Column(String)
    team = Column(String)
    position = Column(String)
    
    # Prop details
    prop_line = Column(String)  # e.g., "Over 24.5 Points"
    
    # Performance data
    consecutive_games = Column(Integer)  # Number of consecutive games hitting the line
    
    # Recent form (last 4 and 5 games)
    last_4_games = Column(JSON)  # {"games_analyzed": 4, "coverage_count": 4, "coverage_percent": 100.0}
    last_5_games = Column(JSON)  # {"games_analyzed": 5, "coverage_count": 5, "coverage_percent": 100.0}
    
    # Update tracking
    data_date = Column(DateTime, index=True)  # Date this data was added/updated
    source = Column(String, default="linemate.io")  # Data source
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
