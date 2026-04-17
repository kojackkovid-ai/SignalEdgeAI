"""
Player Props Prediction Service
Wrapper around ESPN Prediction Service for player prop predictions
Uses LinesMate enrichment for enhanced statistics and Vegas lines
"""

from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from app.services.espn_prediction_service import ESPNPredictionService

logger = logging.getLogger(__name__)


class PlayerPropsService:
    """Generate player prop predictions using ESPN data with LinesMate enrichment"""
    
    def __init__(self, db: AsyncSession = None):
        self.db = db
        self.espn_service = ESPNPredictionService()
    
    async def generate_player_prop_predictions(
        self,
        event_id: str,
        sport_key: str,
        home_team: str = '',
        away_team: str = ''
    ) -> List[Dict]:
        """
        Generate predictions for all available player props in an event
        
        Args:
            event_id: ESPN event ID
            sport_key: Sport key (e.g., 'nba', 'nfl', 'mlb', 'nhl', 'soccer')
            home_team: Home team name (optional - not used, for API compatibility)
            away_team: Away team name (optional - not used, for API compatibility)
        
        Returns:
            List of player props with predictions and stats from LinesMate
        """
        try:
            logger.info(f"Generating player props for event {event_id} ({sport_key})")
            
            # Use ESPN service to get player props with LinesMate enrichment
            # The ESPN service handles all the enrichment automatically
            props = await self.espn_service.get_player_props(sport_key, event_id)
            
            if not props:
                logger.warning(f"No player props found for event {event_id}")
                return []
            
            logger.info(f"Generated {len(props)} player prop predictions")
            return props
        
        except Exception as e:
            logger.error(f"Error generating player props: {e}", exc_info=True)
            return []
    
    async def get_player_props_by_stat_type(
        self,
        event_id: str,
        sport_key: str,
        stat_type: str
    ) -> List[Dict]:
        """Get player props filtered by stat type"""
        
        try:
            props = await self.generate_player_prop_predictions(
                event_id=event_id,
                sport_key=sport_key
            )
            
            # Filter by stat type
            filtered = [p for p in props if p.get('stat_type', '').lower() == stat_type.lower()]
            logger.info(f"Filtered to {len(filtered)} props of type {stat_type}")
            return filtered
        
        except Exception as e:
            logger.error(f"Error getting props by stat type: {e}")
            return []
    
    async def get_player_props_for_player(
        self,
        event_id: str,
        sport_key: str,
        player_name: str
    ) -> List[Dict]:
        """Get all props for a specific player"""
        
        try:
            props = await self.generate_player_prop_predictions(
                event_id=event_id,
                sport_key=sport_key
            )
            
            # Filter by player name
            filtered = [
                p for p in props 
                if p.get('player_name', '').lower() == player_name.lower()
            ]
            
            logger.info(f"Found {len(filtered)} props for player {player_name}")
            return filtered
        
        except Exception as e:
            logger.error(f"Error getting props for player: {e}")
            return []
    
    async def get_high_confidence_props(
        self,
        event_id: str,
        sport_key: str,
        min_confidence: float = 0.55
    ) -> List[Dict]:
        """Get only high confidence player prop predictions"""
        
        try:
            props = await self.generate_player_prop_predictions(
                event_id=event_id,
                sport_key=sport_key
            )
            
            # Filter by confidence
            filtered = [
                p for p in props
                if max(p.get('over_confidence', 0.5), p.get('under_confidence', 0.5)) >= min_confidence
            ]
            
            logger.info(f"Found {len(filtered)} props above {min_confidence} confidence")
            return filtered
        
        except Exception as e:
            logger.error(f"Error getting high confidence props: {e}")
            return []
