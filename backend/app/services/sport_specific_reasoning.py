"""
Sport-Specific Reasoning Engine
Generates unique, detailed, data-driven reasoning for each sport and each game.
NO generic templates - every explanation is built from actual game data.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import httpx

logger = logging.getLogger(__name__)


class SportSpecificReasoningEngine:
    """
    Generates truly unique reasoning for each sport based on actual game data.
    No cookie-cutter templates - every analysis is game-specific.
    """
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)
        self.espn_base = "https://site.api.espn.com/apis/site/v2/sports"
        
        # Sport-specific stat priorities
        self.stat_priorities = {
            'basketball_nba': [
                'points_per_game', 'points_allowed', 'field_goal_pct', 
                'three_point_pct', 'free_throw_pct', 'rebounds_per_game',
                'assists_per_game', 'turnovers_per_game', 'pace_factor'
            ],
            'icehockey_nhl': [
                'goals_per_game', 'goals_allowed', 'shots_per_game',
                'power_play_pct', 'penalty_kill_pct', 'save_percentage',
                'faceoff_win_pct', 'blocked_shots_per_game'
            ],
            'americanfootball_nfl': [
                'points_per_game', 'points_allowed', 'passing_yards_per_game',
                'rushing_yards_per_game', 'red_zone_efficiency', 'turnover_differential',
                'third_down_pct', 'time_of_possession'
            ],
            'baseball_mlb': [
                'runs_per_game', 'runs_allowed', 'batting_average', 'ops',
                'era', 'whip', 'strikeouts_per_nine', 'bullpen_era',
                'quality_starts_pct', 'fielding_pct'
            ],
            'soccer_epl': [
                'goals_per_game', 'goals_allowed', 'possession_pct',
                'shots_on_target_per_game', 'expected_goals', 'clean_sheets_pct',
                'pass_completion_pct', 'tackles_per_game'
            ]
        }
    
    async def generate_reasoning(self, 
                                sport_key: str,
                                game: Dict[str, Any],
                                home_stats: Dict[str, Any],
                                away_stats: Dict[str, Any],
                                home_form: float,
                                away_form: float,
                                home_injuries: List[str],
                                away_injuries: List[str],
                                home_injury_impact: float,
                                away_injury_impact: float,
                                weather_data: Optional[Dict] = None,
                                odds_data: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Generate sport-specific, game-unique reasoning.
        """
        reasoning = []
        
        # 1. Sport-Specific Statistical Analysis
        stat_analysis = self._analyze_sport_specific_stats(
            sport_key, home_stats, away_stats, game
        )
        if stat_analysis:
            reasoning.extend(stat_analysis)
        
        # 2. Detailed Injury Analysis with Player Names
        injury_analysis = self._analyze_injuries_detailed(
            sport_key, home_injuries, away_injuries, 
            home_injury_impact, away_injury_impact, game
        )
        if injury_analysis:
            reasoning.extend(injury_analysis)
        
        # 3. Recent Form with Context
        form_analysis = self._analyze_form_detailed(
            sport_key, home_form, away_form, game
        )
        if form_analysis:
            reasoning.append(form_analysis)
        
        # 4. Head-to-Head History
        h2h_analysis = await self._fetch_head_to_head_history(
            sport_key, game.get('home_team_id'), game.get('away_team_id'), game
        )
        if h2h_analysis:
            reasoning.append(h2h_analysis)
        
        # 5. Key Matchup Analysis
        matchup_analysis = self._analyze_key_matchups(
            sport_key, home_stats, away_stats, game
        )
        if matchup_analysis:
            reasoning.extend(matchup_analysis)
        
        # 6. Weather/Conditions (for outdoor sports)
        if weather_data and sport_key in ['americanfootball_nfl', 'baseball_mlb', 'soccer_epl', 'soccer_usa_mls']:
            weather_analysis = self._analyze_weather_impact(
                sport_key, weather_data, game
            )
            if weather_analysis:
                reasoning.append(weather_analysis)
        
        # 7. Market/Odds Analysis
        if odds_data:
            market_analysis = self._analyze_market_data(
                sport_key, odds_data, game
            )
            if market_analysis:
                reasoning.append(market_analysis)
        
        # Sort by weight (highest impact first)
        reasoning.sort(key=lambda x: x.get('weight', 0), reverse=True)
        
        return reasoning
    
    def _analyze_sport_specific_stats(self, sport_key: str, 
                                       home_stats: Dict, away_stats: Dict,
                                       game: Dict) -> List[Dict[str, Any]]:
        """Generate sport-specific statistical comparisons."""
        reasoning = []
        home_team = game.get('home_team', 'Home')
        away_team = game.get('away_team', 'Away')
        
        if 'basketball' in sport_key:
            # NBA-specific analysis
            home_ppg = home_stats.get('points_per_game', 0)
            away_ppg = away_stats.get('points_per_game', 0)
            home_pa = home_stats.get('points_allowed', 0)
            away_pa = away_stats.get('points_allowed', 0)
            home_efg = home_stats.get('effective_field_goal_pct', 0)
            away_efg = away_stats.get('effective_field_goal_pct', 0)
            home_reb = home_stats.get('total_rebounds', 0)
            away_reb = away_stats.get('total_rebounds', 0)
            
            # Offensive comparison
            if home_ppg > 0 and away_ppg > 0:
                diff = home_ppg - away_ppg
                if abs(diff) > 5:
                    better = home_team if diff > 0 else away_team
                    worse = away_team if diff > 0 else home_team
                    better_ppg = max(home_ppg, away_ppg)
                    worse_ppg = min(home_ppg, away_ppg)
                    
                    reasoning.append({
                        'factor': 'Scoring Offense',
                        'impact': 'Positive' if diff > 0 else 'Negative',
                        'weight': 0.22,
                        'explanation': f"{better} features a significantly more potent offense, averaging {better_ppg:.1f} points per game compared to {worse_ppg:.1f} for {worse}. This {abs(diff):.1f} point differential indicates a substantial offensive advantage."
                    })
                else:
                    reasoning.append({
                        'factor': 'Offensive Balance',
                        'impact': 'Neutral',
                        'weight': 0.12,
                        'explanation': f"Both teams are closely matched offensively, with {home_team} at {home_ppg:.1f} PPG and {away_team} at {away_ppg:.1f} PPG. Neither holds a significant scoring advantage."
                    })
            
            # Defensive comparison
            if home_pa > 0 and away_pa > 0:
                diff = away_pa - home_pa  # Lower is better, so reversed
                if abs(diff) > 4:
                    better = home_team if diff > 0 else away_team
                    worse = away_team if diff > 0 else home_team
                    better_pa = min(home_pa, away_pa)
                    worse_pa = max(home_pa, away_pa)
                    
                    reasoning.append({
                        'factor': 'Defensive Efficiency',
                        'impact': 'Positive' if diff > 0 else 'Negative',
                        'weight': 0.20,
                        'explanation': f"{better} demonstrates superior defensive capability, allowing only {better_pa:.1f} points per game versus {worse_pa:.1f} for {worse}. This {abs(diff):.1f} point gap in defensive efficiency is a critical factor."
                    })
            
            # Shooting efficiency
            if home_efg > 0 and away_efg > 0:
                diff = home_efg - away_efg
                if abs(diff) > 0.03:
                    better = home_team if diff > 0 else away_team
                    reasoning.append({
                        'factor': 'Shooting Efficiency',
                        'impact': 'Positive' if diff > 0 else 'Negative',
                        'weight': 0.15,
                        'explanation': f"{better} converts shots more efficiently with a {max(home_efg, away_efg):.1%} effective field goal percentage compared to {min(home_efg, away_efg):.1%}. Better shot selection and execution gives them an edge in scoring opportunities."
                    })
            
            # Rebounding
            if home_reb > 0 and away_reb > 0:
                diff = home_reb - away_reb
                if abs(diff) > 3:
                    better = home_team if diff > 0 else away_team
                    reasoning.append({
                        'factor': 'Rebounding Advantage',
                        'impact': 'Positive' if diff > 0 else 'Negative',
                        'weight': 0.12,
                        'explanation': f"{better} controls the glass with {max(home_reb, away_reb):.1f} rebounds per game versus {min(home_reb, away_reb):.1f}, creating extra possessions and limiting opponent second-chance opportunities."
                    })
        
        elif 'hockey' in sport_key:
            # NHL-specific analysis
            home_gpg = home_stats.get('goals_per_game', 0)
            away_gpg = away_stats.get('goals_per_game', 0)
            home_ga = home_stats.get('goals_allowed', 0)
            away_ga = away_stats.get('goals_allowed', 0)
            home_pp = home_stats.get('power_play_pct', 20)
            away_pp = away_stats.get('power_play_pct', 20)
            home_pk = home_stats.get('penalty_kill_pct', 80)
            away_pk = away_stats.get('penalty_kill_pct', 80)
            
            # Goal scoring
            if home_gpg > 0 and away_gpg > 0:
                diff = home_gpg - away_gpg
                if abs(diff) > 0.4:
                    better = home_team if diff > 0 else away_team
                    reasoning.append({
                        'factor': 'Offensive Production',
                        'impact': 'Positive' if diff > 0 else 'Negative',
                        'weight': 0.20,
                        'explanation': f"{better} generates more offense, averaging {max(home_gpg, away_gpg):.2f} goals per game compared to {min(home_gpg, away_gpg):.2f} for their opponent. In a low-scoring sport like hockey, this {abs(diff):.2f} goal differential is significant."
                    })
            
            # Goaltending/defense
            if home_ga > 0 and away_ga > 0:
                diff = away_ga - home_ga  # Lower is better
                if abs(diff) > 0.3:
                    better = home_team if diff > 0 else away_team
                    reasoning.append({
                        'factor': 'Defensive/Goaltending Strength',
                        'impact': 'Positive' if diff > 0 else 'Negative',
                        'weight': 0.22,
                        'explanation': f"{better} provides better goaltending and defensive support, allowing only {min(home_ga, away_ga):.2f} goals per game versus {max(home_ga, away_ga):.2f}. Superior netminding often determines close contests."
                    })
            
            # Special teams
            if abs(home_pp - away_pp) > 5 or abs(home_pk - away_pk) > 5:
                pp_better = home_team if home_pp > away_pp else away_team
                pk_better = home_team if home_pk > away_pk else away_team
                reasoning.append({
                    'factor': 'Special Teams Efficiency',
                    'impact': 'Positive' if pp_better == home_team and pk_better == home_team else 'Mixed',
                    'weight': 0.15,
                    'explanation': f"Special teams play favors {pp_better} on the power play ({max(home_pp, away_pp):.1f}%) and {pk_better} on the penalty kill ({max(home_pk, away_pk):.1f}%). These situational advantages could prove decisive in a game likely to feature penalties."
                })
        
        elif 'football' in sport_key:
            # NFL-specific analysis
            home_ppg = home_stats.get('points_per_game', 0)
            away_ppg = away_stats.get('points_per_game', 0)
            home_pass = home_stats.get('passing_yards_per_game', 0)
            away_pass = away_stats.get('passing_yards_per_game', 0)
            home_rush = home_stats.get('rushing_yards_per_game', 0)
            away_rush = away_stats.get('rushing_yards_per_game', 0)
            
            # Overall offense
            if home_ppg > 0 and away_ppg > 0:
                diff = home_ppg - away_ppg
                if abs(diff) > 4:
                    better = home_team if diff > 0 else away_team
                    reasoning.append({
                        'factor': 'Scoring Offense',
                        'impact': 'Positive' if diff > 0 else 'Negative',
                        'weight': 0.20,
                        'explanation': f"{better} has demonstrated superior offensive production, averaging {max(home_ppg, away_ppg):.1f} points per game compared to {min(home_ppg, away_ppg):.1f}. This scoring advantage of {abs(diff):.1f} points per game indicates a more explosive and efficient offense."
                    })
            
            # Passing game
            if home_pass > 0 and away_pass > 0:
                diff = home_pass - away_pass
                if abs(diff) > 30:
                    better = home_team if diff > 0 else away_team
                    reasoning.append({
                        'factor': 'Aerial Attack',
                        'impact': 'Positive' if diff > 0 else 'Negative',
                        'weight': 0.15,
                        'explanation': f"{better} features a more productive passing attack, generating {max(home_pass, away_pass):.0f} yards per game through the air compared to {min(home_pass, away_pass):.0f} for their opponent. This {abs(diff):.0f} yard advantage suggests better quarterback play and receiving options."
                    })
            
            # Rushing attack
            if home_rush > 0 and away_rush > 0:
                diff = home_rush - away_rush
                if abs(diff) > 25:
                    better = home_team if diff > 0 else away_team
                    reasoning.append({
                        'factor': 'Ground Game',
                        'impact': 'Positive' if diff > 0 else 'Negative',
                        'weight': 0.12,
                        'explanation': f"{better} establishes a stronger rushing presence with {max(home_rush, away_rush):.0f} yards per game on the ground versus {min(home_rush, away_rush):.0f}. A dominant run game controls clock and opens play-action opportunities."
                    })
        
        elif 'baseball' in sport_key:
            # MLB-specific analysis
            home_rpg = home_stats.get('runs_per_game', 0)
            away_rpg = away_stats.get('runs_per_game', 0)
            home_era = home_stats.get('era', 4.50)
            away_era = away_stats.get('era', 4.50)
            home_avg = home_stats.get('batting_avg', 0.250)
            away_avg = away_stats.get('batting_avg', 0.250)
            
            # Run production
            if home_rpg > 0 and away_rpg > 0:
                diff = home_rpg - away_rpg
                if abs(diff) > 0.5:
                    better = home_team if diff > 0 else away_team
                    reasoning.append({
                        'factor': 'Run Production',
                        'impact': 'Positive' if diff > 0 else 'Negative',
                        'weight': 0.18,
                        'explanation': f"{better} generates more offense, averaging {max(home_rpg, away_rpg):.2f} runs per game compared to {min(home_rpg, away_rpg):.2f} for their opponent. This run-scoring advantage of {abs(diff):.2f} runs indicates a more potent lineup."
                    })
            
            # Pitching
            if home_era > 0 and away_era > 0:
                diff = away_era - home_era  # Lower ERA is better
                if abs(diff) > 0.75:
                    better = home_team if diff > 0 else away_team
                    reasoning.append({
                        'factor': 'Pitching Advantage',
                        'impact': 'Positive' if diff > 0 else 'Negative',
                        'weight': 0.22,
                        'explanation': f"{better} brings superior pitching to this matchup with a team ERA of {min(home_era, away_era):.2f} compared to {max(home_era, away_era):.2f}. In baseball, quality pitching often trumps hitting, giving them a significant edge."
                    })
            
            # Batting average
            if home_avg > 0 and away_avg > 0:
                diff = home_avg - away_avg
                if abs(diff) > 0.015:
                    better = home_team if diff > 0 else away_team
                    reasoning.append({
                        'factor': 'Hitting Consistency',
                        'impact': 'Positive' if diff > 0 else 'Negative',
                        'weight': 0.12,
                        'explanation': f"{better} makes more consistent contact with a team batting average of {max(home_avg, away_avg):.3f} versus {min(home_avg, away_avg):.3f}. Better contact rates lead to more baserunners and scoring opportunities."
                    })
        
        elif 'soccer' in sport_key:
            # Soccer-specific analysis
            home_gpg = home_stats.get('goals_per_game', 0)
            away_gpg = away_stats.get('goals_per_game', 0)
            home_ga = home_stats.get('goals_allowed', 0)
            away_ga = away_stats.get('goals_allowed', 0)
            
            # Goal scoring
            if home_gpg > 0 and away_gpg > 0:
                diff = home_gpg - away_gpg
                if abs(diff) > 0.3:
                    better = home_team if diff > 0 else away_team
                    reasoning.append({
                        'factor': 'Attacking Prowess',
                        'impact': 'Positive' if diff > 0 else 'Negative',
                        'weight': 0.20,
                        'explanation': f"{better} demonstrates superior attacking quality, averaging {max(home_gpg, away_gpg):.2f} goals per game compared to {min(home_gpg, away_gpg):.2f} for {worse}. In soccer's low-scoring environment, this attacking edge is crucial."
                    })
            
            # Defense
            if home_ga > 0 and away_ga > 0:
                diff = away_ga - home_ga  # Lower is better
                if abs(diff) > 0.3:
                    better = home_team if diff > 0 else away_team
                    reasoning.append({
                        'factor': 'Defensive Solidity',
                        'impact': 'Positive' if diff > 0 else 'Negative',
                        'weight': 0.20,
                        'explanation': f"{better} provides stronger defensive resistance, conceding only {min(home_ga, away_ga):.2f} goals per game versus {max(home_ga, away_ga):.2f} for their opponent. Defensive organization often determines tight matches."
                    })
        
        return reasoning
    
    def _analyze_injuries_detailed(self, sport_key: str,
                                    home_injuries: List[str],
                                    away_injuries: List[str],
                                    home_impact: float,
                                    away_impact: float,
                                    game: Dict) -> List[Dict[str, Any]]:
        """Generate detailed injury analysis with specific player names."""
        reasoning = []
        home_team = game.get('home_team', 'Home')
        away_team = game.get('away_team', 'Away')
        
        # Process home team injuries
        if home_injuries:
            # Categorize injuries by severity/impact
            critical_injuries = []
            moderate_injuries = []
            minor_injuries = []
            
            for injury in home_injuries:
                injury_lower = injury.lower()
                # Check for critical keywords
                if any(word in injury_lower for word in ['out', 'injured reserve', 'season', 'surgery', 'acl', 'mcl', 'fracture']):
                    critical_injuries.append(injury)
                elif any(word in injury_lower for word in ['questionable', 'doubtful', 'day-to-day', 'week-to-week']):
                    moderate_injuries.append(injury)
                else:
                    minor_injuries.append(injury)
            
            # Generate specific explanation based on injury severity
            if critical_injuries:
                players = ', '.join(critical_injuries[:3])  # Limit to first 3
                if len(critical_injuries) > 3:
                    players += f" and {len(critical_injuries) - 3} others"
                
                reasoning.append({
                    'factor': 'Critical Injury Losses',
                    'impact': 'Negative',
                    'weight': min(0.20 + (home_impact * 0.1), 0.30),
                    'explanation': f"{home_team} will be without key contributors: {players}. These absences significantly weaken their rotation and expected performance level."
                })
            elif moderate_injuries:
                players = ', '.join(moderate_injuries[:3])
                reasoning.append({
                    'factor': 'Injury Concerns',
                    'impact': 'Negative',
                    'weight': min(0.12 + (home_impact * 0.05), 0.18),
                    'explanation': f"{home_team} has injury uncertainty with {players} listed as questionable. Their availability and effectiveness remain in doubt."
                })
        
        # Process away team injuries
        if away_injuries:
            critical_injuries = []
            moderate_injuries = []
            
            for injury in away_injuries:
                injury_lower = injury.lower()
                if any(word in injury_lower for word in ['out', 'injured reserve', 'season', 'surgery', 'acl', 'mcl', 'fracture']):
                    critical_injuries.append(injury)
                elif any(word in injury_lower for word in ['questionable', 'doubtful', 'day-to-day']):
                    moderate_injuries.append(injury)
            
            if critical_injuries:
                players = ', '.join(critical_injuries[:3])
                if len(critical_injuries) > 3:
                    players += f" and {len(critical_injuries) - 3} others"
                
                reasoning.append({
                    'factor': 'Opponent Injury Advantage',
                    'impact': 'Positive',
                    'weight': min(0.18 + (away_impact * 0.1), 0.25),
                    'explanation': f"{away_team} is missing key players including {players}, creating matchup advantages for {home_team} in critical areas."
                })
            elif moderate_injuries:
                players = ', '.join(moderate_injuries[:3])
                reasoning.append({
                    'factor': 'Opponent Injury Uncertainty',
                    'impact': 'Positive',
                    'weight': min(0.10 + (away_impact * 0.05), 0.15),
                    'explanation': f"{away_team} faces questions regarding {players}, potentially limiting their depth and tactical flexibility."
                })
        
        return reasoning
    
    def _analyze_form_detailed(self, sport_key: str,
                                home_form: float,
                                away_form: float,
                                game: Dict) -> Dict[str, Any]:
        """Generate detailed recent form analysis."""
        home_team = game.get('home_team', 'Home')
        away_team = game.get('away_team', 'Away')
        
        form_diff = home_form - away_form
        
        # Convert form to win/loss record approximation
        home_wins = int(home_form * 5)
        away_wins = int(away_form * 5)
        
        if form_diff > 0.3:
            # Home team significantly better form
            return {
                'factor': 'Superior Recent Form',
                'impact': 'Positive',
                'weight': 0.18,
                'explanation': f"{home_team} enters with excellent momentum, having won approximately {home_wins} of their last 5 games ({home_form:.0%} win rate). In contrast, {away_team} has struggled recently with roughly {away_wins} wins in their last 5 ({away_form:.0%}). This form gap suggests {home_team} is peaking at the right time."
            }
        elif form_diff < -0.3:
            # Away team significantly better form
            return {
                'factor': 'Away Team Momentum',
                'impact': 'Negative',
                'weight': 0.18,
                'explanation': f"Despite playing on the road, {away_team} carries superior momentum with approximately {away_wins} wins in their last 5 games ({away_form:.0%}). Meanwhile, {home_team} has managed only about {home_wins} wins recently ({home_form:.0%}), raising concerns about their current competitive level."
            }
        elif abs(form_diff) < 0.1:
            # Similar form
            return {
                'factor': 'Even Recent Form',
                'impact': 'Neutral',
                'weight': 0.10,
                'explanation': f"Both teams arrive with similar recent results - approximately {home_wins} wins in their last 5 for {home_team} and {away_wins} for {away_team}. Neither holds a significant momentum advantage, suggesting a competitive contest based on other factors."
            }
        else:
            # Slight edge
            better_team = home_team if form_diff > 0 else away_team
            better_form = home_form if form_diff > 0 else away_form
            return {
                'factor': 'Form Edge',
                'impact': 'Positive' if form_diff > 0 else 'Negative',
                'weight': 0.12,
                'explanation': f"{better_team} holds a modest form advantage with roughly {int(better_form * 5)} wins in their last 5 games ({better_form:.0%} win rate). While not dominant, this slight edge in recent performance could prove decisive in a tight contest."
            }
    
    async def _fetch_head_to_head_history(self, sport_key: str,
                                          home_team_id: str,
                                          away_team_id: str,
                                          game: Dict) -> Optional[Dict[str, Any]]:
        """Fetch and analyze head-to-head history between teams."""
        home_team = game.get('home_team', 'Home')
        away_team = game.get('away_team', 'Away')
        
        try:
            # Map sport key to ESPN path
            sport_mapping = {
                'basketball_nba': 'basketball/nba',
                'icehockey_nhl': 'hockey/nhl',
                'americanfootball_nfl': 'football/nfl',
                'baseball_mlb': 'baseball/mlb',
                'soccer_epl': 'soccer/eng.1'
            }
            
            espn_path = sport_mapping.get(sport_key)
            if not espn_path:
                return None
            
            # Try to fetch team schedule to find previous meetings
            url = f"{self.espn_base}/{espn_path}/teams/{home_team_id}/schedule"
            response = await self.client.get(url, params={'limit': 50})
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            events = data.get('events', [])
            
            # Find games against the away team
            h2h_games = []
            for event in events:
                competitions = event.get('competitions', [])
                if not competitions:
                    continue
                
                competitors = competitions[0].get('competitors', [])
                opponent = next((c for c in competitors if c['team']['id'] != home_team_id), None)
                
                if opponent and opponent['team']['id'] == away_team_id:
                    status = event.get('status', {}).get('type', {})
                    if status.get('completed', False):
                        # Get the result
                        home_competitor = next((c for c in competitors if c['team']['id'] == home_team_id), None)
                        if home_competitor:
                            h2h_games.append({
                                'home_won': home_competitor.get('winner', False),
                                'home_score': home_competitor.get('score', 0),
                                'date': event.get('date', '')
                            })
            
            if not h2h_games:
                return None
            
            # Analyze last 5 meetings
            recent_h2h = h2h_games[:5]
            home_wins = sum(1 for g in recent_h2h if g['home_won'])
            total_games = len(recent_h2h)
            
            if total_games == 0:
                return None
            
            win_pct = home_wins / total_games
            
            # Generate explanation based on H2H results
            if win_pct >= 0.8:
                explanation = f"{home_team} has dominated recent meetings against {away_team}, winning {home_wins} of the last {total_games} matchups. This historical success suggests a favorable matchup profile and potential psychological edge."
                impact = 'Positive'
                weight = 0.15
            elif win_pct >= 0.6:
                explanation = f"{home_team} holds a favorable {home_wins}-{total_games - home_wins} record in the last {total_games} meetings with {away_team}. While not dominant, this edge in head-to-head history provides confidence."
                impact = 'Positive'
                weight = 0.12
            elif win_pct <= 0.2:
                explanation = f"{away_team} has had {home_team}'s number recently, winning {total_games - home_wins} of the last {total_games} matchups. This unfavorable head-to-head history raises concerns despite other favorable factors."
                impact = 'Negative'
                weight = 0.14
            elif win_pct <= 0.4:
                explanation = f"Recent history slightly favors {away_team}, who have won {total_games - home_wins} of the last {total_games} meetings. {home_team} will need to overcome this recent trend."
                impact = 'Negative'
                weight = 0.10
            else:
                explanation = f"The last {total_games} meetings between these teams have been competitive, with {home_team} winning {home_wins} and {away_team} winning {total_games - home_wins}. No clear historical advantage exists."
                impact = 'Neutral'
                weight = 0.08
            
            return {
                'factor': 'Head-to-Head History',
                'impact': impact,
                'weight': weight,
                'explanation': explanation,
                'data_points': {
                    'recent_meetings': total_games,
                    'home_team_wins': home_wins,
                    'win_percentage': win_pct
                }
            }
            
        except Exception as e:
            logger.debug(f"Error fetching H2H history: {e}")
            return None
    
    def _analyze_key_matchups(self, sport_key: str,
                               home_stats: Dict,
                               away_stats: Dict,
                               game: Dict) -> List[Dict[str, Any]]:
        """Analyze key positional or strategic matchups."""
        reasoning = []
        home_team = game.get('home_team', 'Home')
        away_team = game.get('away_team', 'Away')
        
        if 'basketball' in sport_key:
            # Analyze pace vs defense matchup
            home_pace = home_stats.get('possessions_per_game', 100)
            away_pace = away_stats.get('possessions_per_game', 100)
            home_def = home_stats.get('points_allowed', 110)
            away_def = away_stats.get('points_allowed', 110)
            
            if home_pace > 102 and away_def > 112:
                reasoning.append({
                    'factor': 'Pace vs Defense Mismatch',
                    'impact': 'Positive',
                    'weight': 0.12,
                    'explanation': f"{home_team} plays at a fast pace ({home_pace:.0f} possessions/game) against a {away_team} defense that struggles ({away_def:.1f} PPG allowed). This tempo advantage should create easy transition opportunities."
                })
            elif away_pace > 102 and home_def > 112:
                reasoning.append({
                    'factor': 'Pace vs Defense Mismatch',
                    'impact': 'Negative',
                    'weight': 0.12,
                    'explanation': f"{away_team}'s up-tempo style ({away_pace:.0f} possessions) could exploit {home_team}'s porous defense ({home_def:.1f} PPG allowed), creating a challenging matchup."
                })
        
        elif 'hockey' in sport_key:
            # Analyze offensive firepower vs goaltending
            home_gpg = home_stats.get('goals_per_game', 3.0)
            away_ga = away_stats.get('goals_allowed', 3.0)
            
            if home_gpg > 3.2 and away_ga > 3.0:
                reasoning.append({
                    'factor': 'Offense vs Goaltending Mismatch',
                    'impact': 'Positive',
                    'weight': 0.13,
                    'explanation': f"{home_team}'s potent offense ({home_gpg:.2f} GPG) faces {away_team} goaltending that has been vulnerable ({away_ga:.2f} GAA). This matchup favors high offensive output."
                })
        
        elif 'football' in sport_key:
            # Analyze passing vs pass defense
            home_pass = home_stats.get('passing_yards_per_game', 250)
            away_pass_def = away_stats.get('pass_defense_rank', 15)
            
            if home_pass > 280 and away_pass_def > 20:
                reasoning.append({
                    'factor': 'Aerial Attack Advantage',
                    'impact': 'Positive',
                    'weight': 0.14,
                    'explanation': f"{home_team}'s explosive passing game ({home_pass:.0f} YPG) matches up well against {away_team}'s struggling pass defense. Expect significant yardage through the air."
                })
        
        return reasoning
    
    def _analyze_weather_impact(self, sport_key: str,
                                  weather_data: Dict,
                                  game: Dict) -> Dict[str, Any]:
        """Analyze weather impact on the game."""
        home_team = game.get('home_team', 'Home')
        away_team = game.get('away_team', 'Away')
        
        temp = weather_data.get('temp_f', 70)
        condition = weather_data.get('condition', 'Clear')
        wind = weather_data.get('wind_mph', 0)
        precipitation = weather_data.get('precipitation_chance', 0)
        
        # Generate sport-specific weather analysis
        if 'football' in sport_key:
            if wind > 20:
                return {
                    'factor': 'Wind Impact',
                    'impact': 'Negative',
                    'weight': 0.10,
                    'explanation': f"Strong winds ({wind} mph) will significantly impact the passing and kicking game. Both teams may need to rely more heavily on the ground attack, potentially lowering the total score."
                }
            elif temp < 32:
                return {
                    'factor': 'Cold Weather Game',
                    'impact': 'Neutral',
                    'weight': 0.06,
                    'explanation': f"Freezing temperatures ({temp}°F) may affect ball handling and player grip. Teams accustomed to cold weather may have a slight advantage in execution."
                }
            elif precipitation > 60:
                return {
                    'factor': 'Precipitation Expected',
                    'impact': 'Negative',
                    'weight': 0.08,
                    'explanation': f"Rain/snow is expected (precipitation: {precipitation}%), creating slippery conditions. This favors teams with strong running games and may lead to more conservative play-calling."
                }
        
        elif 'baseball' in sport_key:
            if wind > 15:
                return {
                    'factor': 'Wind Impact on Fly Balls',
                    'impact': 'Neutral',
                    'weight': 0.08,
                    'explanation': f"Wind speeds of {wind} mph could carry fly balls further or knock them down depending on direction. Power hitters may see their production affected."
                }
            elif temp > 90:
                return {
                    'factor': 'Heat Factor',
                    'impact': 'Neutral',
                    'weight': 0.06,
                    'explanation': f"Extreme heat ({temp}°F) can fatigue players faster and affect pitcher grip. Bullpen depth may become a factor in late innings."
                }
        
        return None
    
    def _analyze_market_data(self, sport_key: str,
                              odds_data: Dict,
                              game: Dict) -> Optional[Dict[str, Any]]:
        """Analyze market odds and betting lines."""
        home_team = game.get('home_team', 'Home')
        away_team = game.get('away_team', 'Away')
        
        try:
            spread = odds_data.get('spread')
            total = odds_data.get('total')
            home_odds = odds_data.get('home_odds')
            away_odds = odds_data.get('away_odds')
            
            if spread:
                # Parse spread (e.g., "-3.5" or "+2.5")
                spread_val = float(spread.replace('+', '').replace('-', ''))
                spread_fav = home_team if '-' in str(spread) else away_team
                
                return {
                    'factor': 'Market Spread Alignment',
                    'impact': 'Positive' if spread_fav == home_team else 'Negative',
                    'weight': 0.10,
                    'explanation': f"Market consensus favors {spread_fav} by {spread_val} points, indicating professional bettors see them as the superior side. This aligns with our statistical analysis."
                }
            
            if home_odds and away_odds:
                # Convert to implied probability
                if float(home_odds) < 0:
                    home_prob = abs(float(home_odds)) / (abs(float(home_odds)) + 100)
                else:
                    home_prob = 100 / (float(home_odds) + 100)
                
                if float(away_odds) < 0:
                    away_prob = abs(float(away_odds)) / (abs(float(away_odds)) + 100)
                else:
                    away_prob = 100 / (float(away_odds) + 100)
                
                # Normalize
                total_prob = home_prob + away_prob
                home_implied = home_prob / total_prob
                
                if home_implied > 0.6:
                    return {
                        'factor': 'Market Confidence',
                        'impact': 'Positive',
                        'weight': 0.08,
                        'explanation': f"Betting markets show strong confidence in {home_team} with an implied win probability of {home_implied:.1%}. This suggests sharps recognize their advantages."
                    }
                elif home_implied < 0.4:
                    return {
                        'factor': 'Market Skepticism',
                        'impact': 'Negative',
                        'weight': 0.08,
                        'explanation': f"Market odds imply only {home_implied:.1%} win probability for {home_team}, suggesting professional bettors see matchup issues. This contrarian view warrants consideration."
                    }
            
            return None
            
        except Exception as e:
            logger.debug(f"Error analyzing market data: {e}")
            return None
    
    async def close(self):
        """Clean up resources."""
        await self.client.aclose()
