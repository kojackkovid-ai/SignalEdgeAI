"""
Direct debug script to test what ESPNPredictionService returns
"""
import asyncio
import json
from app.services.espn_prediction_service import ESPNPredictionService

async def debug_props():
    service = ESPNPredictionService()
    
    # Test soccer props
    print("=" * 80)
    print("Testing SOCCER PLAYER PROPS AND TEAM PROPS")
    print("=" * 80)
    
    try:
        # First get a game ID
        games = await service.get_upcoming_games("soccer_epl")
        if games:
            game = games[0]
            event_id = game.get("id")
            print(f"\nUsing game: {game['away_team']['name']} @ {game['home_team']['name']} (ID: {event_id})")
            print(f"Game date: {game.get('date')}")
            
            # Get props for this game
            all_props = await service.get_player_props("soccer_epl", event_id)
            
            print(f"\n✓ TOTAL PROPS RETURNED: {len(all_props)}")
            
            if all_props:
                # Show sample of different types
                player_props = [p for p in all_props if p.get('prediction_type') == 'player_prop']
                team_props = [p for p in all_props if p.get('prediction_type') == 'team_prop']
                
                print(f"  - Player props: {len(player_props)}")
                print(f"  - Team props: {len(team_props)}")
                print(f"  - Other: {len(all_props) - len(player_props) - len(team_props)}")
                
                # Show player prop sample
                if player_props:
                    print("\n" + "=" * 80)
                    print("SAMPLE PLAYER PROP:")
                    print("=" * 80)
                    player_prop = player_props[0]
                    print(f"Keys in player prop: {list(player_prop.keys())}")
                    print(f"\nPlayer: {player_prop.get('player')}")
                    print(f"Market: {player_prop.get('market_key')}")
                    print(f"Prediction: {player_prop.get('prediction')}")
                    print(f"Confidence: {player_prop.get('confidence')}")
                    print(f"Season Avg: {player_prop.get('season_avg')}")
                    print(f"Recent 10 Avg: {player_prop.get('recent_10_avg')}")
                    print(f"\nFull player prop:")
                    print(json.dumps(player_prop, indent=2, default=str))
                
                # Show team prop sample
                if team_props:
                    print("\n" + "=" * 80)
                    print("SAMPLE TEAM PROP:")
                    print("=" * 80)
                    team_prop = team_props[0]
                    print(f"Keys in team prop: {list(team_prop.keys())}")
                    print(f"Market: {team_prop.get('market_key')}")
                    print(f"Prediction: {team_prop.get('prediction')}")
                    print(f"Confidence: {team_prop.get('confidence')}")
                    print(f"Home GPG: {team_prop.get('home_gpg')}")
                    print(f"Away GPG: {team_prop.get('away_gpg')}")
                    print(f"Home GA: {team_prop.get('home_ga')}")
                    print(f"Away GA: {team_prop.get('away_ga')}")
                    print(f"\nFull team prop:")
                    print(json.dumps(team_prop, indent=2, default=str))
            else:
                print("No props returned!")
        else:
            print("No upcoming games found for soccer_epl")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_props())
