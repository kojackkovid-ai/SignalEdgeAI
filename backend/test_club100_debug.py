#!/usr/bin/env python3
"""Debug Club 100 unlock restrictions"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from app.models.tier_features import TierFeatures

# Test tier configuration
print("=== TIER_LIMITS CHECK ===")
from app.services.prediction_service import PredictionService
service = PredictionService()

print("PredictionService.TIER_LIMITS:")
for tier, limit in service.TIER_LIMITS.items():
    print(f"  {tier}: {limit} picks/day")

print("\n=== TierFeatures.TIER_CONFIG CHECK ===")
for tier_name in ['free', 'basic', 'pro', 'pro_plus', 'elite']:
    config = TierFeatures.get_tier_config(tier_name)
    if config:
        daily_limit = config.get('predictions_per_day')
        print(f"{tier_name}: {daily_limit} picks/day (from tier_features.py)")
    else:
        print(f"{tier_name}: NOT FOUND in tier_features.py")

print("\n=== MISMATCH CHECK ===")
for tier, service_limit in service.TIER_LIMITS.items():
    config = TierFeatures.get_tier_config(tier)
    if config:
        tier_limit = config.get('predictions_per_day')
        match = "✅" if service_limit == tier_limit else "❌ MISMATCH"
        print(f"{tier}: service={service_limit}, tier_config={tier_limit} {match}")
    else:
        print(f"{tier}: ⚠️ Not found in tier_features.py")

print("\n=== CLUB 100 ACCESS COST ===")
print("Club 100 access costs: 5 picks")
print("Testing with Free tier (5 picks/day):")
print("  - User starts day with 5 picks available")
print("  - After 0 picks used: 5 picks remaining (enough for Club 100 ✅)")
print("  - After 1 pick used: 4 picks remaining (NOT enough for Club 100 ❌)")
print("  - After 5 picks used: 0 picks remaining (NOT enough for Club 100 ❌)")
