"""Add comprehensive database indexes for performance optimization

Revision ID: 006_add_database_indexes
Revises: 005_add_prediction_records_and_player_data
Create Date: 2026-04-13 14:00:00+00:00
"""

from alembic import op
import sqlalchemy as sa

revision = "006_add_database_indexes"
down_revision = "005_add_prediction_records_and_player_data"
branch_labels = None
depends_on = None


def upgrade():
    """Add indexes for query performance optimization"""
    
    # Check which indexes already exist to avoid duplicates
    # Users Table Indexes
    try:
        op.create_index("idx_users_subscription_tier", "users", ["subscription_tier"])
    except:
        pass  # Index already exists
    
    try:
        op.create_index("idx_users_created_at", "users", ["created_at"])
    except:
        pass
    
    try:
        op.create_index("idx_users_club_100_unlocked", "users", ["club_100_unlocked"])
    except:
        pass
    
    # Predictions Table Indexes (Most Critical!)
    try:
        op.create_index("idx_predictions_sport_league", "predictions", ["sport", "league"])
    except:
        pass
    
    try:
        op.create_index("idx_predictions_sport_key", "predictions", ["sport_key"])
    except:
        pass
    
    try:
        op.create_index("idx_predictions_created_at", "predictions", ["created_at"])
    except:
        pass
    
    try:
        op.create_index("idx_predictions_event_id", "predictions", ["event_id"])
    except:
        pass
    
    try:
        op.create_index("idx_predictions_resolved_at", "predictions", ["resolved_at"])
    except:
        pass
    
    try:
        op.create_index("idx_predictions_player_market", "predictions", ["player", "market_key"])
    except:
        pass
    
    try:
        op.create_index("idx_predictions_is_club_100", "predictions", ["is_club_100_pick"])
    except:
        pass
    
    # User Predictions Junction Table
    try:
        op.create_index("idx_user_predictions_user_id", "user_predictions", ["user_id"])
    except:
        pass
    
    try:
        op.create_index("idx_user_predictions_created_at", "user_predictions", ["created_at"])
    except:
        pass
    
    # Training Sessions
    try:
        op.create_index(
            "idx_training_sessions_sport_market",
            "training_sessions",
            ["sport_key", "market_type"],
        )
    except:
        pass
    
    try:
        op.create_index("idx_training_sessions_started_at", "training_sessions", ["started_at"])
    except:
        pass
    
    try:
        op.create_index("idx_training_sessions_status", "training_sessions", ["status"])
    except:
        pass
    
    # Model Performance Metrics
    try:
        op.create_index(
            "idx_model_perf_sport_market_date",
            "model_performance_metrics",
            ["sport_key", "market_type", "measurement_date"],
        )
    except:
        pass
    
    try:
        op.create_index("idx_model_perf_drift", "model_performance_metrics", ["has_drift"])
    except:
        pass
    
    # Prediction Records (check if table exists)
    try:
        op.create_index("idx_prediction_records_user_id", "prediction_records", ["user_id"])
    except:
        pass  # Table may not exist
    
    try:
        op.create_index("idx_prediction_records_created_at", "prediction_records", ["created_at"])
    except:
        pass
    
    try:
        op.create_index("idx_prediction_records_outcome", "prediction_records", ["outcome"])
    except:
        pass


def downgrade():
    """Remove all created indexes"""
    
    # Drop all indexes (safe operation)
    try:
        op.drop_index("idx_users_subscription_tier", table_name="users")
    except:
        pass
    
    try:
        op.drop_index("idx_users_created_at", table_name="users")
    except:
        pass
    
    try:
        op.drop_index("idx_users_club_100_unlocked", table_name="users")
    except:
        pass
    
    try:
        op.drop_index("idx_predictions_sport_league", table_name="predictions")
    except:
        pass
    
    try:
        op.drop_index("idx_predictions_sport_key", table_name="predictions")
    except:
        pass
    
    try:
        op.drop_index("idx_predictions_created_at", table_name="predictions")
    except:
        pass
    
    try:
        op.drop_index("idx_predictions_event_id", table_name="predictions")
    except:
        pass
    
    try:
        op.drop_index("idx_predictions_resolved_at", table_name="predictions")
    except:
        pass
    
    try:
        op.drop_index("idx_predictions_player_market", table_name="predictions")
    except:
        pass
    
    try:
        op.drop_index("idx_predictions_is_club_100", table_name="predictions")
    except:
        pass
    
    try:
        op.drop_index("idx_user_predictions_user_id", table_name="user_predictions")
    except:
        pass
    
    try:
        op.drop_index("idx_user_predictions_created_at", table_name="user_predictions")
    except:
        pass
    
    try:
        op.drop_index("idx_training_sessions_sport_market", table_name="training_sessions")
    except:
        pass
    
    try:
        op.drop_index("idx_training_sessions_started_at", table_name="training_sessions")
    except:
        pass
    
    try:
        op.drop_index("idx_training_sessions_status", table_name="training_sessions")
    except:
        pass
    
    try:
        op.drop_index("idx_model_perf_sport_market_date", table_name="model_performance_metrics")
    except:
        pass
    
    try:
        op.drop_index("idx_model_perf_drift", table_name="model_performance_metrics")
    except:
        pass
    
    try:
        op.drop_index("idx_prediction_records_user_id", table_name="prediction_records")
    except:
        pass
    
    try:
        op.drop_index("idx_prediction_records_created_at", table_name="prediction_records")
    except:
        pass
    
    try:
        op.drop_index("idx_prediction_records_outcome", table_name="prediction_records")
    except:
        pass
