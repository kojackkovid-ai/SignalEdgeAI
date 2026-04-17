# Frontend Implementation Checklist - Anytime Goal Unlock Feature

## Quick Start

### Component Tree
```
GameDetailsView
├── StatsTabsContainer
│   ├── TeamStatsTab
│   ├── PlayerStatsTab  
│   └── ⭐ NEW: UnlockAnytimeGoalTab (or Button)
│
└── (Modal Container)
    └── AnytimeGoalScorersModal (when unlocked)
```

---

## Implementation Steps

### Step 1: Add Tab/Button to Stats Section
**Location**: Your game details component where Team Stats and Player Stats tabs are shown

```typescript
import { useState } from 'react';

function GameDetailsView({ eventId, sportKey, gameData }) {
  const [showScorerModal, setShowScorerModal] = useState(false);
  const [scorersData, setScorersData] = useState(null);

  const handleUnlockClick = async () => {
    try {
      const response = await fetch(
        `/api/predictions/anytime-goal-scorers/${sportKey}/${eventId}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        }
      );
      const data = await response.json();
      
      if (response.ok) {
        setScorersData(data);
        setShowScorerModal(true);
      } else if (response.status === 403) {
        // Show upsell modal - tier required
        showUpgradeModal('Upgrade to unlock Anytime Goal scorers');
      }
    } catch (error) {
      console.error('Error fetching scorers:', error);
    }
  };

  return (
    <div className="game-details">
      {/* Existing tabs */}
      <div className="stats-tabs">
        <button className="tab">Team Stats</button>
        <button className="tab">Player Stats</button>
        
        {/* NEW: Unlock button */}
        <button 
          className="tab unlock-button"
          onClick={handleUnlockClick}
        >
          🔓 Unlock Anytime Goal
        </button>
      </div>

      {/* Existing content */}
      {/* ... Team Stats, Player Stats content ... */}

      {/* Modal */}
      {showScorerModal && (
        <AnytimeGoalScorersModal
          data={scorersData}
          onClose={() => setShowScorerModal(false)}
        />
      )}
    </div>
  );
}
```

### Step 2: Create Modal Component
**Create file**: `src/components/AnytimeGoalScorersModal.tsx`

```typescript
import React from 'react';
import './AnytimeGoalScorersModal.css';

interface Scorer {
  player: string;
  confidence: number;
  season_avg: number;
  recent_avg: number;
  prediction: string;
  reasoning?: string;
}

interface TeamScorers {
  name: string;
  top_scorers: Scorer[];
}

interface AnytimeGoalScorersModalProps {
  data: {
    home_team: TeamScorers;
    away_team: TeamScorers;
    league: string;
    event_id: string;
  };
  onClose: () => void;
}

export function AnytimeGoalScorersModal({ data, onClose }: AnytimeGoalScorersModalProps) {
  if (!data) return null;

  const { home_team, away_team } = data;

  const ScorerCard = ({ scorer, rank }: { scorer: Scorer; rank: number }) => (
    <div className={`scorer-card rank-${rank}`}>
      <div className="scorer-header">
        <span className="rank-badge">{rank}</span>
        <span className="player-name">{scorer.player}</span>
        <span className="confidence-badge">{Math.round(scorer.confidence)}%</span>
      </div>
      <div className="scorer-stats">
        <div className="stat">
          <span className="label">Season Avg:</span>
          <span className={`value ${scorer.season_avg > 0.4 ? 'high' : ''}`}>
            {scorer.season_avg?.toFixed(2)} goals/game
          </span>
        </div>
        <div className="stat">
          <span className="label">Last 10:</span>
          <span className={`value ${scorer.recent_avg > 0.4 ? 'high' : ''}`}>
            {scorer.recent_avg?.toFixed(2)} goals/game
          </span>
        </div>
      </div>
      {scorer.reasoning && (
        <div className="reasoning">
          <p className="text-sm text-gray-600">{scorer.reasoning}</p>
        </div>
      )}
    </div>
  );

  return (
    <>
      {/* Overlay */}
      <div className="modal-overlay" onClick={onClose}></div>

      {/* Modal */}
      <div className="anytime-goal-modal">
        <div className="modal-header">
          <h2>🔓 Anytime Goal Scorers</h2>
          <p className="subtitle">
            Top 2 players from each team most likely to score
          </p>
          <button className="close-btn" onClick={onClose}>✕</button>
        </div>

        <div className="modal-content">
          {/* Home Team */}
          <div className="team-section home-team">
            <div className="team-header">
              <span className="home-indicator">🏠 HOME</span>
              <h3>{home_team.name}</h3>
            </div>
            <div className="scorers-list">
              {home_team.top_scorers.length > 0 ? (
                home_team.top_scorers.map((scorer, idx) => (
                  <ScorerCard key={`${scorer.player}-${idx}`} scorer={scorer} rank={idx + 1} />
                ))
              ) : (
                <p className="no-scorers">No scorers available</p>
              )}
            </div>
          </div>

          {/* Away Team */}
          <div className="team-section away-team">
            <div className="team-header">
              <span className="away-indicator">✈️ AWAY</span>
              <h3>{away_team.name}</h3>
            </div>
            <div className="scorers-list">
              {away_team.top_scorers.length > 0 ? (
                away_team.top_scorers.map((scorer, idx) => (
                  <ScorerCard key={`${scorer.player}-${idx}`} scorer={scorer} rank={idx + 1} />
                ))
              ) : (
                <p className="no-scorers">No scorers available</p>
              )}
            </div>
          </div>
        </div>

        <div className="modal-footer">
          <p className="text-xs text-gray-500">
            Rankings based on statistical analysis and recent performance data from ESPN
          </p>
          <button className="btn-close" onClick={onClose}>Close</button>
        </div>
      </div>
    </>
  );
}
```

### Step 3: Add Styling
**Create file**: `src/components/AnytimeGoalScorersModal.css`

```css
/* Modal Overlay */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 999;
}

