#!/usr/bin/env python3
"""
Accuracy Audit Script
Analyzes current predictions in database and calculates actual accuracy metrics.

Usage:
    python audit_accuracy.py --days 30 --sport basketball_nba
    python audit_accuracy.py --all
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import statistics

# Add backend to path  
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(Path(__file__).parent))

# SQLAlchemy imports
from sqlalchemy import select, func, inspect
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker

# Models and database
try:
    from app.models.db_models import Prediction, User
    from app.database import get_database_url
except ImportError:
    # Fallback: try direct import
    import os
    db_path = Path(__file__).parent / "sports_predictions.db"
    if not db_path.exists():
        db_path = Path(__file__).parent.parent / "sports_predictions.db"
    
    def get_database_url():
        return f"sqlite+aiosqlite:///{db_path}"
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AccuracyAudit:
    def __init__(self):
        self.engine = None
        self.async_session = None
        
    async def connect(self):
        """Connect to database"""
        db_url = get_database_url()
        logger.info(f"Connecting to database: {db_url}")
        
        self.engine = create_async_engine(db_url, echo=False)
        self.async_session = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
    
    async def disconnect(self):
        """Disconnect from database"""
        if self.engine:
            await self.engine.dispose()
    
    async def get_predictions(
        self, 
        days: int = 30, 
        sport: Optional[str] = None,
        resolved_only: bool = True
    ) -> List[Dict]:
        """Fetch predictions from database"""
        
        async with self.async_session() as session:
            query = select(Prediction)
            
            # Time filter
            cutoff_date = datetime.now() - timedelta(days=days)
            query = query.where(Prediction.created_at >= cutoff_date)
            
            # Sport filter
            if sport:
                query = query.where(Prediction.sport == sport)
            
            # Resolution filter
            if resolved_only:
                query = query.where(Prediction.resolved_at != None)
                query = query.where(Prediction.result != None)
            
            result = await session.execute(query)
            predictions = result.scalars().all()
            
            return [
                {
                    'id': p.id,
                    'sport': p.sport,
                    'matchup': p.matchup,
                    'prediction': p.prediction,
                    'confidence': p.confidence,
                    'odds': p.odds,
                    'prediction_type': p.prediction_type,
                    'created_at': p.created_at,
                    'resolved_at': p.resolved_at,
                    'result': p.result,
                    'actual_value': p.actual_value,
                    'model_weights': p.model_weights
                }
                for p in predictions
            ]
    
    async def calculate_accuracy(
        self,
        predictions: List[Dict]
    ) -> Dict:
        """Calculate accuracy metrics"""
        
        if not predictions:
            logger.warning("No predictions found")
            return {}
        
        # Basic counts
        total = len(predictions)
        wins = sum(1 for p in predictions if p.get('result') == 'win')
        losses = sum(1 for p in predictions if p.get('result') == 'loss')
        pushes = sum(1 for p in predictions if p.get('result') == 'push')
        
        win_rate = wins / total if total > 0 else 0
        
        # Confidence analysis
        confidences = [p.get('confidence', 0) for p in predictions if p.get('confidence')]
        avg_confidence = statistics.mean(confidences) if confidences else 0
        median_confidence = statistics.median(confidences) if confidences else 0
        
        # Calibration: bucket by confidence and compare to actual accuracy
        confidence_buckets = self._calculate_calibration(predictions)
        
        # Per-sport breakdown
        by_sport = self._breakdown_by_field(predictions, 'sport')
        
        # By prediction type
        by_type = self._breakdown_by_field(predictions, 'prediction_type')
        
        # By model (if available in model_weights)
        by_model = self._breakdown_by_model(predictions)
        
        # By odds (if available)
        by_odds = self._breakdown_by_odds(predictions)
        
        # ROI calculation
        roi_data = self._calculate_roi(predictions)
        
        return {
            'summary': {
                'total_predictions': total,
                'wins': wins,
                'losses': losses,
                'pushes': pushes,
                'win_rate': round(win_rate, 4),
                'loss_rate': round(losses / total if total > 0 else 0, 4),
                'push_rate': round(pushes / total if total > 0 else 0, 4),
            },
            'confidence_metrics': {
                'average': round(avg_confidence, 2),
                'median': round(median_confidence, 2),
                'min': round(min(confidences), 2) if confidences else 0,
                'max': round(max(confidences), 2) if confidences else 0,
            },
            'calibration': confidence_buckets,
            'by_sport': by_sport,
            'by_prediction_type': by_type,
            'by_model': by_model,
            'by_odds': by_odds,
            'roi': roi_data,
            'assessment': self._assess_accuracy(win_rate, confidence_buckets, roi_data),
        }
    
    def _calculate_calibration(self, predictions: List[Dict]) -> Dict:
        """Calculate how well confidence matches actual accuracy"""
        
        # Create confidence buckets
        buckets = {}
        bucket_size = 5  # 5% buckets: 50-55%, 55-60%, etc
        
        for i in range(50, 100, bucket_size):
            bucket_key = f"{i}-{i+bucket_size}%"
            buckets[bucket_key] = {
                'confidence_min': i,
                'confidence_max': i + bucket_size,
                'predictions': [],
                'accuracy': None,
            }
        
        # Distribute predictions into buckets
        for pred in predictions:
            conf = pred.get('confidence', 0)
            for bucket in buckets.values():
                if bucket['confidence_min'] <= conf < bucket['confidence_max']:
                    bucket['predictions'].append(pred)
                    break
        
        # Calculate accuracy per bucket
        for bucket_key, bucket in buckets.items():
            if not bucket['predictions']:
                bucket['sample_size'] = 0
                bucket['accuracy'] = None
                continue
            
            wins = sum(1 for p in bucket['predictions'] if p.get('result') == 'win')
            total = len(bucket['predictions'])
            bucket['sample_size'] = total
            bucket['accuracy'] = round(wins / total if total > 0 else 0, 4)
        
        # Calculate calibration error
        errors = []
        for bucket_key, bucket in buckets.items():
            if bucket['accuracy'] is None or bucket['sample_size'] < 5:
                continue
            
            expected = (bucket['confidence_min'] + bucket['confidence_max']) / 2 / 100
            actual = bucket['accuracy']
            error = abs(expected - actual)
            errors.append(error)
        
        calibration_error = round(statistics.mean(errors), 4) if errors else None
        
        return {
            'calibration_error': calibration_error,  # 0 = perfect calibration, <0.10 = good
            'error_interpretation': self._interpret_calibration_error(calibration_error),
            'buckets': buckets,
        }
    
    def _breakdown_by_field(self, predictions: List[Dict], field: str) -> Dict:
        """Break down predictions by a specific field"""
        breakdown = {}
        
        for pred in predictions:
            key = pred.get(field, 'unknown')
            if key not in breakdown:
                breakdown[key] = {'wins': 0, 'total': 0}
            
            breakdown[key]['total'] += 1
            if pred.get('result') == 'win':
                breakdown[key]['wins'] += 1
        
        # Calculate accuracy for each
        for key in breakdown:
            data = breakdown[key]
            data['accuracy'] = round(data['wins'] / data['total'] if data['total'] > 0 else 0, 4)
        
        return breakdown
    
    def _breakdown_by_model(self, predictions: List[Dict]) -> Dict:
        """Break down by model used in ensemble"""
        breakdown = {}
        
        for pred in predictions:
            weights = pred.get('model_weights')
            if not weights:
                continue
            
            # weights is typically {'xgboost': 0.35, 'lightgbm': 0.30, ...}
            if isinstance(weights, dict):
                for model_name in weights.keys():
                    if model_name not in breakdown:
                        breakdown[model_name] = {'wins': 0, 'total': 0}
                    
                    breakdown[model_name]['total'] += 1
                    if pred.get('result') == 'win':
                        breakdown[model_name]['wins'] += 1
        
        # Calculate accuracy
        for model_name in breakdown:
            data = breakdown[model_name]
            data['accuracy'] = round(data['wins'] / data['total'] if data['total'] > 0 else 0, 4)
        
        return breakdown
    
    def _breakdown_by_odds(self, predictions: List[Dict]) -> Dict:
        """Break down by odds ranges"""
        breakdown = {}
        
        for pred in predictions:
            odds_str = pred.get('odds', '')
            if not odds_str:
                continue
            
            # Parse odds like "+110" or "-110"
            try:
                odds_val = int(odds_str)
                if odds_val > 200:
                    bucket = "Long odds (>+200)"
                elif odds_val > 100:
                    bucket = "Moderate odds (+100 to +200)"
                elif odds_val > -100:
                    bucket = "Even odds (±100)"
                else:
                    bucket = "Favorite odds (<-100)"
                
                if bucket not in breakdown:
                    breakdown[bucket] = {'wins': 0, 'total': 0}
                
                breakdown[bucket]['total'] += 1
                if pred.get('result') == 'win':
                    breakdown[bucket]['wins'] += 1
            except:
                pass
        
        # Calculate accuracy
        for bucket in breakdown:
            data = breakdown[bucket]
            data['accuracy'] = round(data['wins'] / data['total'] if data['total'] > 0 else 0, 4)
        
        return breakdown
    
    def _calculate_roi(self, predictions: List[Dict]) -> Dict:
        """Calculate return on investment"""
        
        # Assume $100 per prediction
        unit_bet = 100
        total_wagered = len(predictions) * unit_bet
        
        # Calculate payouts based on odds
        total_returned = 0
        winning_count = 0
        losing_count = 0
        
        for pred in predictions:
            if pred.get('result') == 'win':
                odds_str = pred.get('odds', '+100')
                try:
                    odds_val = int(odds_str)
                    if odds_val > 0:
                        payout = unit_bet + (unit_bet * odds_val / 100)
                    else:
                        payout = unit_bet + (unit_bet * 100 / abs(odds_val))
                    
                    total_returned += payout
                    winning_count += 1
                except:
                    total_returned += unit_bet
                    winning_count += 1
            else:
                losing_count += 1
        
        profit_loss = total_returned - total_wagered
        roi = profit_loss / total_wagered if total_wagered > 0 else 0
        
        return {
            'total_wagered': total_wagered,
            'total_returned': round(total_returned, 2),
            'profit_loss': round(profit_loss, 2),
            'roi': round(roi, 4),
            'roi_percentage': f"{roi * 100:.1f}%",
            'winning_predictions': winning_count,
            'losing_predictions': losing_count,
        }
    
    def _interpret_calibration_error(self, error: Optional[float]) -> str:
        """Interpret calibration error"""
        if error is None:
            return "Insufficient data"
        elif error < 0.05:
            return "✅ EXCELLENT - Very well calibrated"
        elif error < 0.10:
            return "✅ GOOD - Well calibrated"
        elif error < 0.15:
            return "⚠️  FAIR - Moderately calibrated"
        else:
            return "❌ POOR - Badly calibrated, confidence scores unreliable"
    
    def _assess_accuracy(self, win_rate: float, calibration: Dict, roi: Dict) -> Dict:
        """Assess overall accuracy and readiness for monetization"""
        
        assessment = {
            'ready_for_monetization': False,
            'issues': [],
            'recommendations': [],
            'score': 0,
        }
        
        # Win rate assessment
        if win_rate < 0.50:
            assessment['issues'].append("❌ Win rate below 50% (worse than random)")
            assessment['recommendations'].append("Model accuracy is poor. Do NOT monetize. Need model retraining.")
        elif win_rate < 0.52:
            assessment['issues'].append("⚠️  Win rate < 52%")
            assessment['recommendations'].append("Barely above random. Need more training data or model improvements.")
        elif win_rate < 0.55:
            assessment['recommendations'].append("✅ Win rate acceptable (52-55%). Can monetize cautiously.")
            assessment['score'] += 40
        else:
            assessment['recommendations'].append("✅ Win rate strong (>55%). Good edge for monetization.")
            assessment['score'] += 60
        
        # Calibration assessment
        cal_error = calibration.get('calibration_error', 0.20)
        if cal_error > 0.15:
            assessment['issues'].append("❌ Poor confidence calibration")
            assessment['recommendations'].append("Confidence scores are unreliable. Fix before showing to users.")
        elif cal_error > 0.10:
            assessment['issues'].append("⚠️  Confidence calibration could improve")
            assessment['score'] += 20
        else:
            assessment['recommendations'].append("✅ Confidence scores well calibrated")
            assessment['score'] += 30
        
        # ROI assessment
        roi = roi.get('roi', 0)
        if roi < -0.05:
            assessment['issues'].append("❌ Negative ROI > -5%")
            assessment['recommendations'].append("Predictions losing money. Do NOT charge for these.")
        elif roi < 0:
            assessment['issues'].append("⚠️  Slight negative ROI")
            assessment['score'] += 10
        elif roi > 0.05:
            assessment['recommendations'].append("✅ Positive ROI (>5%). Good economic viability.")
            assessment['score'] += 30
        else:
            assessment['score'] += 20
        
        # Final verdict
        if not assessment['issues']:
            assessment['ready_for_monetization'] = True
        
        return assessment


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Audit prediction accuracy')
    parser.add_argument('--days', type=int, default=30, help='Number of days to analyze')
    parser.add_argument('--sport', type=str, help='Specific sport to analyze')
    parser.add_argument('--all', action='store_true', help='Analyze all unresolved predictions')
    parser.add_argument('--unresolved', action='store_true', help='Include unresolved predictions')
    
    args = parser.parse_args()
    
    audit = AccuracyAudit()
    
    try:
        await audit.connect()
        
        logger.info(f"Fetching predictions (days={args.days}, sport={args.sport}, unresolved={args.unresolved})...")
        predictions = await audit.get_predictions(
            days=args.days,
            sport=args.sport,
            resolved_only=not args.unresolved
        )
        
        logger.info(f"Found {len(predictions)} predictions")
        
        if not predictions:
            logger.warning("No predictions found. Need to populate resolved outcomes first.")
            logger.info("See ACCURACY_AUDIT_PLAN.md for instructions.")
            return
        
        logger.info("Calculating accuracy metrics...")
        accuracy = await audit.calculate_accuracy(predictions)
        
        # Print results
        print("\n" + "="*80)
        print("PREDICTION ACCURACY AUDIT")
        print("="*80)
        
        if accuracy.get('summary'):
            print("\n📊 SUMMARY:")
            summary = accuracy['summary']
            print(f"  Total Predictions: {summary['total_predictions']}")
            print(f"  Wins: {summary['wins']}")
            print(f"  Losses: {summary['losses']}")
            print(f"  Pushes: {summary['pushes']}")
            print(f"  Win Rate: {summary['win_rate']*100:.1f}%")
        
        if accuracy.get('confidence_metrics'):
            print("\n🎯 CONFIDENCE METRICS:")
            cm = accuracy['confidence_metrics']
            print(f"  Average: {cm['average']}%")
            print(f"  Median: {cm['median']}%")
            print(f"  Range: {cm['min']}% - {cm['max']}%")
        
        if accuracy.get('calibration'):
            print("\n📈 CALIBRATION:")
            cal = accuracy['calibration']
            print(f"  Calibration Error: {cal['calibration_error']}")
            print(f"  Assessment: {cal['error_interpretation']}")
            print("\n  By Confidence Bucket:")
            for bucket, data in cal['buckets'].items():
                if data['sample_size'] > 0:
                    print(f"    {bucket}: {data['accuracy']*100:.1f}% accuracy ({data['sample_size']} predictions)")
        
        if accuracy.get('by_sport'):
            print("\n🏀 BY SPORT:")
            for sport, data in accuracy['by_sport'].items():
                print(f"  {sport}: {data['accuracy']*100:.1f}% ({data['total']} predictions)")
        
        if accuracy.get('roi'):
            print("\n💰 ROI:")
            roi = accuracy['roi']
            print(f"  Total Wagered: ${roi['total_wagered']}")
            print(f"  Total Returned: ${roi['total_returned']}")
            print(f"  Profit/Loss: ${roi['profit_loss']}")
            print(f"  ROI: {roi['roi_percentage']}")
        
        if accuracy.get('assessment'):
            print("\n✅ ASSESSMENT:")
            assess = accuracy['assessment']
            print(f"  Score: {assess['score']}/100")
            if assess['ready_for_monetization']:
                print(f"  Ready for monetization: ✅ YES")
            else:
                print(f"  Ready for monetization: ❌ NO")
            
            if assess['issues']:
                print(f"\n  Issues:")
                for issue in assess['issues']:
                    print(f"    {issue}")
            
            if assess['recommendations']:
                print(f"\n  Recommendations:")
                for rec in assess['recommendations']:
                    print(f"    {rec}")
        
        print("\n" + "="*80)
        
        # Save to JSON
        output_file = Path(__file__).parent / "accuracy_audit_report.json"
        with open(output_file, 'w') as f:
            # Convert datetime objects to strings for JSON serialization
            accuracy_clean = json.loads(
                json.dumps(accuracy, default=str)
            )
            json.dump(accuracy_clean, f, indent=2)
        
        logger.info(f"Audit report saved to: {output_file}")
    
    finally:
        await audit.disconnect()


if __name__ == '__main__':
    asyncio.run(main())
