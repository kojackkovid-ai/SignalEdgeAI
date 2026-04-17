"""
Email Models
Manages email templates and user email preferences
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import uuid


class EmailPreferences(Base):
    """Store user email subscription preferences"""
    __tablename__ = "email_preferences"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'), unique=True, index=True)
    
    # Email subscription preferences
    prediction_results = Column(Boolean, default=True)  # When predictions resolve
    daily_digest = Column(Boolean, default=True)  # Daily summary of picks
    weekly_digest = Column(Boolean, default=True)  # Weekly performance summary
    tier_updates = Column(Boolean, default=True)  # Tier upgrades, features unlocked
    promotional = Column(Boolean, default=True)  # Promotions, special offers
    account_updates = Column(Boolean, default=True)  # Password resets, login alerts
    new_features = Column(Boolean, default=True)  # New features, platform updates
    accuracy_milestone = Column(Boolean, default=True)  # Hit rate milestones (>50%, >70%, etc)
    
    # Email management
    verified = Column(Boolean, default=False)  # Email verified
    last_digest_sent = Column(DateTime, nullable=True)  # Track when digest was last sent
    unsubscribe_token = Column(String, unique=True, index=True, nullable=True)  # One-click unsubscribe
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EmailLog(Base):
    """Track all emails sent to users"""
    __tablename__ = "email_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'), index=True)
    recipient_email = Column(String, index=True)
    
    # Email details
    subject = Column(String)
    email_type = Column(String, index=True)  # prediction_result, daily_digest, password_reset, tier_upgrade, etc
    template_name = Column(String)  # Name of template used
    
    # Tracking
    mailgun_message_id = Column(String, unique=True, nullable=True)  # Mailgun tracking ID
    status = Column(String, default='sent')  # sent, bounced, complained, opened, clicked, failed
    sent_at = Column(DateTime, default=datetime.utcnow, index=True)
    opened_at = Column(DateTime, nullable=True)
    
    # Context
    context_data = Column(JSON)  # Store the data used in email (predictions, stats, etc)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class EmailTemplate(Base):
    """Store email templates"""
    __tablename__ = "email_templates"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, index=True)  # prediction_result, daily_digest, password_reset, etc
    subject = Column(String)
    html_body = Column(String)  # HTML template with {{ placeholders }}
    text_body = Column(String, nullable=True)  # Plain text fallback
    
    # Template management
    is_active = Column(Boolean, default=True)
    version = Column(String, default="1.0")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
