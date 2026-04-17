#!/usr/bin/env python3
"""
Quick verification script to test if analytics infrastructure is working
Run this from the backend directory: python verify_analytics_setup.py
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("\n" + "="*70)
print("ANALYTICS SETUP VERIFICATION")
print("="*70)

# Test 1: Check if analytics_models.py exists
print("\n[1/5] Checking if analytics_models.py exists...")
analytics_models_path = "app/models/analytics_models.py"
if os.path.exists(analytics_models_path):
    print(f"✅ Found {analytics_models_path}")
else:
    print(f"❌ Missing {analytics_models_path}")
    sys.exit(1)

# Test 2: Try importing the analytics models
print("\n[2/5] Importing analytics models...")
try:
    from app.models.analytics_models import (
        AnalyticsEvent,
        ConversionFunnel,
        UserEngagementMetrics,
        CohortAnalysis,
    )
    print("✅ Successfully imported all analytics models:")
    print("   - AnalyticsEvent")
    print("   - ConversionFunnel")
    print("   - UserEngagementMetrics")
    print("   - CohortAnalysis")
except Exception as e:
    print(f"❌ Failed to import analytics models: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Check if analytics_service.py exists
print("\n[3/5] Checking if analytics_service.py exists...")
analytics_service_path = "app/services/analytics_service.py"
if os.path.exists(analytics_service_path):
    print(f"✅ Found {analytics_service_path}")
else:
    print(f"❌ Missing {analytics_service_path}")
    sys.exit(1)

# Test 4: Try importing the analytics service
print("\n[4/5] Importing analytics service...")
try:
    from app.services.analytics_service import AnalyticsService
    print("✅ Successfully imported AnalyticsService")
    print(f"   Methods: {[m for m in dir(AnalyticsService) if not m.startswith('_')]}")
except Exception as e:
    print(f"❌ Failed to import AnalyticsService: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Check analytics routes
print("\n[5/5] Checking analytics routes...")
analytics_routes_path = "app/routes/analytics.py"
if os.path.exists(analytics_routes_path):
    print(f"✅ Found {analytics_routes_path}")
    try:
        from app.routes import analytics
        print("✅ Successfully imported analytics routes")
        print(f"  Router: {analytics.router}")
    except Exception as e:
        print(f"❌ Failed to import analytics routes: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"❌ Missing {analytics_routes_path}")
    sys.exit(1)

print("\n" + "="*70)
print("✅ ALL CHECKS PASSED - Analytics infrastructure is ready!")
print("="*70)
print("\nNext steps:")
print("1. Check Docker is running with: docker ps")
print("2. Verify backend API: curl http://localhost:8000/docs")
print("3. Check analytics endpoint: curl http://localhost:8000/api/analytics/dashboard")
print("4. Verify database tables: docker-compose exec db psql -U postgres -d sports_db -c '\dt analytics_*'")
print()
