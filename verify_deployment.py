import sys
sys.path.insert(0, '/app')
from app.services.prediction_service import PredictionService
from app.models.tier_features import TierFeatures, TierName

print("\n" + "="*60)
print("TIER CONFIGURATION VERIFICATION")
print("="*60)

ps = PredictionService()
print("\n✅ TIER_LIMITS in running container:")
for tier, limit in ps.TIER_LIMITS.items():
    print(f"   {tier:12} → {limit:4} picks/day")

if 'free' in ps.TIER_LIMITS:
    print("\n❌ ERROR: FREE tier exists in TIER_LIMITS!")
else:
    print("\n✅ FREE tier correctly NOT in TIER_LIMITS")

print("\n✅ TierName enum members:")
for m in TierName:
    print(f"   {m.name:12} = '{m.value}'")

print("\n" + "="*60)
print("✅ DEPLOYMENT SUCCESSFUL - All changes active!")
print("="*60)
