#!/usr/bin/env bash
# ==========================================================
# KINOCHI BOT PRO — 1-CLICK ISHGA TUSHIRISH SKRIPTI
# ==========================================================

set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR"

echo "=========================================================="
echo "🎬 KINOCHI BOT PRO (AIOGRAM 3 + FASTAPI DASHBOARD)"
echo "=========================================================="

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Xatolik: Python 3 o'rnatilmagan!"
    exit 1
fi

# Check venv
if [ ! -d "venv" ]; then
    echo "📦 Virtual muhit (venv) yaratilmoqda..."
    python3 -m venv venv
    echo "📥 Kutubxonalar o'rnatilmoqda..."
    ./venv/bin/pip install --upgrade pip
    ./venv/bin/pip install -r requirements.txt
fi

# Check .env
if [ ! -f ".env" ]; then
    echo "⚠️ .env fayli topilmadi, .env.example dan nusxalandi."
    cp .env.example .env
    echo "👉 Iltimos, .env faylini ochib BOT_TOKEN va ADMIN_IDS ni kiriting!"
fi

echo "🚀 Bot va Web Admin Panel ishga tushirilmoqda..."
echo "🌐 Web Dashboard: http://localhost:8080"
echo "=========================================================="

exec ./venv/bin/python3 main.py
