#!/usr/bin/env python3
import sys
sys.path.insert(0, ".")

from app.routes import predictions

print("Routes with 'club-100':")
for route in predictions.router.routes:
    if 'club-100' in route.path:
        print(f"  {route.path}")

print("\nTotal routes found!")
