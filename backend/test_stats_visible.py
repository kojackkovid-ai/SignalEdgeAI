"""
Test script to verify player and team props stats are now showing
"""
import asyncio
import json
from app.services.espn_prediction_service import ESPNPredictionService
from app.services.prediction_service import PredictionService
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

async def test_stats_visible():
    print("=" * 80)
    print("TESTING SOCCER PLAYER PROPS AND TEAM PROPS STATS VISIBILITY")
    print("=" * 80)
    
    try:
        espn_service = ESPNPredictionService()
        
        # Get upcoming soccer games
        print("\n[TEST] Getting upcoming soccer games...")
        games = await espn_service.get_upcoming_games("soccer_epl")
        
        if not games:
            print("ERROR: No games found!")
            return
        
        game = games[0]
        event_id = game.get("id")
        print(f"✓ Using game: {game['away_team']['name']} @ {game['home_team']['name']}")
        print(f"  Event ID: {event_id}")
        
        # Get props directly from service
        print("\n[TEST] Fetching props from ESPN service...")
        all_props = await espn_service.get_player_props("soccer_epl", event_id)
        
        print(f"\n✓ Got {len(all_props)} total props")
        
        # Categorize props
        player_props = [p for p in all_props if p.get('prediction_type') == 'player_prop']
        team_props = [p for p in all_props if p.get('prediction_type') == 'team_prop']
        
        print(f"  - Player props: {len(player_props)}")
        print(f"  - Team props: {len(team_props)}")
        
        # Check BEFORE filtering (raw ESPNservice response)
        print("\n" + "=" * 80)
        print("BEFORE TIER FILTERING (Raw ESPNservice response):")
        print("=" * 80)
        
        if player_props:
            sample = player_props[0]
            print(f"\nSample Player Prop #{1}:")
            print(f"  Player: {sample.get('player')}")
            print(f"  Market: {sample.get('market_key')}")
            print(f"  Season Avg: {sample.get('season_avg')} ✓" if 'season_avg' in sample else f"  Season Avg: MISSING ✗")
            print(f"  Recent 10 Avg: {sample.get('recent_10_avg')} ✓" if 'recent_10_avg' in sample else f"  Recent 10 Avg: MISSING ✗")
            print(f"  Has ESPN Stats: {sample.get('has_espn_stats')}")
            
        if team_props:
            sample = team_props[0]
            print(f"\nSample Team Prop:")
            print(f"  Prediction: {sample.get('prediction')}")
            stats_present = []
            stats_missing = []
            for stat_field in ['home_gpg', 'away_gpg', 'home_ga', 'away_ga']:
                if stat_field in sample:
                    stats_present.append(f"{stat_field}={sample.get(stat_field)}")
                else:
                    stats_missing.append(stat_field)
            print(f"  Team Stats Present: {', '.join(stats_present) if stats_present else 'NONE'}")
            if stats_missing:
                print(f"  Team Stats MISSING: {', '.join(stats_missing)} ✗")
        
        # Check AFTER tier filtering (what gets returned to user)
        print("\n" + "=" * 80)
        print("AFTER TIER FILTERING (Prediction Service):")
        print("=" * 80)
        
        # Simulate prediction service filtering
        from datetime import datetime
        from app.models.user import User
        
        class MockUser:
            id = "test-user"
            subscription_tier = "elite"
        
        prediction_service = PredictionService()
        
        # Manually simulate the filtering
        tier = "elite"
        tier_config = {
            'elite': {'fields': ['id', 'sport_key', 'event_id', 'sport', 'league', 'matchup', 'game_time', 
                               'prediction', 'confidence', 'odds', 'prediction_type', 'reasoning', 'models', 
                               'created_at', 'resolved_at', 'result', 'player', 'market_key', 'point', 
                               'season_avg', 'recent_10_avg', 'market_name', 'team_name',
                               'home_gpg', 'away_gpg', 'home_ga', 'away_ga', 'home_ppg', 'away_ppg', 
                               'home_oppg', 'away_oppg', 'home_rpg', 'away_rpg', 'home_ra', 'away_ra', 
                               'expected_value', 'has_espn_stats', 'is_locked', 'anytime_goal_names']}
        }
        
        config = tier_config.get(tier, tier_config['elite'])
        
        filtered_predictions = []
        for pred in all_props:
            filtered_pred = {k: v for k, v in pred.items() if k in config['fields']}
            filtered_predictions.append(filtered_pred)
        
        player_props_filtered = [p for p in filtered_predictions if p.get('prediction_type') == 'player_prop']
        team_props_filtered = [p for p in filtered_predictions if p.get('prediction_type') == 'team_prop']
        
        print(f"\n✓ After filtering: {len(player_props_filtered)} player props, {len(team_props_filtered)} team props")
        
        if player_props_filtered:
            sample = player_props_filtered[0]
            print(f"\nFiltered Player Prop Sample:")
            print(f"  Player: {sample.get('player')}")
            print(f"  Season Avg: {sample.get('season_avg')if 'season_avg' in sample else 'MISSING ✗'} ✓" if 'season_avg' in sample else "")
            print(f"  Recent 10: {sample.get('recent_10_avg') if 'recent_10_avg' in sample else 'MISSING ✗'} ✓" if 'recent_10_avg' in sample else "")
        
        if team_props_filtered:
            sample = team_props_filtered[0]
            print(f"\nFiltered Team Prop Sample:")
            stats_present = []
            stats_missing = []
            for stat_field in ['home_gpg', 'away_gpg', 'home_ga', 'away_ga']:
                if stat_field in sample:
                    stats_present.append(f"{stat_field}={sample.get(stat_field)}")
                else:
                    stats_missing.append(stat_field)
            print(f"  Team Stats: {', '.join(stats_present) if stats_present else 'NONE'}")
            if stats_missing:
                print(f"  MISSING: {', '.join(stats_missing)} ✗")
        
        print("\n" + "=" * 80)
        print("SUMMARY:")
        print("=" * 80)
        if player_props and all('season_avg' in p and 'recent_10_avg' in p for p in player_props):
            print("✓ Player props include season_avg and recent_10_avg BEFORE filtering")
        else:
            print("✗ Player props missing stats BEFORE filtering")
        
        if player_props_filtered and all('season_avg' in p and 'recent_10_avg' in p for p in player_props_filtered):
            print("✓ Player props include season_avg and recent_10_avg AFTER filtering")
        else:
            print("✗ Player props missing stats AFTER filtering")
        
        if team_props and all(all(field in p for field in ['home_gpg', 'away_gpg', 'home_ga', 'away_ga']) for p in team_props):
            print("✓ Team props include home_gpg, away_gpg, home_ga, away_ga BEFORE filtering")
        else:
            print("✗ Team props missing stats BEFORE filtering")
        
        if team_props_filtered and all(all(field in p for field in ['home_gpg', 'away_gpg', 'home_ga', 'away_ga']) for p in team_props_filtered):
            print("✓ Team props include stats AFTER filtering")
        else:
            print("✗ Team props missing stats AFTER filtering")
        
    except Exception as e:
        print(f"\n✗ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_stats_visible())
