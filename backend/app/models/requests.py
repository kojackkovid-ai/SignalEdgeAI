"""
Request/Input validation models using Pydantic
Ensures all API inputs are properly validated before processing
"""

from pydantic import BaseModel, validator, Field
from typing import Optional, List
from datetime import datetime


class PredictionFilterRequest(BaseModel):
    """Request model for filtering predictions"""
    sport: Optional[str] = Field(None, description="Sport name (nba, nhl, mlb, nfl, soccer, ncaab)")
    league: Optional[str] = Field(None, description="League name")
    min_confidence: float = Field(0.0, ge=0, le=1, description="Minimum confidence score (0-1)")
    max_confidence: float = Field(1.0, ge=0, le=1, description="Maximum confidence score (0-1)")
    prediction_type: Optional[str] = Field(None, description="Type of prediction (moneyline, spread, total, props)")
    limit: int = Field(10, ge=1, le=1000, description="Number of predictions to return")
    offset: int = Field(0, ge=0, description="Offset for pagination")
    sort_by: Optional[str] = Field("confidence", description="Sort field: confidence, created_at, odds")
    sort_order: Optional[str] = Field("desc", description="Sort order: asc or desc")
    
    @validator('sport')
    def validate_sport(cls, v):
        if v is None:
            return v
        valid_sports = {'nba', 'nhl', 'mlb', 'nfl', 'soccer', 'ncaab'}
        if v.lower() not in valid_sports:
            raise ValueError(f'Sport must be one of: {valid_sports}')
        return v.lower()
    
    @validator('min_confidence')
    def validate_min_confidence(cls, v, values):
        if 'max_confidence' in values and v > values['max_confidence']:
            raise ValueError('min_confidence must be <= max_confidence')
        return v
    
    @validator('prediction_type')
    def validate_prediction_type(cls, v):
        if v is None:
            return v
        valid_types = {'moneyline', 'spread', 'total', 'props', 'player_props'}
        if v.lower() not in valid_types:
            raise ValueError(f'Prediction type must be one of: {valid_types}')
        return v.lower()
    
    @validator('sort_by')
    def validate_sort_by(cls, v):
        if v is None:
            return "confidence"
        valid_sorts = {'confidence', 'created_at', 'odds'}
        if v.lower() not in valid_sorts:
            raise ValueError(f'Sort field must be one of: {valid_sorts}')
        return v.lower()
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v is None:
            return "desc"
        if v.lower() not in {'asc', 'desc'}:
            raise ValueError('Sort order must be asc or desc')
        return v.lower()


class FollowPredictionRequest(BaseModel):
    """Request to follow/believe in a prediction"""
    amount: float = Field(..., gt=0, le=10000, description="Amount to follow ($)")
    
    @validator('amount')
    def validate_amount(cls, v):
        # Ensure 2 decimal places for currency
        if v < 1.0:
            raise ValueError('Minimum amount is $1.00')
        if v > 10000:
            raise ValueError('Maximum amount is $10,000')
        return round(v, 2)
    
    class Config:
        schema_extra = {
            "example": {
                "amount": 50.00
            }
        }


class PlayerPropsFilterRequest(BaseModel):
    """Request model for filtering player props"""
    sport: str = Field(..., description="Sport (nba, nhl, mlb, nfl)")
    player: Optional[str] = Field(None, description="Player name filter")
    market: Optional[str] = Field(None, description="Market type (points, rebounds, assists, goals, etc)")
    min_confidence: float = Field(0.0, ge=0, le=1)
    max_confidence: float = Field(1.0, ge=0, le=1)
    min_odds: float = Field(-10000, ge=-10000, le=10000, description="Minimum odds")
    max_odds: float = Field(10000, ge=-10000, le=10000, description="Maximum odds")
    limit: int = Field(50, ge=1, le=500)
    
    @validator('sport')
    def validate_sport(cls, v):
        valid_sports = {'nba', 'nhl', 'mlb', 'nfl', 'soccer', 'ncaab'}
        if v.lower() not in valid_sports:
            raise ValueError(f'Sport must be one of: {valid_sports}')
        return v.lower()
    
    @validator('player')
    def validate_player(cls, v):
        if v and len(v) < 2:
            raise ValueError('Player name must be at least 2 characters')
        return v
    
    @validator('market')
    def validate_market(cls, v):
        if v is None:
            return v
        valid_markets = {
            'points', 'rebounds', 'assists', 'goals', 'saves',
            'home_runs', 'strikeouts', 'pass_yards', 'rushing_yards',
            'receiving_yards', 'touchdowns', 'interceptions', 'sacks'
        }
        if v.lower() not in valid_markets:
            raise ValueError(f'Market must be one of: {valid_markets}')
        return v.lower()


