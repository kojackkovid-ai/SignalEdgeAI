"""
Unit Tests for Tier Features

Tests subscription tier configuration and access control.
"""

import pytest
from app.models.tier_features import TierFeatures, TierName, get_user_tier_features, check_tier_access


class TestTierConfiguration:
    """Test tier configuration"""
    
    def test_all_tiers_exist(self):
        """Test that all tiers are defined"""
        tiers = TierFeatures.all_tiers()
        
        assert TierName.FREE in tiers
        assert TierName.BASIC in tiers
        assert TierName.PRO in tiers
        assert TierName.ELITE in tiers
    
    def test_free_tier_config(self):
        """Test free tier configuration"""
        config = TierFeatures.get_tier_config(TierName.FREE)
        
        assert config is not None
        assert config['price']['monthly'] == 0
        assert config['predictions_per_day'] == 5
        assert len(config['sports_enabled']) == 2  # Only NBA and EPL
        assert config['prediction_types'] == ['moneyline']
        assert config['show_reasoning'] is False
        assert config['ads_enabled'] is True
    
    def test_basic_tier_config(self):
        """Test basic tier configuration"""
        config = TierFeatures.get_tier_config(TierName.BASIC)
        
        assert config is not None
        assert config['price']['monthly'] == 900  # $9.00 in cents
        assert config['predictions_per_day'] == 50
        assert 'basketball_nba' in config['sports_enabled']
        assert 'moneyline' in config['prediction_types']
        assert 'over_under' in config['prediction_types']
        assert config['show_reasoning'] is True
        assert config['show_model_breakdown'] is False
    
    def test_pro_tier_config(self):
        """Test pro tier configuration"""
        config = TierFeatures.get_tier_config(TierName.PRO)
        
        assert config is not None
        assert config['price']['monthly'] == 2900  # $29.00 in cents
        assert config['predictions_per_day'] == 9999  # Unlimited
        assert len(config['sports_enabled']) == 11  # All sports
        assert 'player_props' in config['prediction_types']
        assert config['show_reasoning'] is True
        assert config['show_model_breakdown'] is True
        assert config['show_historical_accuracy'] is True
        assert config['ads_enabled'] is False
    
    def test_elite_tier_config(self):
        """Test elite tier configuration"""
        config = TierFeatures.get_tier_config(TierName.ELITE)
        
        assert config is not None
        assert config['price']['monthly'] == 9900  # $99.00 in cents
        assert config['predictions_per_day'] == 9999  # Unlimited
        assert config['sports_enabled'] == 'all'  # All sports
        assert 'combination_props' in config['prediction_types']
        assert config['api_access'] is True
        assert config['custom_models'] is True
        assert config['dedicated_account_manager'] is True
    
    def test_invalid_tier(self):
        """Test handling of invalid tier"""
        config = TierFeatures.get_tier_config('invalid_tier')
        
        assert config is None


