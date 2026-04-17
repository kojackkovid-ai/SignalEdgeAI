"""
Test script to verify all sports display correctly
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.services.espn_prediction_service import ESPNPredictionService

async def test_all_sports():
    """Test fetching games for all supported sports"""
    service = ESPNPredictionService()
    
    sports = [
        ("basketball_nba", "NBA"),
        ("basketball_ncaa", "NCAAB"),
        ("icehockey_nhl", "NHL"),
        ("americanfootball_nfl", "NFL"),
        ("soccer_epl", "EPL"),
        ("soccer_usa_mls", "MLS"),
        ("baseball_mlb", "MLB")
    ]
    
    results = {}
    
    print("=" * 70)
    print("TESTING ALL SPORTS - GAME FETCHING")
    print("=" * 70)
    
    for sport_key, sport_name in sports:
        try:
            print(f"\n🏀 Testing {sport_name} ({sport_key})...")
            games = await service.get_upcoming_games(sport_key)
            
            if games:
                results[sport_key] = {
                    "status": "✅ SUCCESS",
                    "count": len(games),
                    "sample": games[0]['matchup'] if games else "N/A"
                }
                print(f"   ✅ Found {len(games)} games")
                if games:
                    print(f"   📋 Sample: {games[0]['matchup']}")
            else:
                results[sport_key] = {
                    "status": "⚠️ NO GAMES",
                    "count": 0,
                    "sample": "N/A"
                }
                print(f"   ⚠️ No games found")
                
        except Exception as e:
            results[sport_key] = {
                "status": f"❌ ERROR: {str(e)[:50]}",
                "count": 0,
                "sample": "N/A"
            }
            print(f"   ❌ Error: {e}")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    total_sports = len(sports)
    successful = sum(1 for r in results.values() if "SUCCESS" in r["status"])
    no_games = sum(1 for r in results.values() if "NO GAMES" in r["status"])
    errors = sum(1 for r in results.values() if "ERROR" in r["status"])
    
    print(f"\nTotal Sports: {total_sports}")
    print(f"✅ Successful: {successful}")
    print(f"⚠️ No Games: {no_games}")
    print(f"❌ Errors: {errors}")
    
    print("\nDetailed Results:")
    for sport_key, result in results.items():
        print(f"  {sport_key}: {result['status']} ({result['count']} games)")
    
    await service.close()
    return results

if __name__ == "__main__":
    results = asyncio.run(test_all_sports())
    
    # Exit with error code if any sport failed
    has_errors = any("ERROR" in r["status"] for r in results.values())
    sys.exit(1 if has_errors else 0)
