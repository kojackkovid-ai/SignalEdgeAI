"""
Prediction Records Models
Tracks user prediction history and accuracy statistics
"""

from sqlalchemy import Column, String, Float, Integer, DateTime, Boolean, ForeignKey, JSON, Index, func
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import uuid

class PredictionRecord(Base):
    """Store every prediction made by users for historical tracking"""
    __tablename__ = "prediction_records"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'), index=True)
    
    # Sport & Event Info
    sport_key = Column(String, index=True)  # nba, nfl, mlb, nhl, soccer
    league_id = Column(String)  # regular, playoffs, postseason
    event_id = Column(String, index=True)  # ESPN event ID
    matchup = Column(String)  # "Lakers vs Celtics"
    home_team = Column(String)
    away_team = Column(String)
    
    # Prediction Details
    prediction_type = Column(String)  # moneyline, spread, over_under, player_props
    prediction = Column(String)  # Home Win, Away Win, Over, Under, etc
    player_name = Column(String, nullable=True)  # For player props
    player_stat_type = Column(String, nullable=True)  # points, rebounds, assists, etc
    line = Column(Float, nullable=True)  # 9.5, 24.5, etc
    
    # Model Output
    confidence = Column(Float)  # 0.0-1.0
    reasoning = Column(JSON)  # List of reasoning strings
    model_weights = Column(JSON)  # Individual model outputs and weights
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    event_start_time = Column(DateTime)
    resolved_at = Column(DateTime, nullable=True)
    
    # Results
    outcome = Column(String)  # hit, miss, pending, void, cancelled
    actual_result = Column(String, nullable=True)  # Final score or result
    hit_amount = Column(Float, default=0.0)  # ROI if applicable
    
    # Relationships
    user = relationship("User", backref="prediction_records")
    
    # Indexes for fast queries
    __table_args__ = (
        Index('idx_user_sport_date', 'user_id', 'sport_key', 'created_at'),
        Index('idx_outcome_date', 'outcome', 'created_at'),
        Index('idx_sport_outcome', 'sport_key', 'outcome'),
    )

class PredictionAccuracyStats(Base):
    """Cached accuracy statistics for users (updated daily/hourly)"""
    __tablename__ = "prediction_accuracy_stats"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'), unique=True)
    sport_key = Column(String, nullable=True)  # Overall if NULL, specific sport if set
    
    # Overall Stats
    total_predictions = Column(Integer, default=0)
    hits = Column(Integer, default=0)
    misses = Column(Integer, default=0)
    voids = Column(Integer, default=0)
    pending = Column(Integer, default=0)
    
    # Calculated Metrics
    win_rate = Column(Float, default=0.0)  # hits / (hits + misses)
    avg_confidence = Column(Float, default=0.0)
    roi = Column(Float, default=0.0)
    
    # Tracking
    last_updated = Column(DateTime, default=datetime.utcnow)
    last_prediction_id = Column(String, ForeignKey('prediction_records.id'), nullable=True)
    
    # Relationships
    # user = relationship("User", backref="accuracy_stats")
    
    __table_args__ = (
        Index('idx_user_sport', 'user_id', 'sport_key'),
        Index('idx_win_rate', 'win_rate'),
    )

class PlayerRecord(Base):
    """Player information for player props predictions"""
    __tablename__ = "player_records"
    
    id = Column(String, primary_key=True)
    name = Column(String, index=True)
    team_key = Column(String)
    sport_key = Column(String, index=True)  # nba, nfl, mlb, nhl
    position = Column(String)
    external_ids = Column(String, nullable=True)
    
    # External IDs
    nba_id = Column(String, nullable=True)
    nfl_id = Column(String, nullable=True)
    nhl_id = Column(String, nullable=True)
    mlb_id = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    
    # Relationships
    season_stats = relationship("PlayerSeasonStats", backref="player", foreign_keys="PlayerSeasonStats.player_id")
    game_logs = relationship("PlayerGameLog", backref="player", foreign_keys="PlayerGameLog.player_id")
    
    __table_args__ = (
        Index('idx_player_sport_id', 'sport_key', 'nba_id'),
    )

class PlayerSeasonStats(Base):
    """Seasonal statistics for each player"""
    __tablename__ = "player_season_stats"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    player_id = Column(String, ForeignKey('player_records.id'), index=True)
    sport_key = Column(String)
    season = Column(Integer, index=True)
    
    # Game info
    games_played = Column(Integer, default=0)
    games_started = Column(Integer, default=0)
    minutes_per_game = Column(Float, default=0.0)
    
    # Basketball stats
    ppg = Column(Float, nullable=True)  # Points per game
    rpg = Column(Float, nullable=True)  # Rebounds per game
    apg = Column(Float, nullable=True)  # Assists per game
    spg = Column(Float, nullable=True)  # Steals per game
    bpg = Column(Float, nullable=True)  # Blocks per game
    fg_percent = Column(Float, nullable=True)
    three_pt_percent = Column(Float, nullable=True)
    ft_percent = Column(Float, nullable=True)
    
    # Football stats
    pass_yards_per_game = Column(Float, nullable=True)
    pass_tds = Column(Integer, nullable=True)
    interceptions = Column(Integer, nullable=True)
    rush_yards_per_game = Column(Float, nullable=True)
    rush_tds = Column(Integer, nullable=True)
    receptions_per_game = Column(Float, nullable=True)
    receiving_yards_per_game = Column(Float, nullable=True)
    receiving_tds = Column(Integer, nullable=True)
    
    # Baseball stats
    batting_avg = Column(Float, nullable=True)
    home_runs = Column(Integer, nullable=True)
    rbi = Column(Integer, nullable=True)
    strikeouts = Column(Integer, nullable=True)
    era = Column(Float, nullable=True)
    strikeouts_per_9 = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_player_season', 'player_id', 'season'),
    )

class PlayerGameLog(Base):
    """Game-by-game statistics for players"""
    __tablename__ = "player_game_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    player_id = Column(String, ForeignKey('player_records.id'), index=True)
    event_id = Column(String, index=True)  # ESPN event ID
    sport_key = Column(String)
    date = Column(DateTime, index=True)
    
    # Opponent info
    opponent = Column(String, nullable=True)  # Opponent team name
    home_away = Column(String, nullable=True)  # "home" or "away"
    
    # Flexible stats storage (JSON handles all sports)
    stats = Column(JSON)  # {points: 25, rebounds: 8, assists: 4, ...}
    
    # Game scores
    team_score = Column(Integer, nullable=True)
    opponent_score = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_player_date', 'player_id', 'date'),
        Index('idx_event', 'event_id'),
    )

class PlayerPropLine(Base):
    """Betting lines for player props"""
    __tablename__ = "player_prop_lines"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String, index=True)
    player_id = Column(String, ForeignKey('player_records.id'))
    sport_key = Column(String)
    stat_type = Column(String)  # points, rebounds, assists, etc
    line = Column(Float)  # 24.5, 9.5, etc
    
    over_odds = Column(Integer, nullable=True)  # -110, -120, etc
    under_odds = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    active = Column(Boolean, default=True)
    
    __table_args__ = (
        Index('idx_event_sport', 'event_id', 'sport_key'),
        Index('idx_active', 'active', 'created_at'),
    )
