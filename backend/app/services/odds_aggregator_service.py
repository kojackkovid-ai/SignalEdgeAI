"""
Real-Time Odds Aggregator Service
Integrates odds from multiple providers and normalizes the data
Week 5-7 Enhancement
"""

import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import numpy as np
from app.models.odds_models import (
    OddsRecord, OddsMovement, ConsensusOdds, OddsProvider,
    MarketType, MovementType, ProbabilityConverter, EdgeDetector
)
from app.cache import cache_manager
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# ODDS AGGREGATOR SERVICE
# ============================================================================

class OddsAggregatorService:
    """
    Multi-provider odds aggregation service
    Pulls odds from multiple providers and maintains a unified view
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.providers = {
            OddsProvider.DRAFTKINGS: DraftKingsOddsProvider(),
            OddsProvider.FANDUEL: FanDuelOddsProvider(),
            OddsProvider.BETMGM: BetMGMOddsProvider(),
            OddsProvider.CAESARS: CaesarsOddsProvider(),
        }
        self.update_interval = 10  # seconds
    
    async def get_event_odds(
        self,
        event_id: str,
        sport_key: str,
        use_cache: bool = True
    ) -> Dict:
        """
        Get current odds for an event from all available providers
        
        Args:
            event_id: Unique event identifier
            sport_key: Sport key (nba, nfl, mlb, nhl)
            use_cache: Whether to use cached data
        
        Returns:
            Dict with odds from all providers
        """
        # Try cache first
        cache_key = f"event_odds:{event_id}:{sport_key}"
        if use_cache:
            cached = await cache_manager.get(cache_key)
            if cached:
                return cached
        
        # Fetch odds from all providers concurrently
        odds_tasks = [
            provider.fetch_odds(event_id, sport_key)
            for provider in self.providers.values()
        ]
        
        odds_results = await asyncio.gather(*odds_tasks, return_exceptions=True)
        
        # Process results
        all_odds = {}
        for i, result in enumerate(odds_results):
            if isinstance(result, Exception):
                logger.error(f"Provider {i} error: {result}")
                continue
            
            if result:
                provider_name = list(self.providers.keys())[i]
                all_odds[provider_name.value] = result
        
        # Store in database
        for provider_name, odds_data in all_odds.items():
            await self._store_odds_record(event_id, sport_key, provider_name, odds_data)
        
        # Calculate consensus
        consensus = await self._calculate_consensus(event_id, sport_key)
        
        response = {
            'event_id': event_id,
            'sport_key': sport_key,
            'providers': all_odds,
            'consensus': consensus,
            'updated_at': datetime.utcnow().isoformat(),
            'providers_count': len(all_odds)
        }
        
        # Cache for 30 seconds
        await cache_manager.set(cache_key, response, ttl=30)
        
        return response
    
    async def get_odds_comparison(
        self,
        event_id: str,
        sport_key: str
    ) -> Dict:
        """
        Compare odds across all providers for an event
        
        Returns best/worst lines for each bet type
        """
        odds_data = await self.get_event_odds(event_id, sport_key)
        providers_odds = odds_data['providers']
        
        # Extract all moneyline odds
        home_odds = []
        away_odds = []
        
        for provider, data in providers_odds.items():
            if 'moneyline' in data:
                home_odds.append({
                    'provider': provider,
                    'odds': data['moneyline']['home']
                })
                away_odds.append({
                    'provider': provider,
                    'odds': data['moneyline']['away']
                })
        
        # Find best and worst odds (for favorites, higher is worse; for underdogs, higher is better)
        best_home = max(home_odds, key=lambda x: x['odds'])
        worst_home = min(home_odds, key=lambda x: x['odds'])
        
        best_away = max(away_odds, key=lambda x: x['odds'])
        worst_away = min(away_odds, key=lambda x: x['odds'])
        
        return {
            'event_id': event_id,
            'best_odds': {
                'home': best_home,
                'away': best_away
            },
            'worst_odds': {
                'home': worst_home,
                'away': worst_away
            },
            'spread_analysis': await self._analyze_spread_consistency(
                event_id, sport_key, providers_odds
            ),
            'consensus': odds_data['consensus']
        }
    
    async def get_implied_probabilities(
        self,
        event_id: str,
        sport_key: str
    ) -> Dict:
        """
        Calculate implied probabilities from consensus odds
        """
        odds_data = await self.get_event_odds(event_id, sport_key)
        consensus = odds_data['consensus']
        
        # Calculate true probabilities (removing vigorish)
        if 'moneyline' in consensus:
            home_true, away_true = ProbabilityConverter.true_probability_moneyline(
                consensus['moneyline']['home'],
                consensus['moneyline']['away']
            )
        else:
            home_true, away_true = 0.5, 0.5
        
        return {
            'event_id': event_id,
            'implied_prob_home': home_true,
            'implied_prob_away': away_true,
            'implied_prob_over': consensus.get('total', {}).get('over_prob'),
            'implied_prob_under': consensus.get('total', {}).get('under_prob'),
            'consensus_odds': consensus,
            'calculated_at': datetime.utcnow().isoformat()
        }
    
    async def detect_sharp_movement(
        self,
        min_move_percentage: float = 2.0,
        providers_threshold: int = 3
    ) -> List[Dict]:
        """
        Detect sharp movement across multiple providers
        
        Sharp movement = coordinated sudden line move indicating smart money
        
        Args:
            min_move_percentage: Minimum line move to consider (e.g., 2%)
            providers_threshold: Minimum providers showing movement
        
        Returns:
            List of detected movements
        """
        # Query recent movements
        recent_movements = await self.db.execute(
            select(OddsMovement).where(
                OddsMovement.detected_at > datetime.utcnow() - timedelta(hours=6)
            )
        )
        
        movements = recent_movements.scalars().all()
        
        # Filter for sharp movement characteristics
        sharp_movements = [
            m for m in movements
            if (m.move_percentage >= min_move_percentage and
                m.provider_count >= providers_threshold and
                m.movement_type == MovementType.STEAM_MOVE.value)
        ]
        
        return [self._movement_to_dict(m) for m in sharp_movements]
    
    async def calculate_market_discord(
        self,
        event_id: str,
        model_prediction: Dict,
        sport_key: str
    ) -> Dict:
        """
        Compare market odds to model prediction
        Identify discrepancies that suggest edge opportunities
        """
        implicit_probs = await self.get_implied_probabilities(event_id, sport_key)
        
        # Calculate edges
        home_edge = EdgeDetector.calculate_edge(
            model_probability=model_prediction.get('home_prob', 0.5),
            market_probability=implicit_probs['implied_prob_home'],
            american_odds=implicit_probs['consensus_odds']['moneyline']['home']
        )
        
        away_edge = EdgeDetector.calculate_edge(
            model_probability=model_prediction.get('away_prob', 0.5),
            market_probability=implicit_probs['implied_prob_away'],
            american_odds=implicit_probs['consensus_odds']['moneyline']['away']
        )
        
        # Identify discord
        discord_detected = (
            home_edge['is_profitable'] or away_edge['is_profitable']
        )
        
        return {
            'event_id': event_id,
            'discord_detected': discord_detected,
            'home_edge': home_edge,
            'away_edge': away_edge,
            'arbitrage_opportunity': home_edge['edge'] + away_edge['edge'] > 0.02,
            'recommended_action': self._recommend_action(home_edge, away_edge),
            'analyzed_at': datetime.utcnow().isoformat()
        }
    
    async def _calculate_consensus(
        self,
        event_id: str,
        sport_key: str
    ) -> Dict:
        """Calculate consensus odds across providers"""
        # Query all recent odds records for this event
        query = select(OddsRecord).where(
            and_(
                OddsRecord.event_id == event_id,
                OddsRecord.sport_key == sport_key,
                OddsRecord.timestamp > datetime.utcnow() - timedelta(minutes=5)
            )
        )
        
        result = await self.db.execute(query)
        records = result.scalars().all()
        
        if not records:
            return {}
        
        # Group by market type
        moneyline_data = {
            'home': [],
            'away': [],
            'draw': []
        }
        spread_data = []
        total_data = {'over': [], 'under': []}
        
        for record in records:
            if record.moneyline_home:
                moneyline_data['home'].append(record.moneyline_home)
            if record.moneyline_away:
                moneyline_data['away'].append(record.moneyline_away)
            if record.moneyline_draw:
                moneyline_data['draw'].append(record.moneyline_draw)
            if record.spread_value:
                spread_data.append(record.spread_value)
            if record.total_over:
                total_data['over'].append(record.total_over)
            if record.total_under:
                total_data['under'].append(record.total_under)
        
        # Calculate medians (more robust than mean)
        consensus = {
            'moneyline': {
                'home': np.median(moneyline_data['home']) if moneyline_data['home'] else None,
                'away': np.median(moneyline_data['away']) if moneyline_data['away'] else None,
                'draw': np.median(moneyline_data['draw']) if moneyline_data['draw'] else None,
            },
            'spread': np.median(spread_data) if spread_data else None,
            'total': {
                'line': None,
                'over': np.median(total_data['over']) if total_data['over'] else None,
                'under': np.median(total_data['under']) if total_data['under'] else None,
            }
        }
        
        return consensus
    
    async def _store_odds_record(
        self,
        event_id: str,
        sport_key: str,
        provider_name: str,
        odds_data: Dict
    ):
        """Store odds record in database"""
        record = OddsRecord(
            id=f"{event_id}_{provider_name}_{datetime.utcnow().timestamp()}",
            sport_key=sport_key,
            event_id=event_id,
            provider=provider_name,
            market_type=MarketType.MONEYLINE.value,
            moneyline_home=odds_data.get('moneyline', {}).get('home'),
            moneyline_away=odds_data.get('moneyline', {}).get('away'),
            implied_prob_home=ProbabilityConverter.american_to_implied_probability(
                odds_data.get('moneyline', {}).get('home', 0)
            ) if odds_data.get('moneyline', {}).get('home') else None,
            timestamp=datetime.utcnow(),
            last_updated=datetime.utcnow(),
            confidence_score=0.95
        )
        
        self.db.add(record)
        await self.db.commit()
    
    async def _analyze_spread_consistency(
        self,
        event_id: str,
        sport_key: str,
        providers_odds: Dict
    ) -> Dict:
        """Analyze spread consistency across providers"""
        spreads = []
        
        for provider, data in providers_odds.items():
            if 'spread' in data and data['spread'].get('value'):
                spreads.append(data['spread']['value'])
        
        if not spreads:
            return {}
        
        return {
            'consensus_spread': float(np.median(spreads)),
            'spread_range': {
                'min': float(np.min(spreads)),
                'max': float(np.max(spreads)),
                'range': float(np.max(spreads) - np.min(spreads))
            },
            'provider_disagreement_score': (np.std(spreads) / np.mean(spreads)) if np.mean(spreads) != 0 else 0
        }
    
    def _movement_to_dict(self, movement: OddsMovement) -> Dict:
        """Convert OddsMovement model to dict"""
        return {
            'event_id': movement.event_id,
            'movement_type': movement.movement_type,
            'opening_line': movement.opening_line,
            'current_line': movement.current_line,
            'move_percentage': movement.move_percentage,
            'provider_count': movement.provider_count,
            'detected_at': movement.detected_at.isoformat()
        }
    
    def _recommend_action(self, home_edge: Dict, away_edge: Dict) -> Optional[str]:
        """Recommend action based on edge detection"""
        if home_edge['edge'] > 0.05:
            return f"Bet home team at {home_edge['edge']:.1%} edge"
        elif away_edge['edge'] > 0.05:
            return f"Bet away team at {away_edge['edge']:.1%} edge"
        elif home_edge['is_profitable'] and away_edge['is_profitable']:
            return "Potential arbitrage opportunity detected"
        else:
            return None

# ============================================================================
# PROVIDER IMPLEMENTATIONS
# ============================================================================

class BaseOddsProvider:
    """Base class for odds providers"""
    
    async def fetch_odds(self, event_id: str, sport_key: str) -> Dict:
        raise NotImplementedError

class DraftKingsOddsProvider(BaseOddsProvider):
    """DraftKings odds provider"""
    
    async def fetch_odds(self, event_id: str, sport_key: str) -> Dict:
        """Fetch odds from DraftKings"""
        # In production, implement actual API integration
        # For now, return mock data structure
        return {
            'moneyline': {
                'home': -110,
                'away': -110
            },
            'spread': {
                'value': -3.5,
                'home': -110,
                'away': -110
            },
            'total': {
                'line': 210.5,
                'over': -110,
                'under': -110
            }
        }

class FanDuelOddsProvider(BaseOddsProvider):
    """FanDuel odds provider"""
    
    async def fetch_odds(self, event_id: str, sport_key: str) -> Dict:
        """Fetch odds from FanDuel"""
        return {
            'moneyline': {
                'home': -110,
                'away': -110
            },
            'spread': {
                'value': -3.5,
                'home': -110,
                'away': -110
            },
            'total': {
                'line': 210.5,
                'over': -110,
                'under': -110
            }
        }

class BetMGMOddsProvider(BaseOddsProvider):
    """BetMGM odds provider"""
    
    async def fetch_odds(self, event_id: str, sport_key: str) -> Dict:
        """Fetch odds from BetMGM"""
        return {
            'moneyline': {
                'home': -115,
                'away': -105
            },
            'spread': {
                'value': -3.5,
                'home': -110,
                'away': -110
            },
            'total': {
                'line': 210.5,
                'over': -110,
                'under': -110
            }
        }

class CaesarsOddsProvider(BaseOddsProvider):
    """Caesars Sportsbook odds provider"""
    
    async def fetch_odds(self, event_id: str, sport_key: str) -> Dict:
        """Fetch odds from Caesars"""
        return {
            'moneyline': {
                'home': -110,
                'away': -110
            },
            'spread': {
                'value': -3.5,
                'home': -110,
                'away': -110
            },
            'total': {
                'line': 210.5,
                'over': -110,
                'under': -110
            }
        }

if __name__ == "__main__":
    print("Odds Aggregator Service module loaded")
