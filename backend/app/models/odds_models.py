"""
Real-Time Odds Integration Models and Data Structures
Week 5-7 Enhancement: Multi-provider odds aggregation
"""

from sqlalchemy import Column, String, Float, DateTime, Integer, JSON, Boolean
from sqlalchemy.orm import declarative_base
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
from pydantic import BaseModel
import numpy as np

Base = declarative_base()

# ============================================================================
# ENUMS
# ============================================================================

class OddsProvider(str, Enum):
    """Supported odds providers"""
    DRAFTKINGS = "draftkings"
    FANDUEL = "fanduel"
    BETMGM = "betmgm"
    CAESARS = "caesars"
    POINTSBET = "pointsbet"
    ESPN = "espn"

class MarketType(str, Enum):
    """Types of betting markets"""
    MONEYLINE = "moneyline"
    SPREAD = "spread"
    TOTAL = "total"
    LINE = "line"

class MovementType(str, Enum):
    """Types of odds movements detected"""
    REVERSAL = "reversal"  # Sharp money detected
    CONSENSUS = "consensus"  # All books moving same direction
    ARBITRAGE = "arbitrage"  # Opportunity detected
    STEAM_MOVE = "steam"  # Fast coordinated movement
    CONTRARIAN = "contrarian"  # Market disagreement

# ============================================================================
# SQLALCHEMY MODELS
# ============================================================================

class OddsRecord(Base):
    """Store real-time odds from multiple providers"""
    __tablename__ = "odds_records"
    
    id = Column(String(64), primary_key=True)
    sport_key = Column(String(20), nullable=False, index=True)
    event_id = Column(String(128), nullable=False, index=True)
    provider = Column(String(50), nullable=False)  # DraftKings, FanDuel, etc.
    market_type = Column(String(20), nullable=False)  # moneyline, spread, total
    
    # Moneyline odds
    moneyline_home = Column(Float, nullable=True)
    moneyline_away = Column(Float, nullable=True)
    moneyline_draw = Column(Float, nullable=True)
    
    # Spread odds
    spread_home = Column(Float, nullable=True)
    spread_away = Column(Float, nullable=True)
    spread_value = Column(Float, nullable=True)  # -3.5, +7, etc.
    
    # Total odds
    total_line = Column(Float, nullable=True)
    total_over = Column(Float, nullable=True)
    total_under = Column(Float, nullable=True)
    
    # Implied probabilities
    implied_prob_home = Column(Float, nullable=True)
    implied_prob_away = Column(Float, nullable=True)
    implied_prob_over = Column(Float, nullable=True)
    implied_prob_under = Column(Float, nullable=True)
    
    # Metadata
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    last_updated = Column(DateTime(timezone=True), nullable=False)
    confidence_score = Column(Float, default=0.95)
    last_movement = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<OddsRecord {self.provider}:{self.event_id}>"

class OddsMovement(Base):
    """Track odds movements and market activities"""
    __tablename__ = "odds_movement"
    
    id = Column(String(64), primary_key=True)
    sport_key = Column(String(20), nullable=False, index=True)
    event_id = Column(String(128), nullable=False, index=True)
    
    # Movement details
    market_type = Column(String(20), nullable=False)
    movement_type = Column(String(50), nullable=False)  # reversal, consensus, etc.
    time_interval = Column(String(20), nullable=False)  # 1h, 6h, 24h, preseason
    
    # Line movement
    opening_line = Column(Float, nullable=False)
    current_line = Column(Float, nullable=False)
    move_amount = Column(Float, nullable=False)
    move_percentage = Column(Float, nullable=False)
    direction = Column(String(10), nullable=False)  # "up" or "down"
    
    # Movement metrics
    provider_count = Column(Integer, default=0)  # How many books moved
    speed_index = Column(Float, nullable=True)  # How fast movement occurred
    confidence_metric = Column(Float, nullable=True)  # 0-1 confidence in detection
    
    # Detection details
    detected_reason = Column(String(256), nullable=True)  # injuries, weather, etc.
    smart_money_detected = Column(Boolean, default=False)
    arbitrage_opportunity = Column(Boolean, default=False)
    
    # Market consensus
    market_consensus = Column(String(50), nullable=True)  # home_heavy, away_heavy
    public_opinion = Column(String(50), nullable=True)  # heavy_public_support
    
    # Timestamps
    detected_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<OddsMovement {self.event_id}:{self.movement_type}>"

