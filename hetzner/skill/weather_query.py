"""
OpenClaw CLI-Skill: Strukturierte Wetter-Abfragen auf der SQLite-Datenbank.

Aufruf:
  python weather_query.py "Wie viel Regen am Männertag 2019?"
  python weather_query.py "Durchschnittstemperatur Sommer 2022"
  python weather_query.py --json "2024-01-15"
  python weather_query.py --json "Mai 2023"
"""

import argparse
import json
import os
import re
import sqlite3
import sys
from datetime import date, datetime, timedelta
from pathlib import Path


DB_PATH = Path(os.getenv("WEATHER_DB_PATH", "/opt/omni-weather-hub/weather.db"))


# --- Feiertags-Lookup (bewegliche Feste nach Gauß) ---

def easter_date(year: int) -> date:
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


MOVING_HOLIDAYS = {
    "männertag":         lambda y: easter_date(y) + timedelta(days=39),
    "vatertag":          lambda y: easter_date(y) + timedelta(days=39),
    "christi himmelfahrt": lambda y: easter_date(y) + timedelta(days=39),
    "ostern":            lambda y: easter_date(y),
    "ostersonntag":      lambda y: easter_date(y),
    "ostermontag":       lambda y: easter_date(y) + timedelta(days=1),
    "pfingstsonntag":    lambda y: easter_date(y) + timedelta(days=49),
    "pfingstmontag":     lambda y: easter_date(y) + timedelta(days=50),
    "pfingsten":         lambda y: easter_date(y) + timedelta(days=49),
}

FIXED_HOLIDAYS = {
    "neujahr":           (1, 1),
    "silvester":         (12, 31),
    "heiligabend":       (12, 24),
    "weihnachten":       (12, 25),
    "nikolaus":          (12, 6),
    "tag der arbeit":    (5, 1),
    "maifeiertag":       (5, 1),
    "tag der deutschen einheit": (10, 3),
    "halloween":         (10, 31),
    "valentinstag":      (2, 14),
}

MONTH_NAMES = {
    "januar":1,"februar":2,"märz":3,"maerz":3,"april":4,"mai":5,"juni":6,
    "juli":7,"august":8,"september":9,"oktober":10,"november":11,"dezember":12,
    "jan":1,"feb":2,"mär":3,"apr":4,"jun":6,"jul":7,"aug":8,
    "sep":9,"okt":10,"nov":11,"dez":12,
}

SEASONS = {
    "frühling": (3, 21, 6, 20), "fruehling": (3, 21, 6, 20),
    "fruehjahr": (3, 21, 6, 20), "frühjahr": (3, 21, 6, 20),
    "sommer": (6, 21, 9, 22),
    "herbst": (9, 23, 12, 20),
    "winter": (12, 21, 3, 20),
}

METRIC_KEYWORDS = {
    "regen": "precipitation", "niederschlag": "precipitation", "regenmenge": "precipitation",
    "temperatur": "temperature", "temp": "temperature", "hitze": "temperature", "kälte": "temperature",
    "wind": "wind_speed", "windgeschwindigkeit": "wind_speed", "böe": "wind_gust", "boe": "wind_gust",
    "luftfeuchtigkeit": "humidity", "feuchte": "humidity", "feuchtigkeit": "humidity",
    "uv": "uv_index", "sonneneinstrahlung": "solar_radiation", "strahlung": "solar_radiation",
    "taupunkt": "dew_point",
}


def detect_year(text: str) -> int | None:
    m = re.search(r'\b(20\d{2})\b', text)
    return int(m.group(1)) if m else None


