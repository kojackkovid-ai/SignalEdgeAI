import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import logging
from sklearn.model_selection import TimeSeriesSplit
from sklearn.calibration import calibration_curve
from sklearn.metrics import brier_score_loss, log_loss

logger = logging.getLogger(__name__)

class ModelValidator:
    """
    Comprehensive model validation and backtesting framework for sports betting
    """
    
    def __init__(self):
        self.results = {}

    def backtest_model(self, 
                      predictions: pd.DataFrame, 
                      actual_results: pd.DataFrame, 
                      min_confidence: float = 0.55,
                      bet_size: float = 100.0) -> Dict[str, Any]:
        """
        Simulate betting strategy over historical data
        
        predictions: DataFrame with ['game_id', 'prediction', 'confidence', 'odds']
        actual_results: DataFrame with ['game_id', 'outcome']
        """
        try:
            # Merge predictions with results
            df = pd.merge(predictions, actual_results, on='game_id', how='inner')
            
            # Filter by confidence threshold
            df_bet = df[df['confidence'] >= min_confidence].copy()
            
            if len(df_bet) == 0:
                return {'status': 'no_bets', 'message': 'No bets met confidence threshold'}
            
            # Calculate bet outcomes
            df_bet['won'] = df_bet['prediction'] == df_bet['outcome']
            
            # Calculate PnL (Profit and Loss)
            # Convert American odds to decimal
            df_bet['decimal_odds'] = df_bet['odds'].apply(self._american_to_decimal)
            
            # PnL: If won, (odds - 1) * bet_size. If lost, -bet_size
            df_bet['pnl'] = np.where(df_bet['won'], 
                                   (df_bet['decimal_odds'] - 1) * bet_size, 
                                   -bet_size)
            
            # Cumulative PnL
            df_bet['cumulative_pnl'] = df_bet['pnl'].cumsum()
            
            # Calculate metrics
            total_bets = len(df_bet)
            wins = df_bet['won'].sum()
            win_rate = wins / total_bets
            total_profit = df_bet['pnl'].sum()
            roi = (total_profit / (total_bets * bet_size)) * 100
            
            # Sharpe Ratio (assuming daily returns)
            # Group by date if available, otherwise use trade-level Sharpe
            avg_return = df_bet['pnl'].mean()
            std_return = df_bet['pnl'].std()
            sharpe_ratio = (avg_return / std_return) * np.sqrt(total_bets) if std_return > 0 else 0
            
            # Max Drawdown
            df_bet['peak'] = df_bet['cumulative_pnl'].cummax()
            df_bet['drawdown'] = df_bet['peak'] - df_bet['cumulative_pnl']
            max_drawdown = df_bet['drawdown'].max()
            
            return {
                'total_bets': total_bets,
                'wins': int(wins),
                'losses': int(total_bets - wins),
                'win_rate': float(win_rate),
                'total_profit': float(total_profit),
                'roi': float(roi),
                'sharpe_ratio': float(sharpe_ratio),
                'max_drawdown': float(max_drawdown),
                'avg_odds': float(df_bet['decimal_odds'].mean()),
                'profit_factor': float(df_bet[df_bet['pnl'] > 0]['pnl'].sum() / abs(df_bet[df_bet['pnl'] < 0]['pnl'].sum())) if len(df_bet[df_bet['pnl'] < 0]) > 0 else float('inf')
            }
            
        except Exception as e:
            logger.error(f"Error in backtest: {e}")
            return {'error': str(e)}

    def evaluate_calibration(self, y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> Dict[str, Any]:
        """
        Check if model confidence matches actual accuracy (Calibration)
        """
        try:
            prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=n_bins)
            
            # Expected Calibration Error (ECE)
            ece = np.mean(np.abs(prob_true - prob_pred))
            
            # Brier Score (Mean Squared Error of probabilities)
            brier = brier_score_loss(y_true, y_prob)
            
            return {
                'prob_true': prob_true.tolist(),
                'prob_pred': prob_pred.tolist(),
                'ece': float(ece),
                'brier_score': float(brier),
                'is_calibrated': float(ece) < 0.05  # Threshold for "good" calibration
            }
            
        except Exception as e:
            logger.error(f"Error evaluating calibration: {e}")
            return {'error': str(e)}

    def time_series_validation(self, 
                             model_class, 
                             X: pd.DataFrame, 
                             y: pd.Series, 
                             n_splits: int = 5) -> Dict[str, List[float]]:
        """
        Perform Time Series Cross-Validation (respecting chronological order)
        """
        try:
            tscv = TimeSeriesSplit(n_splits=n_splits)
            scores = {
                'accuracy': [],
                'precision': [],
                'recall': [],
                'roi': []  # ROI on validation set
            }
            
            for train_index, test_index in tscv.split(X):
                X_train, X_test = X.iloc[train_index], X.iloc[test_index]
                y_train, y_test = y.iloc[train_index], y.iloc[test_index]
                
                # Train model
                model = model_class()
                model.fit(X_train, y_train)
                
                # Predict
                y_pred = model.predict(X_test)
                
                # Calculate metrics
                scores['accuracy'].append(np.mean(y_pred == y_test))
                
            return scores
            
        except Exception as e:
            logger.error(f"Error in time series validation: {e}")
            return {'error': str(e)}

    def _american_to_decimal(self, odds: float) -> float:
        """Convert American odds to Decimal odds"""
        try:
            odds = float(odds)
            if odds > 0:
                return 1 + (odds / 100)
            else:
                return 1 + (100 / abs(odds))
        except:
            return 1.91  # Default to -110