class ConsensusOdds(Base):
    """Store consensus odds across providers"""
    __tablename__ = "consensus_odds"
    
    id = Column(String(64), primary_key=True)
    sport_key = Column(String(20), nullable=False, index=True)
    event_id = Column(String(128), nullable=False, index=True)
    
    # Consensus values (median across providers)
    consensus_moneyline_home = Column(Float, nullable=True)
    consensus_moneyline_away = Column(Float, nullable=True)
    consensus_spread = Column(Float, nullable=True)
    consensus_total = Column(Float, nullable=True)
    
    # Spread metrics
    spread_range_min = Column(Float, nullable=True)
    spread_range_max = Column(Float, nullable=True)
    provider_disagreement_score = Column(Float, nullable=True)
    
    # Provider counts
    moneyline_providers = Column(Integer, default=0)
    spread_providers = Column(Integer, default=0)
    total_providers = Column(Integer, default=0)
    
    # Timestamps
    last_calculated = Column(DateTime(timezone=True), nullable=False)
    next_update = Column(DateTime(timezone=True), nullable=False)
    
    def __repr__(self):
        return f"<ConsensusOdds {self.event_id}>"

# ============================================================================
# PYDANTIC MODELS (API schemas)
# ============================================================================

class OddsDataResponse(BaseModel):
    """Response schema for odds data"""
    sport_key: str
    event_id: str
    provider: str
    market_type: str
    
    moneyline_home: Optional[float] = None
    moneyline_away: Optional[float] = None
    spread_value: Optional[float] = None
    spread_home: Optional[float] = None
    total_line: Optional[float] = None
    total_over: Optional[float] = None
    
    implied_prob_home: Optional[float] = None
    implied_prob_away: Optional[float] = None
    
    timestamp: datetime
    last_movement: Optional[datetime] = None
    confidence_score: float
    
    class Config:
        from_attributes = True

class ConsensusOddsResponse(BaseModel):
    """Response for consensus odds across providers"""
    event_id: str
    sport_key: str
    
    consensus_moneyline_home: Optional[float] = None
    consensus_moneyline_away: Optional[float] = None
    consensus_spread: Optional[float] = None
    consensus_total: Optional[float] = None
    
    spread_range: Optional[Dict[str, float]] = None
    provider_disagreement_score: Optional[float] = None
    
    providers_reporting: Dict[str, int]  # {"moneyline": 5, "spread": 4}
    
    last_calculated: datetime
    
    class Config:
        from_attributes = True

class ImpliedProbabilityResponse(BaseModel):
    """Response for implied probability calculations"""
    event_id: str
    sport_key: str
    
    implied_prob_home: float
    implied_prob_away: float
    implied_prob_draw: Optional[float] = None
    
    # Comparison to model
    model_prediction_home: Optional[float] = None
    edge_home: Optional[float] = None  # Difference in probability
    edge_away: Optional[float] = None
    
    # Market assessment
    market_overvalued: Optional[str] = None  # "home" or "away"
    expected_value: Optional[float] = None
    
    calculated_at: datetime
    
    class Config:
        from_attributes = True

class OddsMovementResponse(BaseModel):
    """Response for odds movement data"""
    event_id: str
    movement_type: str  # reversal, consensus, etc.
    time_interval: str
    
    opening_line: float
    current_line: float
    move_amount: float
    move_percentage: float
    direction: str
    
    provider_count: int
    speed_index: Optional[float] = None
    confidence_metric: float
    
    detected_reason: Optional[str] = None
    smart_money_detected: bool
    arbitrage_opportunity: bool
    
    market_consensus: Optional[str] = None
    
    detected_at: datetime
    
    class Config:
        from_attributes = True

class OddsComparisonResponse(BaseModel):
    """Response comparing odds across providers"""
    event_id: str
    sport_key: str
    market_type: str
    
    providers: Dict[str, Dict]  # Provider -> {moneyline, spread, etc.}
    consensus: Dict[str, float]
    
    best_odds: Dict[str, Dict]  # {home: {provider, odds}, away: {provider, odds}}
    worst_odds: Dict[str, Dict]
    
    spread_range: Dict[str, float]  # {min, max, range}
    
    last_updated: datetime
    
    class Config:
        from_attributes = True

class SharpMovementAlertResponse(BaseModel):
    """Response for sharp movement detection"""
    events: List[Dict]  # List of events with detected movements
    
    movement_type: str
    total_events_affected: int
    
    details: List[OddsMovementResponse]
    recommended_action: Optional[str] = None
    
    alert_severity: str  # "info", "warning", "critical"
    timestamp: datetime
    
    class Config:
        from_attributes = True

# ============================================================================
# PROBABILITY CONVERSION UTILITIES
# ============================================================================

