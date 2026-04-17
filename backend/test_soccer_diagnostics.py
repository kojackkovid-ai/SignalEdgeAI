"""
Diagnostic script to test soccer predictions end-to-end
"""
import asyncio
import logging
from app.services.espn_prediction_service import ESPNPredictionService
from app.services.prediction_service import PredictionService

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_soccer():
    print("\n" + "="*80)
    print("TESTING SOCCER PREDICTIONS END-TO-END")
    print("="*80)
    
    espn_service = ESPNPredictionService()
    pred_service = PredictionService()
    
    # Step 1: Get upcoming games
    print("\n[STEP 1] Fetching upcoming soccer games...")
    try:
        games = await asyncio.wait_for(
            espn_service.get_upcoming_games("soccer_epl"),
            timeout=10.0
        )
        print(f"✓ Found {len(games)} upcoming soccer_epl games")
        if games:
            for i, g in enumerate(games[:3]):
                print(f"  Game {i+1}: {g['away_team']['name']} @ {g['home_team']['name']} (ID: {g.get('id')})")
        else:
            print("✗ No games found")
            return
    except asyncio.TimeoutError:
        print("✗ TIMEOUT fetching games")
        return
    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 2: Test enrichment (what get_predictions does internally)
    print("\n[STEP 2] Testing prediction enrichment...")
    try:
        sample_game = games[0]
        predictions = await asyncio.wait_for(
            asyncio.gather(
                asyncio.wait_for(
                    espn_service._enrich_prediction(sample_game, "soccer_epl"),
                    timeout=15.0
                ),
                return_exceptions=True
            ),
            timeout=20.0
        )
        pred = predictions[0] if predictions else None
        if isinstance(pred, Exception):
            print(f"✗ EXCEPTION during enrichment: {pred}")
            return
        elif isinstance(pred, dict):
            print(f"✓ Enrichment successful")
            print(f"  Prediction: {pred.get('prediction')}")
            print(f"  Confidence: {pred.get('confidence')}")
            print(f"  Type: {pred.get('prediction_type')}")
        else:
            print(f"✗ Unexpected response type: {type(pred)}")
    except asyncio.TimeoutError:
        print("✗ TIMEOUT during enrichment (15s)")
        return
    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 3: Call full get_predictions (what frontend calls)
    print("\n[STEP 3] Testing full get_predictions call...")
    try:
        preds = await asyncio.wait_for(
            espn_service.get_predictions(sport="soccer_epl", limit=10),
            timeout=60.0
        )
        print(f"✓ Got {len(preds)} predictions")
        if preds:
            print(f"  Sample prediction keys: {list(preds[0].keys())[:10]}...")
            print(f"  Has stats fields: season_avg={' season_avg' in preds[0]}, recent_10_avg={'recent_10_avg' in preds[0]}")
        else:
            print("✗ Empty predictions list returned")
    except asyncio.TimeoutError:
        print("✗ TIMEOUT fetching predictions (60s)")
        return
    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "="*80)
    print("DIAGNOSTICS COMPLETE")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(test_soccer())
