#!/usr/bin/env python3
"""
Model Retraining Script - Self-contained
Retrains ALL ML models using ONLY real ESPN API data
NO synthetic data - NO mock data - ONLY real game outcomes
"""

import asyncio
import sys
import os
from pathlib import Path
import logging
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import httpx
import joblib

ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR / "backend"))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ESPNDataCollector:
    """Collects real game data from ESPN API"""
    
    BASE_URL = "https://site.api.espn.com/apis/site/v2/sports"
    
    SPORT_MAPPING = {
        "basketball_nba": "basketball/nba",
        "basketball_ncaa": "basketball/mens-college-basketball",
        "icehockey_nhl": "hockey/nhl", 
        "americanfootball_nfl": "football/nfl",
        "baseball_mlb": "baseball/mlb",
        "soccer_epl": "soccer/eng.1",
        "soccer_usa_mls": "soccer/usa.1"
    }
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def close(self):
        await self.client.aclose()
    
    async def collect_historical_data(self, sport_key: str, days_back: int = 90) -> pd.DataFrame:
        """Collect historical game data from ESPN API"""
        
        espn_path = self.SPORT_MAPPING.get(sport_key)
        if not espn_path:
            logger.warning(f"No ESPN mapping for {sport_key}")
            return pd.DataFrame()
        
        all_games = []
        
        for day_offset in range(0, days_back, 7):
            date = datetime.now() - timedelta(days=day_offset)
            date_str = date.strftime("%Y%m%d")
            
            try:
                url = f"{self.BASE_URL}/{espn_path}/scoreboard"
                response = await self.client.get(url, params={"dates": date_str})
                
                if response.status_code != 200:
                    continue
                    
                data = response.json()
                events = data.get("events", [])
                
                for event in events:
                    try:
                        competition = event["competitions"][0]
                        competitors = competition["competitors"]
                        
                        home_team = next((c for c in competitors if c["homeAway"] == "home"), None)
                        away_team = next((c for c in competitors if c["homeAway"] == "away"), None)
                        
                        if not home_team or not away_team:
                            continue
                        
                        completed = event["status"]["type"]["completed"]
                        
                        if not completed:
                            continue
                        
                        home_record = home_team.get("records", [])
                        away_record = away_team.get("records", [])
                        
                        home_wins, home_losses = self._parse_record(home_record)
                        away_wins, away_losses = self._parse_record(away_record)
                        
                        home_score = int(home_team.get("score", 0))
                        away_score = int(away_team.get("score", 0))
                        
                        if home_score > away_score:
                            target = 1
                        elif away_score > home_score:
                            target = 0
                        else:
                            target = 2
                        
                        record = {
                            "target": target,
                            "home_wins": home_wins,
                            "home_losses": home_losses,
                            "away_wins": away_wins,
                            "away_losses": away_losses,
                            "home_win_pct": home_wins / (home_wins + home_losses) if (home_wins + home_losses) > 0 else 0.5,
                            "away_win_pct": away_wins / (away_wins + away_losses) if (away_wins + away_losses) > 0 else 0.5,
                            "home_score": home_score,
                            "away_score": away_score,
                            "point_differential": home_score - away_score,
                            "home_team": home_team["team"]["displayName"],
                            "away_team": away_team["team"]["displayName"],
                            "sport_key": sport_key,
                            "game_date": date_str,
                            "data_source": "espn_api_real"
                        }
                        
                        all_games.append(record)
                        
                    except Exception as e:
                        continue
                        
            except Exception as e:
                logger.debug(f"Error fetching {sport_key} for {date_str}: {e}")
                continue
        
        if all_games:
            df = pd.DataFrame(all_games)
            logger.info(f"Collected {len(df)} real games for {sport_key}")
            return df
        else:
            logger.warning(f"No games collected for {sport_key}")
            return pd.DataFrame()
    
    def _parse_record(self, records: list) -> tuple:
        """Parse wins/losses from team records"""
        wins, losses = 0, 0
        
        if records and len(records) > 0:
            summary = records[0].get("summary", "")
            if summary and "-" in summary:
                parts = summary.split("-")
                try:
                    wins = int(parts[0])
                    losses = int(parts[1])
                except:
                    pass
        
        return wins, losses


