# Frontend Integration Guide - Player Props (NHL & Soccer)

## 🎯 Unified Endpoint for Frontend

### Main Endpoint: Get All Props Organized
```
GET /predictions/game/{sport_key}/{event_id}/full
```

**Headers**: `Authorization: Bearer {token}`

**Parameters**:
- `sport_key`: `icehockey_nhl` or `soccer_epl` (or other soccer leagues)
- `event_id`: Game event ID

**Response**:
```json
{
  "event_id": "401234567",
  "sport_key": "icehockey_nhl",
  "sport": "NHL",
  "props_summary": {
    "total_goals": 5,
    "total_assists": 5,
    "total_anytime_goals": 5,
    "total_players": 5
  },
  "goals": [
    {
      "id": "401234567_goals_Connor_McDavid",
      "player": "Connor McDavid",
      "market_name": "Goals",
      "prediction": "Over 0.5 Goals",
      "confidence": 78.5,
      "season_avg": 1.2,
      "recent_10_avg": 1.4,
      "point": 0.5,
      "over_line": 1.0,
      "under_line": 0.0
    }
  ],
  "assists": [
    {
      "id": "401234567_assists_Connor_McDavid",
      "player": "Connor McDavid",
      "market_name": "Assists",
      "prediction": "Over 0.5 Assists",
      "confidence": 72.1,
      "season_avg": 0.95,
      "recent_10_avg": 1.05
    }
  ],
  "anytime_goal": [
    {
      "id": "401234567_anytime_goal_Connor_McDavid",
      "player": "Connor McDavid",
      "market_name": "Anytime Goal",
      "prediction": "Anytime Goal: Yes",
      "confidence": 78.5,
      "season_avg": 1.2,
      "recent_10_avg": 1.4,
      "reasoning": [...]
    }
  ]
}
```

---

## 📋 Props Tab Component Structure

### State Management
```javascript
const [gameProps, setGameProps] = useState(null);
const [loading, setLoading] = useState(false);
const [error, setError] = useState(null);
const [activeTab, setActiveTab] = useState('goals'); // goals | assists | anytime_goal
```

### Fetch Props
```javascript
async function fetchGameProps(sportKey, eventId) {
  setLoading(true);
  try {
    const response = await fetch(
      `/api/predictions/game/${sportKey}/${eventId}/full`,
      {
        headers: { 'Authorization': `Bearer ${token}` }
      }
    );
    
    if (!response.ok) throw new Error('Failed to fetch');
    
    const data = await response.json();
    setGameProps(data);
  } catch (err) {
    setError(err.message);
  } finally {
    setLoading(false);
  }
}
```

---

## 🎨 UI Layout

### Tabs Structure
```
┌─────────────────────────────────────┐
│  GOALS  │  ASSISTS  │  ANYTIME GOAL │ ← Tabs
├─────────────────────────────────────┤
│                                     │
│  Player Props Display Below         │
│  (changes based on active tab)      │
│                                     │
└─────────────────────────────────────┘
```

### Goals/Assists Tab UI
```
┌────────────────────────────────────────────────┐
│ Connor McDavid              Over/Under Buttons │
├────────────────────────────────────────────────┤
│ Goals O/U - Confidence: 78.5%                  │
│ Line: 0.5                                      │
│ Season Avg: 1.2  |  Last 10: 1.4              │
│                                                │
│ [Over 1.0] [Under 0.0]                         │
│  78%        68%                                │
├────────────────────────────────────────────────┤
│ Leon Draisaitl              Over/Under Buttons │
│ Assists O/U - Confidence: 72.1%                │
│ ...                                            │
└────────────────────────────────────────────────┘
```

### Anytime Goal Tab UI
```
┌────────────────────────────────────────┐
│ Connor McDavid          78.5% Confident│
│ Likely to Score Anytime in Game?       │
│                                        │
│ ✓ YES     Anytime Goal in Game        │
│           Season: 1.20 goals/game      │
│           Last 10: 1.40 goals/game     │
├────────────────────────────────────────┤
│ Leon Draisaitl          72.1% Confident│
│                                        │
│ ✓ YES     Anytime Goal in Game        │
│           Season: 0.95 goals/game      │
│           Last 10: 1.05 goals/game     │
└────────────────────────────────────────┘
```

