"""
Database access layer using aiosqlite for Kinochi Bot Pro.
Supports asynchronous queries, migrations, dynamic settings, and full CRUD.
"""
import aiosqlite
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from config import settings

logger = logging.getLogger(__name__)

DB_PATH = settings.DATABASE_PATH

DEFAULT_SETTINGS = {
    "bot_name": "Gala Kino",
    "start_message": (
        "👋 <b>Assalomu alaykum, {user_name}!</b>\n\n"
        "🎬 <b>Gala Kino</b> rasmiy botiga xush kelibsiz.\n"
        "Bu yerda siz eng sara o'zbekcha tarjima kinolar, premyeralar va seriallarni tomosha qilishingiz mumkin!\n\n"
        "🔍 Kino ko'rish uchun uning <b>kodini</b> yuboring yoki quyidagi menyudan foydalaning."
    ),
    "start_media_url": "",
    "caption_template": (
        "🎬 <b>{title}</b> ({year})\n\n"
        "🎭 <b>Janr:</b> {genres}\n"
        "🌐 <b>Davlati:</b> {country}\n"
        "🔊 <b>Tili:</b> {language}\n"
        "⭐ <b>Reyting:</b> {rating}/10\n"
        "⏱ <b>Davomiyligi:</b> {duration}\n\n"
        "📝 <b>Tavsif:</b> {description}\n\n"
        "🔢 <b>Kodi:</b> <code>{code}</code>\n"
        "🤖 <b>Botimiz:</b> @{bot_username}"
    ),
    "maintenance_mode": "0",
    "maintenance_text": "⚠️ <b>Botda texnik ishlar olib borilmoqda!</b>\n\nIltimos, birozdan so'ng qayta urinib ko'ring.",
    "force_sub_mode": "strict",  # strict, timer, disabled
    "force_sub_timer_seconds": "60",  # vaqtli obuna taymeri
    "force_sub_text": (
        "⚠️ <b>Botdan to'liq foydalanish uchun quyidagi kanallarimizga obuna bo'ling!</b>\n\n"
        "Obuna bo'lgach, <b>«✅ Obunani tekshirish»</b> tugmasini bosing."
    ),
    "daily_download_limit": "10",
    "limit_exceeded_text": "⚠️ <b>Kunlik bepul limitingiz tugadi!</b>\nKuniga maksimal {limit} ta kino yuklay olasiz.\nCheksiz yuklash uchun VIP obunaga ega bo'ling.",
    "anti_flood_rate": "2",
    "auto_post_channel": "",
    "auto_post_enabled": "1",
    "referral_friends_for_vip": "5",
    "referral_reward_vip_days": "7",
    "referral_reward_downloads": "3",
    "movie_request_enabled": "1",
    "movie_request_text": (
        "📥 <b>KINO BUYURTMA QILISH</b>\n\n"
        "Qidirgan kinongiz bazamizda topilmadimi? Marhamat, kino nomini yuboring, "
        "adminlarimiz tez orada uni botga joylashadi va sizga avtomatik xabar keladi!"
    ),
    "ad_banner_text": "🔥 <b>Homiylik reklamasi:</b> Eng so'nggi premyeralar faqat bizda!",
    "vip_info_text": (
        "💎 <b>VIP STATUS IMTIYOZLARI:</b>\n\n"
        "✅ Barcha kinolarni cheksiz yuklab olish\n"
        "✅ Reklamasiz va majburiy obunasiz foydalanish\n"
        "✅ Faqat VIP lar uchun eksklyuziv premyeralar\n"
        "✅ Yuqori tezlikda yuklab olish\n\n"
        "💰 <b>Narxlar:</b>\n"
        "• 1 oy: 15,000 so'm\n"
        "• 3 oy: 35,000 so'm\n"
        "• 1 yil: 99,000 so'm\n\n"
        "Murojaat uchun: {admin_contact}"
    ),
    "admin_contact": "@Odiljon_n3",
    "payment_card_number": "8600 •••• •••• 1234 (Odiljon N.)"
}


