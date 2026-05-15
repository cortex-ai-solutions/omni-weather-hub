#!/usr/bin/env bash
# Installations- und Deployment-Script für den Hetzner-Server (Elestio).
# Ausführen als root oder mit sudo.
set -euo pipefail

INSTALL_DIR=/opt/omni-weather-hub
SERVICE_NAME=omni-weather-hub
API_PORT=8765

echo "==> Installiere System-Abhängigkeiten..."
apt-get update -q
apt-get install -y python3 python3-pip python3-venv

echo "==> Lege Installationsverzeichnis an..."
mkdir -p "$INSTALL_DIR"
cp -r hetzner/api    "$INSTALL_DIR/api"
cp -r hetzner/skill  "$INSTALL_DIR/skill"
cp hetzner/requirements.txt "$INSTALL_DIR/"

echo "==> Erstelle Python-Virtualenv..."
python3 -m venv "$INSTALL_DIR/venv"
"$INSTALL_DIR/venv/bin/pip" install --quiet -r "$INSTALL_DIR/requirements.txt"

echo "==> Setze Umgebungsvariable..."
echo "WEATHER_DB_PATH=$INSTALL_DIR/weather.db" > "$INSTALL_DIR/.env"

echo "==> Erstelle systemd-Service..."
cat > /etc/systemd/system/${SERVICE_NAME}.service <<EOF
[Unit]
Description=Omni-Weather-Hub FastAPI
After=network.target

[Service]
User=root
WorkingDirectory=$INSTALL_DIR
EnvironmentFile=$INSTALL_DIR/.env
ExecStart=$INSTALL_DIR/venv/bin/uvicorn api.main:app --host 0.0.0.0 --port $API_PORT
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable  "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"

echo ""
echo "==> Fertig! API läuft auf Port $API_PORT"
echo "    Healthcheck: curl http://localhost:$API_PORT/health"