/* Modal Container */
.anytime-goal-modal {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  z-index: 1000;
  max-width: 600px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  padding: 24px;
  border-bottom: 1px solid #e5e7eb;
  position: relative;
}

.modal-header h2 {
  margin: 0 0 8px 0;
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
}

.modal-header .subtitle {
  margin: 0;
  font-size: 14px;
  color: #6b7280;
}

.close-btn {
  position: absolute;
  top: 16px;
  right: 16px;
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #6b7280;
}

.close-btn:hover {
  color: #1f2937;
}

/* Modal Content */
.modal-content {
  padding: 24px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

@media (max-width: 600px) {
  .modal-content {
    grid-template-columns: 1fr;
  }
}

/* Team Sections */
.team-section {
  background: #f9fafb;
  border-radius: 8px;
  padding: 16px;
}

.team-section.home-team {
  border: 2px solid #dbeafe;
}

.team-section.away-team {
  border: 2px solid #fef3c7;
}

.team-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e5e7eb;
}

.team-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  flex: 1;
}

.home-indicator {
  font-size: 14px;
  background: #dbeafe;
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: 500;
}

.away-indicator {
  font-size: 14px;
  background: #fef3c7;
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: 500;
}

/* Scorers List */
.scorers-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* Scorer Card */
.scorer-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 12px;
  transition: all 0.2s ease;
}

.scorer-card:hover {
  border-color: #3b82f6;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1);
}

.scorer-card.rank-1 {
  border-left: 4px solid #fbbf24;
  background: #fffbeb;
}

.scorer-card.rank-2 {
  border-left: 4px solid #a8a29e;
  background: #fafaf9;
}

.scorer-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.rank-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: linear-gradient(135deg, #3b82f6, #1e40af);
  color: white;
  border-radius: 50%;
  font-weight: 600;
  font-size: 14px;
}

.player-name {
  font-weight: 600;
  color: #1f2937;
  font-size: 14px;
  flex: 1;
}

.confidence-badge {
  background: #dcfce7;
  color: #15803d;
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: 600;
  font-size: 12px;
}

.scorer-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 8px;
}

