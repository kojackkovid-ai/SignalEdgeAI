import asyncio
import sys
sys.path.append('.')
from app.services.club_100_streak_service import get_club_100_streak_service

async def debug_club100():
    service = get_club_100_streak_service()

    # Test ESPN scoreboard history for NBA
    print("Testing ESPN scoreboard history for NBA...")
    player_data = await service._build_player_history_from_scoreboards("nba", days=5)  # Shorter period for testing

    print(f"Found {len(player_data)} players with historical data")

    if player_data:
        # Show sample player data
        sample_player_id = list(player_data.keys())[0]
        sample_player = player_data[sample_player_id]
        print(f"Sample player: {sample_player['name']} ({sample_player['team']})")
        print(f"Games: {len(sample_player['games'])}")
        for date, game_data in list(sample_player['games'].items())[:3]:
            print(f"  {date}: {game_data}")

    # Test today's games
    from app.services.espn_player_stats_service import get_player_stats_service
    espn_service = get_player_stats_service()
    today_games = await espn_service.get_today_games_player_stats("nba")
    print(f"\nToday's NBA games: {len(today_games)}")

    if today_games:
        today_dict = service._build_today_games_dict("nba", today_games)
        print(f"Players in today's games: {len(today_dict)}")

        # Test the scoreboard analysis
        print("\nTesting scoreboard streak analysis...")
        streaks = await service._analyze_sport_streaks_from_scoreboards("nba", 3, today_dict, today_games)
        print(f"Found {len(streaks)} streaks")

        if streaks:
            print("Sample streak:")
            print(streaks[0])

if __name__ == "__main__":
    asyncio.run(debug_club100())