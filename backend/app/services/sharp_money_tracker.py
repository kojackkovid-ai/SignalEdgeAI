"""
Sharp Money Tracking System
Detects reverse line movement and sharp betting indicators
Uses real betting data when available, ESPN data as primary source
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class SharpMoneyTracker:
    """
    Track line movements and detect sharp betting indicators.
    Uses ESPN data as primary source for game analysis.
    """
    
    def __init__(self):
        """Initialize sharp money tracker"""
        self.line_history: Dict[str, List[Dict]] = defaultdict(list)
        self.public_betting: Dict[str, Dict] = {}
        self.movement_alerts: List[Dict] = []
    
    def _make_key(self, game_id: str, line_type: str = 'h2h') -> str:
        """Create unique key for line tracking"""
        return f"{game_id}_{line_type}"
    
    def _odds_to_probability(self, odds: int) -> float:
        """Convert American odds to implied probability"""
        if odds > 0:
            return 100 / (odds + 100)
        else:
            return abs(odds) / (abs(odds) + 100)
    
    def _probability_to_odds(self, prob: float) -> int:
        """Convert probability to American odds"""
        if prob >= 0.5:
            return int((prob / (1 - prob)) * 100)
        else:
            return int(-((1 - prob) / prob) * 100)
    
    def record_line(
        self,
        game_id: str,
        sport: str,
        home_team: str,
        away_team: str,
        home_odds: int,
        away_odds: int,
        total_line: Optional[float] = None,
        spread: Optional[float] = None,
        sportsbook: str = 'consensus',
        timestamp: Optional[datetime] = None
    ):
        """
        Record a line from a sportsbook.
        
        Args:
            game_id: Unique game identifier
            sport: Sport key
            home_team: Home team name
            away_team: Away team name
            home_odds: American odds for home team
            away_odds: American odds for away team
            total_line: Over/Under total
            spread: Point spread
            sportsbook: Sportsbook source
            timestamp: When line was recorded
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        key = self._make_key(game_id)
        
        line_data = {
            'timestamp': timestamp,
            'sportsbook': sportsbook,
            'sport': sport,
            'home_team': home_team,
            'away_team': away_team,
            'home_odds': home_odds,
            'away_odds': away_odds,
            'home_implied': self._odds_to_probability(home_odds),
            'away_implied': self._odds_to_probability(away_odds),
            'total_line': total_line,
            'spread': spread,
            'key': key
        }
        
        self.line_history[key].append(line_data)
        
        # Keep only last 48 hours
        cutoff = datetime.utcnow() - timedelta(hours=48)
        self.line_history[key] = [
            l for l in self.line_history[key]
            if l['timestamp'] >= cutoff
        ]
        
        logger.debug(f"Recorded line: {game_id} {home_team} {home_odds} vs {away_team} {away_odds}")
    
    def analyze_line_movement(
        self,
        game_id: str,
        line_type: str = 'h2h'
    ) -> Dict[str, Any]:
        """
        Analyze line movement for sharp money indicators.
        
        Returns analysis of line movement patterns.
        """
        key = self._make_key(game_id, line_type)
        history = self.line_history.get(key, [])
        
        if len(history) < 2:
            return {
                'indicator': 'insufficient_data',
                'message': 'Not enough line movement data available',
                'confidence': 'LOW'
            }
        
        # Get opening and current lines
        opening = history[0]
        current = history[-1]
        
        # Calculate movement
        home_movement = current['home_odds'] - opening['home_odds']
        away_movement = current['away_odds'] - opening['away_odds']
        total_movement = abs(home_movement) + abs(away_movement)
        
        # Detect sharp money indicators
        
        # 1. Reverse Line Movement (sharpest indicator)
        # Line moved opposite to public betting (if we had public data)
        if opening['home_odds'] != current['home_odds']:
            # Line has moved
            if home_movement < 0 and opening['home_implied'] > current['home_implied']:
                # Home odds decreased (became more favorable) despite being favored
                # This often indicates sharp money
                return {
                    'indicator': 'reverse_line_movement',
                    'type': 'sharp_money',
                    'confidence': 'HIGH',
                    'message': f'Line moved from {opening["home_odds"]} to {current["home_odds"]} - sharp money likely',
                    'direction': 'home',
                    'original_odds': opening['home_odds'],
                    'current_odds': current['home_odds'],
                    'movement': home_movement,
                    'probability_shift': round(
                        (current['home_implied'] - opening['home_implied']) * 100, 1
                    )
                }
            elif home_movement > 0 and opening['home_implied'] < current['home_implied']:
                return {
                    'indicator': 'reverse_line_movement',
                    'type': 'sharp_money',
                    'confidence': 'HIGH',
                    'message': f'Line moved from {opening["home_odds"]} to {current["home_odds"]} - sharp money likely',
                    'direction': 'away',
                    'original_odds': opening['away_odds'],
                    'current_odds': current['away_odds'],
                    'movement': away_movement,
                    'probability_shift': round(
                        (current['away_implied'] - opening['away_implied']) * 100, 1
                    )
                }
        
        # 2. Steam Move (rapid line movement)
        if total_movement >= 150:  # Major line move (150+ cents)
            direction = 'over' if current.get('total_line', 0) > opening.get('total_line', 0) else 'under'
            return {
                'indicator': 'steam_move',
                'type': 'sharp_money',
                'confidence': 'MEDIUM-HIGH',
                'message': f'Heavy betting causing {direction} line movement of {total_movement} cents',
                'direction': direction,
                'movement': total_movement,
                'original_total': opening.get('total_line'),
                'current_total': current.get('total_line')
            }
        
        # 3. Significant spread movement
        if opening.get('spread') and current.get('spread'):
            spread_movement = abs(current['spread'] - opening['spread'])
            if spread_movement >= 2.5:
                return {
                    'indicator': 'spread_movement',
                    'type': 'sharp_money',
                    'confidence': 'MEDIUM',
                    'message': f'Spread moved {spread_movement} points - significant betting action',
                    'original_spread': opening['spread'],
                    'current_spread': current['spread'],
                    'movement': spread_movement
                }
        
        # 4. Consensus / Standard movement
        return {
            'indicator': 'normal_movement',
            'type': 'standard',
            'confidence': 'LOW',
            'message': 'No sharp betting indicators detected',
            'movement': total_movement,
            'current_line': {
                'home': current['home_odds'],
                'away': current['away_odds']
            }
        }
    
    def get_consensus_line(self, game_id: str) -> Optional[Dict]:
        """
        Get consensus (average) line from all recorded sportsbooks.
        """
        key = self._make_key(game_id)
        history = self.line_history.get(key, [])
        
        if not history:
            return None
        
        # Get latest lines from each sportsbook
        sportsbooks = {}
        for line in history:
            sb = line['sportsbook']
            if sb not in sportsbooks:
                sportsbooks[sb] = line
        
        if not sportsbooks:
            return None
        
        # Calculate average (consensus)
        avg_home_odds = sum(l['home_odds'] for l in sportsbooks.values()) / len(sportsbooks)
        avg_away_odds = sum(l['away_odds'] for l in sportsbooks.values()) / len(sportsbooks)
        
        return {
            'game_id': game_id,
            'sportsbook_count': len(sportsbooks),
            'home_odds': round(avg_home_odds),
            'away_odds': round(avg_away_odds),
            'home_implied_prob': round(self._odds_to_probability(round(avg_home_odds)) * 100, 1),
            'away_implied_prob': round(self._odds_to_probability(round(avg_away_odds)) * 100, 1),
            'consensus_favorite': 'home' if avg_home_odds < avg_away_odds else 'away',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def record_public_betting(
        self,
        game_id: str,
        home_percent: float,
        away_percent: float,
        handle_home: Optional[float] = None,
        handle_away: Optional[float] = None,
        total_over_percent: Optional[float] = None,
        total_under_percent: Optional[float] = None
    ):
        """
        Record public betting percentages.
        
        Args:
            game_id: Game identifier
            home_percent: % of bets on home team
            away_percent: % of bets on away team
            handle_home: $ amount on home (optional)
            handle_away: $ amount on away (optional)
            total_over_percent: % on over (optional)
            total_under_percent: % on under (optional)
        """
        self.public_betting[game_id] = {
            'timestamp': datetime.utcnow(),
            'home_percent': home_percent,
            'away_percent': away_percent,
            'handle_home': handle_home,
            'handle_away': handle_away,
            'total_over_percent': total_over_percent,
            'total_under_percent': total_under_percent
        }
    
    def analyze_public_betting(self, game_id: str) -> Dict:
        """
        Analyze public betting percentages and provide recommendations.
        
        Profading public is usually +EV long term.
        """
        data = self.public_betting.get(game_id)
        
        if not data:
            return {
                'indicator': 'no_data',
                'message': 'No public betting data available',
                'confidence': 'LOW'
            }
        
        # Determine which side is public
        home_heavy = data['home_percent'] >= 65
        away_heavy = data['away_percent'] >= 65
        over_heavy = data.get('total_over_percent', 50) >= 65
        under_heavy = data.get('total_under_percent', 50) >= 65
        
        recommendations = []
        
        # Moneyline recommendations
        if home_heavy:
            recommendations.append({
                'type': 'moneyline',
                'fade_public': True,
                'public_side': 'home',
                'public_percent': data['home_percent'],
                'recommendation': 'fade_home',
                'reason': f'{data["home_percent"]}% of bets on home - contrarian play',
                'confidence': 'HIGH' if data['home_percent'] >= 75 else 'MEDIUM'
            })
        elif away_heavy:
            recommendations.append({
                'type': 'moneyline',
                'fade_public': True,
                'public_side': 'away',
                'public_percent': data['away_percent'],
                'recommendation': 'fade_away',
                'reason': f'{data["away_percent"]}% of bets on away - contrarian play',
                'confidence': 'HIGH' if data['away_percent'] >= 75 else 'MEDIUM'
            })
        
        # Total recommendations
        if over_heavy:
            recommendations.append({
                'type': 'total',
                'fade_public': True,
                'public_side': 'over',
                'public_percent': data.get('total_over_percent', 0),
                'recommendation': 'under',
                'reason': f'{data.get("total_over_percent", 0)}% on over - fade the public',
                'confidence': 'HIGH' if data.get('total_over_percent', 0) >= 75 else 'MEDIUM'
            })
        elif under_heavy:
            recommendations.append({
                'type': 'total',
                'fade_public': True,
                'public_side': 'under',
                'public_percent': data.get('total_under_percent', 0),
                'recommendation': 'over',
                'reason': f'{data.get("total_under_percent", 0)}% on under - fade the public',
                'confidence': 'HIGH' if data.get('total_under_percent', 0) >= 75 else 'MEDIUM'
            })
        
        if not recommendations:
            return {
                'indicator': 'balanced',
                'message': 'Betting evenly split - no clear edge',
                'confidence': 'LOW'
            }
        
        return {
            'indicator': 'public_betting_edge',
            'recommendations': recommendations,
            'data': data
        }
    
    def generate_betting_report(
        self,
        game_id: str,
        home_team: str,
        away_team: str
    ) -> Dict:
        """
        Generate comprehensive betting report for a game.
        
        Combines line movement and public betting analysis.
        """
        report = {
            'game_id': game_id,
            'home_team': home_team,
            'away_team': away_team,
            'generated_at': datetime.utcnow().isoformat(),
            'line_movement': self.analyze_line_movement(game_id),
            'consensus_line': self.get_consensus_line(game_id),
            'public_betting': self.analyze_public_betting(game_id)
        }
        
        # Generate combined recommendation
        recommendations = []
        
        # From line movement
        lm = report['line_movement']
        if lm.get('type') == 'sharp_money':
            recommendations.append({
                'source': 'line_movement',
                'recommendation': lm.get('direction', 'unknown'),
                'confidence': lm.get('confidence', 'LOW'),
                'reason': lm.get('message', '')
            })
        
        # From public betting
        pb = report['public_betting']
        if pb.get('indicator') == 'public_betting_edge':
            for rec in pb.get('recommendations', []):
                recommendations.append({
                    'source': 'public_betting',
                    'recommendation': rec.get('recommendation', ''),
                    'confidence': rec.get('confidence', 'LOW'),
                    'reason': rec.get('reason', '')
                })
        
        report['combined_recommendations'] = recommendations
        
        # Determine best bet
        if recommendations:
            # Find highest confidence sharp money indicator
            best = max(
                recommendations,
                key=lambda x: {'HIGH': 3, 'MEDIUM-HIGH': 2.5, 'MEDIUM': 2, 'LOW': 1}.get(
                    x.get('confidence', 'LOW'), 0
                )
            )
            report['best_bet'] = best
        else:
            report['best_bet'] = None
        
        return report
    
    def clear_old_data(self, hours: int = 48):
        """Clear data older than specified hours"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        # Clear line history
        for key in list(self.line_history.keys()):
            self.line_history[key] = [
                l for l in self.line_history[key]
                if l['timestamp'] >= cutoff
            ]
            if not self.line_history[key]:
                del self.line_history[key]
        
        # Clear public betting
        for game_id in list(self.public_betting.keys()):
            if self.public_betting[game_id]['timestamp'] < cutoff:
                del self.public_betting[game_id]
        
        logger.info(f"Cleared sharp money data older than {hours} hours")


# Global instance
sharp_money_tracker = SharpMoneyTracker()