class ModelTrainer:
    """Train ML models with real data"""
    
    def __init__(self, models_dir: str = None):
        if models_dir is None:
            models_dir = ROOT_DIR / "ml-models" / "trained"
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
    async def train_model(self, sport_key: str, market_type: str, data: pd.DataFrame, min_samples: int = 30) -> dict:
        """Train a single model"""
        
        if len(data) < min_samples:
            return {"status": "error", "message": f"Insufficient data ({len(data)} < {min_samples})"}
        
        try:
            feature_cols = [
                "home_wins", "home_losses", "away_wins", "away_losses",
                "home_win_pct", "away_win_pct", "home_score", "away_score"
            ]
            
            feature_cols = [c for c in feature_cols if c in data.columns]
            
            X = data[feature_cols].values
            y = data["target"].values
            
            X = np.nan_to_num(X, nan=0.0)
            
            try:
                import xgboost as xgb
                HAS_XGB = True
            except:
                HAS_XGB = False
                
            try:
                import lightgbm as lgb
                HAS_LGB = True
            except:
                HAS_LGB = False
            
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.preprocessing import StandardScaler
            from sklearn.model_selection import train_test_split
            
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            models = {}
            scores = {}
            
            # Random Forest
            rf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
            rf.fit(X_train_scaled, y_train)
            rf_score = rf.score(X_test_scaled, y_test)
            models["random_forest"] = rf
            scores["random_forest"] = rf_score
            logger.info(f"  RandomForest accuracy: {rf_score:.3f}")
            
            # XGBoost
            if HAS_XGB:
                xg = xgb.XGBClassifier(n_estimators=100, max_depth=6, random_state=42, use_label_encoder=False, eval_metric='logloss')
                xg.fit(X_train_scaled, y_train)
                xg_score = xg.score(X_test_scaled, y_test)
                models["xgboost"] = xg
                scores["xgboost"] = xg_score
                logger.info(f"  XGBoost accuracy: {xg_score:.3f}")
            
            # LightGBM
            if HAS_LGB:
                lg = lgb.LGBMClassifier(n_estimators=100, max_depth=6, random_state=42, verbose=-1)
                lg.fit(X_train_scaled, y_train)
                lg_score = lg.score(X_test_scaled, y_test)
                models["lightgbm"] = lg
                scores["lightgbm"] = lg_score
                logger.info(f"  LightGBM accuracy: {lg_score:.3f}")
            
            model_key = f"{sport_key}_{market_type}"
            
            model_data = {
                "models": models,
                "scaler": scaler,
                "feature_names": feature_cols,
                "scores": scores
            }
            
            save_path = self.models_dir / f"{model_key}_models.joblib"
            joblib.dump(model_data, save_path)
            logger.info(f"  Saved models to {save_path}")
            
            return {
                "status": "success",
                "model_key": model_key,
                "scores": scores,
                "samples": len(data)
            }
            
        except Exception as e:
            logger.error(f"Error training {sport_key} {market_type}: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "message": str(e)}


async def main():
    """Main retraining function"""
    print("=" * 80)
    print("SPORTS PREDICTION MODEL RETRAINING")
    print("Using ONLY Real ESPN API Data")
    print("NO Synthetic Data - NO Mock Data")
    print("=" * 80)
    print()
    
    results = {
        'start_time': datetime.now().isoformat(),
        'sports_trained': [],
        'models_trained': [],
        'errors': []
    }
    
    sports = [
        "basketball_nba",
        "basketball_ncaa", 
        "icehockey_nhl",
        "americanfootball_nfl",
        "baseball_mlb",
        "soccer_epl",
        "soccer_usa_mls"
    ]
    
    markets = ["moneyline", "spread", "total"]
    
    try:
        # Step 1: Collect real data
        logger.info("[1/3] Collecting REAL data from ESPN API...")
        
        collector = ESPNDataCollector()
        all_data = {}
        
        # Collect more historical data for sports with less activity
        days_map = {
            "basketball_nba": 90,
            "basketball_ncaa": 90,
            "icehockey_nhl": 90,
            "americanfootball_nfl": 180,  # More days for NFL (season)
            "baseball_mlb": 180,  # More days for MLB (season)
            "soccer_epl": 90,
            "soccer_usa_mls": 180
        }
        
        for sport in sports:
            days = days_map.get(sport, 90)
            logger.info(f"  Fetching {sport} (last {days} days)...")
            data = await collector.collect_historical_data(sport, days_back=days)
            if data is not None and len(data) > 0:
                all_data[sport] = data
                logger.info(f"    Got {len(data)} games")
            else:
                logger.warning(f"    No data for {sport}")
        
        await collector.close()
        
        if not all_data:
            raise RuntimeError("No data collected from ESPN!")
        
        combined = pd.concat(all_data.values(), ignore_index=True)
        results['data_summary'] = {
            'total_records': len(combined),
            'sports': list(all_data.keys())
        }
        logger.info(f"Total: {len(combined)} real games collected")
        
        # Step 2: Train models
        logger.info("[2/3] Training models...")
        
        trainer = ModelTrainer()
        
        for sport in sports:
            if sport not in all_data:
                continue
                
            sport_data = all_data[sport]
            
            for market in markets:
                logger.info(f"  Training {sport} {market}...")
                
                # Use lower threshold for sports with less data
                min_samples = 30 if len(sport_data) < 50 else 50
                result = await trainer.train_model(sport, market, sport_data, min_samples=min_samples)
                
                if result.get('status') == 'success':
                    results['models_trained'].append({
                        'sport': sport,
                        'market': market,
                        'accuracy': result.get('scores', {})
                    })
                    logger.info(f"    Trained successfully")
                else:
                    results['errors'].append(f"{sport} {market}: {result.get('message')}")
                    logger.error(f"    Failed: {result.get('message')}")
        
        # Step 3: Save report
        logger.info("[3/3] Saving report...")
        
        results['end_time'] = datetime.now().isoformat()
        
        report_path = ROOT_DIR / "ml-models" / "logs" / f"retrain_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print()
        print("=" * 80)
        print("RETRAINING COMPLETE")
        print("=" * 80)
        print(f"Data Source: ESPN API ONLY (NO synthetic data)")
        print(f"Total Games Collected: {len(combined)}")
        print(f"Models Trained: {len(results['models_trained'])}")
        print(f"Errors: {len(results['errors'])}")
        print(f"Report: {report_path}")
        print("=" * 80)
        
        if results['models_trained']:
            print("\nModels successfully retrained with real ESPN data!")
            return True
        else:
            print("\nTraining completed but no models were saved")
            return False
            
    except Exception as e:
        logger.error(f"Critical error: {e}")
        import traceback
        traceback.print_exc()
        results['errors'].append(str(e))
        return False


if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
