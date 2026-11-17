"""
Autonomous Cloudflare Tunnel Manager & Self-Healing Watchdog for Gala Kino.
Ensures the Telegram Mini App HTTPS tunnel never drops, auto-restarts on Cloudflare Error 1033,
and real-time synchronizes SQLite database and Telegram Bot Menu Buttons.
"""
import os
import re
import time
import asyncio
import logging
import subprocess
import threading
import urllib.request
from pathlib import Path
from typing import Optional, Tuple
from aiogram import Bot
from aiogram.types import MenuButtonWebApp, WebAppInfo
from dotenv import load_dotenv, dotenv_values

from config import settings, BASE_DIR
from database import set_setting, get_setting

logger = logging.getLogger("tunnel_watchdog")
CLOUDFLARED_BIN = BASE_DIR / "bin" / "cloudflared"
ENV_FILE = BASE_DIR / ".env"


class CloudflareTunnelManager:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.proc: Optional[subprocess.Popen] = None
        self.current_url: str = ""
        self.is_running: bool = False
        self.consecutive_failures: int = 0

    def start_process(self) -> Optional[str]:
        """Spawn cloudflared tunnel process and parse initial trycloudflare URL."""
        if not CLOUDFLARED_BIN.exists():
            logger.warning("cloudflared binary not found. Skipping auto-tunnel.")
            return None

        # Terminate old process if still running
        if self.proc:
            try:
                self.proc.terminate()
                self.proc.wait(timeout=3)
            except Exception:
                pass

        cmd = [str(CLOUDFLARED_BIN), "tunnel", "--url", "http://127.0.0.1:8080"]
        try:
            self.proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
        except Exception as e:
            logger.error(f"Failed to launch cloudflared: {e}")
            return None

        tunnel_url = None
        start_time = time.time()

        # Parse stdout for trycloudflare.com
        for line in self.proc.stdout:
            match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
            if match:
                tunnel_url = match.group(0)
                break
            if time.time() - start_time > 35:
                logger.warning("Cloudflare tunnel launch timed out.")
                break

        if not tunnel_url:
            logger.error("Failed to acquire trycloudflare tunnel URL.")
            return None

        # Continuously drain stdout in background thread to avoid pipe deadlock
        def drain(stream):
            try:
                for _ in stream:
                    pass
            except Exception:
                pass

        t = threading.Thread(target=drain, args=(self.proc.stdout,), daemon=True)
        t.start()

        self.current_url = tunnel_url
        logger.info(f"🚀 Live Cloudflare Tunnel online: {tunnel_url}")
        return tunnel_url

    async def update_all_destinations(self, url: str):
        """Save to .env, SQLite DB, and Telegram Bot Menu Button."""
        self.current_url = url
        
        # 1. Update SQLite DB (instant across all processes)
        try:
            await set_setting("web_app_url", url)
            logger.info("Saved web_app_url to SQLite database.")
        except Exception as e:
            logger.warning(f"Error saving web_app_url to DB: {e}")

        # 2. Update .env file
        try:
            if ENV_FILE.exists():
                content = ENV_FILE.read_text(encoding="utf-8")
                if "WEB_APP_URL=" in content:
                    content = re.sub(r"WEB_APP_URL=.*", f"WEB_APP_URL={url}", content)
                else:
                    content += f"\nWEB_APP_URL={url}\n"
                ENV_FILE.write_text(content, encoding="utf-8")
        except Exception as e:
            logger.warning(f"Error updating .env: {e}")

        # 3. Update Telegram Bot Menu Button
        miniapp_url = f"{url}/app"
        try:
            await self.bot.set_chat_menu_button(
                menu_button=MenuButtonWebApp(
                    text="🎬 Kinolar (Mini App)",
                    web_app=WebAppInfo(url=miniapp_url)
                )
            )
            logger.info(f"✅ Telegram Menu Button updated: {miniapp_url}")
        except Exception as e:
            logger.warning(f"Error updating Telegram menu button: {e}")

    def test_tunnel_health(self) -> bool:
        """Perform quick HTTP check to verify tunnel is reachable and not Error 1033."""
        if not self.current_url or "trycloudflare.com" not in self.current_url:
            return True

        check_url = f"{self.current_url}/api/vip_info"
        req = urllib.request.Request(
            check_url,
            headers={"User-Agent": "GalaKinoWatchdog/1.0"}
        )
        try:
            with urllib.request.urlopen(req, timeout=8) as response:
                return response.status == 200
        except Exception:
            return False

    async def run_watchdog(self):
        """Main loop: starts tunnel and auto-heals if connection drops or returns Error 1033."""
        auto_tunnel = os.getenv("AUTO_TUNNEL", "1").strip()
        if auto_tunnel == "0":
            logger.info("AUTO_TUNNEL=0 disabled. Skipping tunnel manager.")
            return

        # Give main FastAPI web server 3 seconds to bind 8080
        await asyncio.sleep(3)

        # Initial launch
        url = self.start_process()
        if url:
            await self.update_all_destinations(url)
            self.consecutive_failures = 0
        else:
            logger.warning("Could not start initial tunnel, will retry in 15 seconds.")

        # Continuous Health Check Loop
        while True:
            await asyncio.sleep(30)
            
            # Check health synchronously in executor
            loop = asyncio.get_running_loop()
            healthy = await loop.run_in_executor(None, self.test_tunnel_health)

            if healthy:
                self.consecutive_failures = 0
            else:
                self.consecutive_failures += 1
                logger.warning(
                    f"⚠️ Tunnel healthcheck failed ({self.consecutive_failures}/2): {self.current_url}"
                )

                if self.consecutive_failures >= 2:
                    logger.error("🚨 Tunnel has died or timed out! Executing auto-healing restart...")
                    new_url = self.start_process()
                    if new_url:
                        await self.update_all_destinations(new_url)
                        self.consecutive_failures = 0
                        logger.info(f"🎉 Tunnel successfully self-healed: {new_url}")
                        
                        # Notify Admins via Telegram
                        for admin_id in settings.ADMIN_IDS:
                            try:
                                await self.bot.send_message(
                                    chat_id=admin_id,
                                    text=(
                                        "🔄 <b>[Gala Kino Avto-Tiklash]</b>\n\n"
                                        "Cloudflare tunneli yangilandi va avtomatik qayta ulandi!\n"
                                        f"🌐 <b>Yangi Mini App:</b> {new_url}/app\n\n"
                                        "<i>Telegram Menyu tugmasi avtomatik yangilandi.</i>"
                                    )
                                )
                            except Exception:
                                pass


async def start_tunnel_watchdog(bot: Bot):
    """Entry point for main.py."""
    mgr = CloudflareTunnelManager(bot)
    await mgr.run_watchdog()