async def init_db():
    """Create all required tables and populate default dynamic settings."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        
        # 1. Users Table
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            first_name TEXT,
            role TEXT DEFAULT 'user',
            is_vip INTEGER DEFAULT 0,
            vip_until TIMESTAMP,
            daily_downloads INTEGER DEFAULT 0,
            last_download_date TEXT,
            is_banned INTEGER DEFAULT 0,
            ban_reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # 2. Channels (Mandatory Subscription) Table
        await db.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            channel_id TEXT,
            username TEXT,
            invite_link TEXT NOT NULL,
            button_text TEXT DEFAULT '➕ Obuna bo''lish',
            timer_seconds INTEGER DEFAULT 0,
            is_join_request INTEGER DEFAULT 0,
            priority INTEGER DEFAULT 1,
            is_active INTEGER DEFAULT 1,
            clicks_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # 3. Movies Table
        await db.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            original_title TEXT,
            year INTEGER,
            country TEXT,
            genres TEXT,
            language TEXT DEFAULT 'O''zbek tilida',
            duration TEXT,
            age_rating TEXT DEFAULT '16+',
            rating REAL DEFAULT 7.5,
            quality_480_file_id TEXT,
            quality_720_file_id TEXT,
            quality_1080_file_id TEXT,
            poster_file_id TEXT,
            trailer_url TEXT,
            description TEXT,
            views_count INTEGER DEFAULT 0,
            downloads_count INTEGER DEFAULT 0,
            likes_count INTEGER DEFAULT 0,
            dislikes_count INTEGER DEFAULT 0,
            is_vip_only INTEGER DEFAULT 0,
            is_series INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # 4. Movie Episodes Table (for series & anime)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS movie_episodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_id INTEGER NOT NULL,
            season_number INTEGER DEFAULT 1,
            episode_number INTEGER NOT NULL,
            episode_title TEXT,
            file_id TEXT NOT NULL,
            quality TEXT DEFAULT '720p',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (movie_id) REFERENCES movies (id) ON DELETE CASCADE
        )
        """)
        
        # 5. Dynamic Bot Settings Table
        await db.execute("""
        CREATE TABLE IF NOT EXISTS bot_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            description TEXT
        )
        """)
        
        # 6. Promocodes Table
        await db.execute("""
        CREATE TABLE IF NOT EXISTS promocodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            duration_days INTEGER DEFAULT 30,
            max_uses INTEGER DEFAULT 1,
            used_count INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # 7. Search Logs Table
        await db.execute("""
        CREATE TABLE IF NOT EXISTS search_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER,
            query TEXT,
            results_count INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # 8. User Subscription Timer Session Table
        await db.execute("""
        CREATE TABLE IF NOT EXISTS user_timer_sessions (
            telegram_id INTEGER PRIMARY KEY,
            channel_id INTEGER,
            timer_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            timer_seconds INTEGER DEFAULT 0,
            is_passed INTEGER DEFAULT 0
        )
        """)

        # 9. Referrals Table
        await db.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id INTEGER NOT NULL,
            referred_id INTEGER UNIQUE NOT NULL,
            reward_granted INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # 10. Movie Requests Table (Buyurtmalar)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS movie_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL,
            user_name TEXT,
            movie_title TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            admin_note TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # 11. Movie Ratings Table (5-yulduzli baholash)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS movie_ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_id INTEGER NOT NULL,
            telegram_id INTEGER NOT NULL,
            stars INTEGER NOT NULL CHECK(stars >= 1 AND stars <= 5),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(movie_id, telegram_id)
        )
        """)

        # 12. User Favorites (Sevimlilar ro'yxati)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS user_favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            movie_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, movie_id)
        )
        """)
        await db.execute("CREATE INDEX IF NOT EXISTS idx_fav_user ON user_favorites(user_id)")
        
        # Insert Default Settings if not exist
        for k, v in DEFAULT_SETTINGS.items():
            await db.execute(
                "INSERT OR IGNORE INTO bot_settings (key, value) VALUES (?, ?)",
                (k, v)
            )
        
        await db.commit()
    logger.info("Database initialized successfully.")


# ===================== DYNAMIC SETTINGS =====================

async def get_setting(key: str, default: str = "") -> str:
    """Retrieve dynamic setting value by key."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT value FROM bot_settings WHERE key = ?", (key,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return row[0]
            return default


async def set_setting(key: str, value: str):
    """Set dynamic setting value by key."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO bot_settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value)
        )
        await db.commit()