---

## 💻 React Component Example

```tsx
import React, { useState, useEffect } from 'react';

interface PropCard {
  player: string;
  prediction: string;
  confidence: number;
  season_avg?: number;
  recent_10_avg?: number;
  over_line?: number;
  under_line?: number;
  reasoning?: Array<any>;
  models?: Array<any>;
}

export function PlayerPropsTab({ sportKey, eventId, token }) {
  const [gameProps, setGameProps] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('goals');
  const [selectedProp, setSelectedProp] = useState(null);

  useEffect(() => {
    fetchProps();
  }, [sportKey, eventId]);

  const fetchProps = async () => {
    try {
      const response = await fetch(
        `/api/predictions/game/${sportKey}/${eventId}/full`,
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );
      const data = await response.json();
      setGameProps(data);
    } catch (error) {
      console.error('Error fetching props:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading props...</div>;
  if (!gameProps) return <div>No props available</div>;

  const currentProps = gameProps[activeTab] || [];

  return (
    <div className="player-props-container">
      {/* Tab Navigation */}
      <div className="props-tabs">
        <button
          className={`tab ${activeTab === 'goals' ? 'active' : ''}`}
          onClick={() => setActiveTab('goals')}
        >
          ⚽ Goals ({gameProps.props_summary.total_goals})
        </button>
        <button
          className={`tab ${activeTab === 'assists' ? 'active' : ''}`}
          onClick={() => setActiveTab('assists')}
        >
          👐 Assists ({gameProps.props_summary.total_assists})
        </button>
        <button
          className={`tab ${activeTab === 'anytime_goal' ? 'active' : ''}`}
          onClick={() => setActiveTab('anytime_goal')}
        >
          🟢 Anytime Goal ({gameProps.props_summary.total_anytime_goals})
        </button>
      </div>

      {/* Props Grid */}
      <div className="props-grid">
        {currentProps.map((prop, idx) => (
          <PropCard
            key={idx}
            prop={prop}
            isSelected={selectedProp?.id === prop.id}
            onSelect={() => setSelectedProp(prop)}
          />
        ))}
      </div>

      {/* Selected Prop Details */}
      {selectedProp && (
        <PropDetails
          prop={selectedProp}
          onClose={() => setSelectedProp(null)}
        />
      )}
    </div>
  );
}

function PropCard({ prop, isSelected, onSelect }) {
  const getConfidenceColor = (conf) => {
    if (conf >= 70) return 'high';
    if (conf >= 55) return 'medium';
    return 'low';
  };

  return (
    <div
      className={`prop-card ${getConfidenceColor(prop.confidence)}`}
      onClick={onSelect}
    >
      <div className="prop-header">
        <h4>{prop.player}</h4>
        <span className={`confidence ${getConfidenceColor(prop.confidence)}`}>
          {Math.round(prop.confidence)}%
        </span>
      </div>

      <p className="prop-prediction">{prop.prediction}</p>

      <div className="prop-stats">
        {prop.season_avg && (
          <div className="stat">
            <span className="label">Season:</span>
            <span className="value">{prop.season_avg.toFixed(2)}</span>
          </div>
        )}
        {prop.recent_10_avg && (
          <div className="stat">
            <span className="label">Last 10:</span>
            <span className="value">{prop.recent_10_avg.toFixed(2)}</span>
          </div>
        )}
      </div>

      {(prop.over_line || prop.under_line) && (
        <div className="prop-lines">
          {prop.over_line && (
            <button className="line-btn">Over {prop.over_line}</button>
          )}
          {prop.under_line && (
            <button className="line-btn">Under {prop.under_line}</button>
          )}
        </div>
      )}
    </div>
  );
}

function PropDetails({ prop, onClose }) {
  return (
    <div className="prop-details-modal">
      <h3>{prop.player} - {prop.market_name}</h3>
      
      <div className="details-section">
        <h4>Analysis</h4>
        {prop.reasoning?.map((r, idx) => (
          <div key={idx} className="reasoning-factor">
            <strong>{r.factor}</strong>: {r.explanation}
          </div>
        ))}
      </div>

      <div className="details-section">
        <h4>Models</h4>
        {prop.models?.map((m, idx) => (
          <div key={idx} className="model">
            {m.name}: {m.prediction} ({Math.round(m.confidence)}%)
          </div>
        ))}
      </div>

      <button onClick={onClose}>Close</button>
    </div>
  );
}
```

