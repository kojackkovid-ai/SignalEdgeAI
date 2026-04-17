"""
Historical Game Data Tracking Service
Tracks game results for form calculations and Bayesian confidence updates.
"""

import sqlite3
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class HistoricalDataService:
    """
    Service to track historical game results for form calculations.
    Stores game data in SQLite database for efficient querying.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize historical data service.
        
        Args:
            db_path: Path to SQLite database file
        """
        if db_path is None:
            # Default to backend directory
            base_path = Path(__file__).parent.parent
            db_path = str(base_path / "historical_data.db")
        
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize database tables."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Games table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS games (
                    id TEXT PRIMARY KEY,
                    sport_key TEXT NOT NULL,
                    home_team_id TEXT NOT NULL,
                    away_team_id TEXT NOT NULL,
                    home_score INTEGER,
                    away_score INTEGER,
                    home_won INTEGER,
                    game_date TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Team performance table (aggregated stats)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS team_performance (
                    team_id TEXT NOT NULL,
                    sport_key TEXT NOT NULL,
                    season TEXT NOT NULL,
                    games_played INTEGER DEFAULT 0,
                    wins INTEGER DEFAULT 0,
                    losses INTEGER DEFAULT 0,
                    draws INTEGER DEFAULT 0,
                    points_scored INTEGER DEFAULT 0,
                    points_allowed INTEGER DEFAULT 0,
                    home_games INTEGER DEFAULT 0,
                    home_wins INTEGER DEFAULT 0,
                    away_games INTEGER DEFAULT 0,
                    away_wins INTEGER DEFAULT 0,
                    last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (team_id, sport_key, season)
                )
            """)
            
            # Recent form table (rolling window)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recent_form (
                    team_id TEXT NOT NULL,
                    sport_key TEXT NOT NULL,
                    game_date TEXT NOT NULL,
                    result TEXT NOT NULL,  -- 'win', 'loss', 'draw'
                    is_home INTEGER DEFAULT 0,
                    points_for REAL DEFAULT 0,
                    points_against REAL DEFAULT 0,
                    PRIMARY KEY (team_id, sport_key, game_date)
                )
            """)
            
            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_games_sport_date 
                ON games(sport_key, game_date)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_games_teams 
                ON games(home_team_id, away_team_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_recent_form_date 
                ON recent_form(team_id, sport_key, game_date DESC)
            """)
            
            conn.commit()
            conn.close()
            
            logger.info(f"Historical database initialized at {self.db_path}")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    def record_game_result(
        self,
        game_id: str,
        sport_key: str,
        home_team_id: str,
        away_team_id: str,
        home_score: int,
        away_score: int,
        game_date: str
    ) -> bool:
        """
        Record a game result.
        
        Args:
            game_id: Unique game identifier
            sport_key: Sport key (e.g., 'basketball_nba')
            home_team_id: Home team ID
            away_team_id: Away team ID
            home_score: Home team score
            away_score: Away team score
            game_date: Game date ISO string
            
        Returns:
            True if recorded successfully
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            home_won = 1 if home_score > away_score else 0
            
            # Insert game result
            cursor.execute("""
                INSERT OR REPLACE INTO games 
                (id, sport_key, home_team_id, away_team_id, home_score, away_score, home_won, game_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (game_id, sport_key, home_team_id, away_team_id, home_score, away_score, home_won, game_date))
            
            # Update team performance
            self._update_team_performance(cursor, home_team_id, sport_key, home_score, away_score, home_won, True)
            self._update_team_performance(cursor, away_team_id, sport_key, away_score, home_score, 1 - home_won, False)
            
            # Update recent form
            self._update_recent_form(cursor, home_team_id, sport_key, game_date, home_won, True, home_score, away_score)
            self._update_recent_form(cursor, away_team_id, sport_key, game_date, 1 - home_won, False, away_score, home_score)
            
            conn.commit()
            conn.close()
            
            logger.info(f"Recorded game result: {game_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error recording game result: {e}")
            return False
    
    def _update_team_performance(
        self,
        cursor: sqlite3.Cursor,
        team_id: str,
        sport_key: str,
        points_for: int,
        points_against: int,
        won: int,
        is_home: bool
    ) -> None:
        """Update team performance statistics."""
        season = self._get_current_season(sport_key)
        
        # Check if record exists
        cursor.execute("""
            SELECT games_played, wins, losses, points_scored, points_allowed,
                   home_games, home_wins, away_games, away_wins
            FROM team_performance
            WHERE team_id = ? AND sport_key = ? AND season = ?
        """, (team_id, sport_key, season))
        
        row = cursor.fetchone()
        
        if row:
            # Update existing record
            games_played, wins, losses, pts_for, pts_against, home_games, home_wins, away_games, away_wins = row
            
            new_games = games_played + 1
            new_wins = wins + won
            new_losses = losses + (1 - won)
            new_pts_for = pts_for + points_for
            new_pts_against = pts_against + points_against
            
            if is_home:
                new_home_games = home_games + 1
                new_home_wins = home_wins + won
                new_away_games = away_games
                new_away_wins = away_wins
            else:
                new_home_games = home_games
                new_home_wins = home_wins
                new_away_games = away_games + 1
                new_away_wins = away_wins + won
            
            cursor.execute("""
                UPDATE team_performance
                SET games_played = ?, wins = ?, losses = ?, 
                    points_scored = ?, points_allowed = ?,
                    home_games = ?, home_wins = ?,
                    away_games = ?, away_wins = ?,
                    last_updated = CURRENT_TIMESTAMP
                WHERE team_id = ? AND sport_key = ? AND season = ?
            """, (new_games, new_wins, new_losses, new_pts_for, new_pts_against,
                  new_home_games, new_home_wins, new_away_games, new_away_wins,
                  team_id, sport_key, season))
        else:
            # Insert new record
            home_games = 1 if is_home else 0
            home_wins = won if is_home else 0
            away_games = 0 if is_home else 1
            away_wins = 0 if is_home else won
            
            cursor.execute("""
                INSERT INTO team_performance
                (team_id, sport_key, season, games_played, wins, losses, 
                 points_scored, points_allowed, home_games, home_wins, away_games, away_wins)
                VALUES (?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?)
            """, (team_id, sport_key, season, won, 1 - won, 
                  points_for, points_against, home_games, home_wins, away_games, away_wins))
    
    def _update_recent_form(
        self,
        cursor: sqlite3.Cursor,
        team_id: str,
        sport_key: str,
        game_date: str,
        result: int,
        is_home: bool,
        points_for: float,
        points_against: float
    ) -> None:
        """Update recent form (last 10 games)."""
        result_str = 'win' if result == 1 else 'loss'
        
        cursor.execute("""
            INSERT OR REPLACE INTO recent_form
            (team_id, sport_key, game_date, result, is_home, points_for, points_against)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (team_id, sport_key, game_date, result_str, 1 if is_home else 0, points_for, points_against))
        
        # Keep only last 20 games per team
        cursor.execute("""
            DELETE FROM recent_form
            WHERE team_id = ? AND sport_key = ? 
            AND game_date NOT IN (
                SELECT game_date FROM recent_form
                WHERE team_id = ? AND sport_key = ?
                ORDER BY game_date DESC
                LIMIT 20
            )
        """, (team_id, sport_key, team_id, sport_key))
    
    def _get_current_season(self, sport_key: str) -> str:
        """Get current season string."""
        now = datetime.now()
        
        if 'nba' in sport_key:
            # NBA: Oct-Jun (e.g., 2024-25)
            if now.month >= 10:
                return f"{now.year}-{str(now.year + 1)[-2:]}"
            else:
                return f"{now.year - 1}-{str(now.year)[-2:]}"
        elif 'nfl' in sport_key:
            # NFL: Sep-Jan (e.g., 2024)
            if now.month >= 9:
                return str(now.year)
            else:
                return str(now.year - 1)
        elif 'mlb' in sport_key:
            # MLB: Apr-Oct (e.g., 2024)
            return str(now.year)
        elif 'nhl' in sport_key:
            # NHL: Oct-Jun
            if now.month >= 10:
                return f"{now.year}-{str(now.year + 1)[-2:]}"
            else:
                return f"{now.year - 1}-{str(now.year)[-2:]}"
        elif 'soccer' in sport_key:
            # Soccer: Aug-May
            if now.month >= 8:
                return f"{now.year}-{str(now.year + 1)[-2:]}"
            else:
                return f"{now.year - 1}-{str(now.year)[-2:]}"
        
        return str(now.year)
    
    def get_team_record(
        self,
        team_id: str,
        sport_key: str,
        season: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get team win-loss record.
        
        Returns:
            Dict with wins, losses, games_played, win_pct
        """
        try:
            if season is None:
                season = self._get_current_season(sport_key)
            
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT games_played, wins, losses, draws,
                       points_scored, points_allowed,
                       home_games, home_wins, away_games, away_wins
                FROM team_performance
                WHERE team_id = ? AND sport_key = ? AND season = ?
            """, (team_id, sport_key, season))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                games = row['games_played']
                win_pct = row['wins'] / games if games > 0 else 0.5
                
                return {
                    'wins': row['wins'],
                    'losses': row['losses'],
                    'draws': row.get('draws', 0),
                    'games_played': games,
                    'win_pct': round(win_pct, 3),
                    'points_for': row['points_scored'],
                    'points_against': row['points_allowed'],
                    'ppg': row['points_scored'] / games if games > 0 else 0,
                    'papg': row['points_allowed'] / games if games > 0 else 0,
                    'home_record': f"{row['home_wins']}-{row['home_games'] - row['home_wins']}",
                    'away_record': f"{row['away_wins']}-{row['away_games'] - row['away_wins']}"
                }
            
            return {
                'wins': 0,
                'losses': 0,
                'draws': 0,
                'games_played': 0,
                'win_pct': 0.5,
                'points_for': 0,
                'points_against': 0,
                'ppg': 0,
                'papg': 0,
                'home_record': '0-0',
                'away_record': '0-0'
            }
            
        except Exception as e:
            logger.error(f"Error getting team record: {e}")
            return {'wins': 0, 'losses': 0, 'games_played': 0, 'win_pct': 0.5}
    
    def get_recent_form(
        self,
        team_id: str,
        sport_key: str,
        n_games: int = 10
    ) -> Dict[str, Any]:
        """
        Get team's recent form (win rate in last N games).
        
        Returns:
            Dict with form_pct, wins, losses, streak
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT result, is_home, points_for, points_against
                FROM recent_form
                WHERE team_id = ? AND sport_key = ?
                ORDER BY game_date DESC
                LIMIT ?
            """, (team_id, sport_key, n_games))
            
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                return {
                    'form_pct': 0.5,
                    'wins': 0,
                    'losses': 0,
                    'games': 0,
                    'streak': 0,
                    'streak_type': 'none',
                    'home_form': 0.5,
                    'away_form': 0.5
                }
            
            wins = sum(1 for r in rows if r[0] == 'win')
            losses = sum(1 for r in rows if r[0] == 'loss')
            games = len(rows)
            
            # Calculate streak
            streak = 0
            streak_type = 'none'
            if rows:
                first_result = rows[0][0]
                for r in rows:
                    if r[0] == first_result:
                        streak += 1
                    else:
                        break
                streak_type = 'win' if first_result == 'win' else 'loss'
            
            # Home vs away form
            home_games = [r for r in rows if r[1] == 1]
            away_games = [r for r in rows if r[1] == 0]
            
            home_wins = sum(1 for r in home_games if r[0] == 'win')
            away_wins = sum(1 for r in away_games if r[0] == 'win')
            
            home_form = home_wins / len(home_games) if home_games else 0.5
            away_form = away_wins / len(away_games) if away_games else 0.5
            
            return {
                'form_pct': round(wins / games, 3) if games > 0 else 0.5,
                'wins': wins,
                'losses': losses,
                'games': games,
                'streak': streak,
                'streak_type': streak_type,
                'home_form': round(home_form, 3),
                'away_form': round(away_form, 3),
                'avg_points_for': sum(r[2] for r in rows) / games if games > 0 else 0,
                'avg_points_against': sum(r[3] for r in rows) / games if games > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting recent form: {e}")
            return {
                'form_pct': 0.5,
                'wins': 0,
                'losses': 0,
                'games': 0,
                'streak': 0,
                'streak_type': 'none'
            }
    
    def get_head_to_head(
        self,
        team1_id: str,
        team2_id: str,
        sport_key: str,
        n_games: int = 10
    ) -> Dict[str, Any]:
        """
        Get head-to-head record between two teams.
        
        Returns:
            Dict with team1_wins, team2_wins, games
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get games where these teams played
            cursor.execute("""
                SELECT home_team_id, away_team_id, home_won
                FROM games
                WHERE sport_key = ?
                AND ((home_team_id = ? AND away_team_id = ?) OR (home_team_id = ? AND away_team_id = ?))
                ORDER BY game_date DESC
                LIMIT ?
            """, (sport_key, team1_id, team2_id, team2_id, team1_id, n_games))
            
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                return {
                    'team1_wins': 0,
                    'team2_wins': 0,
                    'games': 0,
                    'team1_pct': 0.5
                }
            
            team1_wins = 0
            team2_wins = 0
            
            for row in rows:
                home_id, away_id, home_won = row
                
                if home_id == team1_id:
                    if home_won == 1:
                        team1_wins += 1
                    else:
                        team2_wins += 1
                else:
                    if home_won == 1:
                        team2_wins += 1
                    else:
                        team1_wins += 1
            
            total = len(rows)
            
            return {
                'team1_wins': team1_wins,
                'team2_wins': team2_wins,
                'games': total,
                'team1_pct': round(team1_wins / total, 3) if total > 0 else 0.5
            }
            
        except Exception as e:
            logger.error(f"Error getting head-to-head: {e}")
            return {
                'team1_wins': 0,
                'team2_wins': 0,
                'games': 0,
                'team1_pct': 0.5
            }
    
    def get_team_stats_for_confidence(
        self,
        team_id: str,
        sport_key: str
    ) -> Dict[str, Any]:
        """
        Get all stats needed for confidence calculation.
        
        Returns:
            Dict with wins, losses, form, home_form, away_form
        """
        record = self.get_team_record(team_id, sport_key)
        form = self.get_recent_form(team_id, sport_key)
        
        return {
            'wins': record['wins'],
            'losses': record['losses'],
            'games': record['games_played'],
            'win_pct': record['win_pct'],
            'form': form['form_pct'],
            'home_form': form['home_form'],
            'away_form': form['away_form'],
            'streak': form['streak'],
            'streak_type': form['streak_type'],
            'ppg': record['ppg'],
            'papg': record['papg']
        }
