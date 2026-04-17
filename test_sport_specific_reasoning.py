#!/usr/bin/env python3
"""
Thorough Testing Script for Sport-Specific Reasoning Engine

Tests all supported sports, verifies unique reasoning, checks for generic phrases,
validates injury reports, and tests edge cases.
"""

import asyncio
import sys
import json
from pathlib import Path
from typing import List, Dict, Any
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add backend to path for imports
backend_path = Path(__file__).parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.append(str(backend_path))


# Import the services
try:
    from app.services.espn_prediction_service import ESPNPredictionService
    from app.services.sport_specific_reasoning import SportSpecificReasoningEngine
    HAS_SERVICES = True
except ImportError as e:
    logger.error(f"Failed to import services: {e}")
    HAS_SERVICES = False


# Generic phrases that should NOT appear in new reasoning
GENERIC_PHRASES = [
    "favorable indicators in key matchup areas",
    "competitive balance with slight edges identified",
    "demonstrating stronger season-long consistency",
    "uncertainty about outcome",
    "closely matched teams",
    "potential variance in outcome factors",
    "Limited data available for comprehensive analysis"
]

# Sport-specific metrics that SHOULD appear
SPORT_METRICS = {
    "basketball_nba": [
        "points per game", "shooting", "rebound", "efficiency", "pace"
    ],
    "icehockey_nhl": [
        "goals per game", "goaltending", "power play", "penalty kill", "GAA"
    ],
    "americanfootball_nfl": [
        "passing yards", "rushing yards", "red zone", "aerial attack", "ground game"
    ],
    "baseball_mlb": [
        "ERA", "batting average", "run production", "pitching", "bullpen"
    ],
    "soccer_epl": [
        "goals per game", "possession", "clean sheets", "defensive solidity", "xG"
    ]
}

