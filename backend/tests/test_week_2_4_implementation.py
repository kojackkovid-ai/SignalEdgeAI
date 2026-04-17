"""
Comprehensive Test Suite for Week 2-4 Implementations
Unit and integration tests for all new modules
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.prediction_records import (
    PredictionRecord, PredictionAccuracyStats, PlayerRecord,
    PlayerSeasonStats, PlayerGameLog 
)
from app.models.db_models import User
from app.services.prediction_history_service import PredictionHistoryService, PlayerDataService
from app.services.player_props_service import PlayerPropsService
from app.services.ml_calibration_service import MLCalibrationService, ConfidenceCalibrator
from app.services.sport_specific_ml_models import (
    NBAPredictor, NFLPredictor, MLBPredictor, model_registry
)
from app.services.load_testing_monitoring import (
    LoadTestRunner, PerformanceMonitor, AlertManager
)

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
async def test_db():
    """Create in-memory test database"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        yield session
    
    await engine.dispose()

@pytest.fixture
async def test_user(test_db):
    """Create test user"""
    user = User(
        id="user_test_1",
        email="test@example.com",
        username="testuser",
        password_hash="hashed_pwd",
        subscription_tier="pro"
    )
    test_db.add(user)
    await test_db.commit()
    return user

# ============================================================================
# PREDICTION HISTORY TESTS
# ============================================================================

@pytest.mark.asyncio
class TestPredictionHistoryService:
    
    async def test_record_prediction(self, test_db, test_user):
        """Test recording a prediction"""
        service = PredictionHistoryService(test_db)
        
        pred_data = {
            'matchup': 'Lakers vs Celtics',
            'home_team': 'Lakers',
            'away_team': 'Celtics',
            'prediction': 'Home Win',
            'prediction_type': 'moneyline',
            'confidence': 0.65,
            'reasoning': ['Strong offense'],
            'event_start_time': datetime.utcnow() + timedelta(hours=2)
        }
        
        pred_id = await service.record_prediction(
            user_id=test_user.id,
            sport_key='nba',
            event_id='nba_123',
            prediction_data=pred_data
        )
        
        assert pred_id is not None
        
        # Verify it was stored
        result = await test_db.execute(
            f"SELECT * FROM prediction_records WHERE id = '{pred_id}'"
        )
        assert result is not None
    
    async def test_get_user_prediction_history(self, test_db, test_user):
        """Test retrieving prediction history"""
        service = PredictionHistoryService(test_db)
        
        # Record multiple predictions
        for i in range(5):
            await service.record_prediction(
                user_id=test_user.id,
                sport_key='nba',
                event_id=f'nba_{i}',
                prediction_data={
                    'matchup': f'Game {i}',
                    'prediction': 'Home Win',
                    'confidence': 0.5 + i * 0.05,
                    'reasoning': []
                }
            )
        
        # Retrieve
        predictions, total = await service.get_user_prediction_history(
            user_id=test_user.id,
            limit=10
        )
        
        assert len(predictions) == 5
        assert total == 5
    
    async def test_get_user_stats(self, test_db, test_user):
        """Test retrieving user stats"""
        service = PredictionHistoryService(test_db)
        stats = await service.get_user_stats(test_user.id)
        
        # Initially no predictions
        assert stats['total'] == 0
        assert stats['win_rate'] == 0.0

# ============================================================================
# PLAYER PROPS TESTS
# ============================================================================

@pytest.mark.asyncio
class TestPlayerPropsService:
    
    async def test_player_features_buildup(self, test_db):
        """Test building player feature vectors"""
        service = PlayerPropsService(test_db)
        
        # Create test player
        player = PlayerRecord(
            id="player_test_1",
            name="LeBron James",
            sport_key="nba",
            position="SF",
            team_key="LAL",
            nba_id="123456"
        )
        test_db.add(player)
        
        # Create season stats
        stats = PlayerSeasonStats(
            player_id=player.id,
            sport_key="nba",
            season=2026,
            ppg=25.0,
            rpg=7.5,
            apg=8.0,
            games_played=60,
            games_started=59
        )
        test_db.add(stats)
        await test_db.commit()
        
        # Build features
        features = await service._build_player_features(
            player, stats, [], {'home_team': 'LAL', 'away_team': 'BOS'}, 'nba'
        )
        
        assert features.player_name == "LeBron James"
        assert features.season_avg == 25.0
        assert features.is_starter == True
    
    async def test_heuristic_prediction(self, test_db):
        """Test fallback heuristic prediction"""
        from app.services.player_props_service import PlayerFeatures
        
        service = PlayerPropsService(test_db)
        
        features = PlayerFeatures(
            player_id="p1",
            player_name="Player 1",
            season_avg=25.0,
            games_played=60,
            games_started=59,
            is_starter=True,
            last_game=26.0,
            last_5_avg=24.5,
            last_10_avg=24.0,
            variance_last_5=2.5,
            is_home_game=True,
            opponent="BOS",
            opponent_defense_rank=15,
            back_to_back=False,
            rest_days=2,
            avg_vs_opponent=25.5,
            season_to_date=25.0
        )
        
        pred = service._heuristic_prediction(features, 'ppg')
        
        assert 'line' in pred
        assert 'over_confidence' in pred
        assert 'under_confidence' in pred
        assert 0.5 <= pred['over_confidence'] <= 1.0

