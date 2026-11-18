#!/usr/bin/env bash
# Gala Kino Bot 24/7 Persistent Runner with Auto-Restart Watchdog
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "==============================================="
echo "  GALA KINO BOT - 24/7 ALWAYS-ON WATCHDOG      "
echo "==============================================="

trap "echo 'Stopping Gala Kino Bot...'; exit 0" SIGINT SIGTERM

while true; do
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting Gala Kino Bot main.py..."
    PYTHONUNBUFFERED=1 ./venv/bin/python main.py || true
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Process exited. Auto-restarting in 5 seconds..."
    sleep 5
done
