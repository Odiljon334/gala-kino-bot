"""
Automated Database Backup Service for Gala Kino Bot.
Sends scheduled SQLite database snapshots directly to Admin Telegram chats.
"""
import os
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from aiogram import Bot
from aiogram.types import FSInputFile

from config import settings

logger = logging.getLogger(__name__)


async def send_db_backup(bot: Bot):
    """Send database file snapshot to all superadmins."""
    db_path = Path(settings.DATABASE_PATH)
    if not db_path.exists():
        logger.warning(f"Backup failed: DB file not found at {db_path}")
        return

    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    caption = (
        f"💾 <b>GALA KINO — AVTOMATIK ZAXIRA NUSXASI (BACKUP)</b>\n\n"
        f"📅 Sana: <code>{date_str}</code>\n"
        f"📦 Fayl hajmi: {round(os.path.getsize(db_path) / 1024, 1)} KB\n\n"
        "<i>Ushbu fayl barcha kinolar, foydalanuvchilar va sozlamalar bazasini o'z ichiga oladi.</i>"
    )

    doc = FSInputFile(str(db_path), filename=f"gala_kino_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.db")
    for admin_id in settings.ADMIN_IDS:
        try:
            await bot.send_document(chat_id=admin_id, document=doc, caption=caption)
            logger.info(f"Backup sent successfully to admin {admin_id}")
        except Exception as e:
            logger.error(f"Failed to send backup to admin {admin_id}: {e}")


async def auto_backup_scheduler(bot: Bot, interval_hours: int = 24):
    """Run automated backup every interval_hours."""
    logger.info(f"Auto-backup scheduler started (Interval: {interval_hours} hours).")
    # Wait 60 seconds on initial boot before sending first or checking
    await asyncio.sleep(60)
    while True:
        try:
            await send_db_backup(bot)
        except Exception as e:
            logger.error(f"Error in backup scheduler: {e}")
        await asyncio.sleep(interval_hours * 3600)
