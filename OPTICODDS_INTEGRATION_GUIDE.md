# OpticOdds Integration Guide

## Overview

OpticOdds API has been integrated into the Sports Prediction Platform to provide **real player props lines and odds data** from multiple sportsbooks. This replaces hardcoded/estimated player prop lines with actual market data.

## What OpticOdds Provides

- **Real Player Props Lines**: Actual over/under numbers for player statistics (points, rebounds, assists, etc.)
- **Multi-Book Odds**: Aggregated odds from major sportsbooks (DraftKings, FanDuel, BetMGM, Caesars, etc.)
- **Best Odds Comparison**: Identifies which sportsbook offers the best odds for each side
- **Real-Time Updates**: Odds are updated frequently as markets move
- **All Sports**: NBA, NFL, MLB, NHL, NCAA, Soccer

## How It Works

### Data Flow

```
ESPN Data (Rosters, Stats) 
         ↓ 
    ML Prediction
         ↓ 
Player Props with ESPN lines
         ↓ 
OpticOdds Enrichment
         ↓ 
Real Props with Actual Market Lines
         ↓ 
Frontend Display
```

### Implementation

1. **ESPN Service**: Generates player props with:
   - Player stats and averages
   - ML model predictions
   - Confidence levels
   - ESPN-derived estimated lines

2. **OpticOdds Enhancement**: Enriches each prop with:
   - Real consensus line
   - Best over/under odds from all books
   - Which sportsbook has the best odds
   - Prop status (active, suspended, closed, etc.)

3. **Frontend Display**: Shows:
   - ML prediction ← from ESPN service
   - Real market line ← from OpticOdds
   - Best available odds ← from OpticOdds
   - Sportsbook options

## Configuration

### Step 1: Get OpticOdds API Key