async def get_all_settings() -> Dict[str, str]:
    """Retrieve all dynamic settings as a dictionary."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT key, value FROM bot_settings") as cursor:
            rows = await cursor.fetchall()
            return {row["key"]: row["value"] for row in rows}


async def get_web_app_url() -> str:
    """Retrieve real-time Telegram Mini App URL from database or .env."""
    url = await get_setting("web_app_url", "")
    if not url:
        from dotenv import dotenv_values
        from config import BASE_DIR
        try:
            env_vals = dotenv_values(BASE_DIR / ".env")
            url = env_vals.get("WEB_APP_URL", "")
        except Exception:
            pass
    if not url:
        from config import settings
        url = settings.WEB_APP_URL

    if url and not url.endswith("/app"):
        url = f"{url}/app"
    return url or "http://localhost:8080/app"


# ===================== USERS =====================

async def get_or_create_user(telegram_id: int, username: Optional[str], first_name: Optional[str]) -> Dict[str, Any]:
    """Get existing user or register a new one."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    role = 'superadmin' if telegram_id in settings.ADMIN_IDS else 'user'
    
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)) as cursor:
            user = await cursor.fetchone()
            
        if user:
            # Update last active and reset daily downloads if new day
            daily_downloads = user["daily_downloads"]
            if user["last_download_date"] != today_str:
                daily_downloads = 0
                
            await db.execute(
                """UPDATE users SET 
                   username = ?, first_name = ?, last_active = CURRENT_TIMESTAMP, 
                   daily_downloads = ?, last_download_date = ?
                   WHERE telegram_id = ?""",
                (username, first_name, daily_downloads, today_str, telegram_id)
            )
            await db.commit()
            
            # Fetch updated
            async with db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)) as cursor:
                return dict(await cursor.fetchone())
        else:
            await db.execute(
                """INSERT INTO users 
                   (telegram_id, username, first_name, role, daily_downloads, last_download_date) 
                   VALUES (?, ?, ?, ?, 0, ?)""",
                (telegram_id, username, first_name, role, today_str)
            )
            await db.commit()
            async with db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)) as cursor:
                return dict(await cursor.fetchone())


async def get_user(telegram_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve user details."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def set_user_vip(telegram_id: int, days: int) -> bool:
    """Grant or extend VIP membership."""
    expire_at = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET is_vip = 1, vip_until = ? WHERE telegram_id = ?",
            (expire_at, telegram_id)
        )
        await db.commit()
    return True


async def check_user_vip_status(user: Dict[str, Any]) -> bool:
    """Check if user VIP is currently active and not expired."""
    if not user.get("is_vip"):
        return False
    vip_until = user.get("vip_until")
    if not vip_until:
        return True  # Lifetime VIP
    try:
        expire_dt = datetime.strptime(vip_until, "%Y-%m-%d %H:%M:%S")
        if datetime.now() <= expire_dt:
            return True
        else:
            # Expired: revoke VIP status
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute("UPDATE users SET is_vip = 0 WHERE telegram_id = ?", (user["telegram_id"],))
                await db.commit()
            return False
    except Exception:
        return False


async def increment_user_downloads(telegram_id: int):
    """Increment user's daily download counter."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET daily_downloads = daily_downloads + 1 WHERE telegram_id = ?",
            (telegram_id,)
        )
        await db.commit()


# ===================== CHANNELS (MANDATORY SUB) =====================

async def add_channel(
    title: str, 
    invite_link: str, 
    channel_id: Optional[str] = None, 
    username: Optional[str] = None,
    button_text: str = "➕ Obuna bo''lish",
    timer_seconds: int = 0,
    is_join_request: int = 0,
    priority: int = 1,
    is_active: int = 1
) -> int:
    """Add new channel for mandatory subscription."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO channels 
               (title, channel_id, username, invite_link, button_text, timer_seconds, is_join_request, priority, is_active)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (title, channel_id, username, invite_link, button_text, timer_seconds, is_join_request, priority, is_active)
        )
        await db.commit()
        return cursor.lastrowid


