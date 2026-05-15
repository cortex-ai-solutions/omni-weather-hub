"""
Generates weather_snapshot.json from the SQLite database.
This file is served via GitHub Pages and loaded by the dashboard.

Usage:
  python generate_snapshot.py
  python generate_snapshot.py --db /path/to/weather.db --out /path/to/snapshot.json
"""

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.db import DB_PATH, get_connection, init_db

DEFAULT_OUT = Path(__file__).parent.parent / "weather_snapshot.json"


def query_current(conn: sqlite3.Connection) -> dict | None:
    row = conn.execute("""
        SELECT * FROM weather_logs
        ORDER BY timestamp DESC
        LIMIT 1
    """).fetchone()
    return dict(row) if row else None


def query_last_7_days(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("""
        SELECT timestamp, temperature, precipitation, wind_speed,
               wind_direction, humidity, apparent_temperature, uv_index
        FROM weather_logs
        WHERE timestamp >= datetime('now', '-7 days')
        ORDER BY timestamp ASC
    """).fetchall()
    return [dict(r) for r in rows]


def query_monthly_stats(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("""
        SELECT
            strftime('%Y-%m', timestamp) AS month,
            ROUND(AVG(temperature), 1) AS avg_temp,
            ROUND(SUM(precipitation), 1) AS total_precip,
            ROUND(MAX(temperature), 1) AS max_temp,
            ROUND(MIN(temperature), 1) AS min_temp
        FROM weather_logs
        GROUP BY month
        ORDER BY month ASC
    """).fetchall()
    return [dict(r) for r in rows]


def query_records(conn: sqlite3.Connection) -> dict:
    hottest = conn.execute("""
        SELECT timestamp, temperature FROM weather_logs
        WHERE temperature IS NOT NULL
        ORDER BY temperature DESC LIMIT 1
    """).fetchone()

    coldest = conn.execute("""
        SELECT timestamp, temperature FROM weather_logs
        WHERE temperature IS NOT NULL
        ORDER BY temperature ASC LIMIT 1
    """).fetchone()

    wettest_day = conn.execute("""
        SELECT strftime('%Y-%m-%d', timestamp) AS day,
               ROUND(SUM(precipitation), 1) AS total
        FROM weather_logs
        GROUP BY day
        ORDER BY total DESC LIMIT 1
    """).fetchone()

    stormiest = conn.execute("""
        SELECT timestamp, wind_gust FROM weather_logs
        WHERE wind_gust IS NOT NULL
        ORDER BY wind_gust DESC LIMIT 1
    """).fetchone()

    return {
        "hottest": dict(hottest) if hottest else None,
        "coldest": dict(coldest) if coldest else None,
        "wettest_day": dict(wettest_day) if wettest_day else None,
        "stormiest": dict(stormiest) if stormiest else None,
    }


def generate(db_path: Path, out_path: Path) -> None:
    conn = get_connection(db_path)
    init_db(conn)

    snapshot = {
        "meta": {
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "location": "Suhl-Goldlauter, Thüringen",
            "lat": 50.631,
            "lon": 10.724,
            "source": "Open-Meteo + lokale Sensorik",
        },
        "current": query_current(conn),
        "last_7_days": query_last_7_days(conn),
        "monthly_stats": query_monthly_stats(conn),
        "records": query_records(conn),
    }

    conn.close()

    out_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    rows_7d = len(snapshot["last_7_days"])
    rows_monthly = len(snapshot["monthly_stats"])
    print(f"Snapshot gespeichert: {out_path}")
    print(f"  7-Tage-Datenpunkte: {rows_7d}, Monatswerte: {rows_monthly}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generiert weather_snapshot.json")
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    generate(args.db, args.out)
