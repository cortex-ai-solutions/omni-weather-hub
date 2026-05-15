"""
Fetches hourly weather data for Suhl-Goldlauter from Open-Meteo and stores it in SQLite.

Usage:
  python fetch_openmeteo.py --full      # Import 2019-01-01 to today (initial run)
  python fetch_openmeteo.py --update    # Import last 30 days (daily cron)
  python fetch_openmeteo.py --year 2022 # Import a single year
"""

import argparse
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import requests
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.db import DB_PATH, get_connection, init_db, upsert_records


LAT = 50.631
LON = 10.724
TIMEZONE = "Europe/Berlin"
START_YEAR = 2019

HOURLY_VARS = [
    "temperature_2m",
    "relativehumidity_2m",
    "precipitation",
    "windspeed_10m",
    "winddirection_10m",
    "apparent_temperature",
    "dewpoint_2m",
    "windgusts_10m",
    "shortwave_radiation",
    "uv_index",
]

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


def fetch_archive(start: date, end: date) -> list[dict]:
    params = {
        "latitude": LAT,
        "longitude": LON,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "hourly": ",".join(HOURLY_VARS),
        "timezone": TIMEZONE,
    }
    resp = requests.get(ARCHIVE_URL, params=params, timeout=60)
    resp.raise_for_status()
    return _parse_response(resp.json())


def fetch_forecast(past_days: int = 16) -> list[dict]:
    params = {
        "latitude": LAT,
        "longitude": LON,
        "hourly": ",".join(HOURLY_VARS),
        "timezone": TIMEZONE,
        "past_days": past_days,
        "forecast_days": 1,
    }
    resp = requests.get(FORECAST_URL, params=params, timeout=60)
    resp.raise_for_status()
    return _parse_response(resp.json())


def _parse_response(data: dict) -> list[dict]:
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    records = []

    for i, ts in enumerate(times):
        # Normalize timestamp: "2019-01-01T00:00" → "2019-01-01 00:00:00"
        timestamp = ts.replace("T", " ")
        if len(timestamp) == 16:
            timestamp += ":00"

        uv = _val(hourly, "uv_index", i)

        records.append({
            "timestamp": timestamp,
            "source": "open-meteo",
            "temperature": _val(hourly, "temperature_2m", i),
            "humidity": _int_val(hourly, "relativehumidity_2m", i),
            "precipitation": _val(hourly, "precipitation", i),
            "wind_speed": _val(hourly, "windspeed_10m", i),
            "wind_direction": _int_val(hourly, "winddirection_10m", i),
            "wind_gust": _val(hourly, "windgusts_10m", i),
            "solar_radiation": _val(hourly, "shortwave_radiation", i),
            "uv_index": uv,
            "apparent_temperature": _val(hourly, "apparent_temperature", i),
            "dew_point": _val(hourly, "dewpoint_2m", i),
            "uv_alert": 1 if (uv is not None and uv >= 6) else 0,
        })

    return records


def _val(hourly: dict, key: str, i: int):
    lst = hourly.get(key, [])
    if i < len(lst):
        return lst[i]
    return None


def _int_val(hourly: dict, key: str, i: int):
    v = _val(hourly, key, i)
    return int(v) if v is not None else None


def date_ranges_by_year(start: date, end: date) -> list[tuple[date, date]]:
    ranges = []
    current = start
    while current <= end:
        year_end = date(current.year, 12, 31)
        batch_end = min(year_end, end)
        ranges.append((current, batch_end))
        current = date(batch_end.year + 1, 1, 1)
    return ranges


def run_full(db_path):
    today = date.today()
    # Archive API covers up to 5 days before today
    archive_end = today - timedelta(days=5)
    archive_start = date(START_YEAR, 1, 1)

    conn = get_connection(db_path)
    init_db(conn)

    batches = date_ranges_by_year(archive_start, archive_end)
    total_inserted = 0

    for start, end in tqdm(batches, desc="Lade Archiv-Daten (jährlich)"):
        records = fetch_archive(start, end)
        n = upsert_records(conn, records)
        total_inserted += n
        time.sleep(0.5)  # Rate-Limiting respektieren

    # Lücke schließen mit Forecast API
    tqdm.write("Lade aktuelle Daten (Forecast API)...")
    records = fetch_forecast(past_days=16)
    n = upsert_records(conn, records)
    total_inserted += n

    conn.close()
    print(f"\nFertig: {total_inserted} Datensätze eingefügt/aktualisiert.")


def run_update(db_path):
    conn = get_connection(db_path)
    init_db(conn)

    # Archive: letzte 30 Tage (minus 5 Tage Puffer)
    today = date.today()
    archive_end = today - timedelta(days=5)
    archive_start = today - timedelta(days=30)

    records = fetch_archive(archive_start, archive_end)
    n1 = upsert_records(conn, records)

    # Forecast: letzte 16 Tage bis heute
    records = fetch_forecast(past_days=16)
    n2 = upsert_records(conn, records)

    conn.close()
    print(f"Update: {n1 + n2} Datensätze eingefügt/aktualisiert.")


def run_year(year: int, db_path):
    conn = get_connection(db_path)
    init_db(conn)

    start = date(year, 1, 1)
    end = min(date(year, 12, 31), date.today() - timedelta(days=5))

    print(f"Lade {year}: {start} bis {end}")
    records = fetch_archive(start, end)
    n = upsert_records(conn, records)
    conn.close()
    print(f"Fertig: {n} Datensätze für {year}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Open-Meteo Wetterdaten-Importer")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--full", action="store_true", help="Vollimport ab 2019")
    group.add_argument("--update", action="store_true", help="Letzte 30 Tage aktualisieren")
    group.add_argument("--year", type=int, help="Einzelnes Jahr importieren")
    parser.add_argument("--db", type=Path, default=DB_PATH, help="Pfad zur SQLite-DB")

    args = parser.parse_args()

    if args.full:
        run_full(args.db)
    elif args.update:
        run_update(args.db)
    elif args.year:
        run_year(args.year, args.db)
