"""
Main Application Entrypoint for Kinochi Bot Pro.
Runs the Aiogram Telegram Bot polling alongside the FastAPI Web Dashboard concurrently.
"""
import asyncio
import logging
import uvicorn
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from database import init_db
from handlers.admin import admin_router
from handlers.user import user_router
from handlers.inline import inline_router
from handlers.referral import referral_router
from handlers.requests import requests_router
from handlers.payment import payment_router
from services.backup import auto_backup_scheduler
from services.keepalive import start_keepalive_service
from web.app import app as web_app

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("kinochi_bot")


async def run_bot(bot: Bot, dp: Dispatcher):
    """Start Telegram bot polling with auto-recovery and anti-sleep resilience."""
    logger.info("Starting Telegram Bot polling with anti-sleep resilience...")
    # Include routers
    dp.include_router(admin_router)
    dp.include_router(inline_router)
    dp.include_router(referral_router)
    dp.include_router(requests_router)
    dp.include_router(payment_router)
    dp.include_router(user_router)
    
    retry_delay = 2
    while True:
        try:
            # Delete webhook if any
            try:
                await bot.delete_webhook(drop_pending_updates=True)
            except Exception as e:
                logger.warning(f"Could not drop webhook: {e}")

            # Configure Telegram Menu Button (Native Default)
            from aiogram.types import MenuButtonDefault
            try:
                await bot.set_chat_menu_button(menu_button=MenuButtonDefault())
                logger.info("Telegram Menu Button set to default.")
            except Exception as e:
                logger.warning(f"Could not set menu button: {e}")
                
            logger.info("Aiogram polling active.")
            await dp.start_polling(bot, handle_signals=False)
            retry_delay = 2
        except asyncio.CancelledError:
            logger.info("Bot polling cancelled.")
            break
        except Exception as e:
            logger.error(f"Polling loop encountered an error: {e}. Reconnecting in {retry_delay}s...")
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 60)


async def run_web():
    """Start FastAPI Web Dashboard."""
    logger.info(f"Starting Web Dashboard on {settings.WEB_HOST}:{settings.WEB_PORT}...")
    config = uvicorn.Config(
        app=web_app,
        host=settings.WEB_HOST,
        port=settings.WEB_PORT,
        log_level="warning"
    )
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    """Initialize DB and run services concurrently."""
    # 1. Initialize SQLite Database & Dynamic Settings
    await init_db()
    logger.info("Database and dynamic settings ready.")
    
    # 2. Check Bot Token
    if not settings.BOT_TOKEN or settings.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.warning(
            "⚠️ BOT_TOKEN is not set in .env! Telegram bot polling will be skipped. "
            "Please add your Telegram bot token to .env file to enable the Telegram bot."
        )
        # Run Web Dashboard only
        await run_web()
        return

    # 3. Create Bot and Dispatcher
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    # 4. Run Bot, Web Dashboard, Auto-Backup Scheduler and Anti-Sleep Keepalive concurrently
    await asyncio.gather(
        run_bot(bot, dp),
        run_web(),
        auto_backup_scheduler(bot),
        start_keepalive_service()
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Kinochi Bot Pro stopped.")
