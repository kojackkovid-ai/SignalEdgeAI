"""
Test the unlock/follow flow for player props
"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.services.espn_prediction_service import ESPNPredictionService
from app.services.prediction_service import PredictionService

async def test():
    service = ESPNPredictionService()
    
    # Get upcoming NBA games
    print("Fetching NBA games...")
    games = await service.get_upcoming_games('basketball_nba')
    print(f'Found {len(games)} NBA games')
    
    if games:
        game = games[0]
        event_id = game['id']
        
        # Get player props
        print(f'Getting props for event {event_id}...')
        props = await service.get_player_props('basketball_nba', event_id)
        print(f'Got {len(props)} props')
        
        if props:
            # Test a prop
            prop = props[0]
            print(f"\nTesting prop: {prop['id']}")
            
            # Check if is_player_prop detection works
            from app.routes.predictions import is_player_prop_id
            is_prop = is_player_prop_id(prop['id'])
            print(f"is_player_prop_id result: {is_prop}")
            
            # Parse the ID parts
            parts = prop['id'].split('_')
            print(f"ID parts: {parts}")
            print(f"Number of parts: {len(parts)}")
            
            # Check if the market key would be detected
            player_prop_markets = {
                'points', 'rebounds', 'assists', 'goals', 'saves', 'hits', 'rbi', 'hr',
                'home_runs', 'pass_yards', 'rush_yards', 'rec_yards', 'passing_yards', 
                'rushing_yards', 'receiving_yards', 'three_pointers', 'steals', 'blocks',
                'shots', 'sog', 'faceoff_wins'
            }
            
            # Test different positions in the ID
            for i in range(1, len(parts) - 1):
                potential_market = '_'.join(parts[1:i+1]).lower()
                if potential_market in player_prop_markets:
                    print(f"Found market at position {i}: {potential_market}")
                    break
            else:
                print("No matching market found!")
                # Try each individual part
                for part in parts[1:-1]:
                    print(f"  Part '{part}' in markets: {part.lower() in player_prop_markets}")
            
            # Show full prop data that would be sent
            print(f"\nProp data to send:")
            print(f"  id: {prop['id']}")
            print(f"  player: {prop.get('player')}")
            print(f"  market_key: {prop.get('market_key')}")
            print(f"  point: {prop.get('point')}")
            print(f"  prediction: {prop.get('prediction')}")
            print(f"  confidence: {prop.get('confidence')}")

if __name__ == "__main__":
    asyncio.run(test())