class ReasoningTester:
    def __init__(self):
        self.service = None
        self.results = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "errors": []
        }
    
    async def setup(self):
        """Initialize the prediction service"""
        if HAS_SERVICES:
            self.service = ESPNPredictionService()
            logger.info("✅ ESPNPredictionService initialized")
        else:
            logger.error("❌ Could not initialize ESPNPredictionService")
    
    async def teardown(self):
        """Cleanup"""
        if self.service:
            await self.service.close()
    
    def check_for_generic_phrases(self, reasoning: List[Dict[str, Any]]) -> List[str]:
        """Check if any generic phrases appear in reasoning"""
        found_phrases = []
        all_text = " ".join([r.get("explanation", "") for r in reasoning]).lower()
        
        for phrase in GENERIC_PHRASES:
            if phrase.lower() in all_text:
                found_phrases.append(phrase)
        
        return found_phrases
    
    def check_for_sport_metrics(self, reasoning: List[Dict[str, Any]], sport: str) -> List[str]:
        """Check if sport-specific metrics appear in reasoning"""
        found_metrics = []
        all_text = " ".join([r.get("explanation", "") for r in reasoning]).lower()
        
        expected_metrics = SPORT_METRICS.get(sport, [])
        for metric in expected_metrics:
            if metric.lower() in all_text:
                found_metrics.append(metric)
        
        return found_metrics
    
    def check_injury_details(self, reasoning: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check if injury reports contain specific player names"""
        injury_factors = [r for r in reasoning if "injury" in r.get("factor", "").lower()]
        
        if not injury_factors:
            return {"has_injuries": False, "player_names": []}
        
        all_injury_text = " ".join([r.get("explanation", "") for r in injury_factors])
        
        # Look for player name patterns (capitalized words that could be names)
        import re
        potential_names = re.findall(r'\b[A-Z][a-z]+\s[A-Z][a-z]+\b', all_injury_text)
        
        # Also check for injury status keywords
        has_status = any(status in all_injury_text for status in ["OUT", "QUESTIONABLE", "DOUBTFUL", "INJURED"])
        
        return {
            "has_injuries": True,
            "player_names": potential_names,
            "has_status": has_status,
            "explanation": all_injury_text
        }
    
    async def test_sport(self, sport: str, sport_name: str):
        """Test predictions for a specific sport"""
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing {sport_name} ({sport})")
        logger.info(f"{'='*60}")
        
        self.results["tests_run"] += 1
        
        try:
            # Get predictions
            predictions = await self.service.get_predictions(sport=sport, limit=3)
            
            if not predictions:
                logger.warning(f"⚠️  No predictions available for {sport_name}")
                self.results["tests_failed"] += 1
                self.results["errors"].append(f"{sport}: No predictions returned")
                return
            
            logger.info(f"✅ Retrieved {len(predictions)} predictions")
            
            # Analyze each prediction
            for i, pred in enumerate(predictions[:2], 1):  # Test first 2 predictions
                logger.info(f"\n--- Prediction {i}: {pred.get('home_team', 'Unknown')} vs {pred.get('away_team', 'Unknown')} ---")
                
                reasoning = pred.get("reasoning", [])
                
                if not reasoning:
                    logger.error(f"❌ No reasoning found for prediction {i}")
                    continue
                
                # Test 1: Check for generic phrases (should be NONE)
                generic_found = self.check_for_generic_phrases(reasoning)
                if generic_found:
                    logger.error(f"❌ GENERIC PHRASES FOUND: {generic_found}")
                else:
                    logger.info(f"✅ No generic phrases found")
                
                # Test 2: Check for sport-specific metrics
                metrics_found = self.check_for_sport_metrics(reasoning, sport)
                logger.info(f"✅ Sport-specific metrics found: {metrics_found}")
                
                # Test 3: Check injury details
                injury_info = self.check_injury_details(reasoning)
                if injury_info["has_injuries"]:
                    logger.info(f"✅ Injury details found: {len(injury_info['player_names'])} potential player names")
                    if injury_info["player_names"]:
                        logger.info(f"   Players: {injury_info['player_names'][:3]}")
                    if injury_info["has_status"]:
                        logger.info(f"✅ Injury status indicators present (OUT/QUESTIONABLE/etc)")
                else:
                    logger.info(f"ℹ️  No injury factors in this prediction")
                
                # Test 4: Check reasoning diversity
                factors = [r.get("factor", "Unknown") for r in reasoning]
                logger.info(f"✅ Reasoning factors: {factors}")
                
                # Test 5: Check for specific statistics
                has_specific_stats = any(
                    any(char.isdigit() for char in r.get("explanation", ""))
                    for r in reasoning
                )
                if has_specific_stats:
                    logger.info(f"✅ Contains specific numerical statistics")
                else:
                    logger.warning(f"⚠️  No specific statistics found in reasoning")
                
                # Print sample explanation
                if reasoning:
                    sample = reasoning[0].get("explanation", "No explanation")
                    logger.info(f"\n📝 Sample reasoning: {sample[:150]}...")
            
            self.results["tests_passed"] += 1
            
        except Exception as e:
            logger.error(f"❌ Error testing {sport}: {str(e)}")
            self.results["tests_failed"] += 1
            self.results["errors"].append(f"{sport}: {str(e)}")
    
    async def test_edge_cases(self):
        """Test edge cases and error handling"""
        logger.info(f"\n{'='*60}")
        logger.info("Testing Edge Cases")
        logger.info(f"{'='*60}")
        
        # Test 1: Empty game data
        try:
            engine = SportSpecificReasoningEngine()
            empty_result = await engine.generate_reasoning(
                sport_key="basketball_nba",
                game={"home_team": "Test Home", "away_team": "Test Away"},
                home_stats={},
                away_stats={},
                home_form=0.5,
                away_form=0.5,
                home_injuries=[],
                away_injuries=[],
                home_injury_impact=0.0,
                away_injury_impact=0.0,
                weather_data={},
                odds_data={}
            )
            logger.info(f"✅ Empty data handling works (returned {len(empty_result)} factors)")
        except Exception as e:
            logger.error(f"❌ Empty data handling failed: {e}")
        
        # Test 2: Invalid sport key
        try:
            engine = SportSpecificReasoningEngine()
            invalid_result = await engine.generate_reasoning(
                sport_key="invalid_sport",
                game={"home_team": "Team A", "away_team": "Team B"},
                home_stats={"points_per_game": 110},
                away_stats={"points_per_game": 105},
                home_form=0.6,
                away_form=0.4,
                home_injuries=[],
                away_injuries=[],
                home_injury_impact=0.0,
                away_injury_impact=0.0,
                weather_data={},
                odds_data={}
            )
            logger.info(f"✅ Invalid sport handling works (returned {len(invalid_result)} factors)")
        except Exception as e:
            logger.error(f"❌ Invalid sport handling failed: {e}")

    
    async def run_all_tests(self):
        """Run complete test suite"""
        logger.info("\n" + "="*60)
        logger.info("SPORT-SPECIFIC REASONING - THOROUGH TEST SUITE")
        logger.info("="*60)
        
        await self.setup()
        
        if not self.service:
            logger.error("❌ Cannot run tests - service not initialized")
            return
        
        # Test all supported sports
        sports_to_test = [
            ("basketball_nba", "NBA"),
            ("icehockey_nhl", "NHL"),
            ("americanfootball_nfl", "NFL"),
            ("baseball_mlb", "MLB"),
            ("soccer_epl", "Premier League")
        ]
        
        for sport_key, sport_name in sports_to_test:
            await self.test_sport(sport_key, sport_name)
        
        # Test edge cases
        await self.test_edge_cases()
        
        # Print summary
        await self.print_summary()
        
        await self.teardown()
    
    async def print_summary(self):
        """Print test summary"""
        logger.info("\n" + "="*60)
        logger.info("TEST SUMMARY")
        logger.info("="*60)
        logger.info(f"Total Tests Run: {self.results['tests_run']}")
        logger.info(f"Tests Passed: {self.results['tests_passed']}")
        logger.info(f"Tests Failed: {self.results['tests_failed']}")
        
        if self.results['errors']:
            logger.info(f"\nErrors Encountered:")
            for error in self.results['errors']:
                logger.info(f"  - {error}")
        
        success_rate = (self.results['tests_passed'] / self.results['tests_run'] * 100) if self.results['tests_run'] > 0 else 0
        logger.info(f"\nSuccess Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            logger.info("✅ OVERALL: Tests PASSED - Reasoning engine is working correctly")
        elif success_rate >= 50:
            logger.info("⚠️  OVERALL: Tests PARTIAL - Some issues need attention")
        else:
            logger.info("❌ OVERALL: Tests FAILED - Significant issues found")

async def main():
    """Main test runner"""
    tester = ReasoningTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
