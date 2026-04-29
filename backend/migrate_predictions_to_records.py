#!/usr/bin/env python3
"""Migrate old predictions from the legacy predictions table into prediction_records."""

import argparse
import json
import os
import sqlite3
from datetime import datetime
from typing import Optional, Tuple


def parse_matchup(matchup: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    if not matchup:
        return None, None
    matchup = matchup.strip()
    if ' vs ' in matchup.lower():
        parts = [p.strip() for p in matchup.split(' vs ')]
        if len(parts) == 2:
            return parts[0], parts[1]
    if ' v ' in matchup.lower():
        parts = [p.strip() for p in matchup.split(' v ')]
        if len(parts) == 2:
            return parts[0], parts[1]
    if '-' in matchup:
        parts = [p.strip() for p in matchup.split('-')]
        if len(parts) == 2:
            return parts[0], parts[1]
    return None, None


def map_prediction_type(old_type: Optional[str], prediction_text: Optional[str]) -> str:
    if not old_type:
        return 'moneyline'
    pt = old_type.strip().lower()
    if pt in ('player_prop', 'player_props'):
        return 'player_props'
    if pt in ('team_prop', 'team-prop', 'prop'):
        if prediction_text:
            lower_text = prediction_text.lower()
            if 'over' in lower_text or 'under' in lower_text:
                return 'over_under'
            if 'spread' in lower_text or '+' in lower_text or '-' in lower_text:
                return 'spread'
        return 'spread'
    if pt in ('spread', 'point_spread', 'line'):
        return 'spread'
    if pt in ('over_under', 'totals', 'total'):
        return 'over_under'
    if pt in ('moneyline', 'ml'):
        return 'moneyline'
    return pt


def map_outcome(old_result: Optional[str]) -> str:
    if not old_result:
        return 'pending'
    normalized = old_result.strip().lower()
    if normalized == 'win':
        return 'hit'
    if normalized == 'loss':
        return 'miss'
    if normalized == 'push':
        return 'void'
    if normalized in ('hit', 'miss', 'void', 'cancelled', 'pending'):
        return normalized
    return 'pending'


def parse_event_start_time(game_time: Optional[str]) -> Optional[str]:
    if not game_time:
        return None
    game_time = game_time.strip()
    for fmt in (
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%S.%f',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M',
        '%m/%d/%Y %H:%M',
        '%m/%d/%Y %I:%M %p',
    ):
        try:
            dt = datetime.strptime(game_time, fmt)
            return dt.isoformat(sep=' ')
        except ValueError:
            continue
    return None


def ensure_prediction_records_table(cursor: sqlite3.Cursor) -> bool:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='prediction_records'")
    return bool(cursor.fetchone())


def load_source_rows(source_conn: sqlite3.Connection) -> list:
    cursor = source_conn.cursor()
    cursor.execute("SELECT * FROM predictions")
    return cursor.fetchall()


def migrate_rows(source_conn: sqlite3.Connection, target_conn: sqlite3.Connection) -> int:
    source_conn.row_factory = sqlite3.Row
    source_cursor = source_conn.cursor()
    target_cursor = target_conn.cursor()

    source_cursor.execute("SELECT * FROM predictions")
    rows = source_cursor.fetchall()
    if not rows:
        print("No rows found in legacy predictions table.")
        return 0

    target_cursor.execute("PRAGMA table_info(prediction_records)")
    target_columns = [row[1] for row in target_cursor.fetchall()]
    if not target_columns:
        raise RuntimeError("prediction_records table does not exist in target database.")

    insert_sql = (
        "INSERT OR IGNORE INTO prediction_records ("
        "id, user_id, sport_key, league_id, event_id, matchup, home_team, away_team, "
        "prediction_type, prediction, player_name, player_stat_type, line, confidence, reasoning, model_weights, "
        "created_at, event_start_time, resolved_at, outcome, actual_result, hit_amount)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
    )

    inserted = 0
    for row in rows:
        home_team, away_team = parse_matchup(row['matchup'])
        prediction_type = map_prediction_type(row['prediction_type'], row['prediction'])
        outcome = map_outcome(row['result'])
        actual_result = str(row['actual_value']) if row['actual_value'] is not None else None
        event_start_time = parse_event_start_time(row['game_time'])
        reasoning = row['reasoning'] if row['reasoning'] is not None else None
        model_weights = row['model_weights'] if row['model_weights'] is not None else None

        # Ensure JSON stored correctly in SQLite as text
        if reasoning is not None and isinstance(reasoning, str):
            try:
                reasoning = json.loads(reasoning)
            except json.JSONDecodeError:
                pass
        if model_weights is not None and isinstance(model_weights, str):
            try:
                model_weights = json.loads(model_weights)
            except json.JSONDecodeError:
                pass

        target_cursor.execute(insert_sql, (
            row['id'],
            None,
            row['sport_key'],
            row['league'],
            row['event_id'],
            row['matchup'],
            home_team,
            away_team,
            prediction_type,
            row['prediction'],
            row['player'],
            row['market_key'],
            row['point'],
            row['confidence'],
            json.dumps(reasoning) if reasoning is not None else None,
            json.dumps(model_weights) if model_weights is not None else None,
            row['created_at'],
            event_start_time,
            row['resolved_at'],
            outcome,
            actual_result,
            0.0,
        ))
        inserted += 1

    target_conn.commit()
    return inserted


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate legacy predictions to prediction_records")
    parser.add_argument("--source-db", default="sports_predictions.db", help="Legacy source SQLite database path")
    parser.add_argument("--target-db", default="sports_predictions.db", help="Target SQLite database path containing prediction_records")
    args = parser.parse_args()

    source_path = os.path.abspath(args.source_db)
    target_path = os.path.abspath(args.target_db)

    if not os.path.exists(source_path):
        raise SystemExit(f"Source database does not exist: {source_path}")
    if not os.path.exists(target_path):
        raise SystemExit(f"Target database does not exist: {target_path}")

    source_conn = sqlite3.connect(source_path)
    source_conn.row_factory = sqlite3.Row
    target_conn = sqlite3.connect(target_path)

    try:
        if not ensure_prediction_records_table(target_conn.cursor()):
            raise SystemExit("Target database does not contain a prediction_records table.")

        source_cursor = source_conn.cursor()
        source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='predictions'")
        if not source_cursor.fetchone():
            raise SystemExit("Source database does not contain a predictions table.")

        inserted = migrate_rows(source_conn, target_conn)
        print(f"Migrated {inserted} legacy prediction(s) into prediction_records.")
    finally:
        source_conn.close()
        target_conn.close()


if __name__ == '__main__':
    main()
