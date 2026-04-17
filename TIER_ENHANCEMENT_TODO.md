# Tier Enhancement Implementation Plan

## Task: Revamp Player Props to be Tier-Specific with Full Data

### Files to Modify:
1. `backend/app/routes/predictions.py` - Add enhanced tier features
2. `backend/app/services/espn_prediction_service.py` - Add team info and richer content
3. `frontend/src/pages/Dashboard.tsx` - Display team name in props

### Implementation Steps:

## Step 1: Update predictions.py - Enhanced Tier Features
- Add new tier feature flags: show_full_reasoning, show_advanced_analysis, show_detailed_models
- Elite: ALL features unlocked
- Pro: Full reasoning, detailed models
- Basic: Basic reasoning, limited models
- Starter: Minimal content (current)

## Step 2: Update espn_prediction_service.py
- Add team_name field to each player prop
- Generate richer reasoning with 5+ factors
- Add more detailed model breakdown

## Step 3: Update Dashboard.tsx
- Display team name next to player name
- Show enhanced content based on tier

### Tier Feature Matrix:
| Feature | Starter | Basic | Pro | Elite |
|---------|---------|-------|-----|-------|
| show_odds | No | Yes | Yes | Yes |
| show_reasoning | No | Yes (2) | Yes (4) | Yes (6+) |
| show_models | No | No | Yes (3) | Yes (ALL) |
| show_line | No | Yes | Yes | Yes |
| show_full_reasoning | No | No | Yes | Yes |
| show_advanced_analysis | No | No | No | Yes |
| show_detailed_models | No | No | No | Yes |

### Progress:
- [x] Step 1: Update predictions.py with enhanced tier features
- [ ] Step 2: Update espn_prediction_service.py (add team info + richer reasoning/models)

