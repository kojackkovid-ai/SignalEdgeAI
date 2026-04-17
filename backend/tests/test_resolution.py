
import asyncio
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.getcwd())

from app.database import AsyncSessionLocal
from app.services.prediction_service import PredictionService
from app.services.espn_service import ESPNService
from app.models.db_models import User, Prediction, user_predictions
from sqlalchemy import select, delete

async def test_resolution():
    print("Starting resolution test...")
    
    # 1. Setup Services
    ps = PredictionService()
    es = ESPNService()
    
    # 2. Find a completed game from yesterday to bet on
    print("Fetching yesterday's scores...")
    yesterday = (datetime.utcnow()).strftime("%Y%m%d") # Actually try today first, or yesterday if early
    # If early morning, might need yesterday. Let's try to get a completed game from 'basketball_nba'
    
    scores = await es.get_scoreboard("basketball_nba")
    
    completed_game = None
    for game in scores:
        if game['completed']:
            completed_game = game
            break
            
    if not completed_game:
        print("No completed NBA games found today. Trying yesterday...")
        from datetime import timedelta
        yesterday_str = (datetime.utcnow() - timedelta(days=1)).strftime("%Y%m%d")
        scores = await es.get_scoreboard("basketball_nba", yesterday_str)
        for game in scores:
            if game['completed']:
                completed_game = game
                break
                
    if not completed_game:
        print("No completed games found to test with. Aborting.")
        return

    print(f"Found Game: {completed_game['away_team']['name']} @ {completed_game['home_team']['name']}")
    print(f"Score: {completed_game['away_team']['score']} - {completed_game['home_team']['score']}")
    
    # Determine Loser
    home_score = completed_game['home_team']['score']
    away_score = completed_game['away_team']['score']
    
    if home_score < away_score:
        loser = completed_game['home_team']['name']
        winner = completed_game['away_team']['name']
    else:
        loser = completed_game['away_team']['name']
        winner = completed_game['home_team']['name']
        
    print(f"Winner: {winner}, Loser: {loser}")
    
    # 3. Create a User and a Prediction for the LOSER
    async with AsyncSessionLocal() as db:
        # Create dummy user
        user_id = "test_user_resolution"
        # Cleanup first
        await db.execute(delete(user_predictions).where(user_predictions.c.user_id == user_id))
        await db.execute(delete(User).where(User.id == user_id))
        await db.execute(delete(Prediction).where(Prediction.id == "test_pred_1"))
        await db.commit()
        
        user = User(id=user_id, username="test_res", email="test_res@example.com")
        db.add(user)
        
        # Create Prediction (Unresolved)
        pred_id = "test_pred_1"
        matchup = f"{completed_game['away_team']['name']} @ {completed_game['home_team']['name']}"
        
        # Predict the LOSER to Win
        pred = Prediction(
            id=pred_id,
            sport="NBA", # Mapped to basketball_nba
            league="NBA",
            matchup=matchup,
            prediction=f"{loser} Win",
            confidence=0.8,
            odds="-110",
            prediction_type="moneyline",
            created_at=datetime.utcnow()
        )
        db.add(pred)
        await db.commit()
        
        # Follow it
        from sqlalchemy import insert
        await db.execute(insert(user_predictions).values(user_id=user_id, prediction_id=pred_id))
        await db.commit()
        
        print("Created prediction for LOSER. Expecting LOSS.")
        
        # 4. Resolve
        print("Resolving...")
        count = await ps.resolve_predictions(db)
        print(f"Resolved count: {count}")
        
        # 5. Check Stats
        stats = await ps.get_user_stats(db, user_id)
        print("User Stats:", stats)
        
        if stats['wins'] == 0 and stats['losses'] == 1:
            print("SUCCESS: Stats reflect the loss correctly.")
        else:
            print("FAILURE: Stats do not reflect the loss.")
            
        # Cleanup
        await db.execute(delete(user_predictions).where(user_predictions.c.user_id == user_id))
        await db.execute(delete(User).where(User.id == user_id))
        await db.execute(delete(Prediction).where(Prediction.id == pred_id))
        await db.commit()

if __name__ == "__main__":
    asyncio.run(test_resolution())
