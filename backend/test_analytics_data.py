"""Create test predictions for analytics testing"""
import asyncio
from app.database import SessionLocal
from app.models.db_models import Prediction
from datetime import datetime, timezone

async def create_test_predictions():
    async with SessionLocal() as session:
        # Create some test resolved predictions
        now = datetime.now(timezone.utc)
        test_preds = [
            # Wins
            Prediction(id="test_1", sport="basketball", league="NBA", sport_key="basketball_nba", 
                      matchup="Lakers vs Celtics", prediction="Lakers", confidence=0.65, 
                      result="win", resolved_at=now, created_at=now, actual_value=1.0),
            Prediction(id="test_2", sport="basketball", league="NBA", sport_key="basketball_nba",
                      matchup="Warriors vs Suns", prediction="Warriors", confidence=0.72, 
                      result="win", resolved_at=now, created_at=now, actual_value=1.0),
            Prediction(id="test_3", sport="football", league="NFL", sport_key="football_nfl",
                      matchup="Cowboys vs Eagles", prediction="Cowboys", confidence=0.58, 
                      result="win", resolved_at=now, created_at=now, actual_value=1.0),
            # Losses
            Prediction(id="test_4", sport="basketball", league="NBA", sport_key="basketball_nba",
                      matchup="Heat vs Bucks", prediction="Over 220", confidence=0.55, 
                      result="loss", resolved_at=now, created_at=now, actual_value=0.0),
            Prediction(id="test_5", sport="baseball", league="MLB", sport_key="baseball_mlb",
                      matchup="Yankees vs Red Sox", prediction="Yankees", confidence=0.60, 
                      result="loss", resolved_at=now, created_at=now, actual_value=0.0),
            # A push
            Prediction(id="test_6", sport="football", league="NFL", sport_key="football_nfl",
                      matchup="Patriots vs Bills", prediction="Patriots -2.5", confidence=0.50, 
                      result="push", resolved_at=now, created_at=now, actual_value=0.5),
        ]
        
        for pred in test_preds:
            session.add(pred)
        
        await session.commit()
        print(f"✓ Created {len(test_preds)} test predictions")
        
        # Verify they're in the database
        from sqlalchemy import select
        count_result = await session.execute(select(Prediction).filter(Prediction.id.like("test_%")))
        count = len(count_result.scalars().all())
        print(f"✓ Verified: {count} test predictions in database")

if __name__ == "__main__":
    asyncio.run(create_test_predictions())
