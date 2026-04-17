"""
Test script to verify Club 100 platform metrics endpoint
"""

import asyncio
import httpx
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"


async def test_platform_metrics():
    """Test the platform metrics endpoint"""
    
    print("=" * 70)
    print("TESTING: Club 100 Platform Metrics Endpoint")
    print("=" * 70)
    
    # Test URLs
    test_urls = [
        f"{BASE_URL}/api/analytics/platform-metrics?days=30",
        f"{BASE_URL}/api/analytics/platform-metrics?days=7",
        f"{BASE_URL}/api/analytics/platform-metrics?days=30&debug=true",
    ]
    
    async with httpx.AsyncClient() as client:
        for url in test_urls:
            print(f"\n📊 Testing: {url}")
            print("-" * 70)
            
            try:
                response = await client.get(url, timeout=10.0)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    print(f"✅ Status: {response.status_code}")
                    print(f"   Response keys: {list(data.keys())}")
                    
                    if 'platform_overall' in data:
                        overall = data['platform_overall']
                        print(f"\n   Platform Overall:")
                        print(f"     - Total predictions: {overall.get('total_predictions', 0)}")
                        print(f"     - Win rate: {overall.get('win_rate', 0)}")
                        print(f"     - ROI: {overall.get('roi', 0)}")
                        print(f"     - Club 100 count: {overall.get('club_100_count', 0)}")
                        print(f"     - Regular count: {overall.get('regular_count', 0)}")
                    
                    if 'club_100' in data:
                        club_100 = data['club_100']
                        print(f"\n   Club 100 Metrics:")
                        print(f"     - Total: {club_100.get('total_predictions', 0)}")
                        print(f"     - Win rate: {club_100.get('win_rate', 0)}")
                        print(f"     - ROI: {club_100.get('roi', 0)}")
                    
                    if 'regular_picks' in data:
                        regular = data['regular_picks']
                        print(f"\n   Regular Picks Metrics:")
                        print(f"     - Total: {regular.get('total_predictions', 0)}")
                        print(f"     - Win rate: {regular.get('win_rate', 0)}")
                        print(f"     - ROI: {regular.get('roi', 0)}")
                    
                    if 'by_sport' in data and data['by_sport']:
                        print(f"\n   By Sport ({len(data['by_sport'])} sports):")
                        for sport, metrics in list(data['by_sport'].items())[:3]:
                            print(f"     - {sport}:")
                            print(f"       • Overall accuracy: {metrics.get('overall_accuracy', 0)}")
                            print(f"       • Club 100 accuracy: {metrics.get('club_100_accuracy', 0)}")
                            print(f"       • Regular accuracy: {metrics.get('regular_accuracy', 0)}")
                    
                    if '_debug' in data:
                        print(f"\n   Debug Info:")
                        for key, value in data['_debug'].items():
                            print(f"     - {key}: {value}")
                
                else:
                    print(f"❌ Status: {response.status_code}")
                    print(f"   Response: {response.text}")
                    
            except httpx.ConnectError:
                print(f"❌ Connection Error - Is the backend running on {BASE_URL}?")
            except Exception as e:
                print(f"❌ Error: {e}")


async def test_individual_metrics():
    """Test that individual user metrics still work"""
    
    print("\n" + "=" * 70)
    print("TESTING: Individual User Metrics (Accuracy Dashboard)")
    print("=" * 70)
    
    # First, we need to login to get a valid token
    # For testing without token, try the public endpoints
    
    async with httpx.AsyncClient() as client:
        # Try to get user stats (may fail without auth, that's ok)
        try:
            response = await client.get(
                f"{BASE_URL}/api/user/predictions/stats",
                timeout=10.0,
                headers={"Authorization": "Bearer test"}  # This will likely fail, but shows the endpoint exists
            )
            print(f"📊 Individual stats endpoint exists: {response.status_code}")
            
        except Exception as e:
            print(f"⚠️ Individual stats endpoint check: {e}")


async def test_database_changes():
    """Verify database changes"""
    
    print("\n" + "=" * 70)
    print("TESTING: Database Schema Verification")
    print("=" * 70)
    
    try:
        from sqlalchemy import text, inspect
        from sqlalchemy.engine import Connection
        from app.database import engine
        
        async def verify_column(conn: Connection):
            inspector = inspect(conn)
            columns = [c['name'] for c in inspector.get_columns('predictions')]
            return 'is_club_100_pick' in columns
        
        async with engine.begin() as conn:
            has_column = await conn.run_sync(verify_column)
            if has_column:
                print("✅ 'is_club_100_pick' column exists in predictions table")
            else:
                print("❌ 'is_club_100_pick' column NOT found in predictions table")
                
    except Exception as e:
        print(f"⚠️ Could not verify database: {e}")


async def main():
    """Run all tests"""
    
    print("\n" + "#" * 70)
    print("# Club 100 Platform Metrics Implementation Verification")
    print(f"# Started: {datetime.now().isoformat()}")
    print("#" * 70)
    
    # Check database first
    await test_database_changes()
    
    # Test endpoints
    await test_individual_metrics()
    await test_platform_metrics()
    
    print("\n" + "#" * 70)
    print("# Testing Complete")
    print(f"# Completed: {datetime.now().isoformat()}")
    print("#" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
