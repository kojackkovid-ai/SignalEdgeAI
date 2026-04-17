import asyncio
from datetime import datetime, timedelta
from app.database import AsyncSessionLocal
from app.models.db_models import Prediction
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as session:
        now = datetime.utcnow()
        
        # Create 5 quick test predictions  
        for i in range(10):
            pred = Prediction(
                sport='NBA' if i < 5 else 'NFL',
                league='NBA' if i < 5 else 'NFL',
                matchup=f'test-match-{i}',
                sport_key='basketball_nba' if i < 5 else 'americanfootball_nfl',
                prediction_type='moneyline',
                prediction='Test',
                confidence=70 + i,
                created_at=now - timedelta(days=i),
                resolved_at=now - timedelta(days=max(0, i - 1)),
                result='win' if i % 2 == 0 else 'loss',
                actual_value=100.0 + i
            )
            session.add(pred)
        
        await session.commit()
        print(f'✓ Created 10 test predictions')
        
        # Check
        result = await session.execute(select(Prediction).where(Prediction.resolved_at.isnot(None)))
        resolved = result.scalars().all()
        print(f'✓ Total resolved: {len(resolved)}')

asyncio.run(main())
