# Omni-Weather-Hub — Projektdokumentation

> Stand: Mai 2026 · Cortex AI Solutions · Tobias Uske

---

## Inhaltsverzeichnis

1. [Projektübersicht](#1-projektübersicht)
2. [Gesamtarchitektur](#2-gesamtarchitektur)
3. [GitHub Repository & Pages](#3-github-repository--pages)
4. [Dashboard (index.html)](#4-dashboard-indexhtml)
5. [Datenpipeline (GitHub Actions)](#5-datenpipeline-github-actions)
6. [Hetzner / Elest.io Server](#6-hetzner--elestio-server)
7. [OpenClaw Skill: weather-history](#7-openclaw-skill-weather-history)
8. [KI-Agent Orsi — Integration](#8-ki-agent-orsi--integration)
9. [Datenquellen & APIs](#9-datenquellen--apis)
10. [Wartung & Betrieb](#10-wartung--betrieb)
11. [Erweiterungen & Roadmap](#11-erweiterungen--roadmap)

---

## 1. Projektübersicht

**Omni-Weather-Hub** ist ein hyperlokales Wetter-Daten-System für den Standort **Suhl-Goldlauter, Thüringen** (50.631°N, 10.724°E, ~550 m ü.NN), das öffentlich über GitHub Pages erreichbar ist und gleichzeitig als Werkzeug für den KI-Agenten Orsi dient.

### Was das System kann

| Feature | Beschreibung |
|---|---|
| **Live-Dashboard** | Öffentlich erreichbare Wetter-Webanwendung (GitHub Pages) |
| **Historische Daten** | Stündliche Wetterdaten ab 2019 (Open-Meteo Archive API) |
| **Live-Radar** | Aktuelles Niederschlagsradar + Nowcast (RainViewer) |
| **Wettervorhersage** | ECMWF-Modell via Windy Embed (4h-Vorhersage) |
| **Ortssuche** | Beliebige Städte weltweit per Eingabe oder URL-Parameter |
| **Pollenwarnung** | Aktuelle Pollenbelastung via Open-Meteo Air Quality |
| **DWD-Warnungen** | Offizielle Wetterwarnungen via NINA API (Bund) |
| **Orsi-Integration** | KI-Skill für natürlichsprachige Wetterhistorie-Abfragen |
| **Telegram-Links** | Orsi generiert shareable Dashboard-Links für beliebige Orte |

---

## 2. Gesamtarchitektur

```
┌─────────────────────────────────────────────────────────────────┐
│  GitHub Repository: cortex-ai-solutions/omni-weather-hub         │
│                                                                   │
│  GitHub Actions (tägl. 06:00 UTC)                                │
│  └── fetch_openmeteo.py → SQLite (Cache) → weather_snapshot.json │
│                                    ↓                             │
│  GitHub Pages                                                     │
│  └── dashboard/index.html  ←  weather_snapshot.json             │
│      URL: https://cortex-ai-solutions.github.io/                 │
│           omni-weather-hub/dashboard/                            │
└─────────────────────────────────────────────────────────────────┘
          ↕ (Browser ruft APIs direkt ab)
┌──────────────────────────────────┐  ┌──────────────────────────┐
│  Open-Meteo APIs                 │  │  RainViewer API           │
│  • Forecast (live Wetterwerte)   │  │  (Radar-Tiles)           │
│  • Archive (hist. Daten, Charts) │  └──────────────────────────┘
│  • Geocoding (Ortssuche)         │  ┌──────────────────────────┐
│  • Air Quality (Pollen)          │  │  NINA API (Bund)          │
└──────────────────────────────────┘  │  DWD-Wetterwarnungen     │
                                      └──────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│  Hetzner Server (Elest.io)                                       │
│  Host: ssp-framework-2-u68900.vm.elestio.app (46.225.236.11)    │
│                                                                   │
│  OpenClaw (Docker-Container: app-openclaw-gateway-1)             │
│  └── Skill: weather-history  (/opt/app/skills/)                  │
│      • Natürlichsprachige Wetterhistorie-Abfragen                │
│      • Beliebige Orte via --city / --lat --lon                   │
│      • JSON-Output für Maschinenverarbeitung                     │
│                                                                   │
│  FastAPI (Port 8765) — WARTEND (kein Ecowitt-Gerät vorhanden)   │
│  └── POST /ecowitt  (für künftige Hardware-Wetterstation)        │
└─────────────────────────────────────────────────────────────────┘
          ↑ Orsi (KI-Agent) ruft Skill auf und generiert Links
┌─────────────────────────────────────────────────────────────────┐
│  Orsi (OpenClaw KI-Agent) via Telegram                           │
│  └── Nutzer fragt: "Wie war das Wetter am Männertag 2019?"      │
│  └── Nutzer fragt: "Zeig mir das Wetter für Kiel"               │
│  └── Orsi antwortet mit Daten oder Dashboard-Link               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. GitHub Repository & Pages

### Repository

| Eigenschaft | Wert |
|---|---|
| URL | `https://github.com/cortex-ai-solutions/omni-weather-hub` |
| Branch | `main` |
| Lizenz | MIT |
| GitHub Pages | Branch `main`, Root-Verzeichnis |
| Dashboard-URL | `https://cortex-ai-solutions.github.io/omni-weather-hub/dashboard/` |

### Projektstruktur

```
omni-weather-hub/
├── .github/
│   └── workflows/
│       └── update_weather.yml      # Täglicher Cron-Job
├── scripts/
│   ├── db.py                       # SQLite-Schema & Helpers
│   ├── fetch_openmeteo.py          # Open-Meteo Daten-Importer
│   └── generate_snapshot.py        # Erstellt weather_snapshot.json
├── dashboard/
│   ├── index.html                  # Das vollständige Dashboard (SPA)
│   └── logo.png                    # Cortex AI Solutions Logo
├── hetzner/
│   ├── api/
│   │   └── main.py                 # FastAPI Ecowitt-Endpunkt (wartend)
│   ├── skill/
│   │   └── weather_query.py        # Python-Skill (lokal, Vorgänger)
│   └── setup.sh                    # Server-Deployment Script
├── weather_snapshot.json           # Auto-generiert (nicht manuell editieren)
├── requirements-actions.txt        # Python-Deps für GitHub Actions
├── README.md                       # Kurz-Dokumentation (GitHub)
├── DOKUMENTATION.md                # Diese Datei
├── LICENSE                         # MIT
└── .gitignore                      # weather.db, .env, __pycache__/
```

### GitHub Pages aktivieren

Falls noch nicht geschehen:
1. Repository → **Settings** → **Pages**
2. Source: **Deploy from a branch**
3. Branch: `main` · Folder: `/ (root)`
4. Speichern → nach ~1 Minute verfügbar

---

## 4. Dashboard (index.html)

Das Dashboard ist eine vollständige Single-Page-Application in reinem HTML5/JS — kein Build-Step, keine Server-Abhängigkeit.

**Technologie-Stack:**
- Tailwind CSS (CDN, Dark Mode)
- Chart.js v4 (CDN)
- Leaflet.js (CDN, für Radar-Karte)
- Alle Daten via `fetch()` direkt vom Browser

### Panels im Überblick

#### Zeile 1: Radar · Aktuell · Vorhersage

| Panel | Inhalt | Datenquelle |
|---|---|---|
| **Live-Radar** | Interaktive Karte mit Regenradar-Animation | RainViewer API |
| **Aktuell** | Temperatur, Gefühlte Temp., Luftfeuchte, Niederschlag, Wind, Taupunkt, UV-Index | Open-Meteo Forecast |
| **4h-Vorhersage** | ECMWF-Wettermodell (Regen/Temp/Wind umschaltbar) | Windy Embed |

#### Zeile 2: Historische Charts

| Panel | Inhalt | Datenquelle |
|---|---|---|
| **Letzte 7 Tage** | Stündliche Temperatur + Niederschlag | Open-Meteo Forecast (past_days=7) |
| **Jahresübersicht** | Monatliche Ø-Temperatur + Gesamtniederschlag, Selektor 2019–heute | Open-Meteo Archive |

#### Zeile 3: Tagesverlauf + Pollen + Warnungen

| Panel | Inhalt | Datenquelle |
|---|---|---|
| **Niederschlag heute** | Stündliches Balkendiagramm, farbkodiert nach Intensität, Alarmhinweis | Open-Meteo Forecast |
| **Pollenflug** | Aktuelle saisonale Pollenbelastung (Erle, Birke, Gräser, Beifuß, Ambrosia) | Open-Meteo Air Quality |
| **DWD-Warnungen** | Aktive amtliche Wetterwarnungen für Deutschland | NINA API / Bund |

#### Zeile 4: Alle-Zeit-Rekorde

Heißester/kältester Moment, regenreichster Tag, stärkste Böe — für den aktuell gewählten Ort (live von Open-Meteo Archive 2019–heute).

### Ortssuche & URL-Parameter

Das Dashboard unterstützt beliebige Orte:

```
# Manuell im Suchfeld (Header) eingeben:
München  →  Geocoding → alle Panels wechseln zu München

# URL-Parameter (direkter Link):
https://cortex-ai-solutions.github.io/omni-weather-hub/dashboard/?city=Kiel
https://cortex-ai-solutions.github.io/omni-weather-hub/dashboard/?city=Hamburg
https://cortex-ai-solutions.github.io/omni-weather-hub/dashboard/?lat=53.55&lon=10.00&name=Hamburg

# Zurück zu Suhl-Goldlauter:
⌂-Button im Header
```

### Aktualisieren-Button

Der **↻ Aktualisieren**-Button im "Aktuell"-Panel ruft direkt die Open-Meteo Forecast API auf (Echtzeit, unabhängig vom täglichen Snapshot). Aktualisiert gleichzeitig:
- Aktuelle Wetterwerte
- Radar-Tiles (neu von RainViewer geladen)
- Windy-Iframe (neu zentriert auf aktiven Ort)

---

## 5. Datenpipeline (GitHub Actions)

### Workflow: `update_weather.yml`

```yaml
Trigger:
  - Täglich um 06:00 UTC (Cron: '0 6 * * *')
  - Manuell via workflow_dispatch

Ablauf:
  1. Checkout Repository
  2. Python 3.11 Setup
  3. pip install -r requirements-actions.txt
  4. SQLite-Cache laden (Key: weather-db-YYYY-MM)
  5. python scripts/fetch_openmeteo.py --update (letzte 30 Tage)
  6. python scripts/generate_snapshot.py
  7. git add weather_snapshot.json
  8. git commit "chore: update weather snapshot [skip ci]"
  9. git push
  10. SQLite-Cache speichern
```

### Erster vollständiger Import

```bash
# Lokal ausführen (einmalig, dauert ~2 Minuten):
WEATHER_DB_PATH=weather.db python scripts/fetch_openmeteo.py --full
python scripts/generate_snapshot.py
```

### weather_snapshot.json — Struktur

```json
{
  "meta": {
    "generated_at": "2026-05-15 06:12:34",
    "source": "open-meteo",
    "location": "Suhl-Goldlauter"
  },
  "current": {
    "timestamp": "...",
    "temperature": 12.4,
    "apparent_temperature": 10.1,
    "humidity": 78,
    "precipitation": 0.0,
    "wind_speed": 8.2,
    "wind_direction": 245,
    "dew_point": 8.9,
    "uv_index": 2.1
  },
  "last_7_days": [ ... ],      // stündliche Werte (168+ Einträge)
  "monthly_stats": [ ... ],    // Ø-Temp + Gesamtniederschlag pro Monat
  "records": {
    "hottest":     { "temperature": 35.8, "timestamp": "..." },
    "coldest":     { "temperature": -18.3, "timestamp": "..." },
    "wettest_day": { "total": 62.4, "day": "..." },
    "stormiest":   { "wind_gust": 94.0, "timestamp": "..." }
  }
}
```

---

## 6. Hetzner / Elest.io Server

### Server-Daten

| Eigenschaft | Wert |
|---|---|
| Provider | Elest.io (Hetzner Nürnberg) |
| Hostname | `ssp-framework-2-u68900.vm.elestio.app` |
| IP | `46.225.236.11` |
| SSH-Zugang | `ssh -i "C:/Users/Tobias/.ssh/ssh-key.txt" root@ssp-framework-2-u68900.vm.elestio.app` |
| Primäre Nutzung | OpenClaw KI-Agent + künftiger Ecowitt-Sensor-Endpunkt |

### Docker-Umgebung

Auf dem Server läuft OpenClaw als Docker-Compose-Stack:

```bash
# Container-Übersicht:
docker ps | grep openclaw

# Relevanter Container:
app-openclaw-gateway-1   # Haupt-Gateway, hat Skill-PATH
```

### Skills-Verzeichnis

Custom Skills werden auf dem Host unter `/opt/app/skills/` abgelegt und sind im Container als `/app/skills/` eingebunden. Der PATH im Container enthält das Skill-Verzeichnis.

```bash
# Skill-Pfad:
/opt/app/skills/weather-history-skill/
├── weather-history     # Node.js-Skript (ausführbar)
├── SKILL.md            # Skill-Dokumentation für OpenClaw
└── package.json        # Node.js-Metadaten

# Test vom Host:
docker exec app-openclaw-gateway-1 weather-history "Maennertag 2019"
```

### FastAPI Ecowitt-Endpunkt (wartend)

Der Endpunkt für Hardware-Wetterstationen ist implementiert aber deaktiviert:

```
Datei:  hetzner/api/main.py
Port:   8765
Status: INAKTIV (kein Ecowitt/Froggit-Gerät vorhanden)

Endpunkte:
  POST /ecowitt  → Empfängt Messwerte der Wetterstation
  GET  /health   → Status + Datenbankgröße
  GET  /export   → Letzte 7 Tage als JSON
```

**Aktivierung wenn Ecowitt-Hardware vorhanden:**
1. Port 8765 am Server freigeben (Firewall/Elest.io Panel)
2. `bash hetzner/setup.sh` auf dem Server ausführen
3. In der Ecowitt/WS View App: *Customized Server → IP: `46.225.236.11` · Port: `8765` · Path: `/ecowitt`*
4. SSL/HTTPS einrichten (Domain nötig für sicheren Betrieb)

---

## 7. OpenClaw Skill: weather-history

### Übersicht

Der Skill `weather-history` ermöglicht natürlichsprachige Wetterhistorie-Abfragen direkt im Gespräch mit Orsi. Er ruft die Open-Meteo API ab — keine eigene Datenbank nötig.

**Datei auf Server:** `/opt/app/skills/weather-history-skill/weather-history`
**Sprache:** Node.js (läuft ohne npm-Abhängigkeiten, nutzt natives `fetch()`)

### Nutzung

```bash
# Standard: Suhl-Goldlauter
weather-history "Maennertag 2019"
weather-history "Sommer 2022"
weather-history "Januar 2024"
weather-history "2023-05-26"

# Beliebiger Ort (automatisches Geocoding via Open-Meteo)
weather-history --city "Berlin" "Sommer 2022"
weather-history --city "Hamburg" "Regen Juli 2023"
weather-history --city "Wien" "Winter 2021"
weather-history --city "Kiel" "Mai 2025"

# Direkte Koordinaten
weather-history --lat 53.551 --lon 9.993 --name "Hamburg Zentrum" "August 2023"

# JSON-Output (für Maschinenverarbeitung / Orsi)
weather-history --json "Maennertag 2019"
weather-history --city "Kiel" --json "Sommer 2025"
```

### Unterstützte Zeitraum-Formate

| Format | Beispiel |
|---|---|
| ISO-Datum | `"2023-05-26"` |
| Deutsches Datum | `"26. Mai 2023"` |
| Bewegliche Feiertage | `"Maennertag 2019"`, `"Ostern 2022"`, `"Karfreitag 2021"` |
| Feste Feiertage | `"Weihnachten 2022"`, `"Silvester 2023"`, `"Neujahr 2024"` |
| Jahreszeiten | `"Sommer 2022"`, `"Winter 2021"`, `"Herbst 2023"` |
| Monat + Jahr | `"Juli 2022"`, `"Januar 2024"` |
| Ganzes Jahr | `"2023"` |

**Wichtig:** Umlaute als ae/oe/ue schreiben: `Maennertag`, `Fruehling`, `Muenchen`, `Duesseldorf`

### Metrik-Schlüsselwörter

| Wort im Text | Angezeigte Metrik |
|---|---|
| (kein Schlüsselwort) | Temperatur (Standard) |
| Regen, Niederschlag | Niederschlag (mm gesamt + stündl. Max) |
| Wind, Windgeschwindigkeit | Windgeschwindigkeit (Min/Max/Avg) |
| Luftfeuchtigkeit, Feuchte | Luftfeuchtigkeit (%) |
| UV | UV-Index |

### JSON-Output-Format

```json
{
  "query": "Sommer 2022",
  "location": "Kiel, Schleswig-Holstein",
  "lat": 54.323,
  "lon": 10.139,
  "dateFrom": "2022-06-21",
  "dateTo": "2022-09-22",
  "metric": "temperature",
  "results": {
    "temperature":   { "min": 8.1, "max": 33.4, "avg": 18.9, "total": ..., "count": 2208 },
    "precipitation": { "min": 0.0, "max": 14.2, "avg": 0.08, "total": 176.3, "count": 2208 },
    "wind_speed":    { "min": 0.0, "max": 67.3, "avg": 14.2, "total": ..., "count": 2208 },
    "humidity":      { "min": 32,  "max": 98,   "avg": 73.1, "total": ..., "count": 2208 },
    "uv_index":      { "min": 0.0, "max": 7.8,  "avg": 1.4,  "total": ..., "count": 2208 }
  }
}
```

---

## 8. KI-Agent Orsi — Integration

### Wer ist Orsi?

Orsi ist der persönliche KI-Agent von Tobias (Cortex AI Solutions), der auf dem Elest.io-Server via OpenClaw läuft und über **Telegram** erreichbar ist. Orsi hat Zugriff auf verschiedene Skills — darunter `weather-history`.

### Memory-Dateien auf dem Server

Orsis Gedächtnis zum Wetter-Skill liegt auf dem Server:

```
Container: app-openclaw-gateway-1
Pfad: /home/node/.openclaw/workspace/memory/memory_weather_history.md
```

Diese Memory-Datei erklärt Orsi:
- Wann der Skill zu aktivieren ist
- Alle Befehle und Syntax
- Hinweis auf Umlaute (ae/oe/ue)
- Wie Dashboard-Links generiert werden

### Orsi als Wetterauskunft

**Historische Daten abfragen:**
```
Du (Telegram):  "Orsi, wie war das Wetter am Männertag 2019 in Suhl?"
Orsi:           Ruft 'weather-history "Maennertag 2019"' auf
                → "Temperatur: Min 4.3°C Max 15.4°C Avg 10.8°C, kein Regen"

Du:             "Wie war der Sommer 2022 in Berlin im Vergleich zu Suhl?"
Orsi:           Ruft beide Abfragen auf (--json) und vergleicht
```

**Dashboard-Links generieren:**
```
Du (Telegram):  "Zeig mir das Wetter-Dashboard für Kiel"
Orsi:           "Hier ist das Wetter-Dashboard für Kiel:
                 https://cortex-ai-solutions.github.io/omni-weather-hub/dashboard/?city=Kiel"
                 (Du klickst → Dashboard öffnet sich direkt für Kiel)

Du:             "Wir fahren nächste Woche nach Wien — wie ist das Wetter dort?"
Orsi:           weather-history --city "Wien" --json "Mai 2026"
                + Link: ...dashboard/?city=Wien
```

### URL-Parameter für Dashboard-Links

Orsi generiert Links nach diesem Schema:

```
Basis-URL:  https://cortex-ai-solutions.github.io/omni-weather-hub/dashboard/

Parameter:
  ?city=STADTNAME          → Geocoding automatisch im Browser
  ?lat=LAT&lon=LON         → Direkte Koordinaten
  ?lat=LAT&lon=LON&name=N  → Koordinaten mit Anzeigename
```

Beim Öffnen des Links:
- Dashboard lädt und geocodiert die Stadt
- Alle Panels wechseln sofort auf den neuen Ort
- Radar, Vorhersage, Charts, Pollen, Warnungen — alles für die gewünschte Stadt

### Orsi aktivieren für Wetterabfragen

Orsi erkennt Wetteranfragen an Schlüsselwörtern wie:
- "Wie war das Wetter …"
- "Wieviel Regen … "
- "Temperatur / Wind / UV …"
- "Dashboard für …" / "Wetter-Link für …"
- "Zeig mir … in [Stadt]"

---

## 9. Datenquellen & APIs

Alle verwendeten APIs sind **kostenlos und ohne API-Key** nutzbar (Open Data):

| API | Zweck | Nutzung |
|---|---|---|
| **Open-Meteo Forecast** | Live-Wetterwerte, 7-Tage, Pollen-Tagesverlauf | Browser + Skill |
| **Open-Meteo Archive** | Historische Daten ab 2019, Jahres-Charts, Rekorde | Browser + Skill + Actions |
| **Open-Meteo Geocoding** | Ortsname → Koordinaten | Browser + Skill |
| **Open-Meteo Air Quality** | Stündliche Pollenwerte (grains/m³) | Browser |
| **RainViewer** | Regenradar-Tiles + Nowcast (~30 Min.) | Browser |
| **Windy Embed** | ECMWF-Modell-Vorhersage (iframe) | Browser |
| **NINA API (Bund)** | Amtliche DWD-Wetterwarnungen | Browser |

**Lizenz der Wetterdaten:** Open-Meteo CC BY 4.0 · RainViewer CC BY-NC 4.0 · DWD Daten: dl-de/by-2-0

---

## 10. Wartung & Betrieb

### Automatisch (kein Eingriff nötig)

| Aufgabe | Wann | Wer |
|---|---|---|
| Wetter-Snapshot aktualisieren | tägl. 06:00 UTC | GitHub Actions |
| `weather_snapshot.json` commiten | tägl. nach Fetch | GitHub Actions |

### Manuell (bei Bedarf)

**GitHub Action manuell triggern** (z.B. nach längerem Ausfall):
- Repository → Actions → "Update Weather Snapshot" → "Run workflow"

**Vollständigen Reimport durchführen** (z.B. nach Datenverlust):
```bash
# Lokal:
WEATHER_DB_PATH=weather.db python scripts/fetch_openmeteo.py --full
python scripts/generate_snapshot.py
git add weather_snapshot.json && git commit -m "chore: manual full reimport" && git push
```

**Skill auf dem Server aktualisieren:**
```bash
ssh -i "C:/Users/Tobias/.ssh/ssh-key.txt" root@ssp-framework-2-u68900.vm.elestio.app
# Neue Skill-Datei nach /opt/app/skills/weather-history-skill/weather-history kopieren
chmod +x /opt/app/skills/weather-history-skill/weather-history
# Test:
docker exec app-openclaw-gateway-1 weather-history "Maennertag 2019"
```

**Skill testen (direkt auf dem Server):**
```bash
docker exec app-openclaw-gateway-1 weather-history "Sommer 2022"
docker exec app-openclaw-gateway-1 weather-history --city "Berlin" "Januar 2024"
docker exec app-openclaw-gateway-1 weather-history --json "Maennertag 2019"
```

### Monitoring

- **GitHub Actions Status:** Repository → Actions → grünes/rotes Badge
- **Dashboard lädt nicht:** Browser-Konsole prüfen, meist CORS oder API-Downtime
- **Skill antwortet nicht:** `docker exec app-openclaw-gateway-1 weather-history "test 2024"` → muss Fehlermeldung "Kein Datum erkannt" zeigen (zeigt dass Skill erreichbar ist)

---

## 11. Erweiterungen & Roadmap

### Geplant / Offen

| Feature | Beschreibung | Voraussetzung |
|---|---|---|
| **Ecowitt-Integration** | Eigene Wetterstation sendet Daten an FastAPI-Endpunkt | Ecowitt/Froggit-Hardware kaufen |
| **Sensordaten im Dashboard** | Lokale Messwerte ergänzen Open-Meteo-Daten | Ecowitt-Integration aktiv |
| **HTTPS für Hetzner-API** | Sicherer Endpunkt mit eigenem Domainname | Domain + SSL-Zertifikat |
| **Historischer Städtevergleich** | Jahres-Charts für 2 Orte nebeneinander | Dashboard-Erweiterung |

### Technische Hinweise für künftige Entwicklung

- **Dashboard-Erweiterungen:** Nur `dashboard/index.html` bearbeiten, committen, pushen → GitHub Pages aktualisiert automatisch
- **Neuer Skill:** Unter `/opt/app/skills/SKILLNAME-skill/` anlegen, in `docker-compose.yml` PATH eintragen, Container neu starten
- **Snapshot-Schema ändern:** `generate_snapshot.py` anpassen + `loadData()` in `index.html` entsprechend aktualisieren

---

*Dokumentation erstellt: 15. Mai 2026*  
*Cortex AI Solutions · Tobias Uske*
