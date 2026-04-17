"""
Historical Data Generator for ML Training
Creates synthetic but realistic training data for initial model training
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from typing import List, Dict, Any

class TrainingDataGenerator:
    """Generate realistic training data for sports predictions"""
    
    def __init__(self):
        self.teams = {
            'NBA': ['Lakers', 'Warriors', 'Celtics', 'Heat', 'Nets', 'Bucks', 'Suns', 'Nuggets'],
            'NFL': ['Chiefs', 'Bills', 'Eagles', 'Cowboys', 'Ravens', 'Bengals', 'Packers', '49ers'],
            'MLB': ['Dodgers', 'Yankees', 'Astros', 'Mets', 'Braves', 'Padres', 'Phillies', 'Blue Jays'],
            'NHL': ['Avalanche', 'Lightning', 'Hurricanes', 'Rangers', 'Maple Leafs', 'Oilers', 'Panthers', 'Wild']
        }
        
    def generate_historical_games(self, sport: str = 'NBA', num_games: int = 5000) -> pd.DataFrame:
        """Generate historical game data for training"""
        games = []
        
        for i in range(num_games):
            # Random teams
            teams = random.sample(self.teams[sport], 2)
            home_team = teams[0]
            away_team = teams[1]
            
            # Generate realistic stats
            home_elo = random.randint(1400, 1600)
            away_elo = random.randint(1400, 1600)
            
            # Recent form (last 5 games)
            home_form = random.uniform(0.2, 0.9)
            away_form = random.uniform(0.2, 0.9)
            
            # Head-to-head history
            h2h_home_winrate = random.uniform(0.1, 0.9)
            h2h_away_winrate = 1 - h2h_home_winrate
            
            # Injury impact (0-1 scale)
            home_injury_impact = random.uniform(0, 0.4)
            away_injury_impact = random.uniform(0, 0.4)
            
            # Market odds (implied probability)
            market_home_prob = random.uniform(0.3, 0.7)
            market_away_prob = 1 - market_home_prob
            
            # Calculate actual outcome based on factors
            home_advantage = 0.1
            home_strength = (home_elo / 1500) + home_form + home_advantage - (away_injury_impact * 0.2)
            away_strength = (away_elo / 1500) + away_form - (home_injury_impact * 0.2)
            
            # Add some randomness
            home_final = home_strength + random.uniform(-0.1, 0.1)
            away_final = away_strength + random.uniform(-0.1, 0.1)
            
            actual_home_win = 1 if home_final > away_final else 0
            
            # Create feature vector
            game_data = {
                # Team strength
                'home_elo': home_elo,
                'away_elo': away_elo,
                
                # Recent form
                'home_form': home_form,
                'away_form': away_form,
                
                # Home advantage
                'home_advantage': home_advantage,
                
                # Head-to-head
                'h2h_home_winrate': h2h_home_winrate,
                'h2h_away_winrate': h2h_away_winrate,
                
                # Injuries
                'home_injury_impact': home_injury_impact,
                'away_injury_impact': away_injury_impact,
                
                # Market data
                'market_home_prob': market_home_prob,
                'market_away_prob': market_away_prob,
                
                # Temporal
                'day_of_week': random.randint(0, 6),
                'season_progress': random.uniform(0, 1),
                'is_playoffs': random.choice([0, 1]) if random.random() < 0.2 else 0,
                
                # Target variable
                'target': actual_home_win
            }
            
            games.append(game_data)
        
        return pd.DataFrame(games)
    
    def generate_player_props_data(self, num_records: int = 3000) -> pd.DataFrame:
        """Generate player prop training data"""
        props = []
        
        positions = ['PG', 'SG', 'SF', 'PF', 'C']
        
        for i in range(num_records):
            # Player stats
            season_avg = random.uniform(5, 35)  # Points, rebounds, assists, etc.
            recent_form = random.uniform(0.3, 1.0)
            position = random.choice(positions)
            
            # Opponent defense
            opponent_defense_rating = random.uniform(0.7, 1.3)
            
            # Line setting
            line = season_avg * random.uniform(0.8, 1.2)
            
            # Game context
            minutes_played = random.uniform(20, 40)
            usage_rate = random.uniform(15, 35)
            
            # Calculate actual outcome
            base_performance = season_avg * recent_form * (minutes_played / 36) * opponent_defense_rating
            actual_performance = base_performance + random.uniform(-3, 3)
            
            over_hit = 1 if actual_performance > line else 0
            
            prop_data = {
                'season_avg': season_avg,
                'recent_form': recent_form,
                'opponent_defense_rating': opponent_defense_rating,
                'line': line,
                'minutes_played': minutes_played,
                'usage_rate': usage_rate,
                'position': position,
                'day_of_week': random.randint(0, 6),
                'is_home': random.choice([0, 1]),
                'target': over_hit
            }
            
            props.append(prop_data)
        
        return pd.DataFrame(props)
    
    def save_training_data(self, data: pd.DataFrame, filename: str):
        """Save training data to CSV"""
        data.to_csv(f'ml-models/data/{filename}', index=False)
        print(f"Saved {len(data)} records to {filename}")

# Generate initial training data
if __name__ == "__main__":
    generator = TrainingDataGenerator()
    
    # Generate game data for multiple sports
    for sport in ['NBA', 'NFL', 'MLB', 'NHL']:
        print(f"Generating training data for {sport}...")
        game_data = generator.generate_historical_games(sport, 2000)
        generator.save_training_data(game_data, f'{sport.lower()}_games_training.csv')
    
    # Generate player prop data
    print("Generating player prop training data...")
    prop_data = generator.generate_player_props_data(3000)
    generator.save_training_data(prop_data, 'player_props_training.csv')
    
    print("Training data generation complete!")