"""
Injury Impact Analysis System
Calculates impact of player injuries on game predictions using real ESPN data
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class InjuryStatus(Enum):
    """Injury status categories"""
    OUT = "out"
    DOUBTFUL = "doubtful"
    QUESTIONABLE = "questionable"
    PROBABLE = "probable"
    HEALTHY = "healthy"
    IR = "ir"  # Injured Reserve
    NA = "n/a"


class Position(Enum):
    """Player positions by sport"""
    # Football
    QB = "qb"
    RB = "rb"
    WR = "wr"
    TE = "te"
    OL = "ol"
    LB = "lb"
    DL = "dl"
    DB = "db"
    K = "k"
    P = "p"
    
    # Basketball
    PG = "pg"
    SG = "sg"
    SF = "sf"
    PF = "pf"
    C = "c"
    
    # Baseball
    SP = "sp"
    RP = "rp"
    CL = "cl"
    CF = "cf"
    LF = "lf"
    RF = "rf"
    ONE_B = "1b"
    TWO_B = "2b"
    THREE_B = "3b"
    SS = "ss"
    
    # Hockey
    G = "g"


@dataclass
class PlayerInjury:
    """Represents a player injury"""
    player_name: str
    position: str
    status: InjuryStatus
    team: str
    is_ir: bool = False
    expected_return: Optional[str] = None
    injury_type: Optional[str] = None
    notes: Optional[str] = None


class InjuryImpactAnalyzer:
    """
    Calculate impact of injuries on team performance.
    Uses real injury data from ESPN.
    """
    
    # Position importance weights by sport (0-1 scale)
    POSITION_WEIGHTS = {
        # NFL - QB is most important
        'qb': 0.40,
        'rb': 0.18,
        'wr': 0.14,
        'te': 0.08,
        'ol': 0.08,
        'lb': 0.05,
        'dl': 0.04,
        'db': 0.03,
        
        # NBA
        'pg': 0.22,
        'sg': 0.18,
        'sf': 0.18,
        'pf': 0.20,
        'c': 0.22,
        
        # MLB
        'sp': 0.45,
        'rp': 0.15,
        'cl': 0.15,
        'cf': 0.08,
        'lf': 0.05,
        'rf': 0.05,
        '1b': 0.08,
        '2b': 0.06,
        '3b': 0.06,
        'ss': 0.07,
        
        # NHL
        'c': 0.18,
        'lw': 0.15,
        'rw': 0.15,
        'd': 0.20,
        'g': 0.32
    }
    
    # Status impact multipliers
    STATUS_MULTIPLIERS = {
        'out': 1.0,
        'ir': 1.0,
        'doubtful': 0.85,
        'questionable': 0.50,
        'probable': 0.20,
        'healthy': 0.0,
        'n/a': 0.0
    }
    
    def __init__(self):
        """Initialize injury analyzer"""
        self.injury_cache: Dict[str, List[PlayerInjury]] = {}
        self.last_update: Optional[datetime] = None
    
    def parse_injury_from_espn(self, injury_data: Dict[str, Any], team: str) -> Optional[PlayerInjury]:
        """
        Parse ESPN injury data into PlayerInjury object.
        
        ESPN typically returns data like:
        {
            "athlete": {"name": "Patrick Mahomes"},
            "position": {"abbreviation": "QB"},
            "status": {"description": "Out"},  # or "injury"
            "type": {"description": "Ankle"}
        }
        """
        try:
            # Extract player name
            athlete = injury_data.get('athlete', {})
            player_name = athlete.get('displayName', athlete.get('fullName', 'Unknown'))
            
            if not player_name or player_name == 'Unknown':
                return None
            
            # Extract position
            position_data = injury_data.get('position', {})
            position = position_data.get('abbreviation', '').lower()
            
            # Extract status
            status_text = ''
            status_obj = injury_data.get('status', {})
            injury_obj = injury_data.get('injury', {})
            
            if status_obj:
                status_text = status_obj.get('description', '').lower()
            if injury_obj:
                status_text = injury_obj.get('description', '').lower()
            
            # Map to enum
            status = self._parse_status(status_text)
            
            # Check for IR
            is_ir = 'ir' in status_text.lower() or 'injured reserve' in status_text.lower()
            
            # Get injury type
            injury_type = injury_obj.get('type', {}).get('description') if injury_obj else None
            
            return PlayerInjury(
                player_name=player_name,
                position=position,
                status=status,
                team=team,
                is_ir=is_ir,
                injury_type=injury_type
            )
            
        except Exception as e:
            logger.warning(f"Error parsing injury data: {e}")
            return None
    
    def _parse_status(self, status_text: str) -> InjuryStatus:
        """Parse status text to enum"""
        status_text = status_text.lower()
        
        if 'out' in status_text or 'ir' in status_text:
            return InjuryStatus.OUT
        elif 'doubtful' in status_text:
            return InjuryStatus.DOUTBFUL
        elif 'questionable' in status_text:
            return InjuryStatus.QUESTIONABLE
        elif 'probable' in status_text:
            return InjuryStatus.PROBABLE
        elif 'healthy' in status_text:
            return InjuryStatus.HEALTHY
        else:
            return InjuryStatus.NA
    
    def calculate_team_injury_impact(
        self,
        injuries: List[PlayerInjury]
    ) -> Dict[str, Any]:
        """
        Calculate total injury impact for a team.
        
        Returns impact score and detailed breakdown.
        """
        total_impact = 0.0
        impact_details = []
        
        for injury in injuries:
            if injury.status in [InjuryStatus.OUT, InjuryStatus.IR]:
                # Get position weight
                position = injury.position.lower()
                weight = self.POSITION_WEIGHTS.get(position, 0.10)
                
                # Apply status multiplier
                status_mult = self.STATUS_MULTIPLIERS.get(injury.status.value, 1.0)
                
                # IR means longer absence = more impact
                if injury.is_ir:
                    impact = weight * status_mult * 1.0
                else:
                    impact = weight * status_mult
                
                total_impact += impact
                
                impact_details.append({
                    'player': injury.player_name,
                    'position': injury.position,
                    'status': injury.status.value,
                    'injury_type': injury.injury_type,
                    'position_weight': weight,
                    'impact_score': round(impact, 3),
                    'impact_percent': f"{impact*100:.1f}%"
                })
        
        # Determine recommendation based on impact
        if total_impact >= 0.35:
            recommendation = 'fade'
            confidence = 'HIGH'
            reason = f"Severe impact: {total_impact*100:.0f}% expected performance reduction"
        elif total_impact >= 0.20:
            recommendation = 'caution'
            confidence = 'MEDIUM'
            reason = f"Moderate impact: {total_impact*100:.0f}% expected performance reduction"
        elif total_impact >= 0.10:
            recommendation = 'slight_negative'
            confidence = 'LOW'
            reason = f"Minor impact: {total_impact*100:.0f}% expected performance reduction"
        else:
            recommendation = 'neutral'
            confidence = 'LOW'
            reason = "Minimal injury impact expected"
        
        return {
            'total_impact_score': round(total_impact, 3),
            'impact_percent': f"{total_impact*100:.1f}%",
            'details': impact_details,
            'recommendation': recommendation,
            'confidence': confidence,
            'reason': reason,
            'affected_players': len(impact_details),
            'key_players_out': len([d for d in impact_details if d['position_weight'] >= 0.20])
        }
    
    def get_key_player_impact(
        self,
        injuries: List[PlayerInjury],
        key_players: List[str]
    ) -> Dict[str, Any]:
        """
        Check impact of injuries to key players specifically.
        
        Args:
            injuries: List of injuries
            key_players: List of important players to track
            
        Returns:
            Dict with key player impact analysis
        """
        key_impacts = []
        
        for injury in injuries:
            # Check if this is a key player
            is_key = any(
                key.lower() in injury.player_name.lower() 
                for key in key_players
            )
            
            if is_key:
                weight = self.POSITION_WEIGHTS.get(
                    injury.position.lower(),
                    0.15
                )
                
                status_mult = self.STATUS_MULTIPLIERS.get(injury.status.value, 1.0)
                impact = weight * status_mult
                
                key_impacts.append({
                    'player': injury.player_name,
                    'position': injury.position,
                    'status': injury.status.value,
                    'injury_type': injury.injury_type,
                    'impact': f"{impact*100:.1f}%",
                    'is_ir': injury.is_ir
                })
        
        if key_impacts:
            return {
                'key_players_affected': len(key_impacts),
                'details': key_impacts,
                'message': f"⚠️ {len(key_impacts)} KEY PLAYERS out - significant impact expected",
                'severity': 'HIGH' if len(key_impacts) >= 2 else 'MEDIUM'
            }
        
        return {
            'key_players_affected': 0,
            'details': [],
            'message': "✅ All key players available",
            'severity': 'NONE'
        }
    
    def compare_injury_impact(
        self,
        home_injuries: List[PlayerInjury],
        away_injuries: List[PlayerInjury]
    ) -> Dict[str, Any]:
        """
        Compare injury impact between two teams.
        
        Returns analysis for betting purposes.
        """
        home_impact = self.calculate_team_injury_impact(home_injuries)
        away_impact = self.calculate_team_injury_impact(away_injuries)
        
        impact_diff = home_impact['total_impact_score'] - away_impact['total_impact_score']
        
        # Determine which team benefits
        if abs(impact_diff) < 0.05:
            comparison = 'even'
            betting_signal = 'neutral'
            message = "Both teams have similar injury situations"
        elif impact_diff > 0:
            comparison = 'away_better'
            betting_signal = 'away'
            message = f"Away team has less injury impact ({abs(impact_diff)*100:.0f}% advantage)"
        else:
            comparison = 'home_better'
            betting_signal = 'home'
            message = f"Home team has less injury impact ({abs(impact_diff)*100:.0f}% advantage)"
        
        return {
            'home_impact': home_impact,
            'away_impact': away_impact,
            'impact_difference': round(impact_diff, 3),
            'comparison': comparison,
            'betting_signal': betting_signal,
            'message': message,
            'confidence': 'HIGH' if abs(impact_diff) >= 0.15 else 'MEDIUM' if abs(impact_diff) >= 0.08 else 'LOW'
        }
    
    def generate_injury_report(
        self,
        team: str,
        sport: str,
        injuries: List[PlayerInjury]
    ) -> str:
        """
        Generate human-readable injury report for display.
        """
        if not injuries:
            return f"✅ {team}: No significant injuries reported."
        
        impact = self.calculate_team_injury_impact(injuries)
        
        report_lines = [
            f"🏥 {team} Injury Report",
            f"Overall Impact: {impact['impact_percent']} ({impact['recommendation'].replace('_', ' ').title()})",
            f"Players Affected: {impact['affected_players']}"
        ]
        
        if impact['key_players_out'] > 0:
            report_lines.append(f"⚠️ Key Players Out: {impact['key_players_out']}")
        
        # List key injuries
        critical = [d for d in impact['details'] if d['position_weight'] >= 0.15]
        if critical:
            report_lines.append("\n🔴 Critical:")
            for c in critical[:3]:  # Top 3
                report_lines.append(f"  • {c['player']} ({c['position']}) - {c['status']}")
        
        moderate = [d for d in impact['details'] if 0.05 <= d['position_weight'] < 0.15]
        if moderate:
            report_lines.append("\n🟡 Moderate:")
            for m in moderate[:3]:
                report_lines.append(f"  • {m['player']} ({m['position']}) - {m['status']}")
        
        return "\n".join(report_lines)


# Global instance
injury_analyzer = InjuryImpactAnalyzer()
