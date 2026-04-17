import requests
import json

def test_soccer_player_props():
    try:
        # Test the soccer player props endpoint
        url = "http://127.0.0.1:8000/api/predictions/player-props"
        params = {
            "sport": "soccer_epl",
            "date": "2024-02-07"
        }
        
        print(f"Testing URL: {url}")
        print(f"Parameters: {params}")
        
        response = requests.get(url, params=params, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Total props returned: {len(data)}")
            
            # Group by prop type
            goals_props = [p for p in data if p.get('market_key') == 'goals']
            assists_props = [p for p in data if p.get('market_key') == 'assists']
            shots_props = [p for p in data if p.get('market_key') == 'shots']
            
            print(f"Goals props: {len(goals_props)}")
            print(f"Assists props: {len(assists_props)}")
            print(f"Shots props: {len(shots_props)}")
            
            # Show first few props of each type
            if goals_props:
                print(f"Sample goals prop: {goals_props[0]['player']} - {goals_props[0]['point']}")
            if assists_props:
                print(f"Sample assists prop: {assists_props[0]['player']} - {assists_props[0]['point']}")
            if shots_props:
                print(f"Sample shots prop: {shots_props[0]['player']} - {shots_props[0]['point']}")
                
        else:
            print(f"Error response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to backend server. Make sure it's running on port 8000.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_soccer_player_props()