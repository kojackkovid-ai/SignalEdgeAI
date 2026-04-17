# 🎯 Quick Reference: Player Props Revamp

## ✅ What's Implemented

### Backend - COMPLETE
- ✅ NHL Props: Goals O/U, Assists O/U, Anytime Goal
- ✅ Soccer Props: Goals O/U, Assists O/U, Anytime Goal  
- ✅ Unlock Feature: Top 2 scorers per team endpoint
- ✅ Data-driven confidence ranking (0-100%)
- ✅ Real ESPN statistics
- ✅ Tier gating (Basic+ required)

---

## 🔌 API Endpoints

### Get Props
```
GET /predictions/props/{sport_key}/{event_id}
```
Returns: Goals/Assists/Anytime Goal props for all players

### Get Scorers (UNLOCK)
```
GET /predictions/anytime-goal-scorers/{sport_key}/{event_id}
Headers: Authorization: Bearer {token}
```
Returns: Top 2 scorers per team

---

## 📁 Documentation

| File | Purpose |
|------|---------|
| `PLAYER_PROPS_REVAMP_STATUS.md` | Complete technical guide |
| `FRONTEND_ANYTIME_GOAL_IMPLEMENTATION.md` | Step-by-step React code |
| `PLAYER_PROPS_COMPLETE_GUIDE.md` | Overview & architecture |
| `QUICK_REFERENCE.md` | This file |

---

## 🎨 Frontend Needs

1. Add "Unlock Anytime Goal" button to stats section
2. Create modal showing top 2 scorers for each team
3. Call `/anytime-goal-scorers` endpoint on button click
4. Handle 403 (tier) and other errors
5. Show loading + error states

---

## 💰 Tier Gating
- Starter: ❌ Blocked (403 Forbidden)
- Basic+: ✅ Unlocked

**Upsell Opportunity**: Show upgrade prompt when Starter tries to unlock

---

## 📊 Response Format

```json
{
  "home_team": {
    "name": "Team Name",
    "top_scorers": [
      {
        "player": "Player Name",
        "confidence": 78.5,
        "season_avg": 1.2,
        "recent_avg": 1.4,
        "prediction": "Yes"
      }
    ]
  },
  "away_team": {
    "name": "Team Name",
    "top_scorers": [...]
  }
}
```

---

## 🚀 Next Steps

1. **Frontend**: Build modal & button
2. **Testing**: Verify with live games
3. **Launch**: Deploy to production
4. **Monitor**: Track tier conversions

---

## 🆘 Support

- Backend code: `/backend/app/services/espn_prediction_service.py`
- Routes: `/backend/app/routes/predictions.py`
- Logs: Look for `[ANYTIME_GOAL]` prefix
- Example: Call endpoint with curl to test

---

**Status**: ✅ Ready for Frontend Integration
