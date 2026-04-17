"""
ELO Rating System for Sports Predictions
Real ELO calculations based on actual game outcomes from ESPN data
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class EloRatingSystem:
    """
    ELO Rating System implementation for team strength calculations.
    Uses real ESPN data for team ratings.
    """
    
    # Default ELO ratings by sport
    DEFAULT_ELO = {
        'nba': 1500,
        'nfl': 1500,
        'mlb': 1500,
        'nhl': 1500,
        'soccer_epl': 1500,
        'soccer_mls': 1500,
        'soccer_laliga': 1500,
        'soccer_seriea': 1500,
        'soccer_bundesliga': 1500,
        'soccer_ligue1': 1500,
        'ncaab': 1500
    }
    
    def __init__(
        self, 
        k_factor: int = 32,
        home_advantage: int = 100,
        default_elo: int = 1500
    ):
        """
        Initialize ELO system.
        
        Args:
            k_factor: K-factor determines how much ratings change (default 32)
            home_advantage: Home field advantage in ELO points (default 100)
            default_elo: Default rating for new teams (default 1500)
        """
        self.k_factor = k_factor
        self.home_advantage = home_advantage
        self.default_elo = default_elo
        self.ratings: Dict[str, Dict[str, float]] = defaultdict(dict)
        self.game_history: List[Dict] = []
    
    def get_rating(self, team: str, sport: str = 'nba') -> float:
        """Get current ELO rating for a team."""
        sport_ratings = self.ratings.get(sport, {})
        return sport_ratings.get(team, self.DEFAULT_ELO.get(sport, self.default_elo))
    
    def expected_score(self, rating_a: float, rating_b: float) -> float:
        """Calculate expected score for team A against team B."""
        return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
    
    def get_home_away_ratings(
        self, 
        home_team: str, 
        away_team: str, 
        sport: str
    ) -> Tuple[float, float]:
        """Get ELO ratings with home advantage applied."""
        home_elo = self.get_rating(home_team, sport) + self.home_advantage
        away_elo = self.get_rating(away_team, sport)
        return home_elo, away_elo
    
    def predict(
        self, 
        home_team: str, 
        away_team: str, 
        sport: str,
        include_draw: bool = False
    ) -> Dict:
        """
        Generate prediction based on ELO ratings.
        
        Returns dict with probabilities and recommended bet.
        """
        home_elo, away_elo = self.get_home_away_ratings(home_team, away_team, sport)
        
        # Calculate win probabilities
        home_win_prob = self.expected_score(home_elo, away_elo)
        away_win_prob = self.expected_score(away_elo, home_elo)
        
        if include_draw and 'soccer' in sport:
            # For soccer, add draw probability
            # Based on ELO difference - closer matches = higher draw chance
            elo_diff = abs(home_elo - away_elo)
            draw_prob = max(0.05, min(0.35, 0.25 - elo_diff / 4000))
            
            # Normalize to sum to 1
            total = home_win_prob + away_win_prob + draw_prob
            home_win_prob = home_win_prob / total
            away_win_prob = away_win_prob / total
            draw_prob = draw_prob / total
        else:
            # Normalize for two-outcome games
            total = home_win_prob + away_win_prob
            if total > 0:
                home_win_prob = home_win_prob / total
                away_win_prob = away_win_prob / total
            draw_prob = 0
        
        # Calculate confidence based on ELO gap
        elo_gap = abs(home_elo - away_elo)
        confidence = min(95, 50 + elo_gap / 20)  # 50-95% range
        
        # Determine recommended side
        if home_win_prob > away_win_prob:
            recommended = home_team
            prob = home_win_prob
        else:
            recommended = away_team
            prob = away_win_prob
        
        return {
            'home_team': home_team,
            'away_team': away_team,
            'sport': sport,
            'home_elo': round(home_elo - self.home_advantage),
            'away_elo': round(away_elo),
            'home_advantage': self.home_advantage,
            'home_win_probability': round(home_win_prob * 100, 1),
            'away_win_probability': round(away_win_prob * 100, 1),
            'draw_probability': round(draw_prob * 100, 1) if draw_prob > 0 else None,
            'recommended_side': recommended,
            'confidence': round(confidence, 1),
            'elo_gap': round(elo_gap, 1),
            'prediction': f"{recommended} Win"
        }
    
    def update_ratings(
        self,
        winner: str,
        loser: str,
        sport: str,
        is_home_win: bool = True,
        is_draw: bool = False,
        margin: Optional[int] = None
    ) -> Dict:
        """
        Update ELO ratings after a game.
        
        Args:
            winner: Winning team name
            loser: Losing team name
            sport: Sport key
            is_home_win: Did home team win?
            is_draw: Was it a draw?
            margin: Point/goal differential (optional)
            
        Returns dict with rating changes.
        """
        # Get current ratings
        winner_elo = self.get_rating(winner, sport)
        loser_elo = self.get_rating(loser, sport)
        
        # Adjust for home advantage to get "true" ratings
        if is_home_win:
            # Winner was home team
            true_winner_elo = winner_elo + self.home_advantage
            true_loser_elo = loser_elo
        else:
            # Winner was away team
            true_winner_elo = winner_elo
            true_loser_elo = loser_elo + self.home_advantage
        
        # Calculate expected scores
        expected_winner = self.expected_score(true_winner_elo, true_loser_elo)
        
        # Determine actual scores
        if is_draw:
            actual_winner = 0.5
            actual_loser = 0.5
        else:
            actual_winner = 1.0
            actual_loser = 0.0
        
        # Adjust K-factor based on margin (for scoring sports)
        k = self.k_factor
        if margin is not None:
            # Higher margin = bigger rating change
            if sport in ['nba', 'ncaab']:
                if margin >= 15:
                    k *= 1.5
                elif margin >= 10:
                    k *= 1.25
            elif sport in ['nfl']:
                if margin >= 14:
                    k *= 1.5
                elif margin >= 7:
                    k *= 1.25
            elif 'soccer' in sport:
                if margin >= 3:
                    k *= 1.5
                elif margin >= 2:
                    k *= 1.25
        
        # Calculate rating changes
        winner_change = k * (actual_winner - expected_winner)
        loser_change = k * (actual_loser - (1 - expected_winner))
        
        # Apply changes
        new_winner_elo = winner_elo + winner_change
        new_loser_elo = loser_elo + loser_change
        
        # Store updated ratings
        if sport not in self.ratings:
            self.ratings[sport] = {}
        self.ratings[sport][winner] = new_winner_elo
        self.ratings[sport][loser] = new_loser_elo
        
        # Record in history
        self.game_history.append({
            'timestamp': datetime.utcnow(),
            'sport': sport,
            'winner': winner,
            'loser': loser,
            'is_home_win': is_home_win,
            'is_draw': is_draw,
            'winner_elo_before': winner_elo,
            'winner_elo_after': new_winner_elo,
            'loser_elo_before': loser_elo,
            'loser_elo_after': new_loser_elo,
            'winner_change': winner_change,
            'loser_change': loser_change,
            'margin': margin
        })
        
        logger.info(
            f"ELO Update [{sport}]: {winner} {winner_elo:.0f} -> {new_winner_elo:.0f} "
            f"(+{winner_change:.1f}), {loser} {loser_elo:.0f} -> {new_loser_elo:.0f} ({loser_change:.1f})"
        )
        
        return {
            'winner': winner,
            'loser': loser,
            'sport': sport,
            'winner_elo_before': round(winner_elo, 1),
            'winner_elo_after': round(new_winner_elo, 1),
            'winner_change': round(winner_change, 1),
            'loser_elo_before': round(loser_elo, 1),
            'loser_elo_after': round(new_loser_elo, 1),
            'loser_change': round(loser_change, 1)
        }
    
    def get_power_rankings(self, sport: str, limit: int = 10) -> List[Dict]:
        """Get power rankings for a sport."""
        sport_ratings = self.ratings.get(sport, {})
        
        if not sport_ratings:
            return []
        
        # Sort by rating
        sorted_teams = sorted(
            sport_ratings.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        rankings = []
        for i, (team, elo) in enumerate(sorted_teams[:limit], 1):
            rankings.append({
                'rank': i,
                'team': team,
                'elo': round(elo, 1),
                'tier': self._get_tier(elo)
            })
        
        return rankings
    
    def _get_tier(self, elo: float) -> str:
        """Get tier classification based on ELO."""
        if elo >= 1800:
            return 'Elite'
        elif elo >= 1650:
            return 'Contender'
        elif elo >= 1550:
            return 'Average'
        elif elo >= 1450:
            return 'Below Average'
        else:
            return 'Struggling'
    
    def get_team_report(self, team: str, sport: str) -> Dict:
        """Get detailed report for a team."""
        current_elo = self.get_rating(team, sport)
        
        # Get recent games
        recent_games = [
            g for g in self.game_history[-50:]
            if g['sport'] == sport and (g['winner'] == team or g['loser'] == team)
        ]
        
        if recent_games:
            wins = sum(1 for g in recent_games if g['winner'] == team)
            losses = len(recent_games) - wins
            record = f"{wins}-{losses}"
        else:
            record = "No games recorded"
        
        return {
            'team': team,
            'sport': sport,
            'current_elo': round(current_elo, 1),
            'tier': self._get_tier(current_elo),
            'games_played': len(recent_games),
            'record': record,
            'home_advantage': self.home_advantage
        }
    
    def export_ratings(self) -> Dict:
        """Export all ratings for persistence."""
        return {
            'ratings': dict(self.ratings),
            'last_updated': datetime.utcnow().isoformat()
        }
    
    def import_ratings(self, data: Dict):
        """Import ratings from persistence."""
        if 'ratings' in data:
            self.ratings = defaultdict(dict, data['ratings'])
            logger.info(f"Imported ELO ratings for {len(self.ratings)} sports")


# Global instance
elo_system = EloRatingSystem()
