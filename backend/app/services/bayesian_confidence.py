"""
Bayesian Confidence Framework
Replaces hash-based confidence calculations with proper statistical inference.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class BayesianConfidenceCalculator:
    """
    Calculates confidence using Bayesian inference based on:
    - Prior team strength (from historical data)
    - Likelihood from recent performance
    - Posterior calculation with uncertainty quantification
    """
    
    def __init__(self, prior_strength: float = 10.0):
        """
        Args:
            prior_strength: Equivalent sample size for prior (higher = stronger prior)
        """
        self.prior_strength = prior_strength
        self.default_prior = 0.5  # 50% win probability as neutral prior
        
    def calculate_confidence(
        self, 
        home_team_data: Dict, 
        away_team_data: Dict,
        historical_results: Optional[List[Dict]] = None,
        recent_games: Optional[List[Dict]] = None
    ) -> Tuple[float, Dict]:
        """
        Calculate confidence using Bayesian framework.
        
        Args:
            home_team_data: Home team statistics
            away_team_data: Away team statistics  
            historical_results: Historical head-to-head results
            recent_games: Recent games for both teams
            
        Returns:
            Tuple of (confidence_score, metadata)
        """
        # Calculate prior from overall team strength
        home_prior = self._calculate_team_prior(home_team_data)
        away_prior = self._calculate_team_prior(away_team_data)
        
        # Calculate likelihood from recent performance
        home_likelihood = self._calculate_recent_likelihood(home_team_data, recent_games)
        away_likelihood = self._calculate_recent_likelihood(away_team_data, recent_games)
        
        # Calculate posterior (Bayesian update)
        home_posterior = self._bayesian_update(home_prior, home_likelihood)
        away_posterior = self._bayesian_update(away_prior, away_likelihood)
        
        # Calculate head-to-head adjustment
        h2h_adjustment = self._calculate_h2h_adjustment(historical_results)
        
        # Final probability
        home_prob = (home_posterior + away_posterior) / 2 + h2h_adjustment
        home_prob = np.clip(home_prob, 0.05, 0.95)
        
        # Calculate confidence based on certainty
        confidence = self._calculate_certainty(
            home_posterior, 
            away_posterior, 
            h2h_adjustment,
            recent_games
        )
        
        metadata = {
            'home_prior': home_prior,
            'away_prior': away_prior,
            'home_likelihood': home_likelihood,
            'away_likelihood': away_likelihood,
            'home_posterior': home_posterior,
            'away_posterior': away_posterior,
            'h2h_adjustment': h2h_adjustment,
            'method': 'bayesian'
        }
        
        return confidence, metadata
    
    def _calculate_team_prior(self, team_data: Dict) -> float:
        """Calculate prior probability from historical team performance."""
        wins = team_data.get('wins', 0)
        losses = team_data.get('losses', 0)
        games = wins + losses
        
        if games == 0:
            return self.default_prior
            
        win_rate = wins / games
        
        # Bayesian smoothing: (wins + prior_strength * default_prior) / (games + prior_strength)
        posterior = (wins + self.prior_strength * self.default_prior) / (games + self.prior_strength)
        
        return posterior
    
    def _calculate_recent_likelihood(self, team_data: Dict, recent_games: Optional[List[Dict]]) -> float:
        """Calculate likelihood from recent game performance."""
        if not recent_games:
            return self.default_prior
            
        # Get last N games
        n_recent = min(10, len(recent_games))
        recent = recent_games[-n_recent:]
        
        wins = sum(1 for g in recent if g.get('won', False))
        games = len(recent)
        
        if games == 0:
            return self.default_prior
            
        return wins / games
    
    def _bayesian_update(self, prior: float, likelihood: float, n_observations: int = 10) -> float:
        """
        Perform Bayesian update combining prior and likelihood.
        
        Args:
            prior: Prior probability
            likelihood: Likelihood from new data
            n_observations: Number of observations in likelihood
        """
        # Effective sample sizes
        prior_weight = self.prior_strength
        likelihood_weight = n_observations
        
        # Posterior = weighted average
        posterior = (prior_weight * prior + likelihood_weight * likelihood) / (prior_weight + likelihood_weight)
        
        return posterior
    
    def _calculate_h2h_adjustment(self, historical_results: Optional[List[Dict]]) -> float:
        """Calculate head-to-head adjustment."""
        if not historical_results or len(historical_results) < 3:
            return 0.0
            
        # Calculate home team H2H record
        home_wins = sum(1 for g in historical_results if g.get('home_won', False))
        total = len(historical_results)
        
        if total == 0:
            return 0.0
            
        h2h_rate = home_wins / total
        
        # Small adjustment (max ±5%)
        adjustment = (h2h_rate - 0.5) * 0.1
        
        return adjustment
    
    def _calculate_certainty(
        self, 
        home_posterior: float, 
        away_posterior: float,
        h2h_adjustment: float,
        recent_games: Optional[List[Dict]]
    ) -> float:
        """
        Calculate confidence based on certainty of predictions.
        Higher certainty = higher confidence.
        """
        # Base certainty from probability difference
        prob_diff = abs(home_posterior - away_posterior)
        
        # Sample size certainty
        n_recent = len(recent_games) if recent_games else 0
        sample_certainty = min(n_recent / 20, 1.0)  # Max certainty at 20 games
        
        # H2H certainty
        h2h_certainty = min(abs(h2h_adjustment) * 10, 1.0)
        
        # Combine factors
        base_confidence = 52  # Minimum baseline
        
        # Scale: 0 diff = 52%, 0.5 diff = 85%
        prob_confidence = base_confidence + (prob_diff * 100 * 0.66)
        
        # Add sample certainty (0-15%)
        sample_bonus = sample_certainty * 15
        
        # Add H2H certainty (0-8%)
        h2h_bonus = h2h_certainty * 8
        
        confidence = min(92, prob_confidence + sample_bonus + h2h_bonus)
        
        return round(confidence, 1)


class UncertaintyAwarePredictor:
    """
    Model uncertainty quantification using dropout-based ensemble.
    Provides confidence based on model agreement.
    """
    
    def __init__(self, model, n_dropout_samples: int = 50):
        self.model = model
        self.n_dropout_samples = n_dropout_samples
        
    def predict_with_uncertainty(self, features: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Make predictions with uncertainty quantification.
        
        Args:
            features: Input features
            
        Returns:
            Tuple of (mean_prediction, confidence)
        """
        predictions = []
        
        # Enable dropout for uncertainty estimation
        self.model.train()
        
        for _ in range(self.n_dropout_samples):
            pred = self.model.predict(features)
            predictions.append(pred)
            
        predictions = np.array(predictions)
        
        # Mean prediction
        mean_pred = np.mean(predictions, axis=0)
        
        # Standard deviation (uncertainty)
        std_pred = np.std(predictions, axis=0)
        
        # Confidence = 1 - normalized uncertainty
        # Scale std to 0-1 range
        max_std = np.max(std_pred) if np.max(std_pred) > 0 else 1
        normalized_uncertainty = std_pred / (max_std + 1e-8)
        
        confidence = 1 - normalized_uncertainty
        
        # Scale to 52-95% range
        confidence = 52 + (confidence * 43)
        
        return mean_pred, float(np.mean(confidence))
    
    def predict_proba_with_uncertainty(self, features: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Predict probabilities with uncertainty for classification.
        """
        predictions = []
        
        self.model.train()
        
        for _ in range(self.n_dropout_samples):
            pred = self.model.predict_proba(features)
            predictions.append(pred)
            
        predictions = np.array(predictions)
        
        # Mean probability
        mean_proba = np.mean(predictions, axis=0)
        
        # Uncertainty from prediction variance
        std_proba = np.std(predictions, axis=0)
        
        # Confidence based on agreement
        max_uncertainty = np.max(std_proba)
        confidence = 1 - max_uncertainty
        
        # Scale to 52-95%
        confidence = 52 + (confidence * 43)
        
        return mean_proba, round(float(confidence), 1)


class TemporalFeatureEngineer:
    """
    Adds temporal features for time-series aware predictions.
    """
    
    def __init__(self, lookback_days: int = 30):
        self.lookback_days = lookback_days
        
    def add_temporal_features(
        self, 
        game_data: Dict, 
        historical_games: List[Dict]
    ) -> Dict:
        """
        Add temporal features to game data.
        
        Features added:
        - Form momentum (rolling average)
        - Rest day advantage
        - Travel impact
        - Home/away performance trends
        """
        home_team = game_data.get('home_team', '')
        away_team = game_data.get('away_team', '')
        
        # Get recent games for both teams
        home_recent = self._get_team_recent_games(home_team, historical_games)
        away_recent = self._get_team_recent_games(away_team, historical_games)
        
        features = {}
        
        # Form momentum
        features['home_momentum'] = self._calculate_momentum(home_recent)
        features['away_momentum'] = self._calculate_momentum(away_recent)
        
        # Rest day advantage
        home_rest = game_data.get('home_days_rest', 0)
        away_rest = game_data.get('away_days_rest', 0)
        features['rest_advantage'] = (home_rest - away_rest) * 0.02
        
        # Travel impact
        home_travel = game_data.get('home_travel_miles', 0)
        away_travel = game_data.get('away_travel_miles', 0)
        features['travel_impact'] = -(home_travel - away_travel) * 0.0001
        
        # Home/away trends
        features['home_trend'] = self._calculate_home_trend(home_recent)
        features['away_trend'] = self._calculate_away_trend(away_recent)
        
        # Recent form vs overall
        features['home_form_vs_avg'] = self._calculate_form_vs_avg(home_recent)
        features['away_form_vs_avg'] = self._calculate_form_vs_avg(away_recent)
        
        return features
    
    def _get_team_recent_games(self, team: str, historical_games: List[Dict]) -> List[Dict]:
        """Get recent games for a team."""
        cutoff = datetime.now() - timedelta(days=self.lookback_days)
        
        recent = [
            g for g in historical_games 
            if (g.get('home_team') == team or g.get('away_team') == team)
            and datetime.fromisoformat(g.get('date', '2000-01-01')) > cutoff
        ]
        
        return sorted(recent, key=lambda x: x.get('date', ''), reverse=True)[:10]
    
    def _calculate_momentum(self, games: List[Dict]) -> float:
        """Calculate form momentum (0-1 scale)."""
        if not games:
            return 0.5
            
        # Weight recent games more heavily
        weights = np.exp(np.linspace(0, 1, len(games)))
        weights = weights / weights.sum()
        
        wins = []
        for g in games:
            won = g.get('won', False)
            wins.append(1.0 if won else 0.0)
            
        momentum = np.average(wins, weights=weights)
        
        return momentum
    
    def _calculate_home_trend(self, games: List[Dict]) -> float:
        """Calculate home performance trend."""
        home_games = [g for g in games if g.get('is_home', True)]
        
        if len(home_games) < 3:
            return 0.0
            
        # Compare recent home to overall home
        recent_home = home_games[:5]
        older_home = home_games[5:10]
        
        if not older_home:
            return 0.0
            
        recent_rate = sum(1 for g in recent_home if g.get('won', False)) / len(recent_home)
        older_rate = sum(1 for g in older_home if g.get('won', False)) / len(older_home)
        
        return recent_rate - older_rate
    
    def _calculate_away_trend(self, games: List[Dict]) -> float:
        """Calculate away performance trend."""
        away_games = [g for g in games if not g.get('is_home', True)]
        
        if len(away_games) < 3:
            return 0.0
            
        recent_away = away_games[:5]
        older_away = away_games[5:10]
        
        if not older_away:
            return 0.0
            
        recent_rate = sum(1 for g in recent_away if g.get('won', False)) / len(recent_away)
        older_rate = sum(1 for g in older_away if g.get('won', False)) / len(older_away)
        
        return recent_rate - older_rate
    
    def _calculate_form_vs_avg(self, games: List[Dict]) -> float:
        """Calculate recent form vs season average."""
        if len(games) < 5:
            return 0.0
            
        recent = games[:5]
        all_games = games
            
        recent_rate = sum(1 for g in recent if g.get('won', False)) / len(recent)
        overall_rate = sum(1 for g in all_games if g.get('won', False)) / len(all_games)
        
        return recent_rate - overall_rate


class MarketIntelligence:
    """
    Integrates betting market data for enhanced predictions.
    """
    
    def __init__(self):
        self.line_movement_threshold = 0.05
        
    def analyze_market(
        self, 
        current_odds: Dict, 
        opening_odds: Optional[Dict] = None,
        historical_lines: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Analyze betting market data.
        
        Returns:
            Dictionary with market analysis
        """
        analysis = {
            'sharp_indicator': 'neutral',
            'line_movement': 0.0,
            'reverse_movement': False,
            'market_confidence': 52.0,
            'steam_moves': [],
            'key_numbers': []
        }
        
        if opening_odds:
            # Calculate line movement
            movement = self._calculate_line_movement(current_odds, opening_odds)
            analysis['line_movement'] = movement
            
            # Detect sharp money
            analysis['sharp_indicator'] = self._detect_sharp_money(movement, current_odds)
            
            # Reverse line movement detection
            analysis['reverse_movement'] = self._detect_reverse_movement(
                current_odds, opening_odds
            )
            
            # Calculate market confidence
            analysis['market_confidence'] = self._calculate_market_confidence(
                analysis['sharp_indicator'],
                movement,
                analysis['reverse_movement']
            )
            
        if historical_lines:
            # Steam moves (rapid line movement)
            analysis['steam_moves'] = self._detect_steam_moves(historical_lines)
            
            # Key numbers analysis
            analysis['key_numbers'] = self._analyze_key_numbers(current_odds)
            
        return analysis
    
    def _calculate_line_movement(self, current: Dict, opening: Dict) -> float:
        """Calculate percentage line movement."""
        current_line = current.get('spread', 0)
        opening_line = opening.get('spread', 0)
        
        if opening_line == 0:
            return 0.0
            
        return (current_line - opening_line) / abs(opening_line)
    
    def _detect_sharp_money(self, movement: float, odds: Dict) -> str:
        """Detect sharp money indicator."""
        # Significant movement suggests sharp money
        if movement > self.line_movement_threshold:
            return 'sharp_pro'
        elif movement < -self.line_movement_threshold:
            return 'sharp_con'
            
        # Check for reverse line movement
        public_bet_pct = odds.get('public_bet_percent', 50)
        if public_bet_pct > 70 and movement > 0:
            return 'sharp_con'  # Public heavily on one side, line moves other way
        elif public_bet_pct < 30 and movement < 0:
            return 'sharp_pro'
            
        return 'neutral'
    
    def _detect_reverse_movement(self, current: Dict, opening: Dict) -> bool:
        """Detect reverse line movement (public vs sharp)."""
        public_bet = current.get('public_bet_percent', 50)
        movement = self._calculate_line_movement(current, opening)
        
        # Public heavily on home, line moves to away = sharp money on away
        if public_bet > 65 and movement < -0.02:
            return True
        if public_bet < 35 and movement > 0.02:
            return True
            
        return False
    
    def _calculate_market_confidence(
        self, 
        sharp_indicator: str, 
        movement: float,
        reverse_movement: bool
    ) -> float:
        """Calculate confidence based on market signals."""
        base = 52.0
        
        # Sharp indicator bonus
        if sharp_indicator == 'sharp_pro':
            base += 15
        elif sharp_indicator == 'sharp_con':
            base += 10
        elif reverse_movement:
            base += 12
            
        # Movement magnitude bonus
        base += min(abs(movement) * 100, 15)
        
        return min(85, base)
    
    def _detect_steam_moves(self, historical_lines: List[Dict]) -> List[Dict]:
        """Detect steam moves (rapid line movement)."""
        steam_moves = []
        
        for i in range(1, len(historical_lines)):
            prev = historical_lines[i-1]
            curr = historical_lines[i]
            
            movement = abs(curr.get('spread', 0) - prev.get('spread', 0))
            
            if movement >= 2.0:  # Significant move
                steam_moves.append({
                    'timestamp': curr.get('timestamp'),
                    'movement': movement,
                    'direction': 'home' if movement > 0 else 'away'
                })
                
        return steam_moves[-5:]  # Last 5 steam moves
    
    def _analyze_key_numbers(self, odds: Dict) -> List[Dict]:
        """Analyze key numbers (common margins in each sport)."""
        spread = odds.get('spread', 0)
        
        # NFL key numbers
        nfl_keys = [3, 7, 10, 14, 17, 21]
        # NBA key numbers
        nba_keys = [4, 5, 7, 10, 12]
        
        key_numbers = []
        for key in nfl_keys + nba_keys:
            distance = abs(spread - key)
            if distance < 0.5:
                key_numbers.append({
                    'key': key,
                    'distance': distance,
                    'significance': 'high' if key in [3, 7] else 'medium'
                })
                
        return key_numbers


class OnlineLearningEngine:
    """
    Continuous model improvement through online learning.
    """
    
    def __init__(self, model, update_frequency: int = 100, performance_threshold: float = 0.55):
        self.model = model
        self.update_frequency = update_frequency
        self.performance_threshold = performance_threshold
        self.recent_results = []
        self.performance_window = 1000
        self.current_accuracy = 0.5
        
    def record_result(self, prediction: Dict, actual_result: bool) -> None:
        """
        Record prediction result for future model updates.
        
        Args:
            prediction: The prediction made
            actual_result: The actual outcome
        """
        self.recent_results.append({
            'prediction': prediction,
            'actual': actual_result,
            'timestamp': datetime.now(),
            'correct': prediction.get('predicted_outcome') == actual_result
        })
        
        # Update running accuracy
        self._update_accuracy()
        
        # Trigger update when enough new data
        if len(self.recent_results) >= self.update_frequency:
            self._update_model()
            
    def _update_accuracy(self) -> None:
        """Update running accuracy metric."""
        if not self.recent_results:
            return
            
        window = self.recent_results[-self.performance_window:]
        correct = sum(1 for r in window if r.get('correct', False))
        self.current_accuracy = correct / len(window)
        
    def _update_model(self) -> bool:
        """
        Update model if performance degraded.
        
        Returns:
            True if model was updated
        """
        logger.info(f"Checking model update. Current accuracy: {self.current_accuracy:.3f}")
        
        if self.current_accuracy < self.performance_threshold:
            logger.warning(f"Model performance ({self.current_accuracy:.3f}) below threshold. Retraining...")
            
            # Prepare incremental training data
            new_data = self._prepare_incremental_data()
            
            # Perform incremental learning
            if hasattr(self.model, 'partial_fit'):
                self.model.partial_fit(
                    new_data['features'],
                    new_data['labels']
                )
            else:
                # Full retrain with new data
                self._full_retrain(new_data)
                
            # Reset for next cycle
            self.recent_results = self.recent_results[-100:]
            
            return True
            
        return False
    
    def _prepare_incremental_data(self) -> Dict:
        """Prepare incremental training data from recent results."""
        features = []
        labels = []
        
        for result in self.recent_results:
            pred = result.get('prediction', {})
            features.append(pred.get('features', []))
            labels.append(1 if result.get('actual') else 0)
            
        return {
            'features': np.array(features),
            'labels': np.array(labels)
        }
    
    def _full_retrain(self, new_data: Dict) -> None:
        """Perform full model retraining."""
        # This would integrate with your existing training pipeline
        logger.info("Performing full model retraining...")
        # Implementation depends on your model framework
        
    def get_performance_metrics(self) -> Dict:
        """Get current performance metrics."""
        return {
            'current_accuracy': self.current_accuracy,
            'total_predictions': len(self.recent_results),
            'recent_correct': sum(1 for r in self.recent_results[-20:] if r.get('correct', False)),
            'needs_update': self.current_accuracy < self.performance_threshold
        }
