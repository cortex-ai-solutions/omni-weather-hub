# Projektstatus: Omni-Weather-Hub
<!-- Cortex AI Dashboard Scanner v1 — wird automatisch durch den Sync-Button eingelesen -->

## Meta
id: omni-weather-hub
status: live
lastUpdate: 2026-06-07
monthlyRevenue: 0
monthlyRunningCost: 0

## Nächste Aktionen
- [ ] Ecowitt/Froggit Hardware-Sensor anbinden (HTTP-POST an FastAPI-Endpunkt)
- [ ] Alexa-Skill finalisieren

## Offene Punkte
🟡 [Mittel] Hardware-Sensor: Ecowitt/Froggit Wetterstation an FastAPI-Endpunkt (Hetzner 46.225.236.11:8765) anbinden
🟢 [Niedrig] Alexa-Skill: Sprachsteuerung für Wetterabfragen fertigstellen

## KPIs
Historische Daten ab: 01.01.2016
Auflösung: Stündlich (Live) / Täglich (Archiv)
Automatisierung: GitHub Actions täglich um 06:00 UTC
Datenquelle: Open-Meteo API (Open Data, CC BY 4.0)
Radar: RainViewer (256px Tiles, Titan-Farbschema)
Server: Hetzner 46.225.236.11:8765 (FastAPI Sensor-Endpunkt)

## Notizen
Live unter https://cortex-ai-solutions.github.io/omni-weather-hub/dashboard/ — täglich automatisch aktualisiert via GitHub Actions.

**Neue Features (07.06.2026):**
- Live-Radar funktionsfähig (256px Tiles, opacity-Fix, helle CARTO-Basemap)
- Hell/Dunkel-Toggle (☀️/🌙 Pill-Button in Kopfzeile) — schaltet Karte, Radar-Farbschema und Charts um
- „Dieser Tag in der Geschichte": 10-Jahres-Vergleich des aktuellen Kalendertags mit 4 Stat-Karten und 2 Balkendiagrammen (Tages-Temperatur + Tages-Niederschlag)
- Rate-Limiting-Fix: ein Archiv-Request statt 11 parallele (vollständige Jahresdaten)

OpenClaw KI-Skill für natürlichsprachige Wetterabfragen auf Elestio verfügbar. Sensor-Endpunkt für Ecowitt/Froggit läuft auf Hetzner, Hardware-Anbindung noch ausstehend.
