"""
Alembic migration for Week 2-4 database schema updates
Creates tables for prediction records, player data, and calibration metrics
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Migration metadata
"""
Revision: 005_add_prediction_records_and_player_data
Revises: 004_previous_migration
Create Date: 2024-12-01 00:00:00.000000
"""

def upgrade():
    """Apply migration"""
    
    # 1. Create prediction_records table
    op.create_table(
        'prediction_records',
        sa.Column('id', sa.String(length=64), nullable=False, primary_key=True),
        sa.Column('user_id', sa.String(length=64), nullable=False),
        sa.Column('sport_key', sa.String(length=20), nullable=False),
        sa.Column('event_id', sa.String(length=128), nullable=False),
        sa.Column('matchup', sa.String(length=256), nullable=False),
        sa.Column('prediction', sa.String(length=128), nullable=False),
        sa.Column('prediction_type', sa.String(length=50), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('calibrated_confidence', sa.Float(), nullable=True),
        sa.Column('reasoning', sa.JSON(), nullable=True),
        sa.Column('outcome', sa.String(length=32), nullable=True),
        sa.Column('hits_under', sa.Boolean(), nullable=True),
        sa.Column('odds', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('outcome_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.Index('idx_prediction_records_user_id', 'user_id'),
        sa.Index('idx_prediction_records_sport_key', 'sport_key'),
        sa.Index('idx_prediction_records_created_at', 'created_at'),
        sa.Index('idx_prediction_records_outcome', 'outcome')
    )
    
    # 2. Create prediction_accuracy_stats table
    op.create_table(
        'prediction_accuracy_stats',
        sa.Column('id', sa.String(length=64), nullable=False, primary_key=True),
        sa.Column('user_id', sa.String(length=64), nullable=False),
        sa.Column('sport_key', sa.String(length=20), nullable=False),
        sa.Column('total_predictions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('win_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('win_rate', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('roi', sa.Float(), nullable=True),
        sa.Column('avg_confidence', sa.Float(), nullable=True),
        sa.Column('confidence_bucket_50_60', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('confidence_bucket_60_70', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('confidence_bucket_70_80', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('confidence_bucket_80_90', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('confidence_bucket_90_100', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('calibration_error', sa.Float(), nullable=True),
        sa.Column('brier_score', sa.Float(), nullable=True),
        sa.Column('last_updated', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.Index('idx_accuracy_stats_user_sport', 'user_id', 'sport_key'),
        sa.UniqueConstraint('user_id', 'sport_key', name='uq_stats_user_sport')
    )
    
    # 3. Create player_records table
    op.create_table(
        'player_records',
        sa.Column('id', sa.String(length=64), nullable=False, primary_key=True),
        sa.Column('name', sa.String(length=256), nullable=False),
        sa.Column('sport_key', sa.String(length=20), nullable=False),
        sa.Column('position', sa.String(length=50), nullable=True),
        sa.Column('team_key', sa.String(length=10), nullable=True),
        sa.Column('nba_id', sa.String(length=20), nullable=True),
        sa.Column('nfl_id', sa.String(length=20), nullable=True),
        sa.Column('mlb_id', sa.String(length=20), nullable=True),
        sa.Column('nhl_id', sa.String(length=20), nullable=True),
        sa.Column('image_url', sa.String(length=512), nullable=True),
        sa.Column('last_synced', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Index('idx_player_records_sport_team', 'sport_key', 'team_key'),
        sa.Index('idx_player_records_name', 'name'),
        sa.UniqueConstraint('sport_key', 'nba_id', name='uq_player_nba'),
        sa.UniqueConstraint('sport_key', 'nfl_id', name='uq_player_nfl'),
        sa.UniqueConstraint('sport_key', 'mlb_id', name='uq_player_mlb'),
        sa.UniqueConstraint('sport_key', 'nhl_id', name='uq_player_nhl')
    )
    
    # 4. Create player_season_stats table
    op.create_table(
        'player_season_stats',
        sa.Column('id', sa.String(length=64), nullable=False, primary_key=True),
        sa.Column('player_id', sa.String(length=64), nullable=False),
        sa.Column('sport_key', sa.String(length=20), nullable=False),
        sa.Column('season', sa.Integer(), nullable=False),
        sa.Column('ppg', sa.Float(), nullable=True),
        sa.Column('rpg', sa.Float(), nullable=True),
        sa.Column('apg', sa.Float(), nullable=True),
        sa.Column('ast', sa.Float(), nullable=True),
        sa.Column('reb', sa.Float(), nullable=True),
        sa.Column('games_played', sa.Integer(), nullable=True),
        sa.Column('games_started', sa.Integer(), nullable=True),
        sa.Column('minutes_per_game', sa.Float(), nullable=True),
        sa.Column('field_goal_percent', sa.Float(), nullable=True),
        sa.Column('three_point_percent', sa.Float(), nullable=True),
        sa.Column('free_throw_percent', sa.Float(), nullable=True),
        sa.Column('yards', sa.Float(), nullable=True),
        sa.Column('touchdowns', sa.Float(), nullable=True),
        sa.Column('interceptions', sa.Float(), nullable=True),
        sa.Column('hits', sa.Float(), nullable=True),
        sa.Column('sacks', sa.Float(), nullable=True),
        sa.Column('era', sa.Float(), nullable=True),
        sa.Column('wins', sa.Integer(), nullable=True),
        sa.Column('strikeouts', sa.Float(), nullable=True),
        sa.Column('goals', sa.Float(), nullable=True),
        sa.Column('assists', sa.Float(), nullable=True),
        sa.Column('plus_minus', sa.Float(), nullable=True),
        sa.Column('last_updated', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['player_id'], ['player_records.id']),
        sa.Index('idx_season_stats_player_season', 'player_id', 'season'),
        sa.UniqueConstraint('player_id', 'season', name='uq_player_season')
    )
    
    # 5. Create player_game_log table
    op.create_table(
        'player_game_log',
        sa.Column('id', sa.String(length=64), nullable=False, primary_key=True),
        sa.Column('player_id', sa.String(length=64), nullable=False),
        sa.Column('event_id', sa.String(length=128), nullable=False),
        sa.Column('game_date', sa.Date(), nullable=False),
        sa.Column('opponent', sa.String(length=50), nullable=False),
        sa.Column('is_home_game', sa.Boolean(), nullable=False),
        sa.Column('starter', sa.Boolean(), nullable=False),
        sa.Column('minutes', sa.Float(), nullable=True),
        sa.Column('points', sa.Float(), nullable=True),
        sa.Column('rebounds', sa.Float(), nullable=True),
        sa.Column('assists', sa.Float(), nullable=True),
        sa.Column('field_goals_made', sa.Float(), nullable=True),
        sa.Column('field_goals_attempted', sa.Float(), nullable=True),
        sa.Column('three_pointers_made', sa.Float(), nullable=True),
        sa.Column('three_pointers_attempted', sa.Float(), nullable=True),
        sa.Column('free_throws_made', sa.Float(), nullable=True),
        sa.Column('free_throws_attempted', sa.Float(), nullable=True),
        sa.Column('turnovers', sa.Float(), nullable=True),
        sa.Column('steals', sa.Float(), nullable=True),
        sa.Column('blocks', sa.Float(), nullable=True),
        sa.Column('personal_fouls', sa.Float(), nullable=True),
        sa.Column('plus_minus', sa.Float(), nullable=True),
        sa.Column('yards', sa.Float(), nullable=True),
        sa.Column('touchdowns', sa.Float(), nullable=True),
        sa.Column('receptions', sa.Float(), nullable=True),
        sa.Column('hits', sa.Float(), nullable=True),
        sa.Column('sacks', sa.Float(), nullable=True),
        sa.Column('interceptions', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['player_id'], ['player_records.id']),
        sa.Index('idx_game_log_player_date', 'player_id', 'game_date'),
        sa.Index('idx_game_log_event_id', 'event_id'),
        sa.UniqueConstraint('player_id', 'event_id', name='uq_player_event')
    )
    
    # 6. Create ml_calibration_metrics table
    op.create_table(
        'ml_calibration_metrics',
        sa.Column('id', sa.String(length=64), nullable=False, primary_key=True),
        sa.Column('sport_key', sa.String(length=20), nullable=False),
        sa.Column('model_name', sa.String(length=128), nullable=False),
        sa.Column('metric_date', sa.Date(), nullable=False),
        sa.Column('total_predictions', sa.Integer(), nullable=False),
        sa.Column('calibration_error', sa.Float(), nullable=False),
        sa.Column('brier_score', sa.Float(), nullable=False),
        sa.Column('log_loss', sa.Float(), nullable=False),
        sa.Column('confidence_50_60_accuracy', sa.Float(), nullable=True),
        sa.Column('confidence_60_70_accuracy', sa.Float(), nullable=True),
        sa.Column('confidence_70_80_accuracy', sa.Float(), nullable=True),
        sa.Column('confidence_80_90_accuracy', sa.Float(), nullable=True),
        sa.Column('confidence_90_100_accuracy', sa.Float(), nullable=True),
        sa.Column('temperature', sa.Float(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Index('idx_calibration_sport_model_date', 'sport_key', 'model_name', 'metric_date'),
        sa.UniqueConstraint('sport_key', 'model_name', 'metric_date', name='uq_calibration_metric')
    )
    
    # 7. Create prediction_performance_cache table (for fast dashboard queries)
    op.create_table(
        'prediction_performance_cache',
        sa.Column('id', sa.String(length=64), nullable=False, primary_key=True),
        sa.Column('user_id', sa.String(length=64), nullable=False),
        sa.Column('sport_key', sa.String(length=20), nullable=False),
        sa.Column('time_period', sa.String(length=32), nullable=False),  # 'week', 'month', 'season'
        sa.Column('total_predictions', sa.Integer(), nullable=False),
        sa.Column('correct_predictions', sa.Integer(), nullable=False),
        sa.Column('win_rate', sa.Float(), nullable=False),
        sa.Column('avg_confidence', sa.Float(), nullable=False),
        sa.Column('roi', sa.Float(), nullable=True),
        sa.Column('cached_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.Index('idx_perf_cache_user_sport_period', 'user_id', 'sport_key', 'time_period'),
        sa.UniqueConstraint('user_id', 'sport_key', 'time_period', name='uq_perf_cache')
    )

def downgrade():
    """Revert migration"""
    
    op.drop_table('prediction_performance_cache')
    op.drop_table('ml_calibration_metrics')
    op.drop_table('player_game_log')
    op.drop_table('player_season_stats')
    op.drop_table('player_records')
    op.drop_table('prediction_accuracy_stats')
    op.drop_table('prediction_records')
