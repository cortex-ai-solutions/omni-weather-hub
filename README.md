# Omni-Weather-Hub

> Hyperlokale Wetter-Zeithistorie für **Suhl-Goldlauter, Thüringen** — mit öffentlichem Dashboard, automatischer Datenpipeline und KI-Agenten-Integration.

[![Update Weather Snapshot](https://github.com/cortex-ai-solutions/omni-weather-hub/actions/workflows/update_weather.yml/badge.svg)](https://github.com/cortex-ai-solutions/omni-weather-hub/actions/workflows/update_weather.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Live-Dashboard

**[→ omni-weather-hub öffnen](https://cortex-ai-solutions.github.io/omni-weather-hub/dashboard/)**

Täglich automatisch aktualisiert via GitHub Actions. Datenquelle: [Open-Meteo](https://open-meteo.com) (Open Data, CC BY 4.0).

---

## Features

- **Historische Daten ab 2019** — stündliche Auflösung, lückenlos
- **Dark-Mode Dashboard** — Temperatur, Niederschlag, Wind, UV-Index, Rekorde
- **Automatische Aktualisierung** — GitHub Actions aktualisiert den Snapshot täglich um 06:00 UTC
- **Hardware-Sensor-Endpunkt** — FastAPI empfängt Ecowitt/Froggit-Stationen per HTTP-POST
- **OpenClaw KI-Skill** — natürlichsprachige Abfragen direkt auf der Datenbank

## Architektur

```
GitHub Actions (täglich)
  └─ Open-Meteo API → SQLite → weather_snapshot.json → GitHub Pages

Hetzner Server (46.225.236.11:8765)
  └─ POST /ecowitt ← Ecowitt/Froggit Wetterstation
  └─ SQLite: lokale Sensordaten

OpenClaw CLI-Skill
  └─ python weather_query.py "Regen am Männertag 2019?"
```

## Messwerte

| Variable | Einheit | Quelle |
|---|---|---|
| Temperatur (2m) | °C | Open-Meteo + Sensor |
| Gefühlte Temperatur | °C | berechnet (Windchill / Heat Index) |
| Luftfeuchtigkeit | % | Open-Meteo + Sensor |
| Niederschlag | mm | Open-Meteo + Sensor |
| Windgeschwindigkeit | km/h | Open-Meteo + Sensor |
| Windböen | km/h | Open-Meteo + Sensor |
| Windrichtung | ° | Open-Meteo + Sensor |
| Sonneneinstrahlung | W/m² | Open-Meteo + Sensor |
| UV-Index | 0–11+ | Open-Meteo + Sensor |
| Taupunkt | °C | berechnet |

---

## Projektstruktur

```
omni-weather-hub/
├── .github/workflows/
│   └── update_weather.yml   # Täglicher Cron-Job
├── scripts/
│   ├── db.py                # SQLite-Schema & Helpers
│   ├── fetch_openmeteo.py   # Open-Meteo Importer
│   └── generate_snapshot.py # Erstellt weather_snapshot.json
├── dashboard/
│   └── index.html           # Statisches Dashboard (GitHub Pages)
├── hetzner/
│   ├── api/main.py          # FastAPI Ecowitt-Endpunkt
│   ├── skill/weather_query.py # OpenClaw CLI-Skill
│   └── setup.sh             # Server-Deployment
├── weather_snapshot.json    # Auto-generiert (nicht manuell editieren)
└── requirements-actions.txt
```

---

## Setup

### Daten-Pipeline (lokal / GitHub Actions)

```bash
pip install -r requirements-actions.txt

# Vollimport 2019 bis heute (einmalig)
python scripts/fetch_openmeteo.py --full

# Dashboard-Snapshot generieren
python scripts/generate_snapshot.py
```

### Hetzner-Server (Ecowitt-Endpunkt)

```bash
# Auf dem Server ausführen:
bash hetzner/setup.sh

# Healthcheck
curl http://SERVER_IP:8765/health
```

**Ecowitt-Station konfigurieren:**  
In der Ecowitt/WS View App: *Customized Server → Server IP: `46.225.236.11` · Port: `8765` · Path: `/ecowitt`*

### OpenClaw CLI-Skill

```bash
export WEATHER_DB_PATH=/opt/omni-weather-hub/weather.db

python hetzner/skill/weather_query.py "Regen am Männertag 2019"
python hetzner/skill/weather_query.py "Durchschnittstemperatur Sommer 2022"
python hetzner/skill/weather_query.py --json "November 2023"
```

---

## GitHub Pages aktivieren

1. Repository-Settings → **Pages**
2. Source: **Deploy from a branch**
3. Branch: `main` · Folder: `/ (root)`
4. Dashboard-URL: `https://cortex-ai-solutions.github.io/omni-weather-hub/dashboard/`

---

## Datenquelle & Lizenz

Wetterdaten: [Open-Meteo.com](https://open-meteo.com) — Open Data unter [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).  
Code: [MIT License](LICENSE)

**Standort:** Suhl-Goldlauter, Thüringen, Deutschland · 50.631°N, 10.724°E · ~550 m ü.NN
