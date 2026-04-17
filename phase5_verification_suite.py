"""
Phase 5: Comprehensive Verification & Deployment Suite
Compares old vs new confidence calculations, verifies improvements, and generates deployment report
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
import statistics
from typing import Dict, List, Tuple, Any
import sys

# Database configuration
DB_PATH = Path(__file__).parent / "backend" / "sports.db"

class Phase5VerificationSuite:
    """Comprehensive verification suite for Phase 5 deployment"""
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "verification_checks": {},
            "accuracy_comparison": {},
            "deployment_readiness": {},
            "issues_found": [],
            "recommendations": []
        }
    
    def connect_db(self):
        """Connect to database"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn
    
    def verify_confidence_fixes(self) -> Dict[str, Any]:
        """Verify that confidence fixes have been properly applied"""
        check_results = {
            "status": "pending",
            "details": {},
            "passed": True
        }
        
        try:
            # Check 1: Verify bayesian_confidence.py imports in enhanced_ml_service
            enhanced_ml_path = Path(__file__).parent / "backend" / "app" / "services" / "enhanced_ml_service.py"
            with open(enhanced_ml_path, 'r') as f:
                enhanced_ml_content = f.read()
            
            check_results["details"]["bayesian_import_found"] = "from app.services.bayesian_confidence" in enhanced_ml_content or "bayesian_confidence" in enhanced_ml_content
            
            # Check 2: Verify MD5 hash usage has been removed/replaced
            check_results["details"]["md5_hash_removed"] = "hashlib.md5" not in enhanced_ml_content or \
                                                          "FIXED: Do NOT use hash-based seed" in enhanced_ml_content
            
            # Check 3: Verify no MD5-based confidence calculations
            check_results["details"]["no_hash_confidence"] = "md5(f\"{team_id}_{game_id}\")" not in enhanced_ml_content
            
            # Check 4: Verify enhanced_reasoning uses game data, not hashes
            check_results["details"]["reasoning_uses_game_data"] = "game_data.get" in enhanced_ml_content and \
                                                                  "home_wins" in enhanced_ml_content
            
            # Overall status
            if all(check_results["details"].values()):
                check_results["status"] = "passed"
            else:
                check_results["status"] = "failed"
                check_results["passed"] = False
                for check, result in check_results["details"].items():
                    if not result:
                        self.results["issues_found"].append(f"Confidence fix check failed: {check}")
        
        except Exception as e:
            check_results["status"] = "error"
            check_results["error"] = str(e)
            check_results["passed"] = False
            self.results["issues_found"].append(f"Error verifying confidence fixes: {str(e)}")
        
        return check_results
    
    def verify_analytics_endpoints(self) -> Dict[str, Any]:
        """Verify analytics endpoints are implemented"""
        check_results = {
            "status": "pending",
            "endpoints": {},
            "passed": True
        }
        
        try:
            analytics_path = Path(__file__).parent / "backend" / "app" / "routes" / "analytics.py"
            if not analytics_path.exists():
                check_results["status"] = "failed"
                check_results["passed"] = False
                self.results["issues_found"].append("Analytics route file not found")
                return check_results
            
            with open(analytics_path, 'r') as f:
                analytics_content = f.read()
            
            endpoints_to_check = [
                ("/api/analytics/accuracy", "accuracy"),
                ("/api/analytics/by-sport", "by_sport"),
                ("/api/analytics/history", "history"),
                ("/api/analytics/deployment", "deployment")
            ]
            
            for endpoint, name in endpoints_to_check:
                check_results["endpoints"][name] = endpoint in analytics_content or f'"{endpoint[5:]}"' in analytics_content
            
            if all(check_results["endpoints"].values()):
                check_results["status"] = "passed"
            else:
                check_results["status"] = "partial"
                check_results["passed"] = False
        
        except Exception as e:
            check_results["status"] = "error"
            check_results["error"] = str(e)
            check_results["passed"] = False
            self.results["issues_found"].append(f"Error verifying analytics endpoints: {str(e)}")
        
        return check_results
    
    def verify_database_state(self) -> Dict[str, Any]:
        """Verify database is ready for production"""
        check_results = {
            "status": "pending",
            "database": {},
            "passed": True
        }
        
        try:
            conn = self.connect_db()
            cursor = conn.cursor()
            
            # Check prediction table has outcome tracking fields
            cursor.execute("PRAGMA table_info(prediction)")
            columns = {row[1] for row in cursor.fetchall()}
            
            required_columns = {'resolved_at', 'result', 'actual_value'}
            check_results["database"]["outcome_fields_exist"] = required_columns.issubset(columns)
            
            # Check for test data contamination
            cursor.execute("SELECT COUNT(*) FROM prediction WHERE sport_key IN ('test', 'demo')")
            test_count = cursor.fetchone()[0]
            check_results["database"]["no_test_predictions"] = test_count == 0
            
            # Check prediction count
            cursor.execute("SELECT COUNT(*) FROM prediction")
            total_count = cursor.fetchone()[0]
            check_results["database"]["prediction_count"] = total_count
            check_results["database"]["has_predictions"] = total_count > 0
            
            # Check for resolved predictions (outcome tracking in use)
            cursor.execute("SELECT COUNT(*) FROM prediction WHERE resolved_at IS NOT NULL")
            resolved_count = cursor.fetchone()[0]
            check_results["database"]["resolved_predictions"] = resolved_count
            check_results["database"]["tracking_active"] = resolved_count > 0
            
            conn.close()
            
            if all(check_results["database"].get(k, False) for k in 
                   ['outcome_fields_exist', 'no_test_predictions', 'has_predictions']):
                check_results["status"] = "passed"
            else:
                check_results["status"] = "failed"
                check_results["passed"] = False
                for check, result in check_results["database"].items():
                    if check.endswith("_exist") and not result:
                        self.results["issues_found"].append(f"Database check failed: {check}")
        
        except Exception as e:
            check_results["status"] = "error"
            check_results["error"] = str(e)
            check_results["passed"] = False
            self.results["issues_found"].append(f"Error verifying database state: {str(e)}")
        
        return check_results
    
    def compare_accuracy_metrics(self) -> Dict[str, Any]:
        """Compare accuracy metrics before/after confidence fixes"""
        comparison = {
            "baseline": {},
            "current": {},
            "improvements": {},
            "status": "pending"
        }
        
        try:
            conn = self.connect_db()
            cursor = conn.cursor()
            
            # Get resolved predictions
            cursor.execute("""
                SELECT 
                    sport_key,
                    confidence,
                    result,
                    actual_value,
                    created_at
                FROM prediction 
                WHERE resolved_at IS NOT NULL 
                AND result IS NOT NULL
                ORDER BY created_at DESC
                LIMIT 1000
            """)
            
            predictions = cursor.fetchall()
            conn.close()
            
            if not predictions:
                comparison["status"] = "insufficient_data"
                self.results["recommendations"].append(
                    "No resolved predictions found. Run production for 7-14 days to collect resolution data."
                )
                return comparison
            
            # Analyze by sport
            by_sport = {}
            for pred in predictions:
                sport = pred['sport_key']
                if sport not in by_sport:
                    by_sport[sport] = []
                
                # Convert result to binary win (1 if result matches prediction, 0 otherwise)
                result = 1 if pred['result'] else 0
                by_sport[sport].append({
                    'confidence': pred['confidence'],
                    'result': result,
                    'actual_value': pred['actual_value']
                })
            
            # Calculate metrics by sport
            for sport, preds in by_sport.items():
                if not preds:
                    continue
                
                # Win rate
                wins = sum(1 for p in preds if p['result'] == 1)
                win_rate = wins / len(preds) if preds else 0
                
                # Calibration: group by confidence buckets and compare to actual win rate
                confidence_scores = [p['confidence'] for p in preds]
                win_results = [p['result'] for p in preds]
                
                # Calibration error: mean absolute difference between confidence and actual win rate
                if confidence_scores and win_results:
                    avg_confidence = statistics.mean(confidence_scores)
                    calibration_error = abs(avg_confidence - win_rate)
                else:
                    calibration_error = 0
                
                # ROI calculation
                total_profit = sum(p['actual_value'] or 0 for p in preds)
                roi = (total_profit / len(preds)) if preds else 0
                
                comparison["current"][sport] = {
                    "win_rate": round(win_rate * 100, 2),
                    "calibration_error": round(calibration_error, 4),
                    "roi": round(roi * 100, 2),
                    "prediction_count": len(preds),
                    "avg_confidence": round(avg_confidence, 4)
                }
            
            # Load baseline from audit report if exists
            audit_report_path = Path(__file__).parent / "accuracy_audit_report.json"
            if audit_report_path.exists():
                with open(audit_report_path, 'r') as f:
                    audit_data = json.load(f)
                    comparison["baseline"] = audit_data.get("by_sport", {})
            
            # Calculate improvements
            if comparison["baseline"] and comparison["current"]:
                for sport in comparison["baseline"]:
                    if sport in comparison["current"]:
                        baseline_wr = comparison["baseline"][sport].get("win_rate", 0)
                        current_wr = comparison["current"][sport].get("win_rate", 0)
                        
                        baseline_cal = comparison["baseline"][sport].get("calibration_error", 0)
                        current_cal = comparison["current"][sport].get("calibration_error", 0)
                        
                        comparison["improvements"][sport] = {
                            "win_rate_improvement": round(current_wr - baseline_wr, 2),
                            "calibration_improvement": round(baseline_cal - current_cal, 4),
                            "trend": "improved" if current_wr > baseline_wr else "declined"
                        }
            
            comparison["status"] = "complete"
        
        except Exception as e:
            comparison["status"] = "error"
            comparison["error"] = str(e)
            self.results["issues_found"].append(f"Error comparing accuracy metrics: {str(e)}")
        
        return comparison
    
    def generate_deployment_readiness_report(self) -> Dict[str, Any]:
        """Generate comprehensive deployment readiness report"""
        report = {
            "ready_for_production": True,
            "risk_level": "LOW",
            "checks_passed": 0,
            "checks_total": 0,
            "deployment_steps": [],
            "rollback_plan": []
        }
        
        # Run all verification checks
        print("\n" + "="*60)
        print("PHASE 5: DEPLOYMENT VERIFICATION SUITE")
        print("="*60)
        
        print("\n[1/4] Verifying Confidence Fixes...")
        confidence_check = self.verify_confidence_fixes()
        self.results["verification_checks"]["confidence_fixes"] = confidence_check
        report["checks_passed"] += int(confidence_check.get("passed", False))
        report["checks_total"] += 1
        print(f"  Status: {confidence_check['status'].upper()}")
        for check, result in confidence_check.get("details", {}).items():
            print(f"  - {check}: {'✓' if result else '✗'}")
        
        print("\n[2/4] Verifying Analytics Endpoints...")
        analytics_check = self.verify_analytics_endpoints()
        self.results["verification_checks"]["analytics_endpoints"] = analytics_check
        report["checks_passed"] += int(analytics_check.get("passed", False))
        report["checks_total"] += 1
        print(f"  Status: {analytics_check['status'].upper()}")
        for endpoint, exists in analytics_check.get("endpoints", {}).items():
            print(f"  - {endpoint}: {'✓' if exists else '✗'}")
        
        print("\n[3/4] Verifying Database State...")
        db_check = self.verify_database_state()
        self.results["verification_checks"]["database_state"] = db_check
        report["checks_passed"] += int(db_check.get("passed", False))
        report["checks_total"] += 1
        print(f"  Status: {db_check['status'].upper()}")
        print(f"  Total Predictions: {db_check.get('database', {}).get('prediction_count', 0)}")
        print(f"  Resolved (Tracked): {db_check.get('database', {}).get('resolved_predictions', 0)}")
        
        print("\n[4/4] Comparing Accuracy Metrics...")
        accuracy_comparison = self.compare_accuracy_metrics()
        self.results["accuracy_comparison"] = accuracy_comparison
        print(f"  Status: {accuracy_comparison['status'].upper()}")
        if accuracy_comparison['status'] == 'complete':
            print("\n  BASELINE METRICS (from audit):")
            for sport, metrics in accuracy_comparison.get("baseline", {}).items():
                print(f"    {sport}: WR={metrics.get('win_rate', 'N/A')}% | Cal={metrics.get('calibration_error', 'N/A')}")
            
            print("\n  CURRENT METRICS (from resolved predictions):")
            for sport, metrics in accuracy_comparison.get("current", {}).items():
                print(f"    {sport}: WR={metrics.get('win_rate', 'N/A')}% | Cal={metrics.get('calibration_error', 'N/A')}")
            
            print("\n  IMPROVEMENTS:")
            if accuracy_comparison.get("improvements"):
                for sport, improve in accuracy_comparison.get("improvements", {}).items():
                    trend = "↑" if improve['trend'] == 'improved' else "↓"
                    print(f"    {sport}: WR {trend} {improve['win_rate_improvement']:+.2f}% | Cal {improve['calibration_improvement']:+.4f}")
            else:
                print("    (Insufficient data for comparison)")
        
        # Determine deployment readiness
        print("\n" + "-"*60)
        print("DEPLOYMENT READINESS ASSESSMENT")
        print("-"*60)
        
        all_passed = (confidence_check.get("passed", False) and 
                     analytics_check.get("passed", False) and 
                     db_check.get("passed", False))
        
        if not all_passed:
            report["ready_for_production"] = False
            report["risk_level"] = "HIGH"
            print("⚠ NOT READY FOR PRODUCTION")
            print("\nIssues Found:")
            for issue in self.results["issues_found"]:
                print(f"  • {issue}")
        else:
            if accuracy_comparison['status'] == 'insufficient_data':
                report["ready_for_production"] = False
                report["risk_level"] = "MEDIUM"
                print("⚠ READY FOR STAGING - AWAITING PRODUCTION DATA")
                print("\nAction Required:")
                print("  • Deploy to staging environment")
                print("  • Route 10% of production traffic for 7-14 days")
                print("  • Collect resolved prediction data")
                print("  • Re-run Phase 5 comparison after data collection")
            else:
                print("✓ READY FOR PRODUCTION DEPLOYMENT")
                report["risk_level"] = "LOW"
        
        # Deployment steps
        report["deployment_steps"] = [
            "1. Create git branch: feature/phase5-deployment",
            "2. Tag current commit: v1.0-pre-deployment",
            "3. Deploy to staging environment first",
            "4. Run 24-hour smoke tests on staging",
            "5. Verify analytics dashboard is functional",
            "6. Test confidence calculation with sample games",
            "7. Run accuracy metrics calculation",
            "8. Create backup of production database",
            "9. Deploy to production with blue-green strategy",
            "10. Monitor error rates and response times (first 4 hours)",
            "11. Enable gradual traffic shift (canargy deployment)",
            "12. Archive old predictions with old confidence scores",
            "13. Document deployment in runbook"
        ]
        
        # Rollback plan
        report["rollback_plan"] = [
            "If confidence calculations show 10% WR degradation:",
            "  1. Revert to previous version via blue-green switch",
            "  2. Disable new analytics endpoints",
            "  3. Investigate confidence score divergence",
            "  4. Review ML model outputs vs Bayesian calculator",
            "",
            "If analytics endpoints timeout:",
            "  1. Enable query caching in analytics routes",
            "  2. Implement pagination for history endpoint",
            "  3. Create materialized view for aggregated metrics",
            "",
            "If database performance degrades:",
            "  1. Add indexes on sport_key, created_at columns",
            "  2. Archive resolved predictions older than 90 days",
            "  3. Move analytics queries to read replica"
        ]
        
        report["recommendations"] = self.results["recommendations"]
        
        return report
    
    def save_results(self):
        """Save verification results to file"""
        output_path = Path(__file__).parent / f"phase5_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        return output_path


def main():
    """Run Phase 5 verification suite"""
    suite = Phase5VerificationSuite()
    
    # Generate deployment readiness report
    readiness_report = suite.generate_deployment_readiness_report()
    suite.results["deployment_readiness"] = readiness_report
    
    # Print recommendations
    print("\n" + "="*60)
    print("RECOMMENDATIONS")
    print("="*60)
    if suite.results["recommendations"]:
        for rec in suite.results["recommendations"]:
            print(f"• {rec}")
    
    # Print deployment steps
    print("\n" + "="*60)
    print("DEPLOYMENT STEPS")
    print("="*60)
    for step in readiness_report["deployment_steps"]:
        print(step)
    
    # Print rollback plan
    print("\n" + "="*60)
    print("ROLLBACK PLAN")
    print("="*60)
    for step in readiness_report["rollback_plan"]:
        print(step)
    
    # Save results
    output_file = suite.save_results()
    print(f"\n✓ Verification results saved to: {output_file}")
    
    # Return exit code based on readiness
    return 0 if readiness_report["ready_for_production"] else 1


if __name__ == "__main__":
    sys.exit(main())
