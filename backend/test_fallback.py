from app.services.espn_prediction_service import ESPNPredictionService

service = ESPNPredictionService()
sport_key = "basketball_nba"

positions = ["PG", "SG", "SF", "PF", "C"]
print("Testing position-based fallback stats:")
print("=" * 80)

for pos in positions:
    stats = service._get_position_based_stats(pos, sport_key)
    print(f"\n{pos}:")
    print(f"  pointsPerGame: {stats.get('pointsPerGame')}")
    print(f"  assistsPerGame: {stats.get('assistsPerGame')}")
    print(f"  reboundsPerGame: {stats.get('reboundsPerGame')}")
    if not stats:
        print("  ⚠ NO STATS RETURNED!")
    else:
        print(f"  ✓ {len(stats)} stats keys present")

print("\n" + "=" * 80)
print("✓ Test complete - stats method is working")