async def get_active_channels() -> List[Dict[str, Any]]:
    """Get all active mandatory subscription channels ordered by priority."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM channels WHERE is_active = 1 ORDER BY priority ASC, id ASC"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_all_channels() -> List[Dict[str, Any]]:
    """Get all channels including inactive ones."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM channels ORDER BY id DESC") as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_channel_by_id(channel_db_id: int) -> Optional[Dict[str, Any]]:
    """Get a single channel by DB ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM channels WHERE id = ?", (channel_db_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def update_channel(channel_db_id: int, **kwargs) -> bool:
    """Update channel fields dynamically."""
    if not kwargs:
        return False
    keys = list(kwargs.keys())
    values = list(kwargs.values())
    set_clause = ", ".join([f"{k} = ?" for k in keys])
    values.append(channel_db_id)
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE channels SET {set_clause} WHERE id = ?", values)
        await db.commit()
    return True


async def delete_channel(channel_db_id: int) -> bool:
    """Delete a mandatory channel."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM channels WHERE id = ?", (channel_db_id,))
        await db.commit()
    return True


async def toggle_channel_status(channel_db_id: int) -> int:
    """Toggle channel active status (1 <-> 0)."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE channels SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END WHERE id = ?",
            (channel_db_id,)
        )
        await db.commit()
        async with db.execute("SELECT is_active FROM channels WHERE id = ?", (channel_db_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


async def increment_channel_click(channel_db_id: int):
    """Increment click count for channel link."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE channels SET clicks_count = clicks_count + 1 WHERE id = ?", (channel_db_id,))
        await db.commit()


# ===================== MOVIES =====================

async def add_movie(data: Dict[str, Any]) -> int:
    """Add a new movie to catalog."""
    fields = [
        "code", "title", "original_title", "year", "country", "genres", 
        "language", "duration", "age_rating", "rating", "quality_480_file_id", 
        "quality_720_file_id", "quality_1080_file_id", "poster_file_id", 
        "trailer_url", "description", "is_vip_only", "is_series"
    ]
    vals = [data.get(f) for f in fields]
    placeholders = ", ".join(["?"] * len(fields))
    col_names = ", ".join(fields)
    
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            f"INSERT INTO movies ({col_names}) VALUES ({placeholders})",
            vals
        )
        await db.commit()
        return cursor.lastrowid


