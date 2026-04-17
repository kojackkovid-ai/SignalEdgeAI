"""
Real-time Model Performance Monitoring Service
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, timedelta
import asyncio
import json
from pathlib import Path
import sqlite3
from dataclasses import dataclass
from collections import defaultdict, deque
import statistics

logger = logging.getLogger(__name__)

@dataclass
class PredictionRecord:
    """Record of a prediction made by the model"""
    prediction_id: str
    sport_key: str
    market_type: str
    game_id: str
    prediction: Any
    confidence: float
    odds: float
    timestamp: datetime
    features: Optional[Dict[str, Any]] = None

@dataclass
class ActualResult:
    """Actual result of a game"""
    game_id: str
    outcome: Any
    timestamp: datetime

class ModelPerformanceMonitor:
    """
    Real-time model performance monitoring with alerting and drift detection
    """
    
    def __init__(self, db_path: str = "model_performance.db"):
        self.db_path = db_path
        self.predictions_buffer = deque(maxlen=10000)
        self.results_buffer = deque(maxlen=10000)
        
        # Performance tracking
        self.daily_performance = defaultdict(lambda: defaultdict(list))
        self.model_accuracy = defaultdict(lambda: defaultdict(list))
        self.confidence_calibration = defaultdict(list)
        
        # Alert thresholds
        self.accuracy_threshold = 0.55  # Minimum acceptable accuracy
        self.confidence_threshold = 0.5  # Minimum confidence threshold
        self.drift_threshold = 0.1  # Data drift threshold
        
        # Initialize database
        self._init_database()
        
        # Start background monitoring
        self.monitoring_active = True
        self.monitor_task = None
    
    def _init_database(self):
        """Initialize SQLite database for performance tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Predictions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                prediction_id TEXT PRIMARY KEY,
                sport_key TEXT,
                market_type TEXT,
                game_id TEXT,
                prediction TEXT,
                confidence REAL,
                odds REAL,
                timestamp TEXT,
                features TEXT
            )
        ''')
        
        # Actual results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS actual_results (
                game_id TEXT PRIMARY KEY,
                outcome TEXT,
                timestamp TEXT
            )
        ''')
        
        # Performance metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sport_key TEXT,
                market_type TEXT,
                date TEXT,
                accuracy REAL,
                precision REAL,
                recall REAL,
                f1_score REAL,
                avg_confidence REAL,
                calibration_error REAL,
                total_predictions INTEGER,
                correct_predictions INTEGER
            )
        ''')
        
        # Alert logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_type TEXT,
                sport_key TEXT,
                market_type TEXT,
                message TEXT,
                severity TEXT,
                timestamp TEXT,
                resolved BOOLEAN DEFAULT FALSE
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def record_prediction(self, prediction: PredictionRecord) -> bool:
        """Record a prediction made by the model"""
        try:
            # Add to buffer
            self.predictions_buffer.append(prediction)
            
            # Store in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            features_json = json.dumps(prediction.features) if prediction.features else None
            
            cursor.execute('''
                INSERT OR REPLACE INTO predictions 
                (prediction_id, sport_key, market_type, game_id, prediction, confidence, odds, timestamp, features)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                prediction.prediction_id, prediction.sport_key, prediction.market_type,
                prediction.game_id, str(prediction.prediction), prediction.confidence,
                prediction.odds, prediction.timestamp.isoformat(), features_json
            ))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Error recording prediction: {e}")
            return False
    
    async def record_actual_result(self, result: ActualResult) -> bool:
        """Record the actual result of a game"""
        try:
            # Add to buffer
            self.results_buffer.append(result)
            
            # Store in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO actual_results 
                (game_id, outcome, timestamp)
                VALUES (?, ?, ?)
            ''', (result.game_id, str(result.outcome), result.timestamp.isoformat()))
            
            conn.commit()
            conn.close()
            
            # Trigger performance update for this game
            await self._update_performance_for_game(result.game_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error recording actual result: {e}")
            return False
    
    async def _update_performance_for_game(self, game_id: str):
        """Update performance metrics for a specific game"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get prediction and result
            cursor.execute('''
                SELECT p.sport_key, p.market_type, p.prediction, p.confidence, a.outcome
                FROM predictions p
                JOIN actual_results a ON p.game_id = a.game_id
                WHERE p.game_id = ?
            ''', (game_id,))
            
            result = cursor.fetchone()
            if result:
                sport_key, market_type, prediction, confidence, actual_outcome = result
                
                # Calculate if prediction was correct
                is_correct = str(prediction) == str(actual_outcome)
                
                # Update daily performance
                today = datetime.utcnow().date().isoformat()
                self.daily_performance[sport_key][market_type].append({
                    'date': today,
                    'correct': is_correct,
                    'confidence': confidence
                })
                
                # Check for performance issues
                await self._check_performance_alerts(sport_key, market_type)
                
                # Update confidence calibration
                self.confidence_calibration[sport_key].append({
                    'confidence': confidence,
                    'correct': is_correct
                })
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error updating performance for game {game_id}: {e}")
    
    async def _check_performance_alerts(self, sport_key: str, market_type: str):
        """Check for performance issues and generate alerts"""
        try:
            # Get recent performance (last 100 predictions)
            recent_predictions = []
            for record in list(self.daily_performance[sport_key][market_type])[-100:]:
                recent_predictions.append(record)
            
            if len(recent_predictions) < 20:  # Need at least 20 predictions for meaningful analysis
                return
            
            # Calculate recent accuracy
            recent_accuracy = sum(1 for p in recent_predictions if p['correct']) / len(recent_predictions)
            
            # Check accuracy threshold
            if recent_accuracy < self.accuracy_threshold:
                await self._create_alert(
                    'low_accuracy',
                    sport_key,
                    market_type,
                    f"Low accuracy detected: {recent_accuracy:.2%} < {self.accuracy_threshold:.2%}",
                    'high'
                )
            
            # Check confidence calibration
            calibration_error = await self._calculate_calibration_error(sport_key)
            if calibration_error > 0.1:  # Poor calibration
                await self._create_alert(
                    'poor_calibration',
                    sport_key,
                    market_type,
                    f"Poor confidence calibration: ECE = {calibration_error:.3f}",
                    'medium'
                )
            
            # Check for sudden performance drop
            if len(recent_predictions) >= 50:
                first_half = recent_predictions[:25]
                second_half = recent_predictions[25:50]
                
                first_accuracy = sum(1 for p in first_half if p['correct']) / len(first_half)
                second_accuracy = sum(1 for p in second_half if p['correct']) / len(second_half)
                
                accuracy_drop = first_accuracy - second_accuracy
                if accuracy_drop > 0.15:  # 15% accuracy drop
                    await self._create_alert(
                        'performance_drop',
                        sport_key,
                        market_type,
                        f"Significant accuracy drop: {accuracy_drop:.2%}",
                        'high'
                    )
                    
        except Exception as e:
            logger.error(f"Error checking performance alerts: {e}")
    
    async def _calculate_calibration_error(self, sport_key: str) -> float:
        """Calculate Expected Calibration Error (ECE)"""
        try:
            calibration_data = self.confidence_calibration[sport_key]
            if len(calibration_data) < 50:
                return 0.0
            
            # Bin predictions by confidence level
            n_bins = 10
            bin_boundaries = np.linspace(0, 1, n_bins + 1)
            
            ece = 0.0
            total_samples = len(calibration_data)
            
            for i in range(n_bins):
                bin_lower = bin_boundaries[i]
                bin_upper = bin_boundaries[i + 1]
                
                # Find samples in this bin
                in_bin = [d for d in calibration_data if bin_lower <= d['confidence'] < bin_upper]
                
                if in_bin:
                    bin_accuracy = sum(1 for d in in_bin if d['correct']) / len(in_bin)
                    bin_confidence = sum(d['confidence'] for d in in_bin) / len(in_bin)
                    bin_weight = len(in_bin) / total_samples
                    
                    ece += bin_weight * abs(bin_accuracy - bin_confidence)
            
            return ece
            
        except Exception as e:
            logger.error(f"Error calculating calibration error: {e}")
            return 0.0
    
    async def _create_alert(self, alert_type: str, sport_key: str, market_type: str, 
                          message: str, severity: str):
        """Create an alert in the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO alerts (alert_type, sport_key, market_type, message, severity, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (alert_type, sport_key, market_type, message, severity, datetime.utcnow().isoformat()))
            
            conn.commit()
            conn.close()
            
            logger.warning(f"ALERT [{severity.upper()}] {sport_key} - {market_type}: {message}")
            
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
    
    async def get_performance_summary(self, sport_key: Optional[str] = None, 
                                    market_type: Optional[str] = None,
                                    days_back: int = 30) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build query
            query = '''
                SELECT sport_key, market_type, date, accuracy, precision, recall, f1_score,
                       avg_confidence, calibration_error, total_predictions, correct_predictions
                FROM performance_metrics
                WHERE date >= ?
            '''
            params = [(datetime.utcnow() - timedelta(days=days_back)).date().isoformat()]
            
            if sport_key:
                query += ' AND sport_key = ?'
                params.append(sport_key)
            
            if market_type:
                query += ' AND market_type = ?'
                params.append(market_type)
            
            query += ' ORDER BY date DESC'
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            # Calculate summary statistics
            if results:
                accuracies = [row[3] for row in results if row[3] is not None]
                f1_scores = [row[6] for row in results if row[6] is not None]
                total_predictions = sum(row[9] for row in results)
                correct_predictions = sum(row[10] for row in results)
                
                summary = {
                    'period': f"Last {days_back} days",
                    'total_predictions': total_predictions,
                    'overall_accuracy': correct_predictions / total_predictions if total_predictions > 0 else 0,
                    'avg_accuracy': statistics.mean(accuracies) if accuracies else 0,
                    'avg_f1_score': statistics.mean(f1_scores) if f1_scores else 0,
                    'daily_breakdown': []
                }
                
                # Add daily breakdown
                for row in results:
                    summary['daily_breakdown'].append({
                        'date': row[2],
                        'sport_key': row[0],
                        'market_type': row[1],
                        'accuracy': row[3],
                        'f1_score': row[6],
                        'predictions': row[9]
                    })
                
                conn.close()
                return summary
            else:
                conn.close()
                return {'message': 'No performance data available for the specified period'}
                
        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return {'error': str(e)}
    
    async def get_active_alerts(self, sport_key: Optional[str] = None, 
                              market_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get active (unresolved) alerts"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = 'SELECT * FROM alerts WHERE resolved = FALSE'
            params = []
            
            if sport_key:
                query += ' AND sport_key = ?'
                params.append(sport_key)
            
            if market_type:
                query += ' AND market_type = ?'
                params.append(market_type)
            
            query += ' ORDER BY timestamp DESC'
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            alerts = []
            for row in results:
                alerts.append({
                    'id': row[0],
                    'alert_type': row[1],
                    'sport_key': row[2],
                    'market_type': row[3],
                    'message': row[4],
                    'severity': row[5],
                    'timestamp': row[6],
                    'resolved': bool(row[7])
                })
            
            conn.close()
            return alerts
            
        except Exception as e:
            logger.error(f"Error getting active alerts: {e}")
            return []
    
    async def resolve_alert(self, alert_id: int) -> bool:
        """Mark an alert as resolved"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('UPDATE alerts SET resolved = TRUE WHERE id = ?', (alert_id,))
            
            conn.commit()
            conn.close()
            
            return cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f"Error resolving alert: {e}")
            return False
    
    async def start_monitoring(self):
        """Start the background monitoring task"""
        if self.monitor_task is None:
            self.monitoring_active = True
            self.monitor_task = asyncio.create_task(self._monitoring_loop())
            logger.info("Model performance monitoring started")
    
    async def stop_monitoring(self):
        """Stop the background monitoring task"""
        self.monitoring_active = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
            self.monitor_task = None
            logger.info("Model performance monitoring stopped")
    
    async def _monitoring_loop(self):
        """Background monitoring loop"""
        while self.monitoring_active:
            try:
                # Daily performance aggregation
                await self._aggregate_daily_performance()
                
                # Clean up old data (keep last 90 days)
                await self._cleanup_old_data()
                
                # Wait 1 hour before next check
                await asyncio.sleep(3600)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def _aggregate_daily_performance(self):
        """Aggregate performance metrics for the previous day"""
        try:
            yesterday = (datetime.utcnow() - timedelta(days=1)).date()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all predictions and results for yesterday
            cursor.execute('''
                SELECT p.sport_key, p.market_type, p.prediction, p.confidence, a.outcome
                FROM predictions p
                JOIN actual_results a ON p.game_id = a.game_id
                WHERE DATE(p.timestamp) = ?
            ''', (yesterday.isoformat(),))
            
            results = cursor.fetchall()
            
            if results:
                # Group by sport_key and market_type
                grouped_results = defaultdict(list)
                for row in results:
                    key = (row[0], row[1])
                    grouped_results[key].append({
                        'prediction': str(row[2]),
                        'confidence': row[3],
                        'actual': str(row[4])
                    })
                
                # Calculate metrics for each group
                for (sport_key, market_type), predictions in grouped_results.items():
                    total = len(predictions)
                    correct = sum(1 for p in predictions if p['prediction'] == p['actual'])
                    accuracy = correct / total if total > 0 else 0
                    
                    avg_confidence = sum(p['confidence'] for p in predictions) / total
                    
                    # Calculate precision, recall, f1 (simplified)
                    unique_labels = set(p['prediction'] for p in predictions) | set(p['actual'] for p in predictions)
                    if len(unique_labels) <= 2:  # Binary classification
                        true_positives = sum(1 for p in predictions if p['prediction'] == p['actual'] == '1')
                        false_positives = sum(1 for p in predictions if p['prediction'] == '1' and p['actual'] != '1')
                        false_negatives = sum(1 for p in predictions if p['prediction'] != '1' and p['actual'] == '1')
                        
                        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
                        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
                        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
                    else:
                        precision = recall = f1 = accuracy  # Fallback for multi-class
                    
                    # Calculate calibration error
                    calibration_error = await self._calculate_daily_calibration_error(predictions)
                    
                    # Insert into performance_metrics table
                    cursor.execute('''
                        INSERT INTO performance_metrics 
                        (sport_key, market_type, date, accuracy, precision, recall, f1_score,
                         avg_confidence, calibration_error, total_predictions, correct_predictions)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (sport_key, market_type, yesterday.isoformat(), accuracy, precision, 
                          recall, f1, avg_confidence, calibration_error, total, correct))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error aggregating daily performance: {e}")
    
    async def _calculate_daily_calibration_error(self, predictions: List[Dict]) -> float:
        """Calculate calibration error for daily predictions"""
        try:
            if len(predictions) < 10:
                return 0.0
            
            n_bins = 5
            bin_boundaries = np.linspace(0, 1, n_bins + 1)
            
            ece = 0.0
            total_samples = len(predictions)
            
            for i in range(n_bins):
                bin_lower = bin_boundaries[i]
                bin_upper = bin_boundaries[i + 1]
                
                in_bin = [p for p in predictions if bin_lower <= p['confidence'] < bin_upper]
                
                if in_bin:
                    bin_accuracy = sum(1 for p in in_bin if p['prediction'] == p['actual']) / len(in_bin)
                    bin_confidence = sum(p['confidence'] for p in in_bin) / len(in_bin)
                    bin_weight = len(in_bin) / total_samples
                    
                    ece += bin_weight * abs(bin_accuracy - bin_confidence)
            
            return ece
            
        except Exception as e:
            logger.error(f"Error calculating daily calibration error: {e}")
            return 0.0
    
    async def _cleanup_old_data(self):
        """Clean up data older than 90 days"""
        try:
            cutoff_date = (datetime.utcnow() - timedelta(days=90)).date().isoformat()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Delete old predictions
            cursor.execute('DELETE FROM predictions WHERE DATE(timestamp) < ?', (cutoff_date,))
            
            # Delete old results
            cursor.execute('DELETE FROM actual_results WHERE DATE(timestamp) < ?', (cutoff_date,))
            
            # Delete old performance metrics
            cursor.execute('DELETE FROM performance_metrics WHERE date < ?', (cutoff_date,))
            
            # Delete old resolved alerts
            cursor.execute('DELETE FROM alerts WHERE resolved = TRUE AND timestamp < ?', (cutoff_date,))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Cleaned up data older than {cutoff_date}")
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")

    async def check_model_performance(self, sport_key: str, market_type: str) -> Dict[str, Any]:
        """
        Check model performance for a specific sport and market type.
        This is called by the auto-training loop to determine if retraining is needed.
        """
        try:
            # Get recent performance metrics
            performance = await self.get_performance_summary(sport_key, market_type, days_back=7)
            
            if 'error' in performance:
                return {
                    'needs_retrain': True,
                    'reason': 'No performance data available',
                    'performance': performance
                }
            
            # Check if accuracy is below threshold
            overall_accuracy = performance.get('overall_accuracy', 0)
            needs_retrain = overall_accuracy < self.accuracy_threshold
            
            # Check for declining trend
            daily_breakdown = performance.get('daily_breakdown', [])
            if len(daily_breakdown) >= 3:
                recent_accuracies = [day['accuracy'] for day in daily_breakdown[-3:] if day.get('accuracy')]
                if len(recent_accuracies) >= 3:
                    # Check if accuracy is declining
                    if recent_accuracies[0] > recent_accuracies[1] > recent_accuracies[2]:
                        needs_retrain = True
            
            return {
                'needs_retrain': needs_retrain,
                'reason': 'Performance below threshold' if needs_retrain else 'Performance acceptable',
                'accuracy': overall_accuracy,
                'threshold': self.accuracy_threshold,
                'performance': performance
            }
            
        except Exception as e:
            logger.error(f"Error checking model performance: {e}")
            return {
                'needs_retrain': False,
                'reason': f'Error checking performance: {str(e)}',
                'error': str(e)
            }
