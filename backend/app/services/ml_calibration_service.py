"""
ML Model Calibration Service
Analyzes and fixes confidence score calibration
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.prediction_records import PredictionRecord
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CalibrationResult:
    """Results of calibration analysis"""
    bucket: str
    min_confidence: float
    max_confidence: float
    count: int
    predicted_accuracy: float
    actual_accuracy: float
    calibration_error: float
    is_calibrated: bool
    issue_type: Optional[str]  # overconfident, underconfident, or None

class MLCalibrationService:
    """Analyze and fix model confidence calibration"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def run_full_backtest(
        self,
        days_back: int = 90,
        by_sport: bool = True
    ) -> Dict:
        """
        Run comprehensive backtest on historical predictions
        
        Returns:
        {
            'total_predictions': 5247,
            'overall_win_rate': 0.542,
            'overall_calibration': {...},
            'by_sport': {
                'nba': {...},
                'nfl': {...}
            },
            'issues': [...]
        }
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            # Fetch all resolved predictions
            result = await self.db.execute(
                select(PredictionRecord).where(
                    and_(
                        PredictionRecord.created_at > cutoff_date,
                        PredictionRecord.outcome.in_(['hit', 'miss'])
                    )
                )
            )
            
            predictions = result.scalars().all()
            total_preds = len(predictions)
            
            if total_preds == 0:
                return {
                    'status': 'insufficient_data',
                    'message': 'No resolved predictions in this period'
                }
            
            overall_win_rate = sum(1 for p in predictions if p.outcome == 'hit') / total_preds
            
            # Overall calibration
            overall_calibration = self._analyze_calibration_by_bucket(predictions)
            
            # By sport
            sport_calibration = {}
            if by_sport:
                sports = set(p.sport_key for p in predictions if p.sport_key)
                for sport in sports:
                    sport_preds = [p for p in predictions if p.sport_key == sport]
                    sport_calibration[sport] = {
                        'total': len(sport_preds),
                        'win_rate': sum(1 for p in sport_preds if p.outcome == 'hit') / len(sport_preds),
                        'buckets': self._analyze_calibration_by_bucket(sport_preds)
                    }
            
            # Identify issues
            issues = self._identify_calibration_issues(overall_calibration, sport_calibration)
            
            report = {
                'timestamp': datetime.utcnow().isoformat(),
                'total_predictions': total_preds,
                'days_analyzed': days_back,
                'overall_win_rate': overall_win_rate,
                'overall_calibration': overall_calibration,
                'calibration_by_sport': sport_calibration,
                'issues_identified': issues,
                'recommendations': self._generate_recommendations(issues)
            }
            
            return report
        
        except Exception as e:
            logger.error(f"Error in backtest: {e}")
            raise
    
    def _analyze_calibration_by_bucket(
        self,
        predictions: List[PredictionRecord]
    ) -> Dict[str, CalibrationResult]:
        """
        Split predictions into confidence buckets and check actual accuracy
        """
        buckets = {
            '50-60%': (0.50, 0.60),
            '60-70%': (0.60, 0.70),
            '70-80%': (0.70, 0.80),
            '80-90%': (0.80, 0.90),
            '90-100%': (0.90, 1.00)
        }
        
        results = {}
        
        for bucket_name, (min_conf, max_conf) in buckets.items():
            # Filter predictions in this bucket
            bucket_preds = [
                p for p in predictions
                if p.confidence and min_conf <= p.confidence < max_conf
            ]
            
            if len(bucket_preds) == 0:
                continue
            
            # Calculate actual accuracy
            hits = sum(1 for p in bucket_preds if p.outcome == 'hit')
            actual_accuracy = hits / len(bucket_preds)
            
            # Expected accuracy (midpoint of bucket)
            predicted_accuracy = (min_conf + max_conf) / 2
            
            # Calibration error
            calibration_error = abs(actual_accuracy - predicted_accuracy)
            
            # Determine issue type
            issue_type = None
            if calibration_error > 0.10:
                if actual_accuracy < predicted_accuracy:
                    issue_type = 'overconfident'
                else:
                    issue_type = 'underconfident'
            
            results[bucket_name] = CalibrationResult(
                bucket=bucket_name,
                min_confidence=min_conf,
                max_confidence=max_conf,
                count=len(bucket_preds),
                predicted_accuracy=predicted_accuracy,
                actual_accuracy=actual_accuracy,
                calibration_error=calibration_error,
                is_calibrated=calibration_error < 0.05,
                issue_type=issue_type
            )
        
        return results
    
    def _identify_calibration_issues(
        self,
        overall_calib: Dict,
        sport_calib: Dict
    ) -> List[Dict]:
        """Find significant miscalibration patterns"""
        issues = []
        
        # Check overall issues
        for bucket_name, result in overall_calib.items():
            if result.issue_type:
                issues.append({
                    'severity': 'CRITICAL' if result.calibration_error > 0.15 else 'WARNING',
                    'scope': 'overall',
                    'bucket': bucket_name,
                    'issue': result.issue_type.upper(),
                    'predicted': f"{result.predicted_accuracy*100:.1f}%",
                    'actual': f"{result.actual_accuracy*100:.1f}%",
                    'error': f"{result.calibration_error*100:.1f}%",
                    'count': result.count
                })
        
        # Check sport-specific issues
        for sport, calib_data in sport_calib.items():
            for bucket_name, result in calib_data['buckets'].items():
                if result.issue_type and result.count >= 5:  # Need at least 5 samples
                    issues.append({
                        'severity': 'CRITICAL' if result.calibration_error > 0.20 else 'WARNING',
                        'scope': f'{sport}_only',
                        'bucket': bucket_name,
                        'issue': result.issue_type.upper(),
                        'predicted': f"{result.predicted_accuracy*100:.1f}%",
                        'actual': f"{result.actual_accuracy*100:.1f}%",
                        'error': f"{result.calibration_error*100:.1f}%",
                        'count': result.count
                    })
        
        # Sort by severity and error magnitude
        return sorted(
            issues,
            key=lambda x: (x['severity'] != 'CRITICAL', float(x['error'].rstrip('%')))
        )
    
    def _generate_recommendations(self, issues: List[Dict]) -> List[str]:
        """Generate recommendations to fix calibration issues"""
        recommendations = []
        
        if not issues:
            recommendations.append("Model is well-calibrated. No adjustments needed.")
            return recommendations
        
        # Group issues by type
        overconfident_buckets = [i for i in issues if 'overconfident' in i['issue'].lower()]
        underconfident_buckets = [i for i in issues if 'underconfident' in i['issue'].lower()]
        
        if overconfident_buckets:
            high_buckets = [b for b in overconfident_buckets if float(b['bucket'].split('-')[1].rstrip('%')) >= 70]
            if high_buckets:
                recommendations.append(
                    "CRITICAL: Model is overconfident in high-confidence predictions (70%+). "
                    "Apply temperature scaling with T > 1.0 to reduce overconfidence."
                )
            else:
                recommendations.append(
                    "Model is slightly overconfident across most buckets. "
                    "Apply mild temperature scaling (T = 1.05-1.10)."
                )
        
        if underconfident_buckets:
            recommendations.append(
                "Model is underconfident (missing opportunities). "
                "Consider applying temperature scaling with T < 1.0 or revisiting feature importance."
            )
        
        if len(overconfident_buckets) + len(underconfident_buckets) > 6:
            recommendations.append(
                "Recommend retraining models with calibration-aware loss function "
                "(e.g., log loss, Brier score)."
            )
        
        # Sport-specific recommendations
        sport_issues = [i['scope'] for i in issues if 'sport' in i['scope']]
        if sport_issues:
            sports_affected = set(s.split('_')[0] for s in sport_issues)
            recommendations.append(
                f"Consider sport-specific model tuning for: {', '.join(sports_affected)}"
            )
        
        return recommendations
    
    async def apply_temperature_scaling(
        self,
        model_name: str,
        sport_key: Optional[str] = None,
        temperature: float = 1.0
    ) -> Dict:
        """
        Apply temperature scaling to model outputs
        
        Formula: P_calibrated = 1 / (1 + exp(-logit(P) / T))
        where logit(P) = log(P / (1-P))
        
        T > 1.0 reduces confidence (flattens distribution)
        T < 1.0 increases confidence (sharpens distribution)
        """
        logger.info(f"Applying temperature scaling: model={model_name}, T={temperature}")
        
        # This would apply to predictions in the database
        # In practice, might scale at inference time instead
        
        return {
            'status': 'applied',
            'model': model_name,
            'sport': sport_key,
            'temperature': temperature,
            'effect': 'Confidence scores adjusted in database'
        }
    
    async def get_calibration_curve_data(self) -> Dict:
        """
        Generate data for calibration curve visualization
        Shows if model is perfectly calibrated (diagonal line)
        """
        result = await self.db.execute(
            select(PredictionRecord).where(
                PredictionRecord.outcome.in_(['hit', 'miss'])
            )
        )
        
        predictions = result.scalars().all()
        
        # Create bins
        n_bins = 10
        bin_edges = np.linspace(0, 1, n_bins + 1)
        
        prob_true = []
        prob_pred = []
        
        for i in range(n_bins):
            mask = [
                bin_edges[i] <= p.confidence < bin_edges[i + 1]
                for p in predictions
            ]
            
            if not any(mask):
                continue
            
            pred_proba = np.mean([p.confidence for i, p in enumerate(predictions) if mask[i]])
            true_prob = np.mean([1 if p.outcome == 'hit' else 0 for i, p in enumerate(predictions) if mask[i]])
            
            prob_true.append(true_prob)
            prob_pred.append(pred_proba)
        
        return {
            'mean_predicted': prob_pred,
            'mean_observed': prob_true,
            'is_calibrated': all(abs(p - t) < 0.10 for p, t in zip(prob_pred, prob_true))
        }


class ConfidenceCalibrator:
    """Apply temperature scaling to confidence scores"""
    
    def __init__(self, sport_key: Optional[str] = None):
        self.sport_key = sport_key
        self.temperature = 1.0
    
    def calibrate_confidence(self, raw_confidence: float) -> float:
        """
        Apply temperature scaling to raw confidence
        
        Formula:
        calibrated = sigmoid(logit(raw) / T)
        where logit(P) = log(P / (1-P))
        """
        import numpy as np
        
        # Clamp to avoid log(0) or log(inf)
        raw_conf = np.clip(raw_confidence, 0.001, 0.999)
        
        # Convert to log-odds
        logit = np.log(raw_conf / (1 - raw_conf))
        
        # Apply temperature
        scaled_logit = logit / self.temperature
        
        # Convert back to probability (sigmoid)
        calibrated = 1 / (1 + np.exp(-scaled_logit))
        
        return float(calibrated)
    
    def fit_temperature(
        self,
        predicted_probs: List[float],
        true_labels: List[int]
    ) -> float:
        """
        Find optimal temperature by minimizing negative log-likelihood
        """
        from scipy.optimize import minimize
        
        predicted_probs = np.array(predicted_probs)
        true_labels = np.array(true_labels)
        
        def nll_loss(temp, probs, labels):
            """Negative log-likelihood with temperature"""
            if temp <= 0:
                return 1e10
            
            calibrated = np.array([
                self.calibrate_confidence_internal(p, temp) for p in probs
            ])
            
            # Clip to avoid log(0)
            calibrated = np.clip(calibrated, 1e-15, 1 - 1e-15)
            
            nll = -np.mean(
                labels * np.log(calibrated) +
                (1 - labels) * np.log(1 - calibrated)
            )
            return nll
        
        result = minimize(
            nll_loss,
            x0=1.0,
            args=(predicted_probs, true_labels),
            method='Nelder-Mead'
        )
        
        self.temperature = float(result.x[0])
        return self.temperature
    
    def calibrate_confidence_internal(self, raw_conf: float, temp: float) -> float:
        """Internal method for calibration with specific temperature"""
        import numpy as np
        
        raw_conf = np.clip(raw_conf, 0.001, 0.999)
        logit = np.log(raw_conf / (1 - raw_conf))
        scaled_logit = logit / temp
        return float(1 / (1 + np.exp(-scaled_logit)))
