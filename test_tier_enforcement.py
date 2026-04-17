#!/usr/bin/env python3
"""Test script to verify tier enforcement is working correctly"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.models.tier_features import TierFeatures, TierName
from app.services.prediction_service import PredictionService

print("=" * 60)
print("TIER ENFORCEMENT VERIFICATION TEST")
print("=" * 60)

# Test 1: Verify TIER_LIMITS dictionary
print("\n✓ TEST 1: TIER_LIMITS Dictionary")
print("-" * 60)
ps = PredictionService()
print(f"TIER_LIMITS = {ps.TIER_LIMITS}")

expected_limits = {
    'starter': 1,
    'basic': 10,
    'pro': 25,
    'pro_plus': 9999,
    'elite': 9999
}

all_correct = True
for tier, limit in expected_limits.items():
    actual = ps.TIER_LIMITS.get(tier)
    status = "✅" if actual == limit else "❌"
    print(f"  {status} {tier:12} → {actual:4} (expected {limit})")
    if actual != limit:
        all_correct = False

# Check for unexpected 'free' tier
if 'free' in ps.TIER_LIMITS:
    print(f"  ❌ FREE tier should NOT exist in TIER_LIMITS!")
    all_correct = False
else:
    print(f"  ✅ FREE tier correctly not in TIER_LIMITS")

print(f"\nResult: {'PASS ✅' if all_correct else 'FAIL ❌'}")

# Test 2: Verify TierName enum
print("\n✓ TEST 2: TierName Enum")
print("-" * 60)
expected_tiers = ['STARTER', 'BASIC', 'PRO', 'PRO_PLUS', 'ELITE']
actual_enums = [f"{member.name}" for member in TierName]
print(f"Expected: {expected_tiers}")
print(f"Actual:   {actual_enums}")

enum_correct = set(expected_tiers) == set(actual_enums)
if enum_correct:
    print(f"\n✅ TierName enum has correct members")
    for member in TierName:
        print(f"  {member.name} = '{member.value}'")
else:
    print(f"\n❌ TierName enum mismatch!")
    missing = set(expected_tiers) - set(actual_enums)
    extra = set(actual_enums) - set(expected_tiers)
    if missing:
        print(f"  Missing: {missing}")
    if extra:
        print(f"  Extra: {extra}")

# Test 3: Verify tier configs
print("\n✓ TEST 3: Tier Configurations")
print("-" * 60)

tier_config_correct = True
for tier_value in ['starter', 'basic', 'pro', 'pro_plus', 'elite']:
    normalized = TierFeatures._normalize_tier_name(tier_value)
    config = TierFeatures.get_tier_config(tier_value)
    
    if normalized is None:
        print(f"  ❌ {tier_value:12} → NOT FOUND (normalized={normalized})")
        tier_config_correct = False
    elif config is None:
        print(f"  ❌ {tier_value:12} → Config is None")
        tier_config_correct = False
    else:
        predictions_per_day = config.get('predictions_per_day')
        print(f"  ✅ {tier_value:12} → {predictions_per_day:4} predictions/day")

# Check that 'free' tier returns None
freed = TierFeatures._normalize_tier_name('free')
if freed is None:
    print(f"  ✅ 'free' tier correctly returns None")
else:
    print(f"  ❌ 'free' tier should return None, got: {freed}")
    tier_config_correct = False

print(f"\nResult: {'PASS ✅' if tier_config_correct else 'FAIL ❌'}")

# Test 4: Simulate tier restriction logic
print("\n✓ TEST 4: Tier Restriction Logic Simulation")
print("-" * 60)

def simulate_daily_limit_check(tier, daily_picks_used, pick_cost=1):
    """Simulate the check in follow_prediction endpoint"""
    daily_limit = ps.TIER_LIMITS.get(tier, 1)
    picks_after_follow = daily_picks_used + pick_cost
    
    # Logic from follow_prediction endpoint (line 996 in predictions.py)
    should_block = tier not in ['elite', 'pro_plus'] and picks_after_follow > daily_limit
    
    return should_block, daily_limit, picks_after_follow

# Test STARTER tier (1 pick/day)
print("\n  STARTER Tier (1 pick/day):")
test_cases = [
    (0, 1, False, "Pick #1 should ALLOW"),   # 0+1=1, not > 1
    (1, 1, True, "Pick #2 should BLOCK"),     # 1+1=2, > 1 ✓
    (2, 1, True, "Pick #3 should BLOCK"),     # 2+1=3, > 1 ✓
]

starter_correct = True
for picks_used, cost, expected_block, description in test_cases:
    should_block, limit, after = simulate_daily_limit_check('starter', picks_used, cost)
    result = "BLOCK" if should_block else "ALLOW"
    expected_result = "BLOCK" if expected_block else "ALLOW"
    status = "✅" if should_block == expected_block else "❌"
    
    print(f"    {status} {picks_used}+{cost}={after} vs limit {limit} → {result} (expected {expected_result}) - {description}")
    if should_block != expected_block:
        starter_correct = False

# Test BASIC tier (10 picks/day)
print("\n  BASIC Tier (10 picks/day):")
test_cases = [
    (0, 1, False, "Pick #1 should ALLOW"),    # 0+1=1, not > 10
    (5, 1, False, "Pick #6 should ALLOW"),    # 5+1=6, not > 10
    (9, 1, False, "Pick #10 should ALLOW"),   # 9+1=10, not > 10
    (10, 1, True, "Pick #11 should BLOCK"),   # 10+1=11, > 10 ✓
]

basic_correct = True
for picks_used, cost, expected_block, description in test_cases:
    should_block, limit, after = simulate_daily_limit_check('basic', picks_used, cost)
    result = "BLOCK" if should_block else "ALLOW"
    expected_result = "BLOCK" if expected_block else "ALLOW"
    status = "✅" if should_block == expected_block else "❌"
    
    print(f"    {status} {picks_used}+{cost}={after} vs limit {limit} → {result} (expected {expected_result}) - {description}")
    if should_block != expected_block:
        basic_correct = False

# Test PRO_PLUS tier (unlimited)
print("\n  PRO_PLUS Tier (unlimited):")
for picks_used in [0, 5, 100, 9999]:
    should_block, limit, after = simulate_daily_limit_check('pro_plus', picks_used, 1)
    result = "BLOCK" if should_block else "ALLOW"
    status = "✅" if not should_block else "❌"
    print(f"    {status} {picks_used}+1={after} vs limit {limit} → {result} (should ALWAYS ALLOW for unlimited tiers)")

logic_correct = starter_correct and basic_correct

print(f"\nResult: {'PASS ✅' if logic_correct else 'FAIL ❌'}")

# Overall result
print("\n" + "=" * 60)
all_tests_pass = all_correct and enum_correct and tier_config_correct and logic_correct
print(f"OVERALL: {'ALL TESTS PASS ✅' if all_tests_pass else 'SOME TESTS FAILED ❌'}")
print("=" * 60)

sys.exit(0 if all_tests_pass else 1)