def parse_query(text: str) -> dict:
    lower = text.lower()
    year = detect_year(lower)

    # --- Datumsbereich bestimmen ---
    date_from = date_to = None

    # Fester Datumsausdruck: "15. Mai 2023" oder "2023-05-15"
    iso_m = re.search(r'(\d{4})-(\d{2})-(\d{2})', text)
    de_m  = re.search(r'(\d{1,2})\.\s*(' + '|'.join(MONTH_NAMES) + r')\.?\s*(20\d{2})', lower)

    if iso_m:
        d = date(int(iso_m.group(1)), int(iso_m.group(2)), int(iso_m.group(3)))
        date_from = d
        date_to   = d
    elif de_m:
        day   = int(de_m.group(1))
        month = MONTH_NAMES[de_m.group(2).rstrip('.')]
        yr    = int(de_m.group(3))
        d = date(yr, month, day)
        date_from = date_to = d
    else:
        # Bewegliche Feiertage
        for name, fn in MOVING_HOLIDAYS.items():
            if name in lower and year:
                d = fn(year)
                date_from = date_to = d
                break

        # Feste Feiertage
        if date_from is None:
            for name, (m, dy) in FIXED_HOLIDAYS.items():
                if name in lower and year:
                    d = date(year, m, dy)
                    date_from = date_to = d
                    break

        # Saison
        if date_from is None:
            for sname, (ms, ds, me, de_) in SEASONS.items():
                if sname in lower and year:
                    date_from = date(year, ms, ds)
                    if me > ms:
                        date_to = date(year, me, de_)
                    else:
                        date_to = date(year + 1, me, de_)
                    break

        # Monatsangabe "Mai 2023" / "Januar 2020"
        if date_from is None:
            for mname, mnum in MONTH_NAMES.items():
                if mname in lower and year:
                    import calendar
                    last = calendar.monthrange(year, mnum)[1]
                    date_from = date(year, mnum, 1)
                    date_to   = date(year, mnum, last)
                    break

        # Nur Jahresangabe
        if date_from is None and year:
            date_from = date(year, 1, 1)
            date_to   = date(year, 12, 31)

    # --- Metrik bestimmen ---
    metric = "temperature"  # Default
    for kw, col in METRIC_KEYWORDS.items():
        if kw in lower:
            metric = col
            break

    return {
        "date_from": date_from,
        "date_to": date_to,
        "metric": metric,
        "raw": text,
    }


def query_db(parsed: dict) -> dict:
    if not DB_PATH.exists():
        return {"error": f"Datenbank nicht gefunden: {DB_PATH}"}

    df = parsed["date_from"]
    dt = parsed["date_to"]
    metric = parsed["metric"]

    if df is None:
        return {"error": "Kein Zeitraum erkannt. Bitte Datum oder Jahr angeben."}

    ts_from = df.strftime("%Y-%m-%d 00:00:00")
    ts_to   = dt.strftime("%Y-%m-%d 23:59:59")

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    rows = conn.execute(f"""
        SELECT timestamp, {metric}, source
        FROM weather_logs
        WHERE timestamp BETWEEN ? AND ?
          AND {metric} IS NOT NULL
        ORDER BY timestamp ASC
    """, (ts_from, ts_to)).fetchall()

    if not rows:
        conn.close()
        return {
            "period": f"{df.isoformat()} – {dt.isoformat()}",
            "metric": metric,
            "count": 0,
            "message": "Keine Daten für diesen Zeitraum gefunden.",
        }

    values = [r[metric] for r in rows]
    result = {
        "period": f"{df.isoformat()} – {dt.isoformat()}",
        "metric": metric,
        "count": len(values),
        "min": round(min(values), 2),
        "max": round(max(values), 2),
        "avg": round(sum(values) / len(values), 2),
    }

    if metric == "precipitation":
        result["total_mm"] = round(sum(values), 2)

    conn.close()
    return result


def human_readable(result: dict, query: str) -> str:
    if "error" in result:
        return f"Fehler: {result['error']}"
    if result.get("count", 0) == 0:
        return f"Keine Daten für den Zeitraum {result.get('period', '?')} gefunden."

    metric_labels = {
        "temperature": "Temperatur", "precipitation": "Niederschlag",
        "wind_speed": "Windgeschwindigkeit", "wind_gust": "Windböen",
        "humidity": "Luftfeuchtigkeit", "uv_index": "UV-Index",
        "solar_radiation": "Sonneneinstrahlung", "dew_point": "Taupunkt",
    }
    metric_units = {
        "temperature": "°C", "precipitation": "mm", "wind_speed": "km/h",
        "wind_gust": "km/h", "humidity": "%", "uv_index": "",
        "solar_radiation": "W/m²", "dew_point": "°C",
    }

    m = result["metric"]
    label = metric_labels.get(m, m)
    unit  = metric_units.get(m, "")
    period = result["period"]

    lines = [f"Anfrage: {query}", f"Zeitraum: {period}", f"Messgröße: {label}"]

    if m == "precipitation":
        lines.append(f"Gesamtniederschlag: {result['total_mm']} mm")
        lines.append(f"Stündl. Max: {result['max']} mm/h")
    else:
        lines.append(f"Min:  {result['min']} {unit}")
        lines.append(f"Max:  {result['max']} {unit}")
        lines.append(f"Ø:    {result['avg']} {unit}")

    lines.append(f"Datenpunkte: {result['count']}")
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OpenClaw Wetter-Skill")
    parser.add_argument("query", help="Natürlichsprachige Wetteranfrage")
    parser.add_argument("--json", action="store_true", dest="as_json",
                        help="Maschinenlesbare JSON-Ausgabe")
    args = parser.parse_args()

    parsed = parse_query(args.query)
    result = query_db(parsed)

    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(human_readable(result, args.query))