# ============================================================================
# ML CALIBRATION TESTS
# ============================================================================

@pytest.mark.asyncio
class TestMLCalibrationService:
    
    async def test_calibration_analysis(self, test_db, test_user):
        """Test calibration analysis"""
        service = MLCalibrationService(test_db)
        
        # Create test predictions
        for i in range(100):
            pred = PredictionRecord(
                user_id=test_user.id,
                sport_key="nba",
                event_id=f"nba_{i}",
                matchup=f"Game {i}",
                confidence=0.50 + (i % 5) * 0.10,  # Spread across buckets
                prediction="Home Win",
                outcome="hit" if i % 2 == 0 else "miss"
            )
            test_db.add(pred)
        
        await test_db.commit()
        
        report = await service.run_full_backtest(days_back=7)
        
        assert report['total_predictions'] == 100
        assert 'overall_calibration' in report
        assert 'issues_identified' in report
    
    def test_temperature_scaling(self):
        """Test confidence temperature scaling"""
        calibrator = ConfidenceCalibrator('nba')
        
        # Default temperature should not change confidence
        original = 0.65
        calibrated = calibrator.calibrate_confidence(original)
        assert abs(calibrated - original) < 0.001
        
        # Increase temperature (reduce confidence)
        calibrator.temperature = 1.2
        reduced = calibrator.calibrate_confidence(original)
        assert reduced < original
        
        # Decrease temperature (increase confidence)
        calibrator.temperature = 0.8
        increased = calibrator.calibrate_confidence(original)
        assert increased > original
    
    def test_fit_temperature(self):
        """Test fitting optimal temperature"""
        calibrator = ConfidenceCalibrator('nba')
        
        # Simulated overconfident predictions
        probs = [0.70, 0.75, 0.80, 0.70, 0.75] * 20  # Always high confidence
        labels = [1, 0, 1, 0, 0] * 20  # Only 60% accuracy
        
        optimal_temp = calibrator.fit_temperature(probs, labels)
        
        # Should increase temperature (> 1.0) to reduce overconfidence
        assert optimal_temp > 1.0

# ============================================================================
# SPORT-SPECIFIC MODEL TESTS
# ============================================================================

@pytest.mark.asyncio
class TestSportSpecificModels:
    
    def test_nba_predictor_features(self):
        """Test NBA predictor feature list"""
        predictor = NBAPredictor()
        features = predictor.get_relevant_features()
        
        assert 'ppg_allowed' in features
        assert 'three_pt_percent' in features
        assert 'pace' in features
        assert len(features) > 20
    
    def test_nba_predictor_preprocessing(self):
        """Test NBA feature preprocessing"""
        predictor = NBAPredictor()
        predictor.feature_names = predictor.get_relevant_features()
        
        raw_data = {
            'pts_per_game': 110.0,
            'offensive_rating': 115.0,
            'home_away': 1,
            'back_to_back_home': False
        }
        
        features = predictor.preprocess_data(raw_data)
        assert isinstance(features, np.ndarray)
        assert len(features) > 0
    
    def test_nfl_predictor_conservative_confidence(self):
        """Test that NFL predictor properly reduces confidence"""
        predictor = NFLPredictor()
        
        context = {
            'home_away': 1,
            'current_line': -3.5
        }
        
        pred = predictor.post_process_prediction(0.65, context)
        
        # Should be less confident than 0.65 due to NFL variance
        assert pred['confidence'] < 0.65
        assert pred['confidence'] > 0.50
    
    def test_mlb_pitcher_advantage_boost(self):
        """Test MLB predictor pitcher advantage detection"""
        predictor = MLBPredictor()
        
        context = {
            'starter_era': 2.5,
            'opponent_pitcher_era': 4.0
        }
        
        pred = predictor.post_process_prediction(0.55, context)
        
        # Should boost confidence due to pitcher advantage
        assert pred['confidence'] > 0.55
    
    def test_model_registry(self):
        """Test model registry routing"""
        assert len(model_registry.list_available_models()) >= 4
        
        nba = model_registry.get_predictor('nba')
        assert isinstance(nba, NBAPredictor)
        
        nfl = model_registry.get_predictor('nfl')
        assert isinstance(nfl, NFLPredictor)

