# Sport-Specific Reasoning Fix - Implementation Plan

## Current Issues
- Generic cookie-cutter reasoning across all sports
- Same phrases like "favorable indicators in key matchup areas" appear everywhere
- No sport-specific analysis (NBA stats vs NHL stats vs NFL stats)
- Injury impact is just a number, not specific player names
- No head-to-head history details
- No key matchup analysis

## Implementation Steps

### Step 1: Create Sport-Specific Reasoning Engine
- [ ] Create `sport_specific_reasoning.py` with dedicated analyzers for each sport
- [ ] NBA: Points, shooting, rebounds, pace, efficiency metrics
- [ ] NHL: Goals, power play, shots, goaltending
- [ ] NFL: Passing, rushing, red zone, turnovers, time of possession
- [ ] MLB: Pitching, batting, bullpen, recent form
- [ ] Soccer: Possession, xG, shots on target, clean sheets

### Step 2: Enhance Injury Analysis
- [ ] Fetch specific injured player names from ESPN API
- [ ] Categorize by importance (starter/key player vs bench)
- [ ] Explain position-specific impact
- [ ] Show expected performance impact in specific terms

### Step 3: Add Head-to-Head History
- [ ] Fetch last 3-5 meetings between teams
- [ ] Show scores and differentials
- [ ] Analyze venue-specific trends
- [ ] Compare current rosters to previous meetings

### Step 4: Implement Key Matchup Analysis
- [ ] Identify critical positional matchups
- [ ] Compare star players to opponent's defensive strengths
- [ ] Show historical performance in these matchups

### Step 5: Update Prediction Service
- [ ] Replace `_generate_unique_reasoning` with new sport-specific system
- [ ] Integrate new reasoning engine
- [ ] Remove generic template-based explanations

### Step 6: Testing
- [ ] Test NBA predictions for detailed basketball analysis
- [ ] Test NHL predictions for hockey-specific metrics
- [ ] Test NFL predictions for football-specific factors
- [ ] Verify no generic phrases appear
- [ ] Confirm each game has unique reasoning

## Progress Tracking
- [x] Step 1: Create Sport-Specific Reasoning Engine - COMPLETED
  - Created `sport_specific_reasoning.py` with detailed analyzers for NBA, NHL, NFL, MLB, Soccer
  - Implemented sport-specific statistical comparisons
  - Added detailed injury analysis with player names
  - Added head-to-head history fetching
  - Added key matchup analysis
  - Added weather impact analysis
  - Added market data analysis
- [x] Step 2: Enhance Injury Analysis - COMPLETED (in new engine)
- [x] Step 3: Add Head-to-Head History - COMPLETED (in new engine)
- [x] Step 4: Implement Key Matchup Analysis - COMPLETED (in new engine)
- [x] Step 5: Update Prediction Service - COMPLETED
  - Modified `espn_prediction_service.py` to use new SportSpecificReasoningEngine
  - Replaced `_generate_unique_reasoning` with `_generate_basic_reasoning` (fallback)
  - Updated imports and initialization
  - Integrated sport-specific reasoning generation in `_create_prediction_from_game`
- [x] Step 6: Testing - READY FOR TESTING
  - All components integrated and ready for testing
  - Sport-specific reasoning engine active
  - Fallback reasoning available if needed
