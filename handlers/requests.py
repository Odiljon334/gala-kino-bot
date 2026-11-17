"""
Movie request and order system for Kinochi Bot Pro.
Allows users to request movies not yet in catalog, notifying admins and updating users.
"""
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import settings
from database import (
    create_movie_request,
    get_all_movie_requests,
    get_movie_request_by_id,
    update_movie_request_status,
    get_setting
)

logger = logging.getLogger(__name__)
requests_router = Router(name="requests")


class MovieOrderFSM(StatesGroup):
    title = State()


@requests_router.message(F.text == "📥 Kino buyurtma qilish")
async def btn_order_movie(message: Message, state: FSMContext):
    """Start movie order flow from main keyboard."""
    await state.set_state(MovieOrderFSM.title)
    text = await get_setting("movie_request_text")
    await message.answer(
        f"{text}\n\n<i>Qidirgan kino nomini yozib yuboring (bekor qilish uchun /cancel):</i>"
    )


@requests_router.callback_query(F.data.startswith("req_movie:"))
async def cb_order_movie_from_search(callback: CallbackQuery, state: FSMContext):
    """Triggered when movie not found in search."""
    suggested = callback.data.split(":", 1)[1]
    if suggested and suggested != "none":
        # Direct submission with suggested title
        req_id = await create_movie_request(
            telegram_id=callback.from_user.id,
            user_name=callback.from_user.first_name,
            movie_title=suggested
        )
        await notify_admins_new_request(callback.bot, req_id, callback.from_user.id, callback.from_user.first_name, suggested)
        await callback.message.answer(
            f"✅ <b>'{suggested}'</b> bo'yicha buyurtmangiz qabul qilindi!\n"
            "Adminlarimiz kinoni tez orada botga joylashadi.",
            show_alert=True
        )
        await callback.answer()
        return

    await state.set_state(MovieOrderFSM.title)
    await callback.message.answer("📥 Qidirgan kino nomini yozib yuboring:")
    await callback.answer()


@requests_router.message(MovieOrderFSM.title)
async def fsm_order_title_received(message: Message, state: FSMContext, bot: Bot):
    """Process requested movie title and inform user and admins."""
    movie_title = message.text.strip()
    await state.clear()
    
    user_id = message.from_user.id
    user_name = message.from_user.first_name or "Foydalanuvchi"
    
    req_id = await create_movie_request(
        telegram_id=user_id,
        user_name=user_name,
        movie_title=movie_title
    )
    
    await notify_admins_new_request(bot, req_id, user_id, user_name, movie_title)
    
    await message.answer(
        "✅ <b>Buyurtmangiz adminga muvaffaqiyatli yetkazildi!</b>\n\n"
        f"🎬 Kino: <b>{movie_title}</b>\n\n"
        "Tez orada ushbu kino botga qo'shiladi va sizga bu haqda avtomatik xabar beriladi. Rahmat!"
    )


async def notify_admins_new_request(bot: Bot, req_id: int, user_id: int, user_name: str, movie_title: str):
    """Send interactive alert to admins with 1-click notification button."""
    text = (
        "📥 <b>YANGI KINO BUYURTMASI!</b>\n\n"
        f"🆔 Buyurtma #{req_id}\n"
        f"👤 Foydalanuvchi: <b>{user_name}</b> (<code>{user_id}</code>)\n"
        f"🎬 So'ralgan kino: <b>{movie_title}</b>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Qo'shildi deb xabar yuborish", 
                callback_data=f"order_done:{req_id}:{user_id}"
            )
        ]
    ])
    for admin_id in settings.ADMIN_IDS:
        try:
            await bot.send_message(chat_id=admin_id, text=text, reply_markup=kb)
        except Exception as e:
            logger.warning(f"Could not notify admin {admin_id}: {e}")


@requests_router.callback_query(F.data.startswith("order_done:"))
async def cb_order_done(callback: CallbackQuery, bot: Bot):
    """Admin marks request as completed and alerts user."""
    parts = callback.data.split(":")
    req_id = int(parts[1])
    target_user_id = int(parts[2])
    
    req = await get_movie_request_by_id(req_id)
    movie_title = req["movie_title"] if req else "Siz buyurtma qilgan kino"
    
    await update_movie_request_status(req_id, "completed", "Qo'shildi")
    
    # Notify User
    try:
        await bot.send_message(
            chat_id=target_user_id,
            text=(
                f"🎉 <b>XUSHXABAR!</b>\n\n"
                f"Siz buyurtma qilgan <b>'{movie_title}'</b> kinosi botimizga qo'shildi!\n\n"
                "Endi botdan qidirib tomosha qilishingiz mumkin. Maroqli tomosha tilaymiz! 🍿"
            )
        )
        user_alerted = "Foydalanuvchiga xabar yuborildi."
    except Exception as e:
        user_alerted = f"Foydalanuvchiga xabar yuborilmadi ({e})."

    await callback.message.edit_text(
        f"{callback.message.text}\n\n✅ <b>BAJARILDI!</b> {user_alerted}"
    )
    await callback.answer("Buyurtma bajarildi deb belgilandi!", show_alert=True)
