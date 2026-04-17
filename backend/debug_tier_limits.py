#!/usr/bin/env python3
"""Debug daily pick limit enforcement"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.tier_features import TierFeatures

# Test tier lookups
print("=== Testing Tier Configurations ===\n")

test_tiers = ['starter', 'free', 'basic', 'pro', 'pro_plus', 'elite']

for tier_name in test_tiers:
    normalized = TierFeatures._normalize_tier_name(tier_name)
    config = TierFeatures.get_tier_config(tier_name)
    
    print(f"Tier: {tier_name}")
    print(f"  Normalized: {normalized}")
    if config:
        print(f"  predictions_per_day: {config.get('predictions_per_day', 'NOT FOUND')}")
    else:
        print(f"  Config: NOT FOUND (None)")
    print()

# Now test the issue: if user has starter tier with 1 pick limit and has used 3 picks
print("\n=== Simulating User Scenario ===")
print("User tier: starter")
print("Daily pick limit: 1")
print("Daily picks used: 3")
print("Attempting to follow: 1 prediction (cost: 1 pick)")

normalized_tier = 'starter'
daily_picks_used = 3
daily_limit = 1
pick_cost = 1
picks_after = daily_picks_used + pick_cost

print(f"\nCheck logic:")
print(f"  normalized_tier = '{normalized_tier}'")
print(f"  picks_after_follow = {picks_after}")
print(f"  daily_limit = {daily_limit}")

# The check from line 996
condition = normalized_tier not in ['elite', 'pro_plus'] and picks_after > daily_limit
print(f"\nCheck expression:")
print(f"  normalized_tier not in ['elite', 'pro_plus'] = {normalized_tier not in ['elite', 'pro_plus']}")
print(f"  picks_after > daily_limit = {picks_after} > {daily_limit} = {picks_after > daily_limit}")
print(f"  Combined (AND): {condition}")
print(f"\nResult: Should {'BLOCK' if condition else 'ALLOW'} the pick")

# But the issue is: how did the user get 3 picks when limit is 1?
print("\n\n=== The Real Problem ===")
print("If daily_limit is 1, the user shouldn't have 3 picks ALREADY PICKED.")
print("This suggests the limit check in /follow is not working at all!")
print("Or the daily_picks_used count is wrong.")
