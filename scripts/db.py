import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).parent.parent / "weather.db"


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS weather_logs (
            timestamp TEXT PRIMARY KEY,
            source TEXT,
            temperature REAL,
            humidity INTEGER,
            precipitation REAL,
            wind_speed REAL,
            wind_direction INTEGER,
            wind_gust REAL,
            solar_radiation REAL,
            uv_index REAL,
            apparent_temperature REAL,
            dew_point REAL,
            uv_alert INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_timestamp ON weather_logs(timestamp)
    """)
    conn.commit()


def upsert_records(conn: sqlite3.Connection, records: list[dict]) -> int:
    if not records:
        return 0
    conn.executemany("""
        INSERT OR REPLACE INTO weather_logs (
            timestamp, source, temperature, humidity, precipitation,
            wind_speed, wind_direction, wind_gust, solar_radiation,
            uv_index, apparent_temperature, dew_point, uv_alert
        ) VALUES (
            :timestamp, :source, :temperature, :humidity, :precipitation,
            :wind_speed, :wind_direction, :wind_gust, :solar_radiation,
            :uv_index, :apparent_temperature, :dew_point, :uv_alert
        )
    """, records)
    conn.commit()
    return len(records)
