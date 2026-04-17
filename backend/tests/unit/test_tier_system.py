"""
Unit Tests for Tier System and Payment Processing
Tests core tier configuration and pricing logic
"""

import pytest
from app.models.tier_features import TierFeatures


class TestTierConfiguration:
    """Test tier configuration is correct"""
    
    def test_starter_tier_has_one_pick_per_day(self):
        """Starter (free) tier should allow 1 pick/day"""
        config = TierFeatures.get_tier_config('starter')
        assert config is not None
        assert config['predictions_per_day'] == 1
        assert config['price']['monthly'] == 0
    
    def test_basic_tier_has_ten_picks_per_day(self):
        """Basic tier should allow 10 picks/day"""
        config = TierFeatures.get_tier_config('basic')
        assert config is not None
        assert config['predictions_per_day'] == 10
        assert config['price']['monthly'] == 1200  # $12
    
    def test_pro_tier_has_25_picks_per_day(self):
        """Pro tier should allow 25 picks/day"""
        config = TierFeatures.get_tier_config('pro')
        assert config is not None
        assert config['predictions_per_day'] == 25
        assert config['price']['monthly'] == 2900  # $29
    
    def test_pro_plus_tier_unlimited(self):
        """Pro Plus tier should have unlimited picks"""
        config = TierFeatures.get_tier_config('pro_plus')
        assert config is not None
        assert config['predictions_per_day'] == 9999  # Unlimited
        assert config['price']['monthly'] == 4900  # $49
    
    def test_elite_tier_unlimited(self):
        """Elite tier should have unlimited picks"""
        config = TierFeatures.get_tier_config('elite')
        assert config is not None
        assert config['predictions_per_day'] == 9999  # Unlimited
        assert config['price']['monthly'] == 9900  # $99
    
    def test_pricing_consistency(self):
        """Monthly and annual pricing should be consistent"""
        for tier_name in TierFeatures.all_tiers():
            config = TierFeatures.get_tier_config(tier_name)
            monthly = config['price']['monthly']
            annual = config['price']['annual']
            
            # Annual should roughly be 12x monthly with 2 months discount
            expected_annual = monthly * 10  # 20% annual discount
            assert annual == expected_annual, f"Pricing mismatch for {tier_name}"
    
    def test_feature_gating(self):
        """Features should be gated by tier correctly"""
        # Starter shouldn't have API access
        assert not TierFeatures.is_feature_enabled('starter', 'api_access')
        
        # Elite should have API access
        assert TierFeatures.is_feature_enabled('elite', 'api_access')
        
        # Basic shouldn't have custom models
        assert not TierFeatures.is_feature_enabled('basic', 'custom_models')
        
        # Elite should have custom models
        assert TierFeatures.is_feature_enabled('elite', 'custom_models')


class TestPricingLogic:
    """Test pricing calculation logic"""
    
    def test_get_tier_price_monthly(self):
        """Get monthly price for tier"""
        price = TierFeatures.get_tier_price('basic', 'monthly')
        assert price == 1200  # $12
    
    def test_get_tier_price_annual(self):
        """Get annual price for tier"""
        price = TierFeatures.get_tier_price('basic', 'annual')
        assert price == 12000  # $120
    
    def test_invalid_tier_returns_none(self):
        """Invalid tier should return None"""
        price = TierFeatures.get_tier_price('invalid_tier', 'monthly')
        assert price is None
    
    def test_all_tiers_have_pricing(self):
        """All tiers should have defined pricing"""
        for tier in TierFeatures.all_tiers():
            monthly = TierFeatures.get_tier_price(tier, 'monthly')
            annual = TierFeatures.get_tier_price(tier, 'annual')
            assert monthly is not None
            assert annual is not None


class TestDailyPicksLimits:
    """Test daily picks limits enforcement"""
    
    def test_get_daily_pick_limit(self):
        """Get daily picks limit for tier"""
        limit = TierFeatures.get_limit('starter', 'predictions_per_day')
        assert limit == 1
        
        limit = TierFeatures.get_limit('pro', 'predictions_per_day')
        assert limit == 25
    
    def test_unlimited_tier_limits(self):
        """Unlimited tiers should return 9999"""
        for tier in ['pro_plus', 'elite']:
            limit = TierFeatures.get_limit(tier, 'predictions_per_day')
            assert limit == 9999