class TestTierAccess:
    """Test tier-based access control"""
    
    def test_free_user_sports_access(self):
        """Test free tier sport access"""
        # Free users: only NBA and EPL
        assert TierFeatures.can_access_sport(TierName.FREE, 'basketball_nba')
        assert TierFeatures.can_access_sport(TierName.FREE, 'soccer_epl')
        
        # Cannot access other sports
        assert not TierFeatures.can_access_sport(TierName.FREE, 'baseball_mlb')
        assert not TierFeatures.can_access_sport(TierName.FREE, 'icehockey_nhl')
    
    def test_pro_user_sports_access(self):
        """Test pro tier has all sports"""
        assert TierFeatures.can_access_sport(TierName.PRO, 'basketball_nba')
        assert TierFeatures.can_access_sport(TierName.PRO, 'baseball_mlb')
        assert TierFeatures.can_access_sport(TierName.PRO, 'icehockey_nhl')
        assert TierFeatures.can_access_sport(TierName.PRO, 'soccer_epl')
        assert TierFeatures.can_access_sport(TierName.PRO, 'americanfootball_nfl')
    
    def test_elite_user_sports_access(self):
        """Test elite tier access to all sports"""
        assert TierFeatures.can_access_sport(TierName.ELITE, 'basketball_nba')
        assert TierFeatures.can_access_sport(TierName.ELITE, 'any_sport')  # All
    
    def test_free_user_prediction_types(self):
        """Test free tier prediction access"""
        assert TierFeatures.can_access_prediction_type(TierName.FREE, 'moneyline')
        
        # Cannot access other types
        assert not TierFeatures.can_access_prediction_type(TierName.FREE, 'over_under')
        assert not TierFeatures.can_access_prediction_type(TierName.FREE, 'player_props')
    
    def test_basic_user_prediction_types(self):
        """Test basic tier prediction access"""
        assert TierFeatures.can_access_prediction_type(TierName.BASIC, 'moneyline')
        assert TierFeatures.can_access_prediction_type(TierName.BASIC, 'over_under')
        
        # Cannot access props yet
        assert not TierFeatures.can_access_prediction_type(TierName.BASIC, 'player_props')
    
    def test_pro_user_prediction_types(self):
        """Test pro tier has all prediction types"""
        assert TierFeatures.can_access_prediction_type(TierName.PRO, 'moneyline')
        assert TierFeatures.can_access_prediction_type(TierName.PRO, 'over_under')
        assert TierFeatures.can_access_prediction_type(TierName.PRO, 'player_props')
        assert TierFeatures.can_access_prediction_type(TierName.PRO, 'team_props')
    
    def test_feature_access_by_tier(self):
        """Test feature access varies by tier"""
        # Reasoning
        assert not TierFeatures.is_feature_enabled(TierName.FREE, 'show_reasoning')
        assert TierFeatures.is_feature_enabled(TierName.BASIC, 'show_reasoning')
        assert TierFeatures.is_feature_enabled(TierName.PRO, 'show_reasoning')
        
        # Model breakdown
        assert not TierFeatures.is_feature_enabled(TierName.FREE, 'show_model_breakdown')
        assert not TierFeatures.is_feature_enabled(TierName.BASIC, 'show_model_breakdown')
        assert TierFeatures.is_feature_enabled(TierName.PRO, 'show_model_breakdown')
        
        # API access
        assert not TierFeatures.is_feature_enabled(TierName.FREE, 'api_access')
        assert not TierFeatures.is_feature_enabled(TierName.BASIC, 'api_access')
        assert not TierFeatures.is_feature_enabled(TierName.PRO, 'api_access')
        assert TierFeatures.is_feature_enabled(TierName.ELITE, 'api_access')
    
    def test_ads_by_tier(self):
        """Test ad configuration by tier"""
        assert TierFeatures.is_feature_enabled(TierName.FREE, 'ads_enabled')
        assert TierFeatures.is_feature_enabled(TierName.BASIC, 'ads_enabled')
        assert not TierFeatures.is_feature_enabled(TierName.PRO, 'ads_enabled')
        assert not TierFeatures.is_feature_enabled(TierName.ELITE, 'ads_enabled')


class TestTierPricing:
    """Test pricing configuration"""
    
    def test_free_tier_price(self):
        """Test free tier costs nothing"""
        monthly = TierFeatures.get_tier_price(TierName.FREE, 'monthly')
        annual = TierFeatures.get_tier_price(TierName.FREE, 'annual')
        
        assert monthly == 0
        assert annual == 0
    
    def test_basic_tier_price(self):
        """Test basic tier pricing"""
        monthly = TierFeatures.get_tier_price(TierName.BASIC, 'monthly')
        annual = TierFeatures.get_tier_price(TierName.BASIC, 'annual')
        
        assert monthly == 900  # $9.00
        assert annual == 9000  # $90.00
    
    def test_pro_tier_price(self):
        """Test pro tier pricing"""
        monthly = TierFeatures.get_tier_price(TierName.PRO, 'monthly')
        annual = TierFeatures.get_tier_price(TierName.PRO, 'annual')
        
        assert monthly == 2900  # $29.00
        assert annual == 29000  # $290.00
    
    def test_elite_tier_price(self):
        """Test elite tier pricing"""
        monthly = TierFeatures.get_tier_price(TierName.ELITE, 'monthly')
        annual = TierFeatures.get_tier_price(TierName.ELITE, 'annual')
        
        assert monthly == 9900  # $99.00
        assert annual == 99000  # $990.00
    
    def test_annual_saves_money(self):
        """Test that annual billing saves money"""
        basic_monthly = TierFeatures.get_tier_price(TierName.BASIC, 'monthly')
        basic_annual = TierFeatures.get_tier_price(TierName.BASIC, 'annual')
        
        # Annual should be 12 months minus 10%
        expected_annual = basic_monthly * 12 * 0.9
        
        assert basic_annual < basic_monthly * 12