async def get_movie_by_code(code: str) -> Optional[Dict[str, Any]]:
    """Find movie by code (case-insensitive)."""
    code_clean = str(code).strip().upper()
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM movies WHERE UPPER(code) = ? AND is_active = 1", 
            (code_clean,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_movie_by_id(movie_id: int) -> Optional[Dict[str, Any]]:
    """Find movie by internal ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM movies WHERE id = ?", (movie_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def search_movies(query: str, limit: int = 15) -> List[Dict[str, Any]]:
    """Fuzzy search movies by title, original title or genres."""
    search_pattern = f"%{query.strip()}%"
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT * FROM movies 
               WHERE (title LIKE ? OR original_title LIKE ? OR genres LIKE ? OR code LIKE ?)
               AND is_active = 1
               ORDER BY views_count DESC LIMIT ?""",
            (search_pattern, search_pattern, search_pattern, search_pattern, limit)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_movies_by_genre(genre: str, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
    """Get movies filtered by genre with pagination."""
    search_pattern = f"%{genre.strip()}%"
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM movies WHERE genres LIKE ? AND is_active = 1 ORDER BY id DESC LIMIT ? OFFSET ?",
            (search_pattern, limit, offset)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_top_movies(limit: int = 10) -> List[Dict[str, Any]]:
    """Get top movies by views / downloads."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM movies WHERE is_active = 1 ORDER BY views_count DESC, downloads_count DESC LIMIT ?",
            (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_random_movie() -> Optional[Dict[str, Any]]:
    """Get a random movie for discovery."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM movies WHERE is_active = 1 ORDER BY RANDOM() LIMIT 1"
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_all_movies(limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    """Get paginated list of all movies."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM movies ORDER BY id DESC LIMIT ? OFFSET ?",
            (limit, offset)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def update_movie(movie_id: int, **kwargs) -> bool:
    """Update movie details."""
    if not kwargs:
        return False
    keys = list(kwargs.keys())
    values = list(kwargs.values())
    set_clause = ", ".join([f"{k} = ?" for k in keys])
    values.append(movie_id)
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE movies SET {set_clause} WHERE id = ?", values)
        await db.commit()
    return True


async def delete_movie(movie_id: int) -> bool:
    """Delete movie."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM movies WHERE id = ?", (movie_id,))
        await db.commit()
    return True


async def increment_movie_stats(movie_id: int, views: int = 1, downloads: int = 0):
    """Increment movie views or downloads count."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """UPDATE movies SET 
               views_count = views_count + ?, 
               downloads_count = downloads_count + ? 
               WHERE id = ?""",
            (views, downloads, movie_id)
        )
        await db.commit()


# ===================== EPISODES (SERIES) =====================

async def add_episode(movie_id: int, episode_number: int, file_id: str, episode_title: str = "", season_number: int = 1, quality: str = "720p") -> int:
    """Add episode to series."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO movie_episodes 
               (movie_id, season_number, episode_number, episode_title, file_id, quality)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (movie_id, season_number, episode_number, episode_title, file_id, quality)
        )
        await db.commit()
        return cursor.lastrowid

add_movie_episode = add_episode


async def get_episodes_by_movie(movie_id: int) -> List[Dict[str, Any]]:
    """Get all episodes of a series ordered by season and episode."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM movie_episodes WHERE movie_id = ? ORDER BY season_number ASC, episode_number ASC",
            (movie_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_movie_seasons(movie_id: int) -> List[int]:
    """Get unique sorted season numbers for a series."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT DISTINCT season_number FROM movie_episodes WHERE movie_id = ? ORDER BY season_number ASC",
            (movie_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [r[0] for r in rows] if rows else [1]


async def get_episodes_by_season(movie_id: int, season_number: int = 1) -> List[Dict[str, Any]]:
    """Get episodes of a specific season."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM movie_episodes WHERE movie_id = ? AND season_number = ? ORDER BY episode_number ASC",
            (movie_id, season_number)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_episode_by_id(episode_id: int) -> Optional[Dict[str, Any]]:
    """Get a single episode by its ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM movie_episodes WHERE id = ?", (episode_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_adjacent_episodes(movie_id: int, season_number: int, episode_number: int) -> tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Get previous and next episode in the same season."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT * FROM movie_episodes 
               WHERE movie_id = ? AND season_number = ? AND episode_number < ? 
               ORDER BY episode_number DESC LIMIT 1""",
            (movie_id, season_number, episode_number)
        ) as cursor:
            prev_row = await cursor.fetchone()

        async with db.execute(
            """SELECT * FROM movie_episodes 
               WHERE movie_id = ? AND season_number = ? AND episode_number > ? 
               ORDER BY episode_number ASC LIMIT 1""",
            (movie_id, season_number, episode_number)
        ) as cursor:
            next_row = await cursor.fetchone()

        return dict(prev_row) if prev_row else None, dict(next_row) if next_row else None


async def get_movies_by_year_range(start_year: int, end_year: int, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
    """Get movies released within a year range (inclusive) with pagination."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT * FROM movies 
               WHERE year >= ? AND year <= ? AND is_active = 1 
               ORDER BY year DESC, rating DESC, id DESC 
               LIMIT ? OFFSET ?""",
            (start_year, end_year, limit, offset)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


# ===================== PROMOCODES =====================

async def create_promocode(code: str, duration_days: int = 30, max_uses: int = 1) -> int:
    """Create a new VIP promo code."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO promocodes (code, duration_days, max_uses) VALUES (?, ?, ?)",
            (code.strip().upper(), duration_days, max_uses)
        )
        await db.commit()
        return cursor.lastrowid


async def redeem_promocode(code: str, telegram_id: int) -> tuple[bool, str]:
    """Redeem promo code for user."""
    code_clean = code.strip().upper()
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM promocodes WHERE code = ? AND is_active = 1", (code_clean,)
        ) as cursor:
            promo = await cursor.fetchone()
            
        if not promo:
            return False, "❌ Bunday promokod mavjud emas yoki muddati tugagan."
            
        if promo["used_count"] >= promo["max_uses"]:
            return False, "⚠️ Bu promokoddan foydalanish limiti tugagan!"
            
        # Update promo usage
        await db.execute(
            "UPDATE promocodes SET used_count = used_count + 1 WHERE id = ?", 
            (promo["id"],)
        )
        await db.commit()
        
    # Grant VIP
    await set_user_vip(telegram_id, promo["duration_days"])
    return True, f"🎉 Tabriklaymiz! Sizga {promo['duration_days']} kunlik VIP status taqdim etildi."


