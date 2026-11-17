"""
Dynamic mandatory subscription and countdown timer engine.
Handles Telegram channel membership verification, countdown timers, and join-requests.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ChatMemberStatus
import aiosqlite

from database import (
    DB_PATH, 
    get_active_channels, 
    get_setting, 
    check_user_vip_status, 
    increment_channel_click
)

logger = logging.getLogger(__name__)


async def get_or_create_timer_session(telegram_id: int, channel_id: int, timer_seconds: int) -> int:
    """
    Returns remaining timer seconds for a user on a timed sponsor channel.
    If timer has expired, returns 0.
    """
    if timer_seconds <= 0:
        return 0
        
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM user_timer_sessions WHERE telegram_id = ? AND channel_id = ?",
            (telegram_id, channel_id)
        ) as cursor:
            session = await cursor.fetchone()
            
        now = datetime.now()
        if session:
            # Check elapsed time
            start_time = datetime.strptime(session["timer_start"], "%Y-%m-%d %H:%M:%S")
            elapsed = int((now - start_time).total_seconds())
            remaining = max(0, timer_seconds - elapsed)
            return remaining
        else:
            # Create new session
            now_str = now.strftime("%Y-%m-%d %H:%M:%S")
            await db.execute(
                """INSERT INTO user_timer_sessions (telegram_id, channel_id, timer_start, timer_seconds)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(telegram_id) DO UPDATE SET 
                   channel_id = excluded.channel_id,
                   timer_start = excluded.timer_start,
                   timer_seconds = excluded.timer_seconds""",
                (telegram_id, channel_id, now_str, timer_seconds)
            )
            await db.commit()
            return timer_seconds


async def check_channel_member(bot: Bot, channel: Dict[str, Any], telegram_id: int) -> bool:
    """
    Check if user is a member of the specific channel.
    Supports chat_id, @username, or fallback to timer.
    """
    channel_identifier = channel.get("channel_id") or channel.get("username")
    
    # If no channel identifier is provided or channel is external sponsor link
    if not channel_identifier:
        # If external link with timer, timer controls unlock
        timer_seconds = channel.get("timer_seconds", 0)
        if timer_seconds > 0:
            remaining = await get_or_create_timer_session(telegram_id, channel["id"], timer_seconds)
            return remaining == 0
        return True

    # Normalize username
    if isinstance(channel_identifier, str) and not channel_identifier.startswith("-") and not channel_identifier.startswith("@"):
        channel_identifier = f"@{channel_identifier}"

    try:
        member = await bot.get_chat_member(chat_id=channel_identifier, user_id=telegram_id)
        if member.status in [
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.CREATOR,
            ChatMemberStatus.RESTRICTED
        ]:
            return True
        return False
    except Exception as e:
        logger.warning(f"Could not check membership in channel {channel_identifier}: {e}")
        # If bot is not admin in channel, check timer fallback
        timer_seconds = channel.get("timer_seconds", 0)
        if timer_seconds > 0:
            remaining = await get_or_create_timer_session(telegram_id, channel["id"], timer_seconds)
            return remaining == 0
        # If no timer and bot cannot verify, do not permanently block user
        return True


async def check_all_subscriptions(
    bot: Bot, 
    telegram_id: int, 
    user: Optional[Dict[str, Any]] = None
) -> Tuple[bool, List[Dict[str, Any]], int]:
    """
    Check all mandatory channels for user.
    Returns:
      (is_subscribed: bool, unsubscribed_channels: list, min_timer_remaining: int)
    """
    # 1. VIP users and Admins bypass forced subscription
    if user:
        if user.get("role") in ["admin", "superadmin"]:
            return True, [], 0
        is_vip = await check_user_vip_status(user)
        if is_vip:
            return True, [], 0

    # 2. Check global setting
    force_sub_mode = await get_setting("force_sub_mode", "strict")
    if force_sub_mode == "disabled":
        return True, [], 0

    # 3. Retrieve active channels
    channels = await get_active_channels()
    if not channels:
        return True, [], 0

    unsubscribed = []
    min_timer = 999999
    has_timer = False

    for ch in channels:
        timer_seconds = ch.get("timer_seconds", 0)
        
        # If channel has a timer
        if timer_seconds > 0:
            remaining = await get_or_create_timer_session(telegram_id, ch["id"], timer_seconds)
            if remaining > 0:
                has_timer = True
                min_timer = min(min_timer, remaining)
                # Channel is still locked by timer, check if user joined early
                is_sub = await check_channel_member(bot, ch, telegram_id)
                if not is_sub:
                    ch_copy = dict(ch)
                    ch_copy["remaining_seconds"] = remaining
                    unsubscribed.append(ch_copy)
            else:
                # Timer elapsed: unlocked!
                pass
        else:
            # Immediate mandatory subscription
            is_sub = await check_channel_member(bot, ch, telegram_id)
            if not is_sub:
                unsubscribed.append(ch)

    is_passed = len(unsubscribed) == 0
    remaining_ret = min_timer if has_timer and min_timer != 999999 else 0
    return is_passed, unsubscribed, remaining_ret


def build_subscription_keyboard(
    channels: List[Dict[str, Any]], 
    target_code: str = "", 
    remaining_seconds: int = 0
) -> InlineKeyboardMarkup:
    """Build dynamic inline buttons for unsubscribed channels and timer."""
    keyboard_buttons = []
    
    for idx, ch in enumerate(channels, 1):
        btn_text = ch.get("button_text") or f"➕ {idx}-Kanalga a'zo bo'lish"
        link = ch.get("invite_link", "https://t.me")
        
        # Optional timer badge on button if timed
        rem = ch.get("remaining_seconds", 0)
        if rem > 0:
            btn_text = f"{btn_text} (⏱ {rem}s)"
            
        keyboard_buttons.append([
            InlineKeyboardButton(text=btn_text, url=link)
        ])
        
    # Timer button if countdown is active
    if remaining_seconds > 0:
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"⏳ Taymer: {remaining_seconds} soniya qoldi", 
                callback_data=f"refresh_sub:{target_code}"
            )
        ])
        
    # Check button
    callback_payload = f"check_sub:{target_code}" if target_code else "check_sub:none"
    keyboard_buttons.append([
        InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data=callback_payload)
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
