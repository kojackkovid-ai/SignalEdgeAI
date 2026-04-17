"""
Advanced Reasoning Engine for Sports Predictions
Generates data-driven, unique reasoning for each prediction
"""

import numpy as np
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class AdvancedReasoningEngine:
    """Generate sophisticated, data-driven reasoning for predictions"""
    
    def __init__(self):
        self.reasoning_templates = {
            'elo_advantage': {
                'high': "Significant ELO rating advantage indicates superior team strength",
                'medium': "Moderate ELO advantage suggests slight edge in team quality",
                'low': "Minimal ELO difference shows closely matched teams"
            },
            'form_trend': {
                'strong_positive': "Exceptional recent form demonstrates current momentum",
                'positive': "Positive recent form indicates good current state",
                'neutral': "Average recent form shows inconsistent performance",
                'negative': "Poor recent form suggests struggles in current stretch"
            },
            'injury_impact': {
                'high': "Key injuries significantly impact team performance potential",
                'medium': "Injury concerns may affect team dynamics",
                'low': "Minimal injury impact on overall team strength"
            },
            'h2h_history': {
                'dominant': "Historical dominance provides psychological advantage",
                'favorable': "Favorable head-to-head record suggests matchup advantage",
                'even': "Balanced historical matchup indicates competitive rivalry"
            },
            'market_consensus': {
                'strong': "Strong market consensus aligns with fundamental analysis",
                'moderate': "Market sentiment supports prediction direction",
                'weak': "Market showing uncertainty about outcome"
            }
        }
    
    def generate_reasoning(self, 
                          prediction_data: Dict[str, Any], 
                          model_predictions: Dict[str, float],
                          market_data: Dict[str, float],
                          confidence: float) -> List[Dict[str, Any]]:
        """
        Generate comprehensive reasoning based on actual data analysis
        
        Args:
            prediction_data: Game/match data including team stats
            model_predictions: Individual model predictions and confidences
            market_data: Market odds and implied probabilities
            confidence: Overall prediction confidence
        
        Returns:
            List of reasoning points with factors, impacts, and explanations
        """
        reasoning = []
        
        # 1. ELO Analysis
        elo_reasoning = self._analyze_elo_advantage(prediction_data)
        if elo_reasoning:
            reasoning.append(elo_reasoning)
        
        # 2. Recent Form Analysis
        form_reasoning = self._analyze_recent_form(prediction_data)
        if form_reasoning:
            reasoning.append(form_reasoning)
        
        # 3. Injury Impact Assessment
        injury_reasoning = self._analyze_injury_impact(prediction_data)
        if injury_reasoning:
            reasoning.append(injury_reasoning)
        
        # 4. Head-to-Head Analysis
        h2h_reasoning = self._analyze_head_to_head(prediction_data)
        if h2h_reasoning:
            reasoning.append(h2h_reasoning)
        
        # 5. Model Consensus Analysis
        model_reasoning = self._analyze_model_consensus(model_predictions, confidence)
        if model_reasoning:
            reasoning.append(model_reasoning)
        
        # 6. Market Analysis
        market_reasoning = self._analyze_market_alignment(market_data, confidence)
        if market_reasoning:
            reasoning.append(market_reasoning)
        
        # 7. Situational Factors
        situational_reasoning = self._analyze_situational_factors(prediction_data)
        if situational_reasoning:
            reasoning.extend(situational_reasoning)
        
        return reasoning
    
    def _analyze_elo_advantage(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze ELO rating differences"""
        home_elo = data.get('home_elo', 1500)
        away_elo = data.get('away_elo', 1500)
        
        elo_diff = abs(home_elo - away_elo)
        favored_team = 'home' if home_elo > away_elo else 'away'
        
        if elo_diff > 100:
            impact = 'high'
            weight = 0.25
        elif elo_diff > 50:
            impact = 'medium'
            weight = 0.18
        elif elo_diff > 20:
            impact = 'low'
            weight = 0.12
        else:
            return None
        
        template = self.reasoning_templates['elo_advantage'][impact]
        
        return {
            'factor': f'ELO Rating Advantage ({favored_team.title()})',
            'impact': 'Positive' if favored_team == 'home' else 'Negative',
            'weight': weight,
            'explanation': f"{template}. ELO difference: {elo_diff:.0f} points.",
            'data_points': {
                'home_elo': home_elo,
                'away_elo': away_elo,
                'elo_difference': elo_diff
            }
        }
    
    def _analyze_recent_form(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze recent form trends"""
        home_form = data.get('home_form', 0.5)
        away_form = data.get('away_form', 0.5)
        
        form_diff = abs(home_form - away_form)
        
        if form_diff < 0.1:
            return None
        
        # Determine which team has better form
        if home_form > away_form:
            favored_team = 'home'
            favored_form = home_form
            other_form = away_form
        else:
            favored_team = 'away'
            favored_form = away_form
            other_form = home_form
        
        # Categorize form strength
        if favored_form > 0.7:
            form_strength = 'strong_positive'
            weight = 0.22
        elif favored_form > 0.6:
            form_strength = 'positive'
            weight = 0.18
        elif favored_form > 0.4:
            form_strength = 'neutral'
            weight = 0.12
        else:
            form_strength = 'negative'
            weight = 0.08
        
        template = self.reasoning_templates['form_trend'][form_strength]
        
        return {
            'factor': f'Recent Form ({favored_team.title()})',
            'impact': 'Positive' if favored_team == 'home' else 'Negative',
            'weight': weight,
            'explanation': f"{template}. Recent form: {favored_form:.1%} vs {other_form:.1%}.",
            'data_points': {
                'home_form': home_form,
                'away_form': away_form,
                'form_difference': form_diff
            }
        }
    
    def _analyze_injury_impact(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze injury impact on teams"""
        home_injuries = data.get('home_injury_impact', 0)
        away_injuries = data.get('away_injury_impact', 0)
        
        # Focus on the team with more significant injuries
        if home_injuries > away_injuries:
            impact_team = 'home'
            injury_level = home_injuries
        else:
            impact_team = 'away'
            injury_level = away_injuries
        
        # Only include if injuries are significant
        if injury_level < 0.15:
            return None
        
        if injury_level > 0.3:
            impact = 'high'
            weight = 0.20
        elif injury_level > 0.2:
            impact = 'medium'
            weight = 0.15
        else:
            impact = 'low'
            weight = 0.10
        
        template = self.reasoning_templates['injury_impact'][impact]
        
        return {
            'factor': f'Injury Impact ({impact_team.title()})',
            'impact': 'Negative' if impact_team == 'home' else 'Positive',
            'weight': weight,
            'explanation': f"{template}. Injury impact score: {injury_level:.2f}.",
            'data_points': {
                'home_injury_impact': home_injuries,
                'away_injury_impact': away_injuries
            }
        }
    
    def _analyze_head_to_head(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze head-to-head historical performance"""
        home_h2h = data.get('h2h_home_winrate', 0.5)
        away_h2h = data.get('h2h_away_winrate', 0.5)
        
        # Calculate H2H advantage
        if home_h2h > away_h2h:
            favored_team = 'home'
            h2h_advantage = home_h2h - away_h2h
        else:
            favored_team = 'away'
            h2h_advantage = away_h2h - home_h2h
        
        if h2h_advantage < 0.15:
            return None
        
        if h2h_advantage > 0.4:
            h2h_strength = 'dominant'
            weight = 0.18
        elif h2h_advantage > 0.25:
            h2h_strength = 'favorable'
            weight = 0.14
        else:
            h2h_strength = 'even'
            weight = 0.10
        
        template = self.reasoning_templates['h2h_history'][h2h_strength]
        
        return {
            'factor': f'Head-to-Head History ({favored_team.title()})',
            'impact': 'Positive' if favored_team == 'home' else 'Negative',
            'weight': weight,
            'explanation': f"{template}. Historical record: {home_h2h:.1%} vs {away_h2h:.1%}.",
            'data_points': {
                'h2h_home_winrate': home_h2h,
                'h2h_away_winrate': away_h2h,
                'h2h_advantage': h2h_advantage
            }
        }
    
    def _analyze_model_consensus(self, model_predictions: Dict[str, float], confidence: float) -> Optional[Dict[str, Any]]:
        """Analyze model consensus and agreement"""
        if not model_predictions:
            return None
        
        predictions = list(model_predictions.values())
        avg_prediction = np.mean(predictions)
        std_prediction = np.std(predictions)
        
        # Model agreement (lower std = higher agreement)
        if std_prediction < 0.05:
            agreement = 'high'
            weight = 0.15
        elif std_prediction < 0.1:
            agreement = 'medium'
            weight = 0.12
        else:
            agreement = 'low'
            weight = 0.08
        
        if confidence > 0.75:
            confidence_desc = 'High'
        elif confidence > 0.55:
            confidence_desc = 'Medium'
        else:
            confidence_desc = 'Low'
        
        return {
            'factor': 'Model Ensemble Consensus',
            'impact': 'Positive' if agreement != 'low' else 'Neutral',
            'weight': weight,
            'explanation': f"{confidence_desc} confidence from ensemble of {len(predictions)} ML models. Model agreement: {agreement}.",
            'data_points': {
                'model_count': len(predictions),
                'average_prediction': avg_prediction,
                'prediction_std': std_prediction,
                'agreement_level': agreement
            }
        }
    
    def _analyze_market_alignment(self, market_data: Dict[str, float], confidence: float) -> Optional[Dict[str, Any]]:
        """Analyze market data alignment with prediction"""
        if not market_data:
            return None
        
        market_home_prob = market_data.get('home_implied_prob', 0.5)
        market_confidence = abs(market_home_prob - 0.5) * 2
        
        if market_confidence > 0.4:
            market_strength = 'strong'
            weight = 0.20
        elif market_confidence > 0.2:
            market_strength = 'moderate'
            weight = 0.15
        else:
            market_strength = 'weak'
            weight = 0.10
        
        template = self.reasoning_templates['market_consensus'][market_strength]
        
        return {
            'factor': 'Market Consensus',
            'impact': 'Positive' if market_strength != 'weak' else 'Neutral',
            'weight': weight,
            'explanation': f"{template}. Market implied probability: {market_home_prob:.1%}.",
            'data_points': {
                'market_implied_probability': market_home_prob,
                'market_confidence': market_confidence
            }
        }
    
    def _analyze_situational_factors(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze situational and contextual factors"""
        reasoning = []
        
        # Home court advantage
        if data.get('is_home', True):
            home_factor = data.get('home_advantage', 0.1)
            if home_factor > 0.15:
                reasoning.append({
                    'factor': 'Home Court Advantage',
                    'impact': 'Positive',
                    'weight': 0.12,
                    'explanation': f"Strong home court advantage factor ({home_factor:.2f}) supports home team.",
                    'data_points': {'home_advantage_factor': home_factor}
                })
        
        # Season timing
        season_progress = data.get('season_progress', 0.5)
        if season_progress > 0.8:
            reasoning.append({
                'factor': 'Late Season Context',
                'impact': 'Neutral',
                'weight': 0.08,
                'explanation': 'Late season games may have playoff implications affecting team motivation.',
                'data_points': {'season_progress': season_progress}
            })
        
        # Day of week (rest considerations)
        day_of_week = data.get('day_of_week', 3)
        if day_of_week in [0, 1]:  # Sunday/Monday (potential fatigue)
            reasoning.append({
                'factor': 'Schedule Consideration',
                'impact': 'Neutral',
                'weight': 0.06,
                'explanation': 'Game timing may affect team rest and preparation.',
                'data_points': {'day_of_week': day_of_week}
            })
        
        return reasoning
    
    def generate_summary(self, reasoning: List[Dict[str, Any]], confidence: float) -> Dict[str, Any]:
        """Generate comprehensive summary of reasoning"""
        if not reasoning:
            return {
                'summary': 'Limited data available for comprehensive analysis',
                'confidence_level': 'Low',
                'key_factors': [],
                'risk_factors': []
            }
        
        # Sort by weight to identify key factors
        sorted_reasoning = sorted(reasoning, key=lambda x: x['weight'], reverse=True)
        key_factors = [r['factor'] for r in sorted_reasoning[:3]]
        
        # Identify risk factors (negative impact)
        risk_factors = [r['factor'] for r in reasoning if r['impact'] == 'Negative']
        
        # Determine confidence level
        if confidence > 0.75:
            confidence_level = 'High'
        elif confidence > 0.60:
            confidence_level = 'Medium-High'
        elif confidence > 0.45:
            confidence_level = 'Medium'
        else:
            confidence_level = 'Low'
        
        # Generate dynamic summary
        if len(key_factors) >= 2:
            summary = f"Prediction supported by strong {key_factors[0].lower()} and {key_factors[1].lower()}."
        elif len(key_factors) == 1:
            summary = f"Primary factor: {key_factors[0].lower()}."
        else:
            summary = "Multiple factors contribute to this prediction."
        
        if risk_factors:
            summary += f" Risk factors: {', '.join(risk_factors).lower()}."
        
        return {
            'summary': summary,
            'confidence_level': confidence_level,
            'key_factors': key_factors,
            'risk_factors': risk_factors,
            'total_factors_analyzed': len(reasoning)
        }