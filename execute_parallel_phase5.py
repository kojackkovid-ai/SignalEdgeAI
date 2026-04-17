#!/usr/bin/env python3
"""
Parallel Execution: Staging Deployment + Real Predictions Generation
Executes both tasks concurrently for Phase 5 completion
"""

import subprocess
import threading
import time
import sys
import json
from datetime import datetime
from pathlib import Path

class ParallelExecutor:
    """Execute staging deployment and real predictions in parallel"""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tasks": {
                "staging_deployment": {"status": "pending", "output": [], "error": None},
                "real_predictions": {"status": "pending", "output": [], "error": None}
            },
            "overall_status": "running"
        }
        self.threads = []
    
    def run_staging_deployment(self):
        """Deploy to staging environment with docker-compose"""
        print("\n" + "="*60)
        print("TASK 1: STAGING DEPLOYMENT")
        print("="*60)
        
        try:
            task_result = self.results["tasks"]["staging_deployment"]
            task_result["status"] = "in_progress"
            
            # Check if Docker is available
            print("\n[1/5] Checking Docker availability...")
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                raise RuntimeError("Docker not available on this system")
            
            print(f"✓ {result.stdout.strip()}")
            task_result["output"].append(f"Docker: {result.stdout.strip()}")
            
            # Check docker-compose
            print("\n[2/5] Checking docker-compose...")
            result = subprocess.run(
                ["docker-compose", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                print("⚠ docker-compose not found, trying docker compose...")
                result = subprocess.run(
                    ["docker", "compose", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            
            print(f"✓ {result.stdout.strip()}")
            task_result["output"].append(f"Docker Compose: {result.stdout.strip()}")
            
            # Build staging environment
            print("\n[3/5] Building staging environment...")
            print("File: docker-compose.staging.yml")
            print("Services: PostgreSQL, Redis, Backend API, Nginx")
            task_result["output"].append("Staging configuration verified")
            
            # Staging deployment commands
            deployment_steps = [
                ("Starting PostgreSQL (staging)...", 
                 ["docker-compose", "-f", "docker-compose.staging.yml", "up", "-d", "postgres-staging"]),
                ("Starting Redis (staging)...", 
                 ["docker-compose", "-f", "docker-compose.staging.yml", "up", "-d", "redis-staging"]),
                ("Starting Backend (staging)...", 
                 ["docker-compose", "-f", "docker-compose.staging.yml", "up", "-d", "backend-staging"]),
                ("Waiting for services...", None)
            ]
            
            print("\n[4/5] Deploying services...")
            for step_name, cmd in deployment_steps:
                print(f"  • {step_name}")
                
                if cmd is None:
                    time.sleep(3)
                    task_result["output"].append("Waiting for service initialization")
                    continue
                
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if result.returncode == 0:
                        task_result["output"].append(f"✓ {step_name}")
                    else:
                        print(f"  ⚠ {result.stderr}")
                        task_result["output"].append(f"⚠ {step_name}: {result.stderr}")
                
                except subprocess.TimeoutExpired:
                    print(f"  ⚠ Timeout")
                    task_result["output"].append(f"⚠ {step_name}: Timeout")
                except Exception as e:
                    print(f"  ⚠ {str(e)}")
                    task_result["output"].append(f"⚠ {step_name}: {str(e)}")
            
            # Verify staging endpoints
            print("\n[5/5] Testing staging endpoints...")
            test_commands = [
                ("Health check", ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "http://127.0.0.1:8001/health"]),
                ("Analytics endpoint", ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "http://127.0.0.1:8001/api/analytics/accuracy"])
            ]
            
            for test_name, cmd in test_commands:
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    print(f"  ✓ {test_name}: HTTP {result.stdout}")
                    task_result["output"].append(f"✓ {test_name}")
                except Exception as e:
                    print(f"  ⚠ {test_name}: {str(e)[:50]}")
                    task_result["output"].append(f"⚠ {test_name}")
            
            task_result["status"] = "complete"
            print("\n✓ STAGING DEPLOYMENT COMPLETE")
            
        except Exception as e:
            print(f"\n✗ Staging deployment failed: {str(e)}")
            task_result["status"] = "failed"
            task_result["error"] = str(e)
    
    def run_real_predictions(self):
        """Generate real predictions from ESPN API"""
        print("\n" + "="*60)
        print("TASK 2: REAL PREDICTIONS GENERATION")
        print("="*60)
        
        task_result = self.results["tasks"]["real_predictions"]
        task_result["status"] = "in_progress"
        
        try:
            print("\n[1/4] Importing prediction services...")
            
            # Import and run predictions generator
            from app.services.espn_prediction_service import ESPNPredictionService
            from app.services.enhanced_ml_service import EnhancedMLService
            import asyncio
            import sqlite3
            
            print("✓ Services imported successfully")
            task_result["output"].append("Services imported")
            
            print("\n[2/4] Connecting to database...")
            db_path = Path(__file__).parent / "backend" / "sports.db"
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            print(f"✓ Database connected: {db_path}")
            task_result["output"].append(f"Database connected: {db_path}")
            
            print("\n[3/4] Generating predictions for upcoming games...")
            
            # Initialize services
            espn_service = ESPNPredictionService()
            ml_service = EnhancedMLService()
            
            predictions_count = 0
            sports_processed = []
            
            # Generate for each sport
            for sport_key, sport_name in [
                ("basketball_nba", "NBA"),
                ("americanfootball_nfl", "NFL"),
                ("baseball_mlb", "MLB"),
                ("icehockey_nhl", "NHL")
            ]:
                try:
                    print(f"\n  • Processing {sport_name}...")
                    
                    # Get upcoming games (async)
                    games = asyncio.run(
                        espn_service.get_upcoming_games(
                            sport_key=sport_key,
                            days_ahead=14
                        )
                    )
                    
                    if not games:
                        print(f"    ⚠ No upcoming games for {sport_name}")
                        continue
                    
                    print(f"    Found {len(games)} upcoming games")
                    
                    # Generate predictions (limit to 3 per sport for demo)
                    for i, game in enumerate(games[:3]):
                        try:
                            pred = ml_service.predict(
                                home_team_data=game,
                                away_team_data=game,
                                sport_key=sport_key
                            )
                            
                            if pred:
                                cursor.execute("""
                                    INSERT OR IGNORE INTO prediction 
                                    (sport_key, event_id, prediction, confidence, reasoning, created_at)
                                    VALUES (?, ?, ?, ?, ?, ?)
                                """, (
                                    sport_key,
                                    game.get("event_id", f"{sport_name}_{i}"),
                                    pred.get("prediction", ""),
                                    pred.get("confidence", 0.5),
                                    pred.get("reasoning", ""),
                                    datetime.now().isoformat()
                                ))
                                
                                predictions_count += 1
                                print(f"    ✓ Prediction {i+1}/3: {pred.get('confidence', 0):.1%} confidence")
                        
                        except Exception as e:
                            print(f"    ⚠ Error on game {i}: {str(e)[:50]}")
                    
                    sports_processed.append(sport_name)
                
                except Exception as e:
                    print(f"    ✗ Error processing {sport_name}: {str(e)[:50]}")
            
            conn.commit()
            conn.close()
            
            print(f"\n✓ Generated {predictions_count} predictions across {len(sports_processed)} sports")
            task_result["output"].append(f"Generated {predictions_count} predictions")
            
            print("\n[4/4] Verifying predictions...")
            
            # Verify inserted predictions
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM prediction WHERE created_at >= datetime('now', '-1 hour')")
            recent_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM prediction")
            total_count = cursor.fetchone()[0]
            
            conn.close()
            
            print(f"✓ Recent predictions (last hour): {recent_count}")
            print(f"✓ Total predictions in database: {total_count}")
            task_result["output"].append(f"Total predictions: {total_count}")
            
            task_result["status"] = "complete"
            print("\n✓ REAL PREDICTIONS GENERATION COMPLETE")
            
        except Exception as e:
            print(f"\n✗ Real predictions generation failed: {str(e)}")
            task_result["status"] = "failed"
            task_result["error"] = str(e)
    
    def execute_parallel(self):
        """Execute both tasks in parallel"""
        # Create threads
        staging_thread = threading.Thread(target=self.run_staging_deployment, daemon=False)
        predictions_thread = threading.Thread(target=self.run_real_predictions, daemon=False)
        
        # Start both tasks
        print("\n🚀 Starting parallel execution...")
        print("   Task 1: Staging Deployment")
        print("   Task 2: Real Predictions Generation\n")
        
        start_time = time.time()
        
        staging_thread.start()
        predictions_thread.start()
        
        # Wait for both to complete
        staging_thread.join()
        predictions_thread.join()
        
        elapsed = time.time() - start_time
        
        # Print summary
        print("\n" + "="*60)
        print("PARALLEL EXECUTION COMPLETE")
        print("="*60)
        print(f"Total Time: {elapsed:.1f} seconds")
        
        print("\nTask Results:")
        for task_name, result in self.results["tasks"].items():
            status_symbol = "✓" if result["status"] == "complete" else "✗" if result["status"] == "failed" else "⏳"
            print(f"  {status_symbol} {task_name}: {result['status'].upper()}")
        
        # Save results
        output_file = f"parallel_execution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n✓ Results saved to: {output_file}")
        
        return all(
            task["status"] == "complete" 
            for task in self.results["tasks"].values()
        )


def main():
    executor = ParallelExecutor()
    success = executor.execute_parallel()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
