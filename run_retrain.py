"""
Simple Retraining Script - Runs model retraining with real ESPN data without user interaction.
Uses ONLY real ESPN API data - NO synthetic, mock, or fake data.
"""

import asyncio
import sys
import os
from pathlib import Path

# Get absolute paths
root_dir = Path(__file__).parent.resolve()
ml_models_dir = root_dir / "ml-models"

# Add paths
sys.path.insert(0, str(root_dir / "backend"))
sys.path.insert(0, str(ml_models_dir))

# Change to ml-models directory for proper logging and imports
os.chdir(ml_models_dir)

# Create logs directory
(ml_models_dir / "logs").mkdir(parents=True, exist_ok=True)

# Now import after changing directory
from training.retrain_with_real_data import RealDataModelRetrainer

async def main():
    """Run the retraining without user interaction"""
    print("\n" + "="*70)
    print("SPORTS PREDICTION MODEL RETRAINING (AUTOMATED)")
    print("Using ONLY Real ESPN API Data")
    print("NO Synthetic Data - NO Mock Data - NO Random Generation")
    print("="*70 + "\n")
    
    # Get days back from environment or use default
    days_back = int(os.environ.get('TRAINING_DAYS_BACK', '90'))
    
    print(f"Configuration:")
    print(f"  Historical data: {days_back} days")
    print(f"  Data source: ESPN API ONLY")
    print(f"  Synthetic data: DISABLED")
    print()
    
    # Run retraining (skip user confirmation)
    retrainer = RealDataModelRetrainer()
    results = await retrainer.retrain_all_models(days_back=days_back)
    
    # Final status
    success_rate = results.get('success_rate', 0)
    if success_rate >= 0.8:
        print(f"\n🎉 Retraining completed successfully! ({success_rate*100:.1f}% success rate)")
    elif success_rate >= 0.5:
        print(f"\n⚠️ Retraining completed with partial success ({success_rate*100:.1f}% success rate)")
    else:
        print(f"\n❌ Retraining completed with many failures ({success_rate*100:.1f}% success rate)")
    
    print(f"\nLog file: ml-models/logs/retrain_real_data.log")
    print(f"Report saved to: ml-models/logs/retrain_report_*.json")
    
    return results

if __name__ == "__main__":
    # Windows event loop policy
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    results = asyncio.run(main())
