# Projektstatus: Omni-Weather-Hub
<!-- Cortex AI Dashboard Scanner v1 — wird automatisch durch den Sync-Button eingelesen -->

## Meta
id: omni-weather-hub
status: live
lastUpdate: 2026-10-22
monthlyRevenue: 0
monthlyRunningCost: 0

## Nächste Aktionen
- [ ] Ecowitt/Froggit Hardware-Sensor anbinden (HTTP-POST an FastAPI-Endpunkt Hetzner 46.225.236.11:8765)
- [ ] ~~Alexa-Skill finalisieren~~ — ZURÜCKGESTELLT (Stand 22.10.2026; alexa-skill/ Ordner bleibt untracked)
- [ ] HTTPS für Hetzner-API (Domain + SSL-Zertifikat)
- [ ] Historischer Städtevergleich (zwei Orte nebeneinander im Dashboard)

## Offene Punkte
🟡 [Mittel] Hardware-Sensor: Ecowitt/Froggit Wetterstation an FastAPI-Endpunkt anbinden
⚪ [Zurückgestellt] Alexa-Skill: Sprachsteuerung für Wetterabfragen (Orsi/Telegram deckt den Bedarf ab)
🟢 [Niedrig] HTTPS für Hetzner-API einrichten
🟢 [Niedrig] Städtevergleich: zwei Standorte nebeneinander vergleichen

## KPIs
Historische Daten ab: 01.01.2016
Auflösung: Stündlich (Live) / Täglich (Archiv)
Automatisierung: GitHub Actions täglich um 06:00 UTC
Datenquelle: Open-Meteo API (Open Data, CC BY 4.0) + RainViewer + NINA/DWD
DB-Grösse: ~10 MB (SQLite, weather.db)
Orsi-Skill: weather-history (live seit 2026-05-15)
URL: https://cortex-ai-solutions.github.io/omni-weather-hub/dashboard/

## Notizen
Live unter https://cortex-ai-solutions.github.io/omni-weather-hub/dashboard/ — täglich automatisch aktualisiert via GitHub Actions.

**Features (Stand 29.06.2026):**
- Live-Radar (RainViewer 256px Tiles, Titan-Farbschema, Esri-Gray-Canvas-Basemap; CARTO verlangt seit 2026 API-Key, RainViewer nur bis Zoom 7, kein Nowcast mehr)
- Hell/Dunkel-Toggle (☀️/🌙) — schaltet Karte, Radar-Farbschema und Charts
- „Dieser Tag in der Geschichte": 10-Jahres-Vergleich mit 4 Stat-Karten + 2 Charts
- Historischer Vergleich: Monat/Jahr mit zirkulärer Navigation + Drill-down
- Monat im Jahresvergleich: Temperatur + Niederschlag über alle verfügbaren Jahre
- Pollenflug (Erle, Birke, Gräser, Beifuß, Ambrosia), DWD-Warnungen, Alle-Zeit-Rekorde
- KI-Skill weather-history für natürlichsprachige Abfragen via Orsi (Telegram)