.stat {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat .label {
  font-size: 11px;
  color: #6b7280;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat .value {
  font-size: 12px;
  color: #374151;
  font-weight: 600;
}

.stat .value.high {
  color: #059669;
  font-weight: 700;
}

.reasoning {
  font-size: 12px;
  color: #6b7280;
  padding-top: 8px;
  border-top: 1px solid #e5e7eb;
  margin-top: 8px;
}

.no-scorers {
  text-align: center;
  color: #9ca3af;
  padding: 16px;
  font-size: 14px;
}

/* Modal Footer */
.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid #e5e7eb;
  background: #f9fafb;
  border-radius: 0 0 12px 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.modal-footer .text-xs {
  font-size: 12px;
  color: #9ca3af;
  text-align: center;
}

.btn-close {
  padding: 8px 16px;
  background: #e5e7eb;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  color: #1f2937;
  transition: all 0.2s ease;
}

.btn-close:hover {
  background: #d1d5db;
}

/* Unlock Button Styling */
.unlock-button {
  background: linear-gradient(135deg, #3b82f6, #1e40af);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.unlock-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
}

.unlock-button:active {
  transform: translateY(0);
}
```

---

## API Integration

### Using a Service/Hook
**Create file**: `src/services/predictions.ts`

```typescript
export interface Scorer {
  player: string;
  confidence: number;
  season_avg: number;
  recent_avg: number;
  prediction: string;
  reasoning?: string;
}

export interface AnytimeGoalScorersResponse {
  home_team: {
    name: string;
    top_scorers: Scorer[];
  };
  away_team: {
    name: string;
    top_scorers: Scorer[];
  };
  event_id: string;
  sport_key: string;
  league: string;
  error?: string;
}

export async function getAnytimeGoalScorers(
  sportKey: string,
  eventId: string
): Promise<AnytimeGoalScorersResponse> {
  const token = localStorage.getItem('auth_token');
  
  const response = await fetch(
    `/api/predictions/anytime-goal-scorers/${sportKey}/${eventId}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    }
  );

  if (!response.ok) {
    if (response.status === 403) {
      throw new Error('TIER_REQUIRED'); // Handle in UI for upsell
    }
    throw new Error(`API Error: ${response.status}`);
  }

  return response.json();
}
```

### Using React Hook
**Create file**: `src/hooks/useAnytimeGoalScorers.ts`

```typescript
import { useState, useCallback } from 'react';
import { getAnytimeGoalScorers, AnytimeGoalScorersResponse } from '../services/predictions';

export function useAnytimeGoalScorers() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<AnytimeGoalScorersResponse | null>(null);

  const fetch = useCallback(async (sportKey: string, eventId: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await getAnytimeGoalScorers(sportKey, eventId);
      setData(result);
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { data, loading, error, fetch };
}
```

---

## Testing Checklist

- [ ] Click "Unlock Anytime Goal" button loads data
- [ ] Modal displays home and away teams correctly
- [ ] Top 2 scorers show for each team
- [ ] Confidence percentages display correctly
- [ ] Season/Recent averages show with 2 decimal places
- [ ] Modal closes when clicking X or overlay
- [ ] Shows loading state while fetching
- [ ] Shows error message if API fails
- [ ] Shows tier upgrade message if user is Starter tier
- [ ] Mobile responsive - single column layout
- [ ] Scores are sorted by confidence (highest first)
- [ ] No duplicate players in list

---

## Error Handling

### 403 - Tier Not Sufficient
```typescript
if (error === 'TIER_REQUIRED') {
  showUpgradePrompt('Unlock player scorers by upgrading to Basic tier');
  // Navigate to subscription page or show upsell modal
}
```

### 504 - Timeout
```typescript
if (error?.includes('timeout')) {
  showErrorMessage('Request timed out. Please try again.');
}
```

### Network Error
```typescript
if (error && !error.includes('TIER')) {
  showErrorMessage('Unable to load scorers. Check your connection.');
}
```

---

## Performance Tips

1. **Caching**: Consider caching scorer data for same event_id within 5 minutes
2. **Lazy Load**: Don't fetch until user clicks unlock button
3. **Debounce**: If multiple unlock attempts within 1s, use cached result
4. **Suspense**: Wrap in React Suspense for cleaner async handling

---

## Accessibility Considerations

- [ ] Modal has proper ARIA labels
- [ ] Keyboard navigation (Esc to close)
- [ ] Color not sole indicator (use badges, icons)
- [ ] Confidence percentage explained in text
- [ ] Player names are large enough to read

---

## Integration Points

**Props Page** → Links to scorers data for context  
**Betting Page** → Can show "Player X to score" betting prop from unlock feature  
**User Dashboard** → Show recommended anytime goal bets  
**Notifications** → Alert when high-confidence scorer available

---

## Support/Help

For questions:
- Backend API docs: See `PLAYER_PROPS_REVAMP_STATUS.md`
- Endpoint curl test: `curl http://localhost:8000/predictions/anytime-goal-scorers/icehockey_nhl/EVENT_ID`
- Backend logs: Check `espn_prediction_service.py` logs with `[ANYTIME_GOAL]` prefix