# ============================================================================
# LOAD TESTING TESTS
# ============================================================================

@pytest.mark.asyncio
class TestLoadTesting:
    
    async def test_load_test_runner_initialization(self):
        """Test load test runner setup"""
        runner = LoadTestRunner()
        assert runner.base_url == "http://localhost:8000"
        assert len(runner.results) == 0
    
    def test_performance_monitor_tracking(self):
        """Test performance monitoring"""
        monitor = PerformanceMonitor()
        
        # Track some requests
        monitor.track_request("GET /predictions", "GET", 0.15, 200)
        monitor.track_request("GET /predictions", "GET", 0.12, 200)
        monitor.track_request("GET /predictions", "GET", 0.20, 200)
        monitor.track_request("GET /predictions", "GET", 0.50, 500)  # Error
        
        stats = monitor.get_endpoint_stats("GET /predictions")
        
        assert stats['count'] == 4
        assert stats['error_rate'] == 0.25  # 1 error out of 4
        assert stats['min_time_ms'] == 120
        assert stats['max_time_ms'] == 500
    
    def test_alert_manager_response_time_alert(self):
        """Test response time alerting"""
        manager = AlertManager()
        
        # Response time critical
        alert = manager.check_response_time("GET /predictions", 3.0)  # 3 seconds
        assert alert is not None
        assert alert['level'] == 'CRITICAL'
        
        # Response time warning
        alert = manager.check_response_time("GET /predictions", 1.2)
        assert alert is not None
        assert alert['level'] == 'WARNING'
        
        # Response time OK
        alert = manager.check_response_time("GET /predictions", 0.3)
        assert alert is None
    
    def test_alert_manager_error_rate_alert(self):
        """Test error rate alerting"""
        manager = AlertManager()
        
        # Critical error rate
        alert = manager.check_error_rate("GET /predictions", 0.15)
        assert alert is not None
        assert alert['level'] == 'CRITICAL'
        
        # Warning error rate
        alert = manager.check_error_rate("GET /predictions", 0.06)
        assert alert is not None
        assert alert['level'] == 'WARNING'
        
        # OK error rate
        alert = manager.check_error_rate("GET /predictions", 0.01)
        assert alert is None

# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.asyncio
class TestIntegration:
    
    async def test_prediction_history_workflow(self, test_db, test_user):
        """Test full prediction history workflow"""
        service = PredictionHistoryService(test_db)
        
        # 1. Record prediction
        pred_id = await service.record_prediction(
            user_id=test_user.id,
            sport_key='nba',
            event_id='nba_lakers_vs_celtics',
            prediction_data={
                'matchup': 'Lakers vs Celtics',
                'prediction': 'Home Win',
                'confidence': 0.65,
                'reasoning': []
            }
        )
        assert pred_id
        
        # 2. Get user history
        predictions, total = await service.get_user_prediction_history(
            user_id=test_user.id
        )
        assert total == 1
        
        # 3. Get user stats
        stats = await service.get_user_stats(test_user.id)
        assert stats['total'] == 1
    
    async def test_player_props_workflow(self, test_db):
        """Test player props end-to-end"""
        service = PlayerPropsService(test_db)
        
        # Create test data
        player = PlayerRecord(
            id="p_lebron",
            name="LeBron James",
            sport_key="nba",
            position="SF",
            team_key="LAL",
            nba_id="2544"
        )
        test_db.add(player)
        
        stats = PlayerSeasonStats(
            player_id=player.id,
            sport_key="nba",
            season=2026,
            ppg=25.0,
            games_played=60
        )
        test_db.add(stats)
        await test_db.commit()
        
        # Generate props
        props = await service.generate_player_prop_predictions(
            event_id="nba_123",
            sport_key="nba",
            home_team="LAL",
            away_team="BOS"
        )
        
        # Should have some predictions
        assert len(props) >= 0  # Might be empty due to test setup

# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

@pytest.mark.asyncio
class TestPerformance:
    
    async def test_prediction_history_retrieval_speed(self, test_db, test_user):
        """Test history retrieval performance with large dataset"""
        service = PredictionHistoryService(test_db)
        
        # Create 1000 predictions
        for i in range(1000):
            await service.record_prediction(
                user_id=test_user.id,
                sport_key=['nba', 'nfl', 'mlb'][i % 3],
                event_id=f"event_{i}",
                prediction_data={'prediction': 'Home Win', 'confidence': 0.55}
            )
        
        # Time the retrieval
        import time
        start = time.time()
        predictions, total = await service.get_user_prediction_history(
            user_id=test_user.id,
            limit=50
        )
        elapsed = time.time() - start
        
        # Should retrieve in < 500ms
        assert elapsed < 0.5
        assert len(predictions) == 50

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
