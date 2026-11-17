"""
Dynamic template engine for movie captions and messages.
Formats text using dynamic templates from database settings without code modification.
"""
from typing import Dict, Any
from database import get_setting
from config import settings

async def format_caption(movie: Dict[str, Any]) -> str:
    """Format movie caption using dynamic caption_template from DB."""
    template = await get_setting("caption_template")
    bot_username = settings.BOT_USERNAME.replace("@", "")
    
    # Safe fallback replacements
    safe_data = {
        "title": movie.get("title", "Noma'lum"),
        "original_title": movie.get("original_title") or movie.get("title", ""),
        "year": movie.get("year", "Noma'lum"),
        "country": movie.get("country", "Noma'lum"),
        "genres": movie.get("genres", "Kino"),
        "language": movie.get("language", "O'zbek tilida"),
        "rating": movie.get("rating", "7.5"),
        "duration": movie.get("duration", "Noma'lum"),
        "description": movie.get("description", "Ajoyib kino tomosha qiling."),
        "code": movie.get("code", "000"),
        "age_rating": movie.get("age_rating", "16+"),
        "bot_username": bot_username,
        "views": movie.get("views_count", 0),
        "downloads": movie.get("downloads_count", 0)
    }
    
    # Format with fallback if template has syntax error
    try:
        formatted = template.format(**safe_data)
    except Exception:
        # Fallback simple template
        formatted = (
            f"🎬 <b>{safe_data['title']}</b> ({safe_data['year']})\n\n"
            f"🎭 <b>Janr:</b> {safe_data['genres']}\n"
            f"🌐 <b>Davlati:</b> {safe_data['country']}\n"
            f"🔊 <b>Tili:</b> {safe_data['language']}\n"
            f"⭐ <b>Reyting:</b> {safe_data['rating']}/10\n\n"
            f"🔢 <b>Kodi:</b> <code>{safe_data['code']}</code>\n"
            f"🤖 <b>Bot:</b> @{bot_username}"
        )
        
    # Append dynamic sponsor/ad banner if configured
    ad_banner = await get_setting("ad_banner_text", "")
    if ad_banner.strip():
        formatted += f"\n\n{ad_banner.strip()}"
        
    return formatted


async def format_start_message(user_name: str, telegram_id: int) -> str:
    """Format start welcome message using dynamic settings."""
    template = await get_setting("start_message")
    bot_name = await get_setting("bot_name", "Gala Kino")
    bot_username = settings.BOT_USERNAME.replace("@", "")
    
    safe_data = {
        "user_name": user_name,
        "telegram_id": telegram_id,
        "bot_name": bot_name,
        "bot_username": bot_username
    }
    try:
        return template.format(**safe_data)
    except Exception:
        return f"👋 Salom {user_name}! {bot_name} botiga xush kelibsiz.\nKino kodini yuboring!"
