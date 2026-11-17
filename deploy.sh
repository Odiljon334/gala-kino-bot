#!/usr/bin/env bash
# ==========================================================
# KINOCHI BOT PRO — 1-CLICK SERVER DEPLOYMENT SCRIPT
# ==========================================================

set -e

echo "🚀 Kinochi Bot Pro serverga o'rnatilmoqda..."

# 1. Tizim paketlarini yangilash
echo "📦 Kerakli paketlar tekshirilmoqda..."
if command -v apt-get &> /dev/null; then
    sudo apt-get update -y
    sudo apt-get install -y python3 python3-pip python3-venv git curl
fi

# 2. Virtual muhit va kutubxonalar
if [ ! -d "venv" ]; then
    echo "🐍 Python virtual muhit yaratilmoqda..."
    python3 -m venv venv
fi

echo "📥 Python kutubxonalari o'rnatilmoqda..."
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

# 3. Systemd servisini o'rnatish
SERVICE_PATH="/etc/systemd/system/kinochi_bot.service"
CURRENT_DIR=$(pwd)

echo "⚙️ Systemd servisi sozlanmoqda ($SERVICE_PATH)..."
cat << EOF | sudo tee $SERVICE_PATH
[Unit]
Description=Kinochi Bot Pro Daemon
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$CURRENT_DIR
ExecStart=$CURRENT_DIR/venv/bin/python main.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable kinochi_bot.service
sudo systemctl restart kinochi_bot.service

echo "=========================================================="
echo "✅ MUVAFFAQISHLI O'RNATILDI VA SERVERDA ISHGA TUSHDI!"
echo "📊 Statusni ko'rish: sudo systemctl status kinochi_bot"
echo "📜 Loglarni ko'rish: sudo journalctl -u kinochi_bot -f"
echo "🌐 Web Dashboard: http://SERVER_IP:8080"
echo "=========================================================="
