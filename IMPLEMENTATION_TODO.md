# Sports Prediction Platform - Implementation TODO

## Phase 1: Remove Fake/Hardcoded Data ✅ IN PROGRESS
- [ ] 1.1 Remove `_get_sport_default_line` hardcoded defaults in espn_prediction_service.py
- [ ] 1.2 Improve `_calculate_dynamic_line` to fail gracefully when ESPN data unavailable
- [ ] 1.3 Add proper null/empty handling instead of fake defaults
- [ ] 1.4 Update `_determine_over_under` to handle missing data properly

## Phase 2: Improve ESPN API Integration
- [ ] 2.1 Add more robust error handling for API failures
- [ ] 2.2 Implement better caching strategies
- [ ] 2.3 Add support for more sports/leagues
- [ ] 2.4 Improve rate limiting and retry logic

## Phase 3: Enhance Confidence Calculations
- [ ] 3.1 Improve Bayesian confidence calculations
- [ ] 3.2 Add more real data validation
- [ ] 3.3 Ensure minimum confidence is data-driven
- [ ] 3.4 Remove hash-based seeding in reasoning generation

## Phase 4: UI Improvements
- [ ] 4.1 Remove fallback UI data when API fails
- [ ] 4.2 Better loading states
- [ ] 4.3 Improved error messaging
- [ ] 4.4 Add retry buttons

## Priority Fixes (Critical)
- [ ] CRITICAL: Remove default point values (15.5, 5.5, etc.) when ESPN data unavailable
- [ ] CRITICAL: Return null/empty instead of fake data for props
- [ ] CRITICAL: Handle API failures gracefully without fallback fake data

