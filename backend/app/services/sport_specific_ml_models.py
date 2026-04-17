"""
Sport-Specific ML Predictors
Optimized models for each sport with different features and hyperparameters
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)

class SportPredictor(ABC):
    """Abstract base class for all sport predictors"""
    
    sport_key: str = None
    
    def __init__(self):
        self.model = None
        self.feature_names = []
        self.scaler = None
    
    @abstractmethod
    def get_relevant_features(self) -> List[str]:
        """Return list of feature names for this sport"""
        pass
    
    @abstractmethod
    def preprocess_data(self, raw_data: Dict) -> np.ndarray:
        """Transform raw data into feature vector"""
        pass
    
    @abstractmethod
    def post_process_prediction(self, raw_pred: float, context: Dict) -> Dict:
        """Apply sport-specific confidence adjustments"""
        pass
    
    @abstractmethod
    def get_hyperparameters(self) -> Dict:
        """Return optimal hyperparameters for this sport"""
        pass
    
    def predict(self, game_data: Dict) -> Dict:
        """Main prediction pipeline"""
        # Preprocess
        features = self.preprocess_data(game_data)
        
        # Model prediction (placeholder - would call actual model)
        raw_probability = 0.55  # self.model.predict([features])[0]
        
        # Post-process
        prediction = self.post_process_prediction(raw_probability, game_data)
        
        return prediction
    
    def train(self, training_data: List[Dict], labels: List[int]):
        """Train model on examples"""
        # Convert data to feature vectors
        features = np.array([
            self.preprocess_data(example) for example in training_data
        ])
        
        # Model training would happen here
        # self.model.fit(features, labels)
        logger.info(f"Trained {self.sport_key} model on {len(training_data)} examples")


class NBAPredictor(SportPredictor):
    """NBA-optimized predictor"""
    
    sport_key = 'nba'
    
    def get_relevant_features(self) -> List[str]:
        """NBA features emphasize pace, shooting, scoring"""
        return [
            'pts_per_game', 'ppg_allowed', 'fg_percent', 'fg_percent_allowed',
            'three_pt_percent', 'three_pt_percent_allowed',
            'ast_per_game', 'ast_allowed', 'trn_per_game', 'trn_allowed',
            'reb_per_game', 'reb_allowed', 'stl_per_game', 'stl_allowed',
            'pts_last_3', 'pts_last_5', 'win_pct_last_3', 'win_pct_last_5',
            'home_away', 'back_to_back_opponent', 'back_to_back_home',
            'days_rest_opponent', 'days_rest_home', 'season_win_pct',
            'offensive_rating', 'defensive_rating', 'pace',
            'opponent_offensive_rating', 'opponent_defensive_rating'
        ]
    
    def preprocess_data(self, raw_data: Dict) -> np.ndarray:
        """Extract and normalize NBA features"""
        features = []
        
        NBA_RANGES = {
            'pts_per_game': (80, 140),
            'fg_percent': (0.35, 0.50),
            'three_pt_percent': (0.25, 0.40),
            'ast_per_game': (20, 35),
            'pace': (95, 105),
            'offensive_rating': (100, 120),
            'defensive_rating': (100, 120)
        }
        
        for feature_name in self.feature_names:
            value = raw_data.get(feature_name, 0.0)
            
            # Normalize using sport-specific ranges
            if feature_name in NBA_RANGES:
                min_val, max_val = NBA_RANGES[feature_name]
                normalized = (value - min_val) / (max_val - min_val)
                normalized = np.clip(normalized, 0, 1)
                features.append(normalized)
            elif isinstance(value, bool):
                features.append(float(value))
            else:
                features.append(value)
        
        return np.array(features)
    
    def post_process_prediction(self, raw_pred: float, context: Dict) -> Dict:
        """Apply NBA-specific adjustments"""
        confidence = raw_pred
        
        # Home court advantage (3-4 points, ~55% win rate)
        if context.get('home_away') == 1 and raw_pred > 0.5:
            confidence = min(1.0, confidence + 0.02)
        
        # Back-to-back increases variance (reduce confidence)
        if context.get('back_to_back_home'):
            confidence = confidence * 0.95
        
        # Playoff games have more variance (regress to 50%)
        if context.get('is_playoff'):
            confidence = 0.5 + (confidence - 0.5) * 0.8
        
        return {
            'prediction': 'home_win' if raw_pred > 0.5 else 'away_win',
            'confidence': round(max(0.5, min(1.0, confidence)), 2),
            'reasoning': self._generate_reasoning(context, raw_pred)
        }
    
    def _generate_reasoning(self, context: Dict, pred: float) -> str:
        """Generate explanation for prediction"""
        reasons = []
        
        if context.get('offensive_rating', 0) > context.get('opponent_defensive_rating', 0):
            reasons.append("Strong offense vs weak defense")
        
        win_pct = context.get('win_pct_last_3', 0.5)
        if win_pct > 0.65:
            reasons.append("Winning streak (>2 in last 3)")
        elif win_pct < 0.35:
            reasons.append("Slumping (losing lately)")
        
        if context.get('home_away') == 1:
            reasons.append("Home court advantage")
        
        return " | ".join(reasons) if reasons else "Balanced matchup"
    
    def get_hyperparameters(self) -> Dict:
        """NBA has 82 games/season, can support complex model"""
        return {
            'num_leaves': 31,
            'learning_rate': 0.05,
            'max_depth': 7,
            'n_estimators': 200,
            'reg_alpha': 0.5,
            'reg_lambda': 1.0,
            'subsample': 0.8,
            'colsample_bytree': 0.8
        }


class NFLPredictor(SportPredictor):
    """NFL-optimized predictor - emphasize conservative confidence"""
    
    sport_key = 'nfl'
    
    def get_relevant_features(self) -> List[str]:
        """NFL features emphasize team strength and Vegas signal"""
        return [
            'pts_per_game', 'pts_allowed',
            'pass_yards_per_game', 'pass_yards_allowed',
            'rush_yards_per_game', 'rush_yards_allowed',
            'turnover_ratio', 'strength_of_schedule',
            'opening_line', 'current_line', 'line_movement',
            'public_percentage', 'sharp_percentage',
            'home_away', 'divisional_game', 'prime_time',
            'weather_temp', 'weather_wind', 'weather_precipitation',
            'key_player_injuries_count', 'qb_is_backup',
            'win_streak', 'ats_record_home', 'ats_record_away'
        ]
    
    def preprocess_data(self, raw_data: Dict) -> np.ndarray:
        """Extract and normalize NFL features"""
        features = []
        
        NFL_RANGES = {
            'pts_per_game': (15, 35),
            'pts_allowed': (15, 35),
            'pass_yards_per_game': (150, 350),
            'rush_yards_per_game': (75, 150)
        }
        
        for feature_name in self.feature_names:
            value = raw_data.get(feature_name, 0.0)
            
            if feature_name in NFL_RANGES:
                min_val, max_val = NFL_RANGES[feature_name]
                normalized = (value - min_val) / (max_val - min_val)
                normalized = np.clip(normalized, 0, 1)
                features.append(normalized)
            else:
                features.append(value)
        
        return np.array(features)
    
    def post_process_prediction(self, raw_pred: float, context: Dict) -> Dict:
        """NFL-specific: Be conservative due to high variance"""
        
        # NFL has only 16 games/season with huge swings
        # Reduce confidence away from 0.5 by 30%
        confidence = 0.5 + (raw_pred - 0.5) * 0.7
        
        # If Vegas strongly agrees, increase slightly
        if self._check_vegas_agreement(context):
            confidence = min(1.0, confidence + 0.03)
        
        # Weather impacts increase variance
        if self._is_bad_weather(context):
            confidence = confidence * 0.95
        
        return {
            'prediction': 'home_win' if raw_pred > 0.5 else 'away_win',
            'confidence': round(max(0.5, min(1.0, confidence)), 2),
            'reasoning': f"Vegas: {context.get('current_line', 'N/A')} | {self._generate_nfl_reasoning(context)}"
        }
    
    def _check_vegas_agreement(self, context: Dict) -> bool:
        """Check if Vegas line matches model prediction"""
        # Placeholder
        return False
    
    def _is_bad_weather(self, context: Dict) -> bool:
        """Check for weather impact"""
        wind = context.get('weather_wind', 0)
        precip = context.get('weather_precipitation', 0)
        return wind > 15 or precip > 0.25
    
    def _generate_nfl_reasoning(self, context: Dict) -> str:
        """Generate explanation"""
        reasons = []
        
        if context.get('home_away') == 1:
            reasons.append("Home field")
        
        if context.get('divisional_game'):
            reasons.append("Division game (unpredictable)")
        
        return " | ".join(reasons) if reasons else "Standard matchup"
    
    def get_hyperparameters(self) -> Dict:
        """NFL has limited data (16 games), need simpler model"""
        return {
            'num_leaves': 15,
            'learning_rate': 0.01,
            'max_depth': 5,
            'n_estimators': 100,
            'reg_alpha': 1.0,
            'reg_lambda': 2.0,
            'subsample': 0.9,
            'colsample_bytree': 0.9
        }


class MLBPredictor(SportPredictor):
    """MLB-optimized predictor - emphasize pitcher matchups"""
    
    sport_key = 'mlb'
    
    def get_relevant_features(self) -> List[str]:
        """MLB features emphasize pitcher-batter matchups"""
        return [
            'starter_era', 'starter_whip', 'starter_strikeouts_per_9',
            'opponent_pitcher_era', 'opponent_whip', 'pitcher_advantage',
            'runs_per_game', 'runs_allowed', 'woba', 'woba_against',
            'team_era', 'team_whip',
            'team_vs_rhp', 'team_vs_lhp',
            'opponent_vs_rhp', 'opponent_vs_lhp',
            'starter_handedness',
            'home_away', 'game_time', 'weather_temp', 'weather_wind',
            'ballpark_factor_runs',
            'days_rest_team', 'days_rest_opponent', 'travel_distance',
            'recent_form_runs_scored', 'recent_form_runs_allowed'
        ]
    
    def preprocess_data(self, raw_data: Dict) -> np.ndarray:
        """Extract and normalize MLB features"""
        features = []
        
        MLB_RANGES = {
            'starter_era': (2.5, 5.0),
            'starter_whip': (1.0, 1.5),
            'runs_per_game': (2.5, 5.0),
            'woba': (0.280, 0.360)
        }
        
        for feature_name in self.feature_names:
            value = raw_data.get(feature_name, 0.0)
            
            if feature_name in MLB_RANGES:
                min_val, max_val = MLB_RANGES[feature_name]
                normalized = (value - min_val) / (max_val - min_val)
                normalized = np.clip(normalized, 0, 1)
                features.append(normalized)
            else:
                features.append(value)
        
        return np.array(features)
    
    def post_process_prediction(self, raw_pred: float, context: Dict) -> Dict:
        """MLB-specific: Pitcher dominance"""
        confidence = raw_pred
        
        # Pitcher advantage is the most important factor
        pitcher_advantage = abs(
            context.get('starter_era', 3.5) - context.get('opponent_pitcher_era', 3.5)
        )
        
        if pitcher_advantage > 1.5:  # Significant ERA difference
            confidence = min(1.0, confidence + 0.10)
        elif pitcher_advantage < 0.5:  # Close matchup
            confidence = 0.5 + (confidence - 0.5) * 0.80
        
        return {
            'prediction': 'home_win' if raw_pred > 0.5 else 'away_win',
            'confidence': round(max(0.5, min(1.0, confidence)), 2),
            'reasoning': f"Pitcher: {context.get('starter_era', 'N/A')} ERA | Advantage: {pitcher_advantage:.2f}"
        }
    
    def get_hyperparameters(self) -> Dict:
        """MLB has 162 games/season, can support more features"""
        return {
            'num_leaves': 31,
            'learning_rate': 0.05,
            'max_depth': 8,
            'n_estimators': 250,
            'reg_alpha': 0.2,
            'reg_lambda': 0.5,
            'subsample': 0.85,
            'colsample_bytree': 0.85
        }

class NCAAPredictor(SportPredictor):
    """NCAA Basketball-optimized predictor - College-specific features"""
    
    sport_key = 'ncaa'
    
    def get_relevant_features(self) -> List[str]:
        """NCAA basketball features - college-specific"""
        return [
            # Scoring features (lower scoring than NBA)
            'pts_per_game', 'ppg_allowed', 'fg_percent', 'fg_percent_allowed',
            'three_pt_percent', 'three_pt_percent_allowed',
            # Pace and efficiency - college has different pace
            'ast_per_game', 'trn_per_game', 'pace',
            'reb_per_game', 'reb_allowed',
            # Conference strength and recent form
            'conference_strength', 'rpi_ranking', 'last_10_record',
            'home_away', 'season_win_pct'
        ]
    
    def preprocess_data(self, raw_data: Dict) -> np.ndarray:
        """Extract and normalize NCAA features - college-specific ranges"""
        features = []
        
        # NCAA ranges are DIFFERENT from NBA
        NCAA_RANGES = {
            'pts_per_game': (60, 80),  # Much lower than NBA (80-120)
            'fg_percent': (0.40, 0.48),  # Lower than NBA
            'three_pt_percent': (0.30, 0.38),  # Lower than NBA
            'ast_per_game': (12, 18),  # Lower than NBA
            'pace': (65, 75),  # Slower pace than NBA
        }
        
        # Fallback - use defaults if data is missing
        home_pts = raw_data.get('home_stats', {}).get('points_per_game', 70)
        away_pts = raw_data.get('away_stats', {}).get('points_per_game', 70)
        
        # Return normalized features
        normalized_home_pts = (home_pts - NCAA_RANGES['pts_per_game'][0]) / (NCAA_RANGES['pts_per_game'][1] - NCAA_RANGES['pts_per_game'][0])
        normalized_away_pts = (away_pts - NCAA_RANGES['pts_per_game'][0]) / (NCAA_RANGES['pts_per_game'][1] - NCAA_RANGES['pts_per_game'][0])
        
        return np.array([
            np.clip(normalized_home_pts, 0, 1),
            np.clip(normalized_away_pts, 0, 1),
            raw_data.get('home_win_pct', 0.5),
            raw_data.get('away_win_pct', 0.5)
        ])
    
    def post_process_prediction(self, raw_pred: float, context: Dict) -> Dict:
        """Apply NCAA-specific confidence adjustments"""
        # College basketball has more variance than NBA
        confidence = raw_pred * 0.75  # Reduce confidence for NCAA volatility
        
        # Home court disadvantage in college is stronger
        home_bonus = 1.05
        if context.get('home_away') == 'home':
            confidence = min(1.0, confidence * home_bonus)
        
        return {
            'prediction': 'home_win' if raw_pred > 0.5 else 'away_win',
            'confidence': round(max(0.5, min(1.0, confidence)), 2),
            'reasoning': f"College basketball with reduced confidence for volatility"
        }
    
    def get_hyperparameters(self) -> Dict:
        """NCAA-specific hyperparameters - less aggressive than NBA"""
        return {
            'num_leaves': 15,  # Fewer leaves than NBA (31)
            'learning_rate': 0.02,  # Lower learning rate
            'max_depth': 5,
            'n_estimators': 100,
            'reg_alpha': 1.0,
            'reg_lambda': 2.0,
            'reg_lambda': 2.0,
            'min_child_weight': 10,
        }

class NHLPredictor(SportPredictor):
    """NHL-optimized predictor"""
    
    sport_key = 'nhl'
    
    def get_relevant_features(self) -> List[str]:
        """NHL features emphasize goalie and team defense"""
        return [
            'goals_per_game', 'goals_allowed_per_game',
            'shots_per_game', 'shots_allowed_per_game',
            'sh_percent', 'sv_percent',
            'starting_goalie_sv_pct', 'opponent_goalie_sv_pct',
            'home_away', 'back_to_back', 'rest_days',
            'season_win_pct', 'last_10_record'
        ]
    
    def preprocess_data(self, raw_data: Dict) -> np.ndarray:
        features = []
        ranges = {
            'goals_per_game': (2.0, 4.0),
            'sh_percent': (0.07, 0.10),
            'sv_percent': (0.910, 0.925)
        }
        
        for feature_name in self.feature_names:
            value = raw_data.get(feature_name, 0.0)
            if feature_name in ranges:
                min_val, max_val = ranges[feature_name]
                normalized = (value - min_val) / (max_val - min_val)
                features.append(np.clip(normalized, 0, 1))
            else:
                features.append(value)
        
        return np.array(features)
    
    def post_process_prediction(self, raw_pred: float, context: Dict) -> Dict:
        confidence = raw_pred
        
        # Goalie advantage
        if context.get('starting_goalie_sv_pct', 0) > context.get('opponent_goalie_sv_pct', 0):
            confidence = min(1.0, confidence + 0.02)
        
        return {
            'prediction': 'home_win' if raw_pred > 0.5 else 'away_win',
            'confidence': round(max(0.5, min(1.0, confidence)), 2),
            'reasoning': f"Goalie advantage and team discipline"
        }
    
    def get_hyperparameters(self) -> Dict:
        return {
            'num_leaves': 25,
            'learning_rate': 0.03,
            'max_depth': 6,
            'n_estimators': 150,
            'reg_alpha': 0.5,
            'reg_lambda': 1.5
        }


class SoccerPredictor(SportPredictor):
    """Soccer/Football-optimized predictor"""
    
    sport_key = 'soccer'
    
    def get_relevant_features(self) -> List[str]:
        """Soccer features emphasize possession and defensive tactics"""
        return [
            'goals_for', 'goals_against', 'possession_pct',
            'pass_completion_pct', 'shots_per_game', 'shots_on_target',
            'defensive_actions', 'tackles_per_game',
            'home_away', 'rest_days', 'weather_wind',
            'season_win_pct', 'form_last_5'
        ]
    
    def preprocess_data(self, raw_data: Dict) -> np.ndarray:
        features = []
        ranges = {
            'goals_for': (0.5, 2.5),
            'possession_pct': (0.40, 0.60),
            'pass_completion_pct': (0.70, 0.85)
        }
        
        for feature_name in self.feature_names:
            value = raw_data.get(feature_name, 0.0)
            if feature_name in ranges:
                min_val, max_val = ranges[feature_name]
                normalized = (value - min_val) / (max_val - min_val)
                features.append(np.clip(normalized, 0, 1))
            else:
                features.append(value)
        
        return np.array(features)
    
    def post_process_prediction(self, raw_pred: float, context: Dict) -> Dict:
        # Soccer is very low scoring and unpredictable
        confidence = 0.5 + (raw_pred - 0.5) * 0.65  # 35% less confident
        
        return {
            'prediction': 'home_win' if raw_pred > 0.5 else 'away_win',
            'confidence': round(max(0.5, min(1.0, confidence)), 2),
            'reasoning': f"Possession: {context.get('possession_pct', 'N/A')}"
        }
    
    def get_hyperparameters(self) -> Dict:
        return {
            'num_leaves': 20,
            'learning_rate': 0.02,
            'max_depth': 5,
            'n_estimators': 120,
            'reg_alpha': 1.0,
            'reg_lambda': 2.0
        }


class ModelRegistry:
    """Registry to manage and route to correct sport-specific model"""
    
    def __init__(self):
        self.models = {}
        self._load_models()
    
    def _load_models(self):
        """Load all sport predictors"""
        self.models['nba'] = NBAPredictor()
        self.models['ncaa'] = NCAAPredictor()
        self.models['nfl'] = NFLPredictor()
        self.models['mlb'] = MLBPredictor()
        self.models['nhl'] = NHLPredictor()
        self.models['soccer'] = SoccerPredictor()
    
    def get_predictor(self, sport_key: str) -> SportPredictor:
        """Get predictor for sport"""
        if sport_key not in self.models:
            logger.warning(f"No specific model for {sport_key}, using NFL as fallback")
            return self.models['nfl']
        return self.models[sport_key]
    
    def predict(self, sport_key: str, game_data: Dict) -> Dict:
        """Make prediction with appropriate model"""
        predictor = self.get_predictor(sport_key)
        return predictor.predict(game_data)
    
    def list_available_models(self) -> List[str]:
        """List all available models"""
        return list(self.models.keys())

# Singleton instance
model_registry = ModelRegistry()