class ProbabilityConverter:
    """Utilities for converting between different odds formats"""
    
    @staticmethod
    def american_to_decimal(american_odds: float) -> float:
        """Convert American odds to decimal odds"""
        if american_odds > 0:
            return (american_odds / 100) + 1
        else:
            return (100 / abs(american_odds)) + 1
    
    @staticmethod
    def american_to_implied_probability(american_odds: float) -> float:
        """Convert American odds to implied probability"""
        decimal = ProbabilityConverter.american_to_decimal(american_odds)
        return 1 / decimal
    
    @staticmethod
    def decimal_to_american(decimal_odds: float) -> float:
        """Convert decimal odds to American odds"""
        if decimal_odds >= 2:
            return (decimal_odds - 1) * 100
        else:
            return -100 / (decimal_odds - 1)
    
    @staticmethod
    def decimal_to_implied_probability(decimal_odds: float) -> float:
        """Convert decimal odds to implied probability"""
        return 1 / decimal_odds
    
    @staticmethod
    def implied_probability_to_american(probability: float) -> float:
        """Convert implied probability to American odds"""
        if probability >= 0.5:
            return -100 / ((1 / probability) - 1)
        else:
            return 100 * ((1 / probability) - 1)
    
    @staticmethod
    def calculate_vig(home_odds: float, away_odds: float) -> float:
        """
        Calculate vigorish (implied juice) in moneyline
        
        Args:
            home_odds: American odds for home team
            away_odds: American odds for away team
        
        Returns:
            Vigorish percentage (0-5% is typical)
        """
        home_prob = ProbabilityConverter.american_to_implied_probability(home_odds)
        away_prob = ProbabilityConverter.american_to_implied_probability(away_odds)
        
        total_prob = home_prob + away_prob
        vig = (total_prob - 1) * 100
        
        return max(0, vig)
    
    @staticmethod
    def true_probability_moneyline(home_odds: float, away_odds: float) -> tuple:
        """
        Remove vigorish and get true probabilities
        
        Returns:
            (true_prob_home, true_prob_away)
        """
        home_implied = ProbabilityConverter.american_to_implied_probability(home_odds)
        away_implied = ProbabilityConverter.american_to_implied_probability(away_odds)
        
        total = home_implied + away_implied
        
        return (home_implied / total, away_implied / total)

# ============================================================================
# EDGE DETECTION UTILITIES
# ============================================================================

class EdgeDetector:
    """Detect betting edges and opportunities"""
    
    @staticmethod
    def calculate_edge(
        model_probability: float,
        market_probability: float,
        american_odds: float
    ) -> Dict:
        """
        Calculate edge between model prediction and market odds
        
        Args:
            model_probability: Model's predicted probability
            market_probability: Implied probability from market odds
            american_odds: American odds for the bet
        
        Returns:
            Dict with edge metrics
        """
        edge = model_probability - market_probability
        
        # Expected value: (prob * payout) - bet_amount
        decimal_odds = ProbabilityConverter.american_to_decimal(american_odds)
        expected_value = (model_probability * (decimal_odds - 1)) - (1 - model_probability)
        
        return {
            'edge': edge,
            'edge_percentage': edge * 100,
            'expected_value': expected_value,
            'is_profitable': edge > 0,
            'confidence_in_edge': EdgeDetector._calculate_edge_confidence(edge),
            'kelly_fraction': EdgeDetector._kelly_criterion(edge, decimal_odds)
        }
    
    @staticmethod
    def _calculate_edge_confidence(edge: float) -> float:
        """Edge confidence based on magnitude"""
        if abs(edge) < 0.02:
            return 0.5  # Low confidence, high uncertainty
        elif abs(edge) < 0.05:
            return 0.7
        elif abs(edge) < 0.10:
            return 0.85
        else:
            return 0.95  # High edge, high confidence
    
    @staticmethod
    def _kelly_criterion(edge: float, decimal_odds: float) -> float:
        """
        Calculate Kelly Criterion stake size
        Kelly = edge / (odds - 1)
        """
        if decimal_odds <= 1:
            return 0
        
        kelly = edge / (decimal_odds - 1)
        
        # Cap Kelly at 25% (quarter Kelly) for safety
        return max(0, min(kelly / 4, 0.25))

if __name__ == "__main__":
    # Example usage
    converter = ProbabilityConverter()
    
    # Convert American odds to probability
    prob = converter.american_to_implied_probability(-110)
    print(f"Probability of -110 odds: {prob:.2%}")
    
    # Calculate vigorish
    vig = converter.calculate_vig(-110, -110)
    print(f"Vigorish: {vig:.2%}")
    
    # Calculate edge
    edge = EdgeDetector.calculate_edge(
        model_probability=0.55,
        market_probability=0.50,
        american_odds=-110
    )
    print(f"Edge: {edge['edge']:.1%}, EV: ${edge['expected_value']:.2f}")
