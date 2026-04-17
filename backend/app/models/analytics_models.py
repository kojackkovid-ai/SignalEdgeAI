"""
Analytics Models - Track user events and metrics
"""

from sqlalchemy import Column, String, DateTime, Float, Integer, JSON, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
from uuid import uuid4


class AnalyticsEvent(Base):
    """Track user actions and events on the platform"""
    __tablename__ = "analytics_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, nullable=True)  # Null for anonymous users
    event_type = Column(String, nullable=False, index=True)  # e.g., "signup", "prediction_view", "tier_upgrade"
    event_data = Column(JSON, nullable=True)  # Additional event data
    
    # Metadata
    created_at = Column(DateTime, nullable=False, index=True, default=datetime.utcnow)
    session_id = Column(String, nullable=True, index=True)  # Group events by session
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    
    # Performance tracking
    request_duration_ms = Column(Float, nullable=True)  # How long did the request take?
    
    __table_args__ = (
        Index('idx_user_event_date', 'user_id', 'event_type', 'created_at'),
        Index('idx_event_type_date', 'event_type', 'created_at'),
    )


class ConversionFunnel(Base):
    """Track user conversion from free to paid"""
    __tablename__ = "conversion_funnels"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, nullable=False, unique=True, index=True)
    
    # Funnel stages
    signup_date = Column(DateTime, nullable=True)
    first_login_date = Column(DateTime, nullable=True)
    first_prediction_view_date = Column(DateTime, nullable=True)
    first_app_unlock_date = Column(DateTime, nullable=True)
    first_tier_upgrade_date = Column(DateTime, nullable=True)
    first_payment_date = Column(DateTime, nullable=True)
    
    # Current status
    current_tier = Column(String, nullable=True)  # free, basic, pro, elite
    current_subscription_value = Column(Float, nullable=True)  # $ per month
    
    # Engagement metrics
    total_predictions_viewed = Column(Integer, default=0)
    total_unlocks = Column(Integer, default=0)
    
    # Churn tracking
    last_active_date = Column(DateTime, nullable=True)
    churn_date = Column(DateTime, nullable=True)  # When did user stop using?
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserEngagementMetrics(Base):
    """Daily engagement metrics per user"""
    __tablename__ = "user_engagement_metrics"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, nullable=False, index=True)
    date = Column(String, nullable=False)  # YYYY-MM-DD format
    
    # Session metrics
    sessions = Column(Integer, default=0)  # How many times did user login?
    session_duration_seconds = Column(Integer, default=0)  # Total time on platform
    
    # Engagement metrics
    predictions_viewed = Column(Integer, default=0)
    predictions_unlocked = Column(Integer, default=0)
    props_viewed = Column(Integer, default=0)
    
    # Monetization metrics
    purchases = Column(Integer, default=0)
    revenue = Column(Float, default=0.0)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_user_date', 'user_id', 'date'),
    )


class CohortAnalysis(Base):
    """Track user cohorts for retention analysis"""
    __tablename__ = "cohort_analysis"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    cohort_date = Column(String, nullable=False)  # When did user sign up? Format: YYYY-MM
    user_count = Column(Integer, nullable=False)
    
    # Retention metrics (updated daily)
    # day_0 = signup day, day_1 = after 1 day, etc.
    day_0_users = Column(Integer, default=0)  # Users on signup day
    day_1_users = Column(Integer, default=0)  # Returned within 1 day
    day_7_users = Column(Integer, default=0)  # Returned within 7 days
    day_30_users = Column(Integer, default=0)  # Returned within 30 days
    day_90_users = Column(Integer, default=0)  # Returned within 90 days
    
    # Conversion metrics
    day_1_converted = Column(Integer, default=0)
    day_7_converted = Column(Integer, default=0)
    day_30_converted = Column(Integer, default=0)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_cohort_date', 'cohort_date'),
    )
