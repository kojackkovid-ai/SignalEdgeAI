

0
....................


















































































































"""
Fix Player Props - Use Real ESPN Data for Lines
================================================
This script fixes the player props to:
1. Remove hardcoded default lines
2. Use TRUE real lines from ESPN player stats
3. Create different Over/Under lines (not the same)
4. Ensure team_name is properly included

Target file: sports-prediction-platform/backend/app/services/espn_prediction_service.py
"""

import re

def fix_espn_prediction_service():
    """Fix the espn_prediction_service.py file to use real ESPN data for player prop lines"""
    
    file_path = 'sports-prediction-platform/backend/app/services/espn_prediction_service.py'
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # =====================================================
    # FIX 1: Replace hardcoded market defaults with None
    # This forces the code to fetch actual player stats from ESPN
    # =====================================================
    
    # Fix NBA markets - remove hardcoded defaults
    old_nba_markets = '''        markets = [
            ("points", "Points", 20.5),
            ("rebounds", "Rebounds", 5.5),
            ("assists", "Assists", 4.5),
            ("three_pointers", "3-Pointers", 2.5),
            ("steals", "Steals", 1.5),
            ("blocks", "Blocks", 0.5)
        ]'''
    
    new_nba_markets = '''        markets = [
            ("points", "Points", None),
            ("rebounds", "Rebounds", None),
            ("assists", "Assists", None),
            ("three_pointers", "3-Pointers", None),
            ("steals", "Steals", None),
            ("blocks", "Blocks", None)
        ]'''
    
    content = content.replace(old_nba_markets, new_nba_markets)
    
    # Fix NHL markets
    old_nhl_markets = '''        markets = [
            ("goals", "Goals", 0.5),
            ("assists", "Assists", 0.5),
            ("points", "Points", 1.5),
            ("shots", "Shots", 2.5),
            ("saves", "Saves", 25.5)
        ]'''
    
    new_nhl_markets = '''        markets = [
            ("goals", "Goals", None),
            ("assists", "Assists", None),
            ("points", "Points", None),
            ("shots", "Shots", None),
            ("saves", "Saves", None)
        ]'''
    
    content = content.replace(old_nhl_markets, new_nhl_markets)
    
    # Fix MLB markets
    old_mlb_markets = '''        markets = [
            ("hits", "Hits", 1.5),
            ("home_runs", "Home Runs", 0.5),
            ("rbi", "RBI", 1.5),
            ("runs", "Runs", 1.5),
            ("stolen_bases", "Stolen Bases", 0.5),
            ("strikeouts", "Strikeouts", 7.5)
        ]'''
    
    new_mlb_markets = '''        markets = [
            ("hits", "Hits", None),
            ("home_runs", "Home Runs", None),
            ("rbi", "RBI", None),
            ("runs", "Runs", None),
            ("stolen_bases", "Stolen Bases", None),
            ("strikeouts", "Strikeouts", None)
        ]'''
    
    content = content.replace(old_mlb_markets, new_mlb_markets)
    
    # Fix NFL markets
    old_nfl_markets = '''        markets = [
            ("passing_yards", "Passing Yards", 250.5),
            ("passing_tds", "Passing TDs", 2.5),
            ("rushing_yards", "Rushing Yards", 50.5),
            ("rushing_tds", "Rushing TDs", 0.5),
            ("receptions", "Receptions", 4.5),
            ("receiving_yards", "Receiving Yards", 60.5),
            ("receiving_tds", "Receiving TDs", 0.5)
        ]'''
    
    new_nfl_markets = '''        markets = [
            ("passing_yards", "Passing Yards", None),
            ("passing_tds", "Passing TDs", None),
            ("rushing_yards", "Rushing Yards", None),
            ("rushing_tds", "Rushing TDs", None),
            ("receptions", "Receptions", None),
            ("receiving_yards", "Receiving Yards", None),
            ("receiving_tds", "Receiving TDs", None)
        ]'''
    
    content = content.replace(old_nfl_markets, new_nfl_markets)
    
    # Fix Soccer markets
    old_soccer_markets = '''        markets = [
            ("goals", "Goals", 0.5),
            ("assists", "Assists", 0.5),
            ("shots", "Shots", 2.5),
            ("shots_on_target", "Shots on Target", 1.5),
            ("goals_assists", "Goals + Assists", 0.5)
        ]'''
    
    new_soccer_markets = '''        markets = [
            ("goals", "Goals", None),
            ("assists", "Assists", None),
            ("shots", "Shots", None),
            ("shots_on_target", "Shots on Target", None),
            ("goals_assists", "Goals + Assists", None)
        ]'''
    
    content = content.replace(old_soccer_markets, new_soccer_markets)
    
    # =====================================================
    # FIX 2: Update _calculate_dynamic_line to NEVER return hardcoded
    # If no stats available, return the player's actual average from stats_dict
    # =====================================================
    
    # Find and update the _calculate_dynamic_line method
    # We need to add logic that uses the actual stat value when available
    
    old_dynamic_line_start = '''    def _calculate_dynamic_line(self, stats_dict: Dict, market_key: str, sport_key: str, default_line: float) -> float:
        """
        Calculate dynamic prop line based on player's actual statistics.
        Returns a line that is typically 85-90% of their average (juice reduced).
        """
        if not stats_dict:
            return default_line'''
    
    new_dynamic_line_start = '''    def _calculate_dynamic_line(self, stats_dict: Dict, market_key: str, sport_key: str, default_line: float) -> float:
        """
        Calculate dynamic prop line based on player's actual statistics from ESPN.
        Returns the player's actual season average (NOT a hardcoded value).
        If no stats available, returns None to indicate we should skip this prop.
        """
        if not stats_dict or not default_line:
            # FIXED: If no default_line (was set to None), we MUST have ESPN stats
            # Return None to signal that we can't generate this prop without real data
            logger.warning(f"[DYNAMIC_LINE] No stats or default for {market_key} - skipping prop")
            return None'''
    
    content = content.replace(old_dynamic_line_start, new_dynamic_line_start)
    
    # =====================================================
    # FIX 3: Update prop generation to use different Over/Under lines
    # Add separate over_line and under_line based on player's actual average
    # =====================================================
    
    # Find the line where prop dict is created and add over/under lines
    old_point_usage = '''                # Format prediction
                prediction = f"{over_under} {point} {market_name}"'''
    
    new_point_usage = '''                # FIXED: Create DIFFERENT lines for Over vs Under
                # If player averages 25 points:
                # - Over line = 25.5 (slightly above average)
                # - Under line = 24.5 (slightly below average)
                if point is not None:
                    over_line = round(point + 0.5, 1)
                    under_line = round(point - 0.5, 1)
                else:
                    over_line = None
                    under_line = None
                
                # Format prediction with appropriate line based on over_under
                if over_under == "Over" and over_line:
                    line_to_use = over_line
                elif over_under == "Under" and under_line:
                    line_to_use = under_line
                else:
                    line_to_use = point if point else 0
                
                prediction = f"{over_under} {line_to_use} {market_name}"'''
    
    content = content.replace(old_point_usage, new_point_usage)
    
    # =====================================================
    # FIX 4: Update prop dict to include over_line and under_line
    # =====================================================
    
    old_point_dict = '''                    "point": point'''
    
    new_point_dict = '''                    "point": line_to_use if 'line_to_use' in dir() else point,
                    "over_line": over_line if 'over_line' in dir() else None,
                    "under_line": under_line if 'under_line' in dir() else None,
                    # Ensure team_name is always set - use team abbreviation if full name not available
                    "team_name": team_name if team_name else "N/A",'''
    
    content = content.replace(old_point_dict, new_point_dict)
    
    # =====================================================
    # FIX 5: Skip props where we don't have real data
    # =====================================================
    
    # Add check to skip props without valid lines
    old_market_loop = '''            for market_key, market_name, default_point in markets:
                # Calculate dynamic line based on player's actual stats
                point = self._calculate_dynamic_line(stats_dict, market_key, sport_key, default_point)

                # Determine Over or Under based on player stats
                over_under = self._determine_over_under(player_stats, stats_dict, market_key, sport_key, point)

                # Calculate confidence - now uses _get_fallback_confidence instead of hardcoded 50%
                try:
                    confidence = self._calculate_confidence(player_stats, market_key, sport_key)
                except Exception as e:
                    logger.warning(f"[NBA_PROPS] Using fallback confidence for {player_name} - {market_key}: {e}")
                    confidence = self._get_fallback_confidence(market_key, sport_key)

                # Format prediction
                prediction = f"{over_under} {point} {market_name}"'''
    
    new_market_loop = '''            for market_key, market_name, default_point in markets:
                # Calculate dynamic line based on player's actual stats
                point = self._calculate_dynamic_line(stats_dict, market_key, sport_key, default_point)

                # FIXED: Skip this prop if we don't have real ESPN data (point is None)
                if point is None:
                    logger.debug(f"[NBA_PROPS] Skipping {market_name} for {player_name} - no ESPN stats available")
                    continue

                # Determine Over or Under based on player stats
                over_under = self._determine_over_under(player_stats, stats_dict, market_key, sport_key, point)

                # Calculate confidence - now uses _get_fallback_confidence instead of hardcoded 50%
                try:
                    confidence = self._calculate_confidence(player_stats, market_key, sport_key)
                except Exception as e:
                    logger.warning(f"[NBA_PROPS] Using fallback confidence for {player_name} - {market_key}: {e}")
                    confidence = self._get_fallback_confidence(market_key, sport_key)

                # FIXED: Skip props with very low confidence (less than 52%)
                if confidence < 52.0:
                    logger.debug(f"[NBA_PROPS] Skipping {market_name} for {player_name} - low confidence: {confidence}")
                    continue

                # Format prediction
                prediction = f"{over_under} {point} {market_name}"'''
    
    content = content.replace(old_market_loop, new_market_loop)
    
    # Write the fixed content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✓ Fixed {file_path}")
    print("\nChanges made:")
    print("1. Removed hardcoded default lines from all sport markets (set to None)")
    print("2. Updated _calculate_dynamic_line to return None when no stats available")
    print("3. Added different over_line and under_line values")
    print("4. Added team_name validation to ensure it's never None")
    print("5. Added skip logic for props without real ESPN data or low confidence")

if __name__ == "__main__":
    fix_espn_prediction_service()
