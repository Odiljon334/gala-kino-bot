"""
Anti-Sleep Keep-Alive Heartbeat Service for Gala Kino Bot.
Prevents cloud platforms (Render, Koyeb, Railway, etc.) from sleeping by sending
periodic self-pings to the web server's /health and /ping endpoints.
"""
import os
import asyncio
import logging
import httpx
from database import get_setting

logger = logging.getLogger("keepalive")


async def get_keepalive_url() -> str:
    """Resolve the external URL to ping."""
    # 1. Check Render's auto-injected external URL
    render_url = os.environ.get("RENDER_EXTERNAL_URL", "").strip()
    if render_url:
        return render_url

    # 2. Check environment variable KEEPALIVE_URL
    env_url = os.environ.get("KEEPALIVE_URL", "").strip()
    if env_url:
        return env_url

    # 3. Check database setting keepalive_url
    db_url = (await get_setting("keepalive_url", "")).strip()
    if db_url:
        return db_url

    # 4. Fallback to web_app_url if set
    web_url = (await get_setting("web_app_url", "")).strip()
    if web_url and web_url.startswith("http"):
        return web_url

    return ""


async def start_keepalive_service(interval_seconds: int = 480):
    """
    Background worker that pings the web server every 8 minutes (480s)
    to keep free cloud instances (like Render) awake 24/7.
    """
    logger.info(f"Keep-Alive Anti-Sleep service initialized (Interval: {interval_seconds}s).")
    # Wait 20 seconds after startup for web server to bind to port
    await asyncio.sleep(20)

    while True:
        try:
            target_url = await get_keepalive_url()
            # If no external URL is configured, ping local web server to verify internal health
            ping_url = f"{target_url.rstrip('/')}/health" if target_url else "http://127.0.0.1:8080/health"
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(ping_url)
                if response.status_code == 200:
                    logger.info(f"🟢 Keep-Alive Anti-Sleep ping successful: {ping_url} (200 OK)")
                else:
                    logger.warning(f"🟡 Keep-Alive ping returned status {response.status_code}: {ping_url}")
        except Exception as e:
            logger.warning(f"⚠️ Keep-Alive ping exception: {e}")

        # Configurable interval
        try:
            db_interval = int(await get_setting("keepalive_interval", str(interval_seconds)))
            sleep_duration = max(60, min(db_interval, 840))  # Between 1m and 14m
        except Exception:
            sleep_duration = interval_seconds

        await asyncio.sleep(sleep_duration)
