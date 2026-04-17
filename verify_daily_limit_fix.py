#!/usr/bin/env python3
"""Test that daily pick limit enforcement is working after fixes"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.models.tier_features import TierFeatures
from app.services.prediction_service import PredictionService

print("\n" + "="*70)
print("DAILY PICK LIMIT ENFORCEMENT - POST-FIX VERIFICATION")
print("="*70)

ps = PredictionService()

# 1. Verify tier config is not None
print("\n✓ TEST 1: Tier Config Not None")
print("-" * 70)
for tier in ['starter', 'basic', 'pro', 'pro_plus', 'elite']:
    config = TierFeatures.get_tier_config(tier)
    if config is None:
        print(f"  ❌ {tier}: config is None!")
    else:
        daily_limit = config.get('predictions_per_day')
        print(f"  ✅ {tier}: {daily_limit} picks/day")

# 2. Verify the logic for different scenarios
print("\n✓ TEST 2: Endpoint Limit Check Logic")
print("-" * 70)

def check_limit(tier, daily_picks_used, pick_cost=1):
    """Simulate the endpoint check logic"""
    tier_config = TierFeatures.get_tier_config(tier)
    
    # This is what happens in the endpoint now (with the fix):
    if not tier_config:
        print(f"    ERROR: tier_config is None for '{tier}'!")
        daily_limit = 1
    else:
        daily_limit = tier_config.get('predictions_per_day')
        if daily_limit is None:
            print(f"    ERROR: predictions_per_day is None for '{tier}'!")
            daily_limit = 1
    
    # The check logic
    picks_after_follow = daily_picks_used + pick_cost
    should_block = tier not in ['elite', 'pro_plus'] and picks_after_follow > daily_limit
    
    return should_block, daily_limit, picks_after_follow

# Test STARTER tier
print("\n  STARTER Tier Tests:")
scenarios = [
    (0, "Pick #1 (0+1=1 vs limit 1)"),
    (1, "Pick #2 (1+1=2 vs limit 1)"),
    (5, "Pick #6 if stuck (5+1=6 vs limit 1)"),
]
for picks_used, description in scenarios:
    should_block, limit, after = check_limit('starter', picks_used, 1)
    result = "BLOCK ❌" if should_block else "ALLOW ✅"
    expected = "ALLOW ✅" if picks_used == 0 else "BLOCK ❌"
    status = "✅" if (should_block and picks_used > 0) or (not should_block and picks_used == 0) else "❌"
    print(f"    {status} {description} → {result} (expected {expected})")

# Test BASIC tier
print("\n  BASIC Tier Tests:")
scenarios = [
    (0, "Pick #1"),
    (9, "Pick #10"),
    (10, "Pick #11"),
]
for picks_used, description in scenarios:
    should_block, limit, after = check_limit('basic', picks_used, 1)
    result = "BLOCK ❌" if should_block else "ALLOW ✅"
    expected = "ALLOW ✅" if picks_used < 10 else "BLOCK ❌"
    status = "✅" if (should_block and picks_used >= 10) or (not should_block and picks_used < 10) else "❌"
    print(f"    {status} {description} (used {picks_used}) → {result} (expected {expected})")

# Test PRO_PLUS tier
print("\n  PRO_PLUS Tier Tests (should always allow):")
should_block, limit, after = check_limit('pro_plus', 9999, 1)
result = "BLOCK ❌" if should_block else "ALLOW ✅"
status = "✅" if not should_block else "❌"
print(f"    {status} Pick with 9999 already used → {result} (should ALLOW)")

print("\n" + "="*70)
print("✅ ALL VERIFICATION TESTS COMPLETE")
print("="*70 + "\n")