---

## 🎨 CSS Styling

```css
.player-props-container {
  padding: 20px;
  background: white;
  border-radius: 8px;
}

/* Tabs */
.props-tabs {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  border-bottom: 2px solid #e5e7eb;
}

.props-tabs .tab {
  padding: 12px 16px;
  background: none;
  border: none;
  border-bottom: 3px solid transparent;
  cursor: pointer;
  font-weight: 600;
  color: #6b7280;
  transition: all 0.2s ease;
}

.props-tabs .tab.active {
  color: #1f2937;
  border-bottom-color: #3b82f6;
}

/* Props Grid */
.props-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

/* Prop Card */
.prop-card {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  background: white;
}

.prop-card:hover {
  border-color: #3b82f6;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1);
}

.prop-card.high {
  border-left: 4px solid #10b981;
}

.prop-card.medium {
  border-left: 4px solid #f59e0b;
}

.prop-card.low {
  border-left: 4px solid #ef4444;
}

.prop-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.prop-header h4 {
  margin: 0;
  font-size: 16px;
}

.confidence {
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: 600;
  font-size: 12px;
}

.confidence.high {
  background: #dcfce7;
  color: #15803d;
}

.confidence.medium {
  background: #fed7aa;
  color: #92400e;
}

.confidence.low {
  background: #fee2e2;
  color: #991b1b;
}

.prop-prediction {
  margin: 0 0 12px 0;
  color: #374151;
  font-weight: 500;
}

.prop-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 12px;
}

.stat {
  background: #f9fafb;
  padding: 8px;
  border-radius: 4px;
  font-size: 12px;
}

.stat .label {
  color: #6b7280;
  display: block;
  margin-bottom: 2px;
}

.stat .value {
  color: #1f2937;
  font-weight: 600;
}

.prop-lines {
  display: flex;
  gap: 8px;
}

.line-btn {
  flex: 1;
  padding: 8px;
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
  font-size: 12px;
  transition: all 0.2s ease;
}

.line-btn:hover {
  background: #e5e7eb;
  border-color: #3b82f6;
}
```

---

## 🔗 Related Endpoints

### Get Anytime Goal Scorers (Unlock Feature)
```
GET /predictions/anytime-goal-scorers/{sport_key}/{event_id}
```
Returns top 2 scorers per team for the unlock feature.

### Get All Props (Legacy)
```
GET /predictions/props/{sport_key}/{event_id}
```
Returns all props in flat array format.

---

## 🚀 Implementation Checklist

- [ ] Fetch game props on component mount
- [ ] Render three tabs (Goals, Assists, Anytime Goal)
- [ ] Display props in grid layout
- [ ] Show confidence with color coding
- [ ] Click prop to show detailed reasoning
- [ ] Display season/recent averages
- [ ] Show over/under lines for goals/assists
- [ ] Handle loading state
- [ ] Handle error state
- [ ] Make mobile responsive
- [ ] Add animations for tab switching

---

## 📊 Data Consistency (NHL = Soccer)

Both NHL and Soccer now have:

✅ **Goals Tab**:
- Dynamic over/under lines
- Season and recent 10-game averages
- 7-factor reasoning analysis
- 6 ML model ensemble outputs
- Confidence 0-100%

✅ **Assists Tab**:
- Dynamic over/under lines
- Season and recent 10-game averages
- 7-factor reasoning analysis
- 6 ML model ensemble outputs
- Confidence 0-100%

✅ **Anytime Goal Tab**:
- Yes/No prediction (50% confidence threshold)
- Season and recent 10-game averages
- 6-factor detailed reasoning
- 5 ML model ensemble outputs
- Confidence 0-100%

---

## 🎯 Testing

```bash
# Test Hockey
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/predictions/game/icehockey_nhl/401234567/full"

# Test Soccer  
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/predictions/game/soccer_epl/789012/full"
```

---

**Status**: ✅ Backend ready for frontend integration. Both NHL and Soccer fully aligned!
