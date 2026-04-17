"""
Tier Features Configuration

Defines what features are available in each subscription tier.
All values are based on business logic, not arbitrary - every limit has a reason.
"""

from typing import Dict, List, Any, Optional
from enum import Enum


class TierName(str, Enum):
    """Available subscription tiers"""
    STARTER = "starter"  # Free tier: 1 pick/day
    BASIC = "basic"
    PRO = "pro"
    PRO_PLUS = "pro_plus"
    ELITE = "elite"


class TierFeatures:
    """
    Complete feature set and limits for each tier.
    
    Tiers are structured to:
    1. FREE: Get users who can't pay yet, show value
    2. BASIC: Low barrier to entry, good for casual users ($12/mo)
    3. PRO: Most features, for serious bettors ($29/mo)
    4. PRO_PLUS: Full AI analysis and unlimited picks ($49/mo)
    5. ELITE: Everything + custom features for power users ($99/mo)
    """
    
    # Tier definitions - REAL features only, no fake benefits
    TIER_CONFIG: Dict[str, Dict[str, Any]] = {
        'starter': {
            'name': 'Starter',
            'price': {
                'monthly': 0,      # Free
                'annual': 0,
                'currency': 'USD'
            },
            'description': 'Very limited free tier - 1 pick per day only',
            
            # Core limits - STRICTLY LIMITED
            'predictions_per_day': 1,      # Only 1 prediction/day
            'predictions_per_month': 30,   # ~1 per day
            'sports_enabled': ['basketball_nba'],  # Only NBA
            'prediction_types': ['moneyline'],  # Moneyline only
            'min_confidence_threshold': 80,  # Only highest confidence
            
            # Features - MINIMAL
            'show_reasoning': False,
            'show_model_breakdown': False,
            'show_historical_accuracy': False,
            'api_access': False,
            'data_export': False,
            'custom_alerts': False,
            'priority_support': False,
            'ads_enabled': True,
            'show_odds': False,
            'show_models': False,
            
            # Account
            'max_saved_predictions': 10,
            'prediction_history_days': 3,
            'leaderboard_access': False,
            
            'marketing_messages': 'Upgrade to Free for more picks',
        },
        
        'basic': {
            'name': 'Basic',
            'price': {
                'monthly': 1200,       # $12.00
                'annual': 12000,       # $120.00 (save $24/year)
                'currency': 'USD'
            },
            'description': 'Perfect for regular bettors',
            
            # Core limits
            'predictions_per_day': 10,       # 10 predictions/day
            'predictions_per_month': 300,    # ~10 per day
            'sports_enabled': [              # 8 sports
                'basketball_nba',
                'basketball_ncaa',
                'icehockey_nhl',
                'americanfootball_nfl',
                'soccer_epl',
                'soccer_usa_mls',
                'baseball_mlb',
                'soccer_esp.1'
            ],
            'prediction_types': ['moneyline', 'over_under'],  # No props yet
            'min_confidence_threshold': 55,  # Can see medium confidence
            
            # Features
            'show_reasoning': True,         # See why prediction made
            'show_model_breakdown': False,  # Still can't see model weights
            'show_historical_accuracy': False,  # Can't see track record
            'api_access': False,            # No API
            'data_export': False,           # Can't export data
            'custom_alerts': False,         # No notifications
            'priority_support': False,      # Email only
            'ads_enabled': True,            # Shows ads
            
            # Account
            'max_saved_predictions': 500,
            'prediction_history_days': 30,
            'leaderboard_access': False,
            
            'marketing_messages': 'Upgrade to Pro for unlimited predictions',
        },
        
        'pro': {
            'name': 'Pro',
            'price': {
                'monthly': 2900,       # $29.00
                'annual': 29000,       # $290.00 (save $58/year)
                'currency': 'USD'
            },
            'description': 'Serious bettors love this',
            
            # Core limits
            'predictions_per_day': 25,      # 25 picks/day
            'predictions_per_month': 750,   # ~25 per day
            'sports_enabled': [             # All 11 sports
                'basketball_nba',
                'basketball_ncaa',
                'icehockey_nhl',
                'americanfootball_nfl',
                'soccer_epl',
                'soccer_usa_mls',
                'soccer_esp.1',
                'soccer_ita.1',
                'soccer_ger.1',
                'soccer_fra.1',
                'baseball_mlb'
            ],
            'prediction_types': [
                'moneyline',
                'over_under',
                'player_props',      # Can see player props
                'team_props'
            ],
            'min_confidence_threshold': 50,  # Can see all predictions
            
            # Features
            'show_reasoning': True,         # See reasoning
            'show_model_breakdown': True,   # See which model predicted what
            'show_historical_accuracy': True,  # See accuracy by sport/type
            'api_access': False,            # Not yet
            'data_export': False,           # Can export (v2 feature)
            'custom_alerts': True,          # Get notifications
            'priority_support': True,       # 24h response
            'ads_enabled': False,           # No ads
            
            # Account
            'max_saved_predictions': 9999,
            'prediction_history_days': 365,
            'leaderboard_access': True,
            
            'marketing_messages': 'Pro user',
        },
        
        'pro_plus': {
            'name': 'Pro Plus',
            'price': {
                'monthly': 4900,       # $49.00
                'annual': 49000,       # $490.00 (save $98/year)
                'currency': 'USD'
            },
            'description': 'Full AI analysis and unlimited picks',
            
            # Core limits
            'predictions_per_day': 9999,    # Unlimited
            'predictions_per_month': 9999,  # Unlimited
            'sports_enabled': [             # All 11 sports
                'basketball_nba',
                'basketball_ncaa',
                'icehockey_nhl',
                'americanfootball_nfl',
                'soccer_epl',
                'soccer_usa_mls',
                'soccer_esp.1',
                'soccer_ita.1',
                'soccer_ger.1',
                'soccer_fra.1',
                'baseball_mlb'
            ],
            'prediction_types': [
                'moneyline',
                'over_under',
                'player_props',      # Can see player props
                'team_props'
            ],
            'min_confidence_threshold': 50,  # Can see all predictions
            
            # Features
            'show_reasoning': True,         # See reasoning
            'show_model_breakdown': True,   # Full AI breakdown
            'show_historical_accuracy': True,  # See accuracy by sport/type
            'api_access': False,            # Not yet
            'data_export': False,           # Can export (v2 feature)
            'custom_alerts': True,          # Get notifications
            'priority_support': True,       # 24h response
            'ads_enabled': False,           # No ads
            'full_ai_breakdown': True,      # Full AI analysis
            
            # Account
            'max_saved_predictions': 9999,
            'prediction_history_days': 365,
            'leaderboard_access': True,
            
            'marketing_messages': 'Pro Plus user - Full AI analysis',
        },
        
        'elite': {
            'name': 'Elite',
            'price': {
                'monthly': 9900,       # $99.00
                'annual': 99000,       # $990.00 (save $198/year)
                'currency': 'USD'
            },
            'description': 'For power users and professionals',
            
            # Core limits
            'predictions_per_day': 9999,    # Unlimited
            'predictions_per_month': 9999,  # Unlimited
            'sports_enabled': 'all',        # Every sport
            'prediction_types': [           # All types
                'moneyline',
                'over_under',
                'player_props',
                'team_props',
                'combination_props'
            ],
            'min_confidence_threshold': 0,  # See everything
            
            # Features - Everything from Pro +
            'show_reasoning': True,
            'show_model_breakdown': True,
            'show_historical_accuracy': True,
            'api_access': True,             # REST API access!
            'api_rate_limit': 10000,        # 10k requests/day
            'data_export': True,            # Full data export
            'custom_alerts': True,
            'priority_support': True,
            'ads_enabled': False,
            
            # Elite-only features
            'custom_models': True,          # Can train custom models
            'white_label_api': False,       # Available in future
            'early_access_features': True,  # Beta features first
            'dedicated_account_manager': True,  # Phone/email support
            'custom_sports_integration': False,  # Available in future
            
            # Account
            'max_saved_predictions': 9999,
            'prediction_history_days': 9999,  # Unlimited history
            'leaderboard_access': True,
            
            'marketing_messages': 'Elite user - Power user benefits',
        }
    }
    
    # Legacy/Deprecated tiers for backwards compatibility
    LEGACY_TIER_MAPPING = {
        'standard': TierName.BASIC,
        'premium': TierName.PRO,
        'ultimate': TierName.ELITE,
    }

    @classmethod
    def get_tier_config(cls, tier_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific tier"""
        tier = cls._normalize_tier_name(tier_name)
        return cls.TIER_CONFIG.get(tier)
    
    @classmethod
    def is_feature_enabled(cls, tier_name: str, feature: str) -> bool:
        """Check if a feature is enabled for a tier"""
        config = cls.get_tier_config(tier_name)
        if not config:
            return False
        return config.get(feature, False)
    
    @classmethod
    def get_limit(cls, tier_name: str, limit_name: str) -> Optional[Any]:
        """Get a specific limit for a tier"""
        config = cls.get_tier_config(tier_name)
        if not config:
            return None
        return config.get(limit_name)
    
    @classmethod
    def can_access_sport(cls, tier_name: str, sport_key: str) -> bool:
        """Check if user can access a specific sport"""
        config = cls.get_tier_config(tier_name)
        if not config:
            return False
        
        enabled_sports = config.get('sports_enabled', [])
        if enabled_sports == 'all':
            return True
        
        return sport_key in enabled_sports
    
    @classmethod
    def can_access_prediction_type(cls, tier_name: str, pred_type: str) -> bool:
        """Check if user can access a prediction type"""
        config = cls.get_tier_config(tier_name)
        if not config:
            return False
        
        enabled_types = config.get('prediction_types', [])
        return pred_type in enabled_types
    
    @classmethod
    def all_tiers(cls) -> List[str]:
        """Get list of all available tiers"""
        return list(cls.TIER_CONFIG.keys())
    
    @classmethod
    def get_tier_price(cls, tier_name: str, billing_cycle: str = 'monthly') -> Optional[int]:
        """
        Get price in cents for a tier.
        
        Args:
            tier_name: The tier to get price for
            billing_cycle: 'monthly' or 'annual'
        
        Returns:
            Price in cents (e.g., 2900 = $29.00)
        """
        config = cls.get_tier_config(tier_name)
        if not config or 'price' not in config:
            return None
        
        price_config = config['price']
        key = 'monthly' if billing_cycle.lower() == 'monthly' else 'annual'
        return price_config.get(key)
    
    @classmethod
    def get_tier_description(cls, tier_name: str) -> str:
        """Get user-friendly description of tier"""
        config = cls.get_tier_config(tier_name)
        if not config:
            return "Unknown tier"
        return config.get('description', '')
    
    @classmethod
    def _normalize_tier_name(cls, tier_name: str) -> Optional[str]:
        """Normalize tier name to standard format"""
        if not tier_name:
            return None
        
        tier_lower = tier_name.lower().strip()
        
        # Direct match
        if tier_lower in cls.TIER_CONFIG:
            return tier_lower
        
        # Legacy mapping
        if tier_lower in cls.LEGACY_TIER_MAPPING:
            return cls.LEGACY_TIER_MAPPING[tier_lower]
        
        return None
    
    @classmethod
    def validate_tier(cls, tier_name: str) -> bool:
        """Check if tier name is valid"""
        return cls._normalize_tier_name(tier_name) is not None
    
    @classmethod
    def get_upgrade_path(cls, current_tier: str) -> List[str]:
        """Get available upgrade paths from current tier"""
        tier_order = ['starter', 'basic', 'pro', 'pro_plus', 'elite']
        current = cls._normalize_tier_name(current_tier)
        
        if not current:
            return []
        
        current_idx = tier_order.index(current) if current in tier_order else -1
        if current_idx == -1:
            return []
        
        return tier_order[current_idx + 1:]
    
    @classmethod
    def compare_tiers(cls, tier1: str, tier2: str) -> int:
        """
        Compare two tiers.
        Returns: 1 if tier1 > tier2, -1 if tier1 < tier2, 0 if equal
        """
        tier_order = [TierName.FREE, TierName.BASIC, TierName.PRO, TierName.PRO_PLUS, TierName.ELITE]
        t1 = cls._normalize_tier_name(tier1)
        t2 = cls._normalize_tier_name(tier2)
        
        idx1 = tier_order.index(t1) if t1 in tier_order else -1
        idx2 = tier_order.index(t2) if t2 in tier_order else -1
        
        if idx1 > idx2:
            return 1
        elif idx1 < idx2:
            return -1
        else:
            return 0


# Helper functions for use in routes/services

def get_user_tier_features(tier_name: str) -> Dict[str, Any]:
    """Get all features for a user's tier"""
    return TierFeatures.get_tier_config(tier_name) or {}


def check_tier_access(tier_name: str, required_feature: str) -> bool:
    """Check if tier has access to required feature"""
    return TierFeatures.is_feature_enabled(tier_name, required_feature)


def get_available_predictions(tier_name: str, total_predictions_today: int) -> int:
    """Get remaining predictions user can make today"""
    limit = TierFeatures.get_limit(tier_name, 'predictions_per_day') or 0
    return max(0, limit - total_predictions_today)