# ===================== ANALYTICS & STATS =====================

async def log_search(telegram_id: int, query: str, results_count: int):
    """Log user search query."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO search_logs (telegram_id, query, results_count) VALUES (?, ?, ?)",
            (telegram_id, query[:100], results_count)
        )
        await db.commit()


async def get_system_stats() -> Dict[str, Any]:
    """Get system overview metrics."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as c:
            total_users = (await c.fetchone())[0]
            
        async with db.execute("SELECT COUNT(*) FROM users WHERE is_vip = 1") as c:
            vip_users = (await c.fetchone())[0]
            
        async with db.execute("SELECT COUNT(*) FROM movies WHERE is_active = 1") as c:
            total_movies = (await c.fetchone())[0]
            
        async with db.execute("SELECT COUNT(*) FROM channels WHERE is_active = 1") as c:
            active_channels = (await c.fetchone())[0]
            
        async with db.execute("SELECT SUM(views_count), SUM(downloads_count) FROM movies") as c:
            row = await c.fetchone()
            total_views = row[0] or 0
            total_downloads = row[1] or 0
            
        # Users active in last 24h
        yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        async with db.execute("SELECT COUNT(*) FROM users WHERE last_active >= ?", (yesterday_str,)) as c:
            active_24h = (await c.fetchone())[0]

        return {
            "total_users": total_users,
            "vip_users": vip_users,
            "total_movies": total_movies,
            "active_channels": active_channels,
            "total_views": total_views,
            "total_downloads": total_downloads,
            "active_24h": active_24h
        }


# ===================== REFERRALS SYSTEM =====================

async def add_referral(referrer_id: int, referred_id: int) -> tuple[bool, str]:
    """Register referral relationship and grant rewards dynamically."""
    if referrer_id == referred_id:
        return False, "O'zingizni taklif qila olmaysiz."

    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute(
                "INSERT INTO referrals (referrer_id, referred_id) VALUES (?, ?)",
                (referrer_id, referred_id)
            )
            await db.commit()
        except aiosqlite.IntegrityError:
            # Already referred
            return False, "Foydalanuvchi allaqachon botdan ro'yxatdan o'tgan."

        # Fetch total referrals of referrer
        async with db.execute(
            "SELECT COUNT(*) FROM referrals WHERE referrer_id = ?", (referrer_id,)
        ) as cursor:
            count = (await cursor.fetchone())[0]

    # Check dynamic VIP reward thresholds
    friends_for_vip = int(await get_setting("referral_friends_for_vip", "5"))
    vip_days = int(await get_setting("referral_reward_vip_days", "7"))
    
    if count % friends_for_vip == 0 and friends_for_vip > 0:
        await set_user_vip(referrer_id, vip_days)
        return True, f"🎉 Siz {count} ta do'stingizni taklif qildingiz va sizga {vip_days} kunlik bepul VIP status berildi!"

    # Download limit bonus
    bonus_downloads = int(await get_setting("referral_reward_downloads", "3"))
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET daily_downloads = MAX(0, daily_downloads - ?) WHERE telegram_id = ?",
            (bonus_downloads, referrer_id)
        )
        await db.commit()

    return True, f"Do'stingiz qo'shildi! Sizga +{bonus_downloads} ta bepul yuklash balansi berildi."


async def get_user_referrals_count(telegram_id: int) -> int:
    """Get count of invited friends by user."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM referrals WHERE referrer_id = ?", (telegram_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


async def get_top_referrers(limit: int = 10) -> List[Dict[str, Any]]:
    """Get top referrers leaderboard."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT u.telegram_id, u.first_name, u.username, COUNT(r.id) as ref_count
               FROM referrals r
               JOIN users u ON r.referrer_id = u.telegram_id
               GROUP BY r.referrer_id
               ORDER BY ref_count DESC
               LIMIT ?""",
            (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


# ===================== MOVIE REQUESTS =====================

async def create_movie_request(telegram_id: int, user_name: str, movie_title: str) -> int:
    """Submit a request for an unlisted movie."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO movie_requests (telegram_id, user_name, movie_title) VALUES (?, ?, ?)",
            (telegram_id, user_name, movie_title.strip())
        )
        await db.commit()
        return cursor.lastrowid