1. Visit [https://opticodds.com](https://opticodds.com)
2. Sign up for an account
3. Get your API key from the dashboard
4. Keep your API key secure (don't commit to git!)

### Step 2: Configure Environment

Add to `.env` file:

```bash
# OpticOdds API - Player Props and Lines Data
OPTIC_ODDS_API_KEY=your_api_key_here
OPTIC_ODDS_BASE_URL=https://api.opticodds.com/v2
```

### Step 3: Restart Backend

```bash
# Stop the current server
Ctrl+C

# Restart with new configuration
python start_dev_server.py
```

### Step 4: Verify Configuration

```bash
# Run the test script
python test_optic_odds_integration.py
```

Expected output:
```
[CONFIG] OpticOdds API Key configured: True
[TEST] Health Check
        ✅ OpticOdds API is accessible
```

## API Response Format

### Player Props with OpticOdds Data

```json
{
  "id": "game123_points_LeBron_James",
  "player": "LeBron James",
  "market_key": "points",
  "market_name": "Points",
  "sport_key": "basketball_nba",
  
  "// ESPN Data": null,
  "prediction": "Over 25.5 Points",
  "confidence": 68.5,
  "season_avg": 25.2,
  "recent_10_avg": 26.1,
  
  "// OpticOdds Real Market Data": null,
  "optic_odds_line": 25.5,
  "optic_odds_over": -110,
  "optic_odds_under": -110,
  "optic_odds_best_book": "DraftKings",
  "optic_odds_all_books": ["DraftKings", "FanDuel", "BetMGM", "Caesars"],
  "optic_odds_consensus": 25.5,
  "optic_odds_status": "active",
  "optic_odds_updated": "2024-03-09T15:30:00Z"
}
```

## Using OpticOdds Data in Frontend

### Display Real Market Line

```jsx
const RealMarketLine = ({ prop }) => {
  const realLine = prop.optic_odds_line || prop.point;
  const bestBook = prop.optic_odds_best_book || 'Multiple';
  
  return (
    <div className="market-line">
      <div>Line: {realLine}</div>
      <div className="best-book">Best @ {bestBook}</div>
    </div>
  );
};
```

### Show Best Odds Options

```jsx
const BestOdds = ({ prop }) => {
  if (!prop.optic_odds_over) return null;
  
  return (
    <div className="odds-display">
      <div className="over-side">
        Over {prop.optic_odds_line}
        <div className="odds">{prop.optic_odds_over}</div>
        <div className="book">{prop.optic_odds_best_book}</div>
      </div>
      
      <div className="under-side">
        Under {prop.optic_odds_line}
        <div className="odds">{prop.optic_odds_under}</div>
        <div className="book">{prop.optic_odds_best_book}</div>
      </div>
    </div>
  );
};
```

### Highlight When ML Disagrees with Market

```jsx
const PropCard = ({ prop }) => {
  const mlPredicts = prop.prediction.includes('Over') ? 'over' : 'under';
  const marketLine = prop.optic_odds_line;
  const espnLine = prop.point;
  
  const lineMovement = Math.abs(marketLine - espnLine);
  
  return (
    <div className="prop-card">
      <div className="ml-prediction">{prop.prediction}</div>
      <div className="market-data">
        <div>Market: {marketLine}</div>
        {lineMovement > 0.5 && (
          <div className="highlight">
            Market has moved {lineMovement} points
          </div>
        )}
      </div>
    </div>
  );
};
```

## Testing OpticOdds Integration

### Run Integration Test

```bash
cd "c:\Users\bigba\Desktop\New folder"
python test_optic_odds_integration.py
```

### Manual API Test

```python
import asyncio
from app.services.optic_odds_service import OpticOddsService

async def test():
    service = OpticOddsService()
    
    # Get props for a sport
    props = await service.get_player_props('basketball_nba')
    print(f"Found {len(props)} NBA props")
    
    # Get specific player prop lines
    line = await service.get_player_prop_lines(
        'basketball_nba',
        'LeBron James',
        'points'
    )
    print(f"LeBron James Points: {line}")
    
    # Get best odds
    odds = await service.get_best_odds(
        'basketball_nba',
        'LeBron James',
        'points'
    )
    print(f"Best odds: {odds}")

asyncio.run(test())
```

### Test in Frontend

```javascript
// In browser console
fetch('/api/v1/games/basketball_nba')
  .then(r => r.json())
  .then(games => games[0])
  .then(game => fetch(`/api/v1/games/${game.event_id}/props`))
  .then(r => r.json())
  .then(props => {
    // Check for OpticOdds data
    props.forEach(prop => {
      console.log({
        player: prop.player,
        market: prop.market_key,
        espn_line: prop.point,
        optic_odds_line: prop.optic_odds_line,
        best_book: prop.optic_odds_best_book
      });
    });
  });
```

## Troubleshooting

### ⚠️ OpticOdds API Key Not Configured

**Problem**: Props don't have `optic_odds_*` fields
**Solution**: 
1. Add API key to `.env`
2. Restart backend server
3. Check logs with `python test_optic_odds_integration.py`

### ⚠️ Health Check Fails

**Problem**: Can't connect to OpticOdds API
**Solution**:
1. Check internet connection
2. Verify API key is correct
3. Check if OpticOdds service is up: `ping api.opticodds.com`

### ⚠️ Some Props Not Enriched

**Problem**: Only some props have OpticOdds data
**Solution**:
1. This is normal - not all props may have active markets
2. Check `optic_odds_status` field - may be "not_found", "suspended", etc.
3. Backend logs will show which props had issues

### ⚠️ Slow Response Times

**Problem**: Getting player props is slower
**Solution**:
1. OpticOdds enrichment adds ~2-5 seconds
2. Caching is built in (10 minute TTL)
3. Consider fetching props separately from predictions

## API Reference

### OpticOddsService Methods

```python
# Get all props for a sport
await service.get_player_props(sport: str) -> List[Dict]

# Get specific player prop lines
await service.get_player_prop_lines(
    sport: str,
    player_name: str,
    prop_type: str
) -> Dict

# Get all props for a specific game
await service.get_all_player_props_for_event(
    sport: str,
    event_id: str
) -> List[Dict]

# Get best odds from all sportsbooks
await service.get_best_odds(
    sport: str,
    player_name: str,
    prop_type: str
) -> Dict

# Search props by player name
await service.search_player_props(
    sport: str,
    player_fragment: str
) -> List[Dict]

# Check API health
await service.health_check() -> bool
```

## Production Deployment

### Environment Variables (Production)

```bash
# .env.production
OPTIC_ODDS_API_KEY=your_prod_api_key
OPTIC_ODDS_BASE_URL=https://api.opticodds.com/v2
```

### Performance Optimization

1. **Enable Redis Caching**: OpticOdds responses cached for 10 minutes
2. **Monitor API Rate Limits**: OpticOdds has rate limits, watch for 429 errors
3. **Use CDN**: Cache player props at CDN level
4. **Batch Requests**: Fetch props for multiple sports in parallel

### Monitoring

```bash
# Check OpticOdds service logs
tail -f backend.log | grep OPTIC_ODDS

# Monitor enrichment success rate
grep "Enriched props with OpticOdds" backend.log
```

## Costs

OpticOdds pricing varies by usage tier. Check their pricing page for details. The integration is efficient:
- Caches results for 10 minutes
- Fetches only once per game
- Handles failures gracefully (falls back to ESPN data)

## Support

For OpticOdds API issues:
- Visit: https://opticodds.com/support
- Check API docs: https://opticodds.com/api-docs
- Contact: support@opticodds.com

For integration issues:
- Check logs: `python test_optic_odds_integration.py`
- Review this guide section: Troubleshooting
- Check backend logs for `[OPTIC_ODDS]` messages
