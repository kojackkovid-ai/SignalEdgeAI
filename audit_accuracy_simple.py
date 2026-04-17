#!/usr/bin/env python3
"""
Accuracy Audit Script - Simplified Version
Analyzes current predictions in database for accuracy.

Usage:
    python audit_accuracy_simple.py --days 30
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import statistics
import sqlite3

# Find the database
db_candidates = [
    Path(__file__).parent / "sports_predictions.db",
    Path(__file__).parent.parent / "sports_predictions.db",
    Path.home() / ".sports_predictions.db",
]

db_path = None
for candidate in db_candidates:
    if candidate.exists():
        db_path = candidate
        print(f"✅ Found database: {db_path}")
        break

if not db_path:
    print("❌ ERROR: Could not find database!")
    print(f"Looked in:")
    for c in db_candidates:
        print(f"  - {c}")
    sys.exit(1)


def get_predictions(days: int = 30, resolved_only: bool = True) -> List[Dict]:
    """Fetch predictions from SQLite database"""
    
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
    
    if resolved_only:
        query = """
        SELECT 
            id, sport, matchup, prediction, confidence, odds, 
            prediction_type, created_at, resolved_at, result, 
            actual_value, model_weights
        FROM predictions
        WHERE created_at >= ?
        AND resolved_at IS NOT NULL
        AND result IS NOT NULL
        """
    else:
        query = """
        SELECT 
            id, sport, matchup, prediction, confidence, odds, 
            prediction_type, created_at, resolved_at, result, 
            actual_value, model_weights
        FROM predictions
        WHERE created_at >= ?
        """
    
    cursor.execute(query, (cutoff_date,))
    rows = cursor.fetchall()
    
    predictions = []
    for row in rows:
        pred = {
            'id': row['id'],
            'sport': row['sport'],
            'matchup': row['matchup'],
            'prediction': row['prediction'],
            'confidence': row['confidence'],
            'odds': row['odds'],
            'prediction_type': row['prediction_type'],
            'created_at': row['created_at'],
            'resolved_at': row['resolved_at'],
            'result': row['result'],
            'actual_value': row['actual_value'],
            'model_weights': row['model_weights']
        }
        predictions.append(pred)
    
    conn.close()
    return predictions


def calculate_accuracy(predictions: List[Dict]) -> Dict:
    """Calculate accuracy metrics"""
    
    if not predictions:
        print("No predictions found.")
        return {'status': 'no_data'}
    
    total = len(predictions)
    wins = sum(1 for p in predictions if p.get('result') == 'win')
    losses = sum(1 for p in predictions if p.get('result') == 'loss')
    pushes = sum(1 for p in predictions if p.get('result') == 'push')
    
    win_rate = wins / total if total > 0 else 0
    
    # Confidence metrics
    confidences = [p.get('confidence', 0) for p in predictions if p.get('confidence')]
    if confidences:
        avg_confidence = statistics.mean(confidences)
        median_confidence = statistics.median(confidences)
        min_confidence = min(confidences)
        max_confidence = max(confidences)
    else:
        avg_confidence = median_confidence = min_confidence = max_confidence = 0
    
    # By sport
    by_sport = {}
    for pred in predictions:
        sport = pred.get('sport', 'unknown')
        if sport not in by_sport:
            by_sport[sport] = {'wins': 0, 'total': 0}
        by_sport[sport]['total'] += 1
        if pred.get('result') == 'win':
            by_sport[sport]['wins'] += 1
    
    for sport in by_sport:
        data = by_sport[sport]
        data['accuracy'] = data['wins'] / data['total'] if data['total'] > 0 else 0
    
    # ROI calculation (assume $100 per prediction)
    roi_data = calculate_roi(predictions)
    
    # Calibration
    calibration = calculate_calibration(predictions)
    
    result = {
        'status': 'success',
        'summary': {
            'total_predictions': total,
            'wins': wins,
            'losses': losses,
            'pushes': pushes,
            'win_rate': round(win_rate, 4),
        },
        'confidence_metrics': {
            'average': round(avg_confidence, 2),
            'median': round(median_confidence, 2),
            'min': round(min_confidence, 2),
            'max': round(max_confidence, 2),
        },
        'by_sport': {sport: {'accuracy': round(data['accuracy'], 4), 'total': data['total']} 
                     for sport, data in by_sport.items()},
        'calibration': calibration,
        'roi': roi_data,
    }
    
    return result


def calculate_roi(predictions: List[Dict]) -> Dict:
    """Calculate return on investment"""
    unit_bet = 100
    total_wagered = len(predictions) * unit_bet
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
        'wins': winning_count,
        'losses': losing_count,
    }


def calculate_calibration(predictions: List[Dict]) -> Dict:
    """Calculate confidence calibration"""
    
    buckets = {}
    for i in range(50, 100, 5):
        bucket_key = f"{i}-{i+5}%"
        buckets[bucket_key] = {'count': 0, 'wins': 0, 'accuracy': None}
    
    for pred in predictions:
        conf = pred.get('confidence', 0)
        if conf and conf >= 50:
            bucket_idx = int((conf - 50) / 5)
            bucket_key = f"{50 + bucket_idx*5}-{50 + (bucket_idx+1)*5}%"
            if bucket_key in buckets:
                buckets[bucket_key]['count'] += 1
                if pred.get('result') == 'win':
                    buckets[bucket_key]['wins'] += 1
    
    # Calculate accuracy per bucket
    errors = []
    for bucket_key, bucket in buckets.items():
        if bucket['count'] > 0:
            bucket['accuracy'] = round(bucket['wins'] / bucket['count'], 4)
            expected = (int(bucket_key.split('-')[0]) + int(bucket_key.split('-')[1].rstrip('%'))) / 2 / 100
            error = abs(expected - bucket['accuracy'])
            errors.append(error)
    
    calibration_error = round(statistics.mean(errors), 4) if errors else None
    
    return {
        'error': calibration_error,
        'buckets': buckets,
    }


def print_results(results: Dict):
    """Print results in human-readable format"""
    
    print("\n" + "="*80)
    print("PREDICTION ACCURACY AUDIT")
    print("="*80)
    
    if results.get('status') == 'no_data':
        print("\n❌ No predictions found in database.")
        print("   Note: This is expected if this is a fresh database.")
        print("   Predictions need to be created and resolved first.")
        return
    
    if results.get('status') != 'success':
        print(f"\n❌ Error: {results.get('error', 'Unknown error')}")
        return
    
    # Summary
    summary = results.get('summary', {})
    print("\n📊 SUMMARY:")
    print(f"  Total Predictions: {summary.get('total_predictions', 0)}")
    print(f"  Wins: {summary.get('wins', 0)}")
    print(f"  Losses: {summary.get('losses', 0)}")
    print(f"  Pushes: {summary.get('pushes', 0)}")
    print(f"  Win Rate: {summary.get('win_rate', 0)*100:.1f}%")
    
    # Confidence
    cm = results.get('confidence_metrics', {})
    print("\n🎯 CONFIDENCE METRICS:")
    print(f"  Average: {cm.get('average', 0)}%")
    print(f"  Median: {cm.get('median', 0)}%")
    print(f"  Range: {cm.get('min', 0)}% - {cm.get('max', 0)}%")
    
    # By Sport
    by_sport = results.get('by_sport', {})
    if by_sport:
        print("\n🏀 BY SPORT:")
        for sport, data in by_sport.items():
            acc = data.get('accuracy', 0)
            total = data.get('total', 0)
            print(f"  {sport}: {acc*100:.1f}% ({total} predictions)")
    
    # ROI
    roi = results.get('roi', {})
    print("\n💰 ROI:")
    print(f"  Total Wagered: ${roi.get('total_wagered', 0)}")
    print(f"  Total Returned: ${roi.get('total_returned', 0)}")
    print(f"  Profit/Loss: ${roi.get('profit_loss', 0)}")
    print(f"  ROI: {roi.get('roi_percentage', '0%')}")
    
    # Calibration
    cal = results.get('calibration', {})
    if cal.get('error'):
        print("\n📈 CALIBRATION:")
        print(f"  Error: {cal.get('error')}")
        buckets = cal.get('buckets', {})
        for bucket, data in buckets.items():
            if data['count'] > 0:
                print(f"    {bucket}: {data.get('accuracy', 0)*100:.1f}% ({data['count']} predictions)")
    
    print("\n" + "="*80)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Audit prediction accuracy')
    parser.add_argument('--days', type=int, default=30, help='Days to analyze (default: 30)')
    parser.add_argument('--unresolved', action='store_true', help='Include unresolved predictions')
    
    args = parser.parse_args()
    
    print(f"\nFetching predictions from last {args.days} days...")
    predictions = get_predictions(days=args.days, resolved_only=not args.unresolved)
    print(f"Found {len(predictions)} predictions\n")
    
    if predictions:
        results = calculate_accuracy(predictions)
        print_results(results)
        
        # Save JSON report
        report_file = Path(__file__).parent / "accuracy_audit_report.json"
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nReport saved to: {report_file}\n")
    else:
        print("No predictions found in database.")
        print(f"(This is normal for a new database or if nothing is resolved yet)\n")
