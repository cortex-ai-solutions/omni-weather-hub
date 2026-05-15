"""
FastAPI-Endpunkt für Ecowitt/Froggit-Wetterstationen.
Empfängt HTTP-POST-Daten im Ecowitt-Protokoll und speichert sie in SQLite.

Start: uvicorn hetzner.api.main:app --host 0.0.0.0 --port 8765
"""

import math
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Form, Response
from fastapi.middleware.cors import CORSMiddleware

# DB-Pfad via Umgebungsvariable konfigurierbar
DB_PATH = Path(os.getenv("WEATHER_DB_PATH", "/opt/omni-weather-hub/weather.db"))

app = FastAPI(title="Omni-Weather-Hub API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# --- Einheiten-Konvertierung ---

def f_to_c(f: float | None) -> float | None:
    return round((f - 32) * 5 / 9, 2) if f is not None else None

def mph_to_kmh(mph: float | None) -> float | None:
    return round(mph * 1.60934, 1) if mph is not None else None

def inch_to_mm(inch: float | None) -> float | None:
    return round(inch * 25.4, 2) if inch is not None else None


def calc_apparent_temp(temp_c: float | None, wind_kmh: float | None, humidity: int | None) -> float | None:
    if temp_c is None:
        return None
    if temp_c <= 10 and wind_kmh is not None:
        # Windchill (Environment Canada)
        wind_kmh = max(wind_kmh, 1.0)
        wc = 13.12 + 0.6215 * temp_c - 11.37 * (wind_kmh ** 0.16) + 0.3965 * temp_c * (wind_kmh ** 0.16)
        return round(wc, 1)
    if temp_c >= 26 and humidity is not None:
        # Heat Index (Rothfusz)
        T, RH = temp_c, humidity
        hi = (-8.78469475556 + 1.61139411 * T + 2.338548839 * RH
              - 0.14611605 * T * RH - 0.012308094 * T**2
              - 0.016424828 * RH**2 + 0.002211732 * T**2 * RH
              + 0.00072546 * T * RH**2 - 0.000003582 * T**2 * RH**2)
        return round(hi, 1)
    return round(temp_c, 1)


def calc_dew_point(temp_c: float | None, humidity: int | None) -> float | None:
    if temp_c is None or humidity is None or humidity <= 0:
        return None
    # Magnus-Formel
    a, b = 17.27, 237.7
    gamma = (a * temp_c / (b + temp_c)) + math.log(humidity / 100.0)
    dew = (b * gamma) / (a - gamma)
    return round(dew, 1)


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
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
    conn.commit()
    return conn


# --- Endpunkte ---

@app.post("/ecowitt")
async def receive_ecowitt(
    # Temperatur & Feuchte
    tempf: Annotated[float | None, Form()] = None,
    humidity: Annotated[int | None, Form()] = None,
    # Niederschlag
    rainratein: Annotated[float | None, Form()] = None,
    # Wind
    windspeedmph: Annotated[float | None, Form()] = None,
    winddir: Annotated[int | None, Form()] = None,
    windgustmph: Annotated[float | None, Form()] = None,
    # Solar & UV
    solarradiation: Annotated[float | None, Form()] = None,
    uv: Annotated[float | None, Form()] = None,
    # Optionaler Zeitstempel von der Station
    dateutc: Annotated[str | None, Form()] = None,
):
    temp_c = f_to_c(tempf)
    wind_kmh = mph_to_kmh(windspeedmph)
    gust_kmh = mph_to_kmh(windgustmph)
    precip_mm = inch_to_mm(rainratein)

    apparent = calc_apparent_temp(temp_c, wind_kmh, humidity)
    dew = calc_dew_point(temp_c, humidity)
    uv_alert = 1 if (uv is not None and uv >= 6) else 0

    if dateutc:
        # Station liefert "YYYY-MM-DD HH:MM:SS" in UTC
        timestamp = dateutc.replace("T", " ")
    else:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    record = {
        "timestamp": timestamp,
        "source": "local_sensor",
        "temperature": temp_c,
        "humidity": humidity,
        "precipitation": precip_mm,
        "wind_speed": wind_kmh,
        "wind_direction": winddir,
        "wind_gust": gust_kmh,
        "solar_radiation": solarradiation,
        "uv_index": uv,
        "apparent_temperature": apparent,
        "dew_point": dew,
        "uv_alert": uv_alert,
    }

    conn = get_conn()
    conn.execute("""
        INSERT OR REPLACE INTO weather_logs VALUES (
            :timestamp, :source, :temperature, :humidity, :precipitation,
            :wind_speed, :wind_direction, :wind_gust, :solar_radiation,
            :uv_index, :apparent_temperature, :dew_point, :uv_alert
        )
    """, record)
    conn.commit()
    conn.close()

    return {"status": "ok", "timestamp": timestamp}


@app.get("/health")
def health():
    conn = get_conn()
    count = conn.execute("SELECT COUNT(*) FROM weather_logs").fetchone()[0]
    latest = conn.execute(
        "SELECT timestamp FROM weather_logs ORDER BY timestamp DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return {
        "status": "ok",
        "db_records": count,
        "latest_timestamp": latest[0] if latest else None,
    }


@app.get("/export")
def export_recent(days: int = 7):
    """Gibt die letzten N Tage lokaler Sensordaten zurück (für optionale GitHub-Action-Integration)."""
    conn = get_conn()
    rows = conn.execute("""
        SELECT * FROM weather_logs
        WHERE source = 'local_sensor'
          AND timestamp >= datetime('now', ? || ' days')
        ORDER BY timestamp ASC
    """, (f"-{days}",)).fetchall()
    conn.close()
    cols = [
        "timestamp", "source", "temperature", "humidity", "precipitation",
        "wind_speed", "wind_direction", "wind_gust", "solar_radiation",
        "uv_index", "apparent_temperature", "dew_point", "uv_alert",
    ]
    return [dict(zip(cols, row)) for row in rows]