class TestTierNormalization:
    """Test tier name normalization and validation"""
    
    def test_normalize_tier_names(self):
        """Test that tier names are normalized"""
        assert TierFeatures._normalize_tier_name('Free') == 'free'
        assert TierFeatures._normalize_tier_name('BASIC') == 'basic'
        assert TierFeatures._normalize_tier_name('Pro') == 'pro'
        assert TierFeatures._normalize_tier_name('elite') == 'elite'
    
    def test_normalize_legacy_names(self):
        """Test legacy tier name mapping"""
        assert TierFeatures._normalize_tier_name('standard') == 'basic'
        assert TierFeatures._normalize_tier_name('premium') == 'pro'
        assert TierFeatures._normalize_tier_name('ultimate') == 'elite'
    
    def test_invalid_tier_normalization(self):
        """Test that invalid tiers return None"""
        assert TierFeatures._normalize_tier_name('invalid') is None
        assert TierFeatures._normalize_tier_name('') is None
        assert TierFeatures._normalize_tier_name(None) is None
    
    def test_validate_tier(self):
        """Test tier validation"""
        assert TierFeatures.validate_tier(TierName.FREE)
        assert TierFeatures.validate_tier('basic')
        assert TierFeatures.validate_tier('Pro')
        
        assert not TierFeatures.validate_tier('invalid')
        assert not TierFeatures.validate_tier('')


class TestTierComparison:
    """Test tier comparison and upgrade paths"""
    
    def test_compare_tiers(self):
        """Test tier comparison"""
        # Pro > Basic
        assert TierFeatures.compare_tiers(TierName.PRO, TierName.BASIC) == 1
        
        # Basic < Pro
        assert TierFeatures.compare_tiers(TierName.BASIC, TierName.PRO) == -1
        
        # Same tiers
        assert TierFeatures.compare_tiers(TierName.PRO, TierName.PRO) == 0
    
    def test_upgrade_path_from_free(self):
        """Test upgrade options from free tier"""
        upgrades = TierFeatures.get_upgrade_path(TierName.FREE)
        
        assert TierName.BASIC in upgrades
        assert TierName.PRO in upgrades
        assert TierName.ELITE in upgrades
    
    def test_upgrade_path_from_basic(self):
        """Test upgrade options from basic"""
        upgrades = TierFeatures.get_upgrade_path(TierName.BASIC)
        
        assert TierName.BASIC not in upgrades
        assert TierName.PRO in upgrades
        assert TierName.ELITE in upgrades
    
    def test_upgrade_path_from_pro(self):
        """Test upgrade options from pro"""
        upgrades = TierFeatures.get_upgrade_path(TierName.PRO)
        
        assert TierName.ELITE in upgrades
        assert TierName.PRO not in upgrades
    
    def test_no_upgrade_from_elite(self):
        """Test no upgrades from elite"""
        upgrades = TierFeatures.get_upgrade_path(TierName.ELITE)
        
        assert len(upgrades) == 0


class TestHelperFunctions:
    """Test helper functions"""
    
    def test_get_user_tier_features(self):
        """Test getting features for user"""
        features = get_user_tier_features(TierName.PRO)
        
        assert features is not None
        assert 'price' in features
        assert 'predictions_per_day' in features
        assert features['show_reasoning'] is True
    
    def test_check_tier_access(self):
        """Test checking feature access"""
        assert check_tier_access(TierName.PRO, 'show_reasoning')
        assert check_tier_access(TierName.PRO, 'api_access') is False
        assert check_tier_access(TierName.ELITE, 'api_access')
        assert check_tier_access(TierName.FREE, 'show_reasoning') is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
