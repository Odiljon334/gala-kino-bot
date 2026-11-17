"""
Cloudflare Tunnel & Telegram Mini App Auto-Connector.
Generates a free HTTPS domain using cloudflared, updates .env,
and registers the Telegram Bot Menu Button in real-time.
"""
import os
import re
import sys
import time
import asyncio
import subprocess
from pathlib import Path
from aiogram import Bot
from aiogram.types import MenuButtonWebApp, WebAppInfo
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
CLOUDFLARED_BIN = BASE_DIR / "bin" / "cloudflared"
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

if not CLOUDFLARED_BIN.exists():
    print(f"❌ Error: cloudflared binary not found at {CLOUDFLARED_BIN}")
    sys.exit(1)


def start_tunnel():
    print("🚀 Cloudflare bepul HTTPS tunneli ishga tushirilmoqda...")
    cmd = [str(CLOUDFLARED_BIN), "tunnel", "--url", "http://127.0.0.1:8080"]
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    tunnel_url = None
    start_time = time.time()

    # Read output to find *.trycloudflare.com
    for line in proc.stdout:
        print(line, end="")
        match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
        if match:
            tunnel_url = match.group(0)
            break
        if time.time() - start_time > 30:
            print("⚠️ Tunnel 30 soniya ichida URL bermadi.")
            break

    if not tunnel_url:
        print("❌ Tunnel yaratib bo'lmadi!")
        return None, proc

    # Continuously drain stdout in background thread so pipe never blocks
    import threading
    def drain_pipe(stream):
        try:
            for _ in stream:
                pass
        except Exception:
            pass
            
    drainer = threading.Thread(target=drain_pipe, args=(proc.stdout,), daemon=True)
    drainer.start()

    return tunnel_url, proc


async def register_bot_menu_button(url: str):
    """Register Menu Button with Telegram Bot API."""
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("⚠️ BOT_TOKEN topilmadi!")
        return

    bot = Bot(token=BOT_TOKEN)
    miniapp_url = f"{url}/app"
    try:
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="🎬 Kinolar (Mini App)",
                web_app=WebAppInfo(url=miniapp_url)
            )
        )
        print(f"✅ Telegram Menu Button muvaffaqiyatli sozlandi: {miniapp_url}")
    except Exception as e:
        print(f"⚠️ Menu button o'rnatishda xatolik: {e}")
    finally:
        await bot.session.close()


def update_env_url(url: str):
    """Save WEB_APP_URL into .env."""
    if not ENV_FILE.exists():
        return
    content = ENV_FILE.read_text(encoding="utf-8")
    if "WEB_APP_URL=" in content:
        content = re.sub(r"WEB_APP_URL=.*", f"WEB_APP_URL={url}", content)
    else:
        content += f"\nWEB_APP_URL={url}\n"
    ENV_FILE.write_text(content, encoding="utf-8")
    print(f"💾 .env fayliga WEB_APP_URL={url} saqlandi.")


def main():
    url, proc = start_tunnel()
    if not url:
        return

    update_env_url(url)
    asyncio.run(register_bot_menu_button(url))

    print("==========================================================")
    print(f"🎉 TELEGRAM MINI APP TAYYOR!")
    print(f"🌐 HTTPS Havola: {url}/app")
    print(f"📱 Endi @galakinobot chatining chap pastki burchagida")
    print(f"   '🎬 Kinolar (Mini App)' tugmasi avtomatik paydo bo'ldi!")
    print("==========================================================")

    try:
        proc.wait()
    except KeyboardInterrupt:
        print("\nTunnel to'xtatildi.")
        proc.terminate()


if __name__ == "__main__":
    main()
