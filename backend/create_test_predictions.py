#!/usr/bin/env python3
"""
Create test resolved predictions for analytics dashboard testing
"""
import asyncio
from datetime import datetime, timedelta
from app.database import AsyncSessionLocal
from app.models.db_models import Prediction
from sqlalchemy import select

async def create_test_predictions():
    """Create resolved predictions for testing"""
    async with AsyncSessionLocal() as session:
        now = datetime.utcnow()
        
        # Create 20 test predictions with various results
        test_predictions = [
            # NBA predictions (10)
            Prediction(
                sport='NBA',
                league='NBA',
                matchup='lakers-celtics',
                sport_key='basketball_nba',
                prediction_type='moneyline',
                prediction='Lakers',
                confidence=75,
                created_at=now - timedelta(days=7),
                resolved_at=now - timedelta(days=6),
                result='win',
                actual_value=105.5
            ),
            Prediction(
                sport='NBA',
                league='NBA',
                teams='Celtics vs 76ers',
                matchup='celtics-76ers',
                sport_key='basketball_nba',
                market_type='moneyline',
                prediction='Celtics',
                confidence=68,
                created_at=now - timedelta(days=6),
                resolved_at=now - timedelta(days=5),
                result='loss',
                actual_value=98.2
            ),
            Prediction(
                user_id=user_id,
                sport='NBA',
                league='NBA',
                teams='Warriors vs Suns',
                matchup='warriors-suns',
                sport_key='basketball_nba',
                market_type='moneyline',
                prediction='Warriors',
                confidence=62,
                created_at=now - timedelta(days=5),
                resolved_at=now - timedelta(days=4),
                result='win',
                actual_value=112.8
            ),
            Prediction(
                user_id=user_id,
                sport='NBA',
                league='NBA',
                teams='Nets vs Heat',
                matchup='nets-heat',
                sport_key='basketball_nba',
                market_type='moneyline',
                prediction='Heat',
                confidence=72,
                created_at=now - timedelta(days=4),
                resolved_at=now - timedelta(days=3),
                result='win',
                actual_value=104.1
            ),
            Prediction(
                user_id=user_id,
                sport='NBA',
                league='NBA',
                teams='Mavericks vs Grizzlies',
                matchup='mavericks-grizzlies',
                sport_key='basketball_nba',
                market_type='moneyline',
                prediction='Mavericks',
                confidence=65,
                created_at=now - timedelta(days=3),
                resolved_at=now - timedelta(days=2),
                result='win',
                actual_value=110.3
            ),
            Prediction(
                user_id=user_id,
                sport='NBA',
                league='NBA',
                teams='Nuggets vs Clippers',
                matchup='nuggets-clippers',
                sport_key='basketball_nba',
                market_type='moneyline',
                prediction='Nuggets',
                confidence=78,
                created_at=now - timedelta(days=2),
                resolved_at=now - timedelta(days=1),
                result='loss',
                actual_value=103.9
            ),
            Prediction(
                user_id=user_id,
                sport='NBA',
                league='NBA',
                teams='Bucks vs Raptors',
                matchup='bucks-raptors',
                sport_key='basketball_nba',
                market_type='moneyline',
                prediction='Bucks',
                confidence=81,
                created_at=now - timedelta(days=1),
                resolved_at=now,
                result='win',
                actual_value=108.7
            ),
            Prediction(
                user_id=user_id,
                sport='NBA',
                league='NBA',
                teams='Kings vs Spurs',
                matchup='kings-spurs',
                sport_key='basketball_nba',
                market_type='moneyline',
                prediction='Kings',
                confidence=55,
                created_at=now - timedelta(hours=12),
                resolved_at=now,
                result='win',
                actual_value=101.2
            ),
            Prediction(
                user_id=user_id,
                sport='NBA',
                league='NBA',
                teams='Pacers vs Cavaliers',
                matchup='pacers-cavaliers',
                sport_key='basketball_nba',
                market_type='moneyline',
                prediction='Cavaliers',
                confidence=70,
                created_at=now - timedelta(hours=6),
                resolved_at=now,
                result='loss',
                actual_value=102.5
            ),
            Prediction(
                user_id=user_id,
                sport='NBA',
                league='NBA',
                teams='Knicks vs Hawks',
                matchup='knicks-hawks',
                sport_key='basketball_nba',
                market_type='moneyline',
                prediction='Knicks',
                confidence=73,
                created_at=now - timedelta(hours=3),
                resolved_at=now,
                result='win',
                actual_value=105.9
            ),
            # NFL predictions (5)
            Prediction(
                user_id=user_id,
                sport='NFL',
                league='NFL',
                teams='49ers vs Cowboys',
                matchup='49ers-cowboys',
                sport_key='americanfootball_nfl',
                market_type='moneyline',
                prediction='49ers',
                confidence=66,
                created_at=now - timedelta(days=3),
                resolved_at=now - timedelta(days=2),
                result='win',
                actual_value=24.1
            ),
            Prediction(
                user_id=user_id,
                sport='NFL',
                league='NFL',
                teams='Chiefs vs Ravens',
                matchup='chiefs-ravens',
                sport_key='americanfootball_nfl',
                market_type='moneyline',
                prediction='Chiefs',
                confidence=75,
                created_at=now - timedelta(days=2),
                resolved_at=now - timedelta(days=1),
                result='win',
                actual_value=27.3
            ),
            Prediction(
                user_id=user_id,
                sport='NFL',
                league='NFL',
                teams='Eagles vs Texans',
                matchup='eagles-texans',
                sport_key='americanfootball_nfl',
                market_type='moneyline',
                prediction='Eagles',
                confidence=58,
                created_at=now - timedelta(days=1),
                resolved_at=now,
                result='loss',
                actual_value=20.2
            ),
            Prediction(
                user_id=user_id,
                sport='NFL',
                league='NFL',
                teams='Patriots vs Bills',
                matchup='patriots-bills',
                sport_key='americanfootball_nfl',
                market_type='moneyline',
                prediction='Bills',
                confidence=72,
                created_at=now - timedelta(hours=12),
                resolved_at=now,
                result='win',
                actual_value=28.1
            ),
            Prediction(
                user_id=user_id,
                sport='NFL',
                league='NFL',
                teams='Packers vs Lions',
                matchup='packers-lions',
                sport_key='americanfootball_nfl',
                market_type='moneyline',
                prediction='Lions',
                confidence=61,
                created_at=now - timedelta(hours=6),
                resolved_at=now,
                result='win',
                actual_value=25.8
            ),
            # Hockey predictions (5)
            Prediction(
                user_id=user_id,
                sport='NHL',
                league='NHL',
                teams='Rangers vs Bruins',
                matchup='rangers-bruins',
                sport_key='icehockey_nhl',
                market_type='moneyline',
                prediction='Rangers',
                confidence=64,
                created_at=now - timedelta(days=2),
                resolved_at=now - timedelta(days=1),
                result='win',
                actual_value=3.2
            ),
            Prediction(
                user_id=user_id,
                sport='NHL',
                league='NHL',
                teams='Avalanche vs Maple Leafs',
                matchup='avalanche-maple_leafs',
                sport_key='icehockey_nhl',
                market_type='moneyline',
                prediction='Avalanche',
                confidence=71,
                created_at=now - timedelta(days=1),
                resolved_at=now,
                result='win',
                actual_value=4.1
            ),
            Prediction(
                user_id=user_id,
                sport='NHL',
                league='NHL',
                teams='Hurricanes vs Capitals',
                matchup='hurricanes-capitals',
                sport_key='icehockey_nhl',
                market_type='moneyline',
                prediction='Hurricanes',
                confidence=67,
                created_at=now - timedelta(hours=12),
                resolved_at=now,
                result='loss',
                actual_value=3.8
            ),
            Prediction(
                user_id=user_id,
                sport='NHL',
                league='NHL',
                teams='Stars vs Kings',
                matchup='stars-kings',
                sport_key='icehockey_nhl',
                market_type='moneyline',
                prediction='Stars',
                confidence=59,
                created_at=now - timedelta(hours=6),
                resolved_at=now,
                result='win',
                actual_value=3.5
            ),
            Prediction(
                user_id=user_id,
                sport='NHL',
                league='NHL',
                teams='Oilers vs Flames',
                matchup='oilers-flames',
                sport_key='icehockey_nhl',
                market_type='moneyline',
                prediction='Oilers',
                confidence=68,
                created_at=now - timedelta(hours=3),
                resolved_at=now,
                result='win',
                actual_value=3.9
            ),
        ]
        
        for pred in test_predictions:
            session.add(pred)
        
        await session.commit()
        print(f"✓ Created {len(test_predictions)} test predictions")
        
        # Verify
        result = await session.execute(select(Prediction).where(Prediction.resolved_at.isnot(None)))
        resolved = result.scalars().all()
        print(f"✓ Total resolved predictions in DB: {len(resolved)}")
        
        # Show breakdown
        by_sport = {}
        for p in resolved:
            sport = p.sport
            if sport not in by_sport:
                by_sport[sport] = {'total': 0, 'wins': 0}
            by_sport[sport]['total'] += 1
            if p.result == 'win':
                by_sport[sport]['wins'] += 1
        
        print(f"\n✓ Breakdown by sport:")
        for sport, stats in by_sport.items():
            wr = (stats['wins'] / stats['total'] * 100) if stats['total'] > 0 else 0
            print(f"  - {sport}: {stats['wins']}/{stats['total']} wins ({wr:.1f}% win rate)")

if __name__ == '__main__':
    asyncio.run(create_test_predictions())
