import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class InjuryImpactService:
    """
    Service to quantify the impact of injuries on team performance
    """
    
    # Approximate "Value Over Replacement" impact for star players by sport
    # Represents % drop in team efficiency/win probability
    IMPACT_WEIGHTS = {
        'basketball_nba': {
            'star': 0.15,      # LeBron/Giannis level
            'starter': 0.08,   # Solid starter
            'rotation': 0.03   # Key bench piece
        },
        'americanfootball_nfl': {
            'QB': 0.20,        # Starting QB
            'WR1': 0.05,
            'LT': 0.04,
            'EDGE': 0.04,
            'CB1': 0.03
        },
        'baseball_mlb': {
            'SP1': 0.12,       # Ace pitcher (for that game)
            'MVP_Bat': 0.05,   # Top hitter
            'C': 0.03
        }
    }

    def calculate_injury_impact(self, sport_key: str, injuries: List[str], team_roster: List[Dict]) -> float:
        """
        Calculate the total negative impact score (0.0 to 1.0) for a team's injuries
        """
        total_impact = 0.0
        
        try:
            # Parse injuries list (assuming format "Player Name (Status)")
            injured_names = [inj.split(' (')[0] for inj in injuries]
            
            for player_name in injured_names:
                # Find player in roster to get role/position
                player = next((p for p in team_roster if p['displayName'] == player_name), None)
                
                if player:
                    impact = self._get_player_impact(sport_key, player)
                    total_impact += impact
                else:
                    # Fallback if player not found in roster (assume rotation player)
                    total_impact += 0.02
            
            # Cap impact at reasonable level (e.g., team can't be >50% worse usually)
            return min(total_impact, 0.50)
            
        except Exception as e:
            logger.error(f"Error calculating injury impact: {e}")
            return 0.0

    def _get_player_impact(self, sport_key: str, player: Dict) -> float:
        """Determine specific player's impact value"""
        
        # Check if "Star" (heuristic based on stats if available, or predefined list)
        is_star = self._is_star_player(player)
        position = player.get('position', {}).get('abbreviation', 'UNK')
        
        if 'nba' in sport_key:
            if is_star: return self.IMPACT_WEIGHTS['basketball_nba']['star']
            if player.get('starter', False): return self.IMPACT_WEIGHTS['basketball_nba']['starter']
            return self.IMPACT_WEIGHTS['basketball_nba']['rotation']
            
        elif 'nfl' in sport_key:
            if position == 'QB' and is_star: return self.IMPACT_WEIGHTS['americanfootball_nfl']['QB']
            if position == 'QB': return 0.10 # Average QB
            if is_star: return 0.05
            return 0.02
            
        return 0.02 # Default

    def _is_star_player(self, player: Dict) -> bool:
        """Heuristic to check if player is a star"""
        # In real app, check against a database of WAR/PER/Rating
        # Here we might check if they are a team leader
        return False # Placeholder