class LoginRequest(BaseModel):
    """Login request validation"""
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")
    
    @validator('email')
    def validate_email(cls, v):
        if '@' not in v or '.' not in v.split('@')[1]:
            raise ValueError('Invalid email format')
        if len(v) > 255:
            raise ValueError('Email too long')
        return v.lower()
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        if len(v) > 128:
            raise ValueError('Password too long')
        return v


class RegisterRequest(BaseModel):
    """User registration request validation"""
    email: str = Field(..., description="User email")
    password: str = Field(..., description="User password")
    password_confirm: str = Field(..., description="Confirm password")
    username: Optional[str] = Field(None, description="Display name")
    
    @validator('email')
    def validate_email(cls, v):
        if '@' not in v or '.' not in v.split('@')[1]:
            raise ValueError('Invalid email format')
        if len(v) > 255:
            raise ValueError('Email too long')
        return v.lower()
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if len(v) > 128:
            raise ValueError('Password too long')
        # Check for complexity
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        if not (has_upper and has_lower and has_digit):
            raise ValueError('Password must contain uppercase, lowercase, and numbers')
        return v
    
    @validator('password_confirm')
    def validate_confirm(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('username')
    def validate_username(cls, v):
        if v and len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        if v and len(v) > 50:
            raise ValueError('Username too long')
        return v


class PaymentRequest(BaseModel):
    """Payment/checkout request validation"""
    tier: str = Field(..., description="Subscription tier (free, basic, pro, elite)")
    payment_method_id: Optional[str] = Field(None, description="Stripe payment method ID")
    use_existing: Optional[bool] = Field(False, description="Use existing payment method")
    
    @validator('tier')
    def validate_tier(cls, v):
        valid_tiers = {'free', 'basic', 'pro', 'elite'}
        if v.lower() not in valid_tiers:
            raise ValueError(f'Tier must be one of: {valid_tiers}')
        return v.lower()


class SearchRequest(BaseModel):
    """General search/filter request"""
    query: Optional[str] = Field(None, description="Search query")
    filters: Optional[dict] = Field(None, description="Filter criteria")
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)
    
    @validator('query')
    def validate_query(cls, v):
        if v and len(v) > 500:
            raise ValueError('Search query too long')
        return v


class BulkActionRequest(BaseModel):
    """Bulk action request validation"""
    action: str = Field(..., description="Action to perform")
    ids: List[str] = Field(..., description="List of prediction/item IDs")
    
    @validator('action')
    def validate_action(cls, v):
        valid_actions = {'delete', 'archive', 'share', 'follow', 'unfollow'}
        if v.lower() not in valid_actions:
            raise ValueError(f'Action must be one of: {valid_actions}')
        return v.lower()
    
    @validator('ids')
    def validate_ids(cls, v):
        if len(v) == 0:
            raise ValueError('Must provide at least one ID')
        if len(v) > 1000:
            raise ValueError('Cannot perform action on more than 1000 items')
        return v


class DateRangeRequest(BaseModel):
    """Date range filter for queries"""
    start_date: Optional[datetime] = Field(None, description="Start date")
    end_date: Optional[datetime] = Field(None, description="End date")
    
    @validator('start_date', 'end_date', pre=True)
    def parse_dates(cls, v):
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                raise ValueError('Invalid date format. Use ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)')
        return v
    
    @validator('end_date')
    def validate_end_after_start(cls, v, values):
        if 'start_date' in values and v and values['start_date'] and v < values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v


class PaginationRequest(BaseModel):
    """Standard pagination request"""
    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.per_page
    
    @property
    def limit(self) -> int:
        return self.per_page
