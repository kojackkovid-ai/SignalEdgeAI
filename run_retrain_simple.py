#!/usr/bin/env python
"""
Simple Retraining Script - Runs from sports-prediction-platform root
Uses ONLY real ESPN API data - NO synthetic, mock, or fake data.
"""

import asyncio
import sys
import os

# Ensure we're in the right directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ml-models'))

# Change to ml-models for proper imports
os.chdir(os.path.join(os.path.dirname(__file__), 'ml-models'))

# Import the retrainer
from training.retrain_with_real_data import RealDataModelRetrainer

async def main():
    print("\n" + "="*70)
    print("MODEL RETRAINING WITH REAL ESPN DATA")
    print("NO synthetic data - NO mock data - ONLY real ESPN API data")
    print("="*70 + "\n")
    
    # Run retraining
    retrainer = RealDataModelRetrainer()
    results = await retrainer.retrain_all_models(days_back=90)
    
    success_rate = results.get('success_rate', 0) * 100
    print(f"\n✅ Retraining complete - {success_rate:.1f}% success rate")
    
    return results

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