async def get_all_movie_requests(status_filter: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve movie requests."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if status_filter:
            query = "SELECT * FROM movie_requests WHERE status = ? ORDER BY id DESC LIMIT ?"
            params = (status_filter, limit)
        else:
            query = "SELECT * FROM movie_requests ORDER BY id DESC LIMIT ?"
            params = (limit,)
            
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_movie_request_by_id(req_id: int) -> Optional[Dict[str, Any]]:
    """Get single movie request."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM movie_requests WHERE id = ?", (req_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def update_movie_request_status(req_id: int, status: str, admin_note: str = "") -> bool:
    """Update movie request status (pending, completed, rejected)."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE movie_requests SET status = ?, admin_note = ? WHERE id = ?",
            (status, admin_note, req_id)
        )
        await db.commit()
    return True


# ===================== MOVIE RATINGS =====================

async def rate_movie(movie_id: int, telegram_id: int, stars: int) -> float:
    """Submit or update user rating (1-5 stars) and recalculate movie average rating."""
    clamped_stars = max(1, min(5, stars))
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO movie_ratings (movie_id, telegram_id, stars)
               VALUES (?, ?, ?)
               ON CONFLICT(movie_id, telegram_id) DO UPDATE SET stars = excluded.stars""",
            (movie_id, telegram_id, clamped_stars)
        )
        # Recalculate average rating (scaled to 10 for IMDb scale)
        async with db.execute(
            "SELECT AVG(stars), COUNT(id) FROM movie_ratings WHERE movie_id = ?",
            (movie_id,)
        ) as cursor:
            row = await cursor.fetchone()
            avg_stars = row[0] or 4.0
            count = row[1] or 1
            scaled_rating = round(avg_stars * 2, 1)  # 5 stars -> 10 scale
            
        await db.execute(
            "UPDATE movies SET rating = ?, likes_count = likes_count + 1 WHERE id = ?",
            (scaled_rating, movie_id)
        )
        await db.commit()
        return scaled_rating


async def get_movie_rating_stats(movie_id: int) -> Dict[str, Any]:
    """Get rating summary for a movie."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT AVG(stars), COUNT(id) FROM movie_ratings WHERE movie_id = ?", (movie_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return {
                "avg_stars": round(row[0], 1) if row[0] else 0,
                "total_ratings": row[1] or 0
            }


# ===================== USER FAVORITES (SEVIMLILAR) =====================

async def add_favorite(user_id: int, movie_id: int) -> bool:
    """Add a movie to user's favorites."""
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute(
                "INSERT OR IGNORE INTO user_favorites (user_id, movie_id) VALUES (?, ?)",
                (user_id, movie_id)
            )
            await db.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding favorite: {e}")
            return False


async def remove_favorite(user_id: int, movie_id: int) -> bool:
    """Remove a movie from user's favorites."""
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute(
                "DELETE FROM user_favorites WHERE user_id = ? AND movie_id = ?",
                (user_id, movie_id)
            )
            await db.commit()
            return True
        except Exception as e:
            logger.error(f"Error removing favorite: {e}")
            return False


async def toggle_favorite(user_id: int, movie_id: int) -> bool:
    """Toggle movie favorite state. Returns True if now favored, False if removed."""
    favored = await is_favorite(user_id, movie_id)
    if favored:
        await remove_favorite(user_id, movie_id)
        return False
    else:
        await add_favorite(user_id, movie_id)
        return True


async def is_favorite(user_id: int, movie_id: int) -> bool:
    """Check if movie is favored by user."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id FROM user_favorites WHERE user_id = ? AND movie_id = ?",
            (user_id, movie_id)
        ) as cursor:
            row = await cursor.fetchone()
            return row is not None


async def get_user_favorites(user_id: int, limit: int = 30) -> List[Dict[str, Any]]:
    """Get all favorite movies of a user with full details."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = """
        SELECT m.* FROM movies m
        JOIN user_favorites f ON m.id = f.movie_id
        WHERE f.user_id = ?
        ORDER BY f.created_at DESC
        LIMIT ?
        """
        async with db.execute(query, (user_id, limit)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


