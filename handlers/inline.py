"""
Telegram Inline Query Handler for Kinochi Bot Pro.
Allows users to search and share movies directly in any Telegram chat using @bot_username <query>.
"""
import hashlib
from typing import List
from aiogram import Router
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from database import search_movies, get_top_movies, get_movie_by_code
from services.template import format_caption
from config import settings

inline_router = Router(name="inline")


@inline_router.inline_query()
async def handle_inline_query(inline_query: InlineQuery):
    """Handle inline movie search requests."""
    query = inline_query.query.strip()
    bot_username = settings.BOT_USERNAME.replace("@", "")

    # If query is empty, show top/recent movies
    if not query:
        movies = await get_top_movies(limit=15)
    else:
        # Check if code match
        exact_movie = await get_movie_by_code(query)
        if exact_movie:
            movies = [exact_movie]
        else:
            movies = await search_movies(query, limit=15)

    results: List[InlineQueryResultArticle] = []

    for m in movies:
        # Unique deterministic ID
        result_id = hashlib.md5(f"movie_{m['id']}_{m['code']}".encode()).hexdigest()
        caption = await format_caption(m)
        
        # Action button to open bot directly with this movie code
        bot_deeplink = f"https://t.me/{bot_username}?start={m['code']}"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🎬 Kinoni Botda Ko'rish", url=bot_deeplink),
                InlineKeyboardButton(text="↗️ Ulashish", switch_inline_query=m["title"])
            ]
        ])

        results.append(
            InlineQueryResultArticle(
                id=result_id,
                title=f"🎬 {m['title']} ({m.get('year', '')})",
                description=f"🎭 {m.get('genres', 'Kino')} | ⭐ {m.get('rating', '7.5')}/10 | Kodi: {m['code']}",
                input_message_content=InputTextMessageContent(
                    message_text=caption,
                    parse_mode="HTML"
                ),
                reply_markup=kb,
                thumbnail_url=m.get("poster_file_id") if (m.get("poster_file_id") and m.get("poster_file_id").startswith("http")) else "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=200"
            )
        )

    await inline_query.answer(
        results=results,
        cache_time=10,
        is_personal=True,
        switch_pm_text="🔍 Barcha kinolarni botda ko'rish",
        switch_pm_parameter="inline_search"
    )
