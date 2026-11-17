"""
Automatic channel posting service for Kinochi Bot Pro.
Publishes new movie releases to the official Telegram channel with deep-link buttons.
"""
import logging
from typing import Dict, Any, Optional
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_setting
from config import settings

logger = logging.getLogger(__name__)


async def auto_post_movie_to_channel(bot: Bot, movie: Dict[str, Any]) -> bool:
    """Publish a new movie post to the configured Telegram channel."""
    # Check if auto posting is enabled
    is_enabled = await get_setting("auto_post_enabled", "1")
    if is_enabled != "1":
        return False

    channel_target = await get_setting("auto_post_channel", "")
    if not channel_target or not channel_target.strip():
        logger.info("Auto post skipped: auto_post_channel is empty.")
        return False

    channel_target = channel_target.strip()
    if not channel_target.startswith("@") and not channel_target.startswith("-"):
        channel_target = f"@{channel_target}"

    bot_username = settings.BOT_USERNAME.replace("@", "")
    deep_link = f"https://t.me/{bot_username}?start={movie['code']}"

    post_caption = (
        f"🔥 <b>YANGI PREMYERA: {movie['title']} ({movie.get('year', '')})</b>\n\n"
        f"🎭 <b>Janr:</b> {movie.get('genres', 'Kino')}\n"
        f"🌐 <b>Davlati:</b> {movie.get('country', 'Noma''lum')}\n"
        f"🔊 <b>Tili:</b> {movie.get('language', 'O''zbek tilida')}\n"
        f"⭐ <b>Reyting:</b> {movie.get('rating', '7.5')}/10\n\n"
        f"📝 {movie.get('description', '')[:250]}...\n\n"
        f"🔢 <b>Kino kodi:</b> <code>{movie['code']}</code>\n\n"
        f"👇 Kinoni to'liq va sifatli ko'rish uchun quyidagi tugmani bosing:"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎬 Kinoni Botda Ko'rish", url=deep_link)
        ],
        [
            InlineKeyboardButton(text="🤖 Rasmiy Kino Botimiz", url=f"https://t.me/{bot_username}")
        ]
    ])

    try:
        poster = movie.get("poster_file_id")
        video = movie.get("quality_720_file_id")

        if poster and (poster.startswith("http") or len(poster) > 15):
            await bot.send_photo(
                chat_id=channel_target,
                photo=poster,
                caption=post_caption,
                reply_markup=kb
            )
        elif video:
            await bot.send_video(
                chat_id=channel_target,
                video=video,
                caption=post_caption,
                reply_markup=kb
            )
        else:
            await bot.send_message(
                chat_id=channel_target,
                text=post_caption,
                reply_markup=kb
            )
            
        logger.info(f"Successfully auto-posted movie {movie['code']} to {channel_target}")
        return True
    except Exception as e:
        logger.warning(f"Could not auto-post movie {movie['code']} to {channel_target}: {e}")
        return False
