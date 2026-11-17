"""
Broadcaster service for mass announcements and promotional campaigns.
Handles rate limits, dead user detection, and progress tracking.
"""
import asyncio
import logging
from typing import Optional
from aiogram import Bot
from aiogram.exceptions import TelegramRetryAfter, TelegramForbiddenError, TelegramBadRequest
import aiosqlite
from database import DB_PATH

logger = logging.getLogger(__name__)


async def broadcast_message(
    bot: Bot,
    text: Optional[str] = None,
    photo_file_id: Optional[str] = None,
    video_file_id: Optional[str] = None,
    pin: bool = False
) -> dict:
    """Broadcast message to all active users."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT telegram_id FROM users WHERE is_banned = 0") as cursor:
            rows = await cursor.fetchall()
            user_ids = [r[0] for r in rows]

    total = len(user_ids)
    sent = 0
    blocked = 0
    failed = 0

    for user_id in user_ids:
        try:
            msg = None
            if video_file_id:
                msg = await bot.send_video(chat_id=user_id, video=video_file_id, caption=text)
            elif photo_file_id:
                msg = await bot.send_photo(chat_id=user_id, photo=photo_file_id, caption=text)
            elif text:
                msg = await bot.send_message(chat_id=user_id, text=text)

            if msg and pin:
                try:
                    await bot.pin_chat_message(chat_id=user_id, message_id=msg.message_id)
                except Exception:
                    pass

            sent += 1
            await asyncio.sleep(0.05)  # Safe Telegram throttle (20 msgs/sec)

        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
            sent += 1
        except TelegramForbiddenError:
            # User blocked the bot
            blocked += 1
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute("UPDATE users SET is_banned = 1, ban_reason = 'blocked_bot' WHERE telegram_id = ?", (user_id,))
                await db.commit()
        except TelegramBadRequest as e:
            failed += 1
            logger.warning(f"Bad request for user {user_id}: {e}")
        except Exception as e:
            failed += 1
            logger.error(f"Error broadcasting to {user_id}: {e}")

    return {
        "total": total,
        "sent": sent,
        "blocked": blocked,
        "failed": failed
    }
