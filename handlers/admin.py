"""
Telegram Native Admin Panel for Kinochi Bot Pro.
Full FSM-based management for channels, timers, movies, dynamic settings, broadcasts and backups.
Zero code modification required.
"""
import os
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import settings
from database import (
    get_user,
    get_all_settings,
    set_setting,
    get_setting,
    get_all_channels,
    add_channel,
    delete_channel,
    toggle_channel_status,
    update_channel,
    add_movie,
    get_movie_by_code,
    get_movie_by_id,
    update_movie,
    delete_movie,
    add_episode,
    get_system_stats,
    create_promocode,
    set_user_vip,
    DB_PATH
)
from services.broadcaster import broadcast_message
from services.autopost import auto_post_movie_to_channel

logger = logging.getLogger(__name__)
admin_router = Router(name="admin")


# ===================== FSM STATES =====================

class AddChannelFSM(StatesGroup):
    link = State()
    channel_id = State()
    timer = State()
    button_text = State()

class AddMovieFSM(StatesGroup):
    code = State()
    title = State()
    year = State()
    country = State()
    genres = State()
    video = State()
    poster = State()
    description = State()

class EditSettingFSM(StatesGroup):
    setting_key = State()
    new_value = State()

class BroadcastFSM(StatesGroup):
    message_content = State()
    confirm = State()

class CreatePromoFSM(StatesGroup):
    code = State()
    days = State()
    max_uses = State()

class GrantVipFSM(StatesGroup):
    user_id = State()
    days = State()

class FindMovieEditFSM(StatesGroup):
    code = State()

class AddEpisodeFSM(StatesGroup):
    movie_id = State()
    season = State()
    episode = State()
    file = State()
    title = State()

class SetTrailerFSM(StatesGroup):
    movie_id = State()
    trailer_url = State()


# ===================== HELPER CHECKER =====================

async def is_admin(user_id: int) -> bool:
    if user_id in settings.ADMIN_IDS:
        return True
    user = await get_user(user_id)
    return user and user.get("role") in ["admin", "superadmin"]


# ===================== KEYBOARD BUILDERS =====================

def get_admin_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📢 Majburiy Obuna & Taymerlar", callback_data="admin_channels"),
            InlineKeyboardButton(text="🎬 Kinolar Boshqaruvi", callback_data="admin_movies")
        ],
        [
            InlineKeyboardButton(text="📊 Jonli Statistika", callback_data="admin_stats"),
            InlineKeyboardButton(text="⚙️ Dinamik Sozlamalar", callback_data="admin_settings")
        ],
        [
            InlineKeyboardButton(text="✉️ Xabarnoma (Broadcast)", callback_data="admin_broadcast"),
            InlineKeyboardButton(text="💎 VIP & Promokodlar", callback_data="admin_vip")
        ],
        [
            InlineKeyboardButton(text="💾 Baza Zaxirasi (.db)", callback_data="admin_backup"),
            InlineKeyboardButton(text="🌐 Web Dashboard", callback_data="admin_web_info")
        ]
    ])


# ===================== ENTRY POINT =====================

@admin_router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    """Open main admin dashboard."""
    await state.clear()
    if not await is_admin(message.from_user.id):
        return  # Silently ignore non-admins
        
    text = (
        "👑 <b>GALA KINO — BOSHQARUV PANELI</b>\n\n"
        "Barcha sozlamalar to'liq dinamik. Kodga tegmasdan quyidagi bo'limlar orqali "
        "majburiy obunalar, taymerlar, kinolar va bot sozlamalarini boshqaring."
    )
    await message.answer(text, reply_markup=get_admin_main_kb())


@admin_router.callback_query(F.data == "admin_menu")
async def cb_admin_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    if not await is_admin(callback.from_user.id):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return
        
    text = (
        "👑 <b>GALA KINO — BOSHQARUV PANELI</b>\n\n"
        "Kerakli bo'limni tanlang:"
    )
    await callback.message.edit_text(text, reply_markup=get_admin_main_kb())


# ===================== STATS =====================

@admin_router.callback_query(F.data == "admin_stats")
async def cb_admin_stats(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return
        
    stats = await get_system_stats()
    text = (
        "📊 <b>BOTNING JONLI STATISTIKASI:</b>\n\n"
        f"👥 <b>Jami foydalanuvchilar:</b> {stats['total_users']} ta\n"
        f"⚡️ <b>24 soatda faol:</b> {stats['active_24h']} ta\n"
        f"💎 <b>VIP a'zolar:</b> {stats['vip_users']} ta\n\n"
        f"🎬 <b>Jami kinolar:</b> {stats['total_movies']} ta\n"
        f"👁 <b>Jami ko'rishlar:</b> {stats['total_views']} marta\n"
        f"📥 <b>Jami yuklab olishlar:</b> {stats['total_downloads']} marta\n"
        f"📢 <b>Faol homiy kanallar:</b> {stats['active_channels']} ta"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Yangilash", callback_data="admin_stats")],
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="admin_menu")]
    ])
    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except Exception:
        pass


# ===================== CHANNELS & TIMERS =====================

@admin_router.callback_query(F.data == "admin_channels")
async def cb_admin_channels(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return
        
    channels = await get_all_channels()
    force_sub_mode = await get_setting("force_sub_mode", "strict")
    
    text = (
        "📢 <b>MAJBURIY OBUNA VA TAYMERLAR BOSHQARUVI:</b>\n\n"
        f"⚡️ <b>Joriy rejim:</b> <code>{force_sub_mode.upper()}</code>\n"
        "• <i>STRICT</i>: Kanallarga obuna bo'lmaguncha kino chiqmaydi.\n"
        "• <i>TIMER</i>: Taymer soniyasi bo'yicha bepul ko'rish imkoni beriladi.\n"
        "• <i>DISABLED</i>: Majburiy obuna vaqtincha to'xtatilgan.\n\n"
        f"Ulangan kanallar soni: <b>{len(channels)} ta</b>\n"
    )
    
    kb_rows = []
    # Toggle global mode
    next_mode = "timer" if force_sub_mode == "strict" else ("disabled" if force_sub_mode == "timer" else "strict")
    kb_rows.append([
        InlineKeyboardButton(text=f"🔄 Rejimni almashtirish: {next_mode.upper()}", callback_data=f"set_sub_mode:{next_mode}")
    ])
    
    # Add Channel Button
    kb_rows.append([
        InlineKeyboardButton(text="➕ Yangi Kanal / Havola Qo'shish", callback_data="add_channel_start")
    ])
    
    # List channels
    for ch in channels:
        status_icon = "🟢" if ch["is_active"] else "🔴"
        timer_info = f"⏱ {ch['timer_seconds']}s" if ch["timer_seconds"] > 0 else "Darhol"
        btn_label = f"{status_icon} {ch['title'][:15]} ({timer_info})"
        kb_rows.append([
            InlineKeyboardButton(text=btn_label, callback_data=f"ch_view:{ch['id']}")
        ])
        
    kb_rows.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="admin_menu")])
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows))


@admin_router.callback_query(F.data.startswith("set_sub_mode:"))
async def cb_set_sub_mode(callback: CallbackQuery):
    mode = callback.data.split(":")[1]
    await set_setting("force_sub_mode", mode)
    await callback.answer(f"Majburiy obuna rejimi: {mode.upper()} ga o'zgartirildi!")
    await cb_admin_channels(callback)


@admin_router.callback_query(F.data.startswith("ch_view:"))
async def cb_channel_view(callback: CallbackQuery):
    ch_id = int(callback.data.split(":")[1])
    channels = await get_all_channels()
    target = next((c for c in channels if c["id"] == ch_id), None)
    if not target:
        await callback.answer("Kanal topilmadi!", show_alert=True)
        return
        
    status_str = "🟢 Faol (Aktiv)" if target["is_active"] else "🔴 O'chirilgan (Noaktiv)"
    text = (
        f"📢 <b>KANAL SOZLAMALARI: #{target['id']}</b>\n\n"
        f"📌 <b>Nomi:</b> {target['title']}\n"
        f"🔗 <b>Havola:</b> {target['invite_link']}\n"
        f"🆔 <b>Kanal ID / Username:</b> <code>{target['channel_id'] or target['username'] or 'Yo''q'}</code>\n"
        f"⏱ <b>Taymer:</b> {target['timer_seconds']} soniya (0 = darhol)\n"
        f"🔘 <b>Tugma matni:</b> {target['button_text']}\n"
        f"📊 <b>O'tishlar soni:</b> {target['clicks_count']} marta\n"
        f"💡 <b>Holati:</b> {status_str}"
    )
    
    toggle_text = "🔴 O'chirish" if target["is_active"] else "🟢 Yoqish"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=toggle_text, callback_data=f"ch_toggle:{target['id']}"),
            InlineKeyboardButton(text="🗑 O'chirib tashlash", callback_data=f"ch_delete:{target['id']}")
        ],
        [InlineKeyboardButton(text="◀️ Kanallar ro'yxati", callback_data="admin_channels")]
    ])
    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except Exception:
        pass


@admin_router.callback_query(F.data.startswith("ch_toggle:"))
async def cb_channel_toggle(callback: CallbackQuery):
    ch_id = int(callback.data.split(":")[1])
    await toggle_channel_status(ch_id)
    await callback.answer("Kanal holati o'zgartirildi!")
    await cb_channel_view(callback)


@admin_router.callback_query(F.data.startswith("ch_delete:"))
async def cb_channel_delete(callback: CallbackQuery):
    ch_id = int(callback.data.split(":")[1])
    await delete_channel(ch_id)
    await callback.answer("Kanal muvaffaqiyatli o'chirildi!", show_alert=True)
    await cb_admin_channels(callback)


# --- Add Channel FSM Flow ---

@admin_router.callback_query(F.data == "add_channel_start")
async def cb_add_channel_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddChannelFSM.link)
    text = (
        "➕ <b>MAJBURIY OBUNAGA KANAL QO'SHISH</b>\n\n"
        "1-qadam: Kanalga taklif havolasini (Link) yuboring.\n"
        "Masalan: <code>https://t.me/mening_kanalim</code> yoki <code>https://t.me/+AbCdEfGh</code>\n\n"
        "<i>Bekor qilish uchun /cancel deb yozing.</i>"
    )
    await callback.message.edit_text(text)


@admin_router.message(AddChannelFSM.link)
async def fsm_channel_link(message: Message, state: FSMContext):
    link = message.text.strip()
    if not link.startswith("http") and not link.startswith("t.me"):
        await message.answer("⚠️ Iltimos, to'g'ri havola yuboring (masalan: https://t.me/kanal_nomi):")
        return
        
    await state.update_data(invite_link=link)
    await state.set_state(AddChannelFSM.channel_id)
    await message.answer(
        "2-qadam: Kanal <b>ID</b> sini (masalan: <code>-1001234567890</code>) yoki <b>@username</b> ini yuboring.\n\n"
        "<i>Eslatma: Agar bot kanalga admin qilib qo'shilgan bo'lsa, a'zolikni avtomatik tekshira oladi. "
        "Agar kanal ID si bo'lmasa yoki tashqi link bo'lsa, 'yoq' deb yozing.</i>"
    )


@admin_router.message(AddChannelFSM.channel_id)
async def fsm_channel_id(message: Message, state: FSMContext):
    ch_id_val = message.text.strip()
    channel_id = None if ch_id_val.lower() in ["yoq", "yo'q", "none", "-"] else ch_id_val
    await state.update_data(channel_id=channel_id)
    await state.set_state(AddChannelFSM.timer)
    await message.answer(
        "3-qadam: <b>Taymerni (soniyalarda)</b> kiriting!\n\n"
        "• <code>0</code> — Darhol majburiy obuna (taymersiz)\n"
        "• <code>30</code> — Foydalanuvchiga 30 soniya bepul ko'rish imkoni beriladi yoki 30 soniyalik homiy taymeri qo'yiladi\n"
        "• <code>60</code> — 1 daqiqalik taymer\n\n"
        "Raqam yozing (masalan: 0 yoki 45):"
    )


@admin_router.message(AddChannelFSM.timer)
async def fsm_channel_timer(message: Message, state: FSMContext):
    try:
        timer_seconds = int(message.text.strip())
    except ValueError:
        await message.answer("⚠️ Iltimos, faqat butun son yozing (masalan: 0 yoki 30):")
        return
        
    await state.update_data(timer_seconds=timer_seconds)
    await state.set_state(AddChannelFSM.button_text)
    await message.answer(
        "4-qadam: <b>Kanal nomi yoki Tugma matnini</b> kiriting.\n"
        "Masalan: <code>➕ 1-Kanalga a'zo bo'lish</code> yoki <code>🔥 Premyera Kanal</code>:"
    )


@admin_router.message(AddChannelFSM.button_text)
async def fsm_channel_button_text(message: Message, state: FSMContext):
    btn_text = message.text.strip()
    data = await state.get_data()
    await state.clear()
    
    # Save to database
    channel_db_id = await add_channel(
        title=btn_text,
        invite_link=data["invite_link"],
        channel_id=data["channel_id"],
        button_text=btn_text,
        timer_seconds=data["timer_seconds"],
        is_active=1
    )
    
    text = (
        "✅ <b>Kanal muvaffaqiyatli qo'shildi!</b>\n\n"
        f"📌 Nomi: {btn_text}\n"
        f"🔗 Link: {data['invite_link']}\n"
        f"⏱ Taymer: {data['timer_seconds']} soniya\n\n"
        "Endi ushbu kanal foydalanuvchilar uchun darhol majburiy obunaga qo'shildi. "
        "Dasturni qayta ishga tushirishga hojat yo'q!"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Kanallarga qaytish", callback_data="admin_channels")],
        [InlineKeyboardButton(text="◀️ Boshqaruv paneli", callback_data="admin_menu")]
    ])
    await message.answer(text, reply_markup=kb)


# ===================== MOVIES MANAGEMENT =====================

@admin_router.callback_query(F.data == "admin_movies")
async def cb_admin_movies(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return
        
    stats = await get_system_stats()
    text = (
        "🎬 <b>KINOLAR VA SERIALLAR BOSHQARUVI:</b>\n\n"
        f"Jami kinolar: <b>{stats['total_movies']} ta</b>\n"
        "Barcha yangi kinolar kod, sifat, janr va posterlar bilan dinamik qo'shiladi."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Yangi Kino Qo'shish", callback_data="add_movie_start")],
        [InlineKeyboardButton(text="🔍 Kinoni Tahrirlash / O'chirish", callback_data="find_movie_edit")],
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="admin_menu")]
    ])
    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except Exception:
        pass


@admin_router.callback_query(F.data == "add_movie_start")
async def cb_add_movie_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddMovieFSM.code)
    text = (
        "🎬 <b>YANGI KINO QO'SHISH</b>\n\n"
        "1-qadam: Kino uchun <b>unikal kod</b> yozing (masalan: <code>101</code> yoki <code>AVATAR</code>):"
    )
    await callback.message.edit_text(text)


@admin_router.message(AddMovieFSM.code)
async def fsm_movie_code(message: Message, state: FSMContext):
    code = message.text.strip().upper()
    existing = await get_movie_by_code(code)
    if existing:
        await message.answer(f"⚠️ <b>{code}</b> kodi bilan allaqachon '{existing['title']}' kinogi mavjud! Boshqa kod kiriting:")
        return
        
    await state.update_data(code=code)
    await state.set_state(AddMovieFSM.title)
    await message.answer("2-qadam: Kino <b>nomini</b> yuboring (masalan: <i>Forsaj 10</i>):")


@admin_router.message(AddMovieFSM.title)
async def fsm_movie_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await state.set_state(AddMovieFSM.year)
    await message.answer("3-qadam: Chiqarilgan <b>yilini</b> kiriting (masalan: <code>2023</code>):")


@admin_router.message(AddMovieFSM.year)
async def fsm_movie_year(message: Message, state: FSMContext):
    try:
        year = int(message.text.strip())
    except ValueError:
        year = 2024
    await state.update_data(year=year)
    await state.set_state(AddMovieFSM.genres)
    await message.answer("4-qadam: <b>Janrlari va davlatini</b> kiriting (masalan: <i>Jangari, Sarguzasht | AQSH</i>):")


@admin_router.message(AddMovieFSM.genres)
async def fsm_movie_genres(message: Message, state: FSMContext):
    parts = message.text.strip().split("|")
    genres = parts[0].strip()
    country = parts[1].strip() if len(parts) > 1 else "AQSH"
    await state.update_data(genres=genres, country=country)
    await state.set_state(AddMovieFSM.video)
    await message.answer(
        "5-qadam: <b>Kino videosini</b> shu yerga yuboring (yoki Telegram file_id sini yozing):\n\n"
        "<i>Bot faylni o'z serverida saqlamaydi, Telegramning xavfsiz file_id tizimidan foydalanadi.</i>"
    )


@admin_router.message(AddMovieFSM.video)
async def fsm_movie_video(message: Message, state: FSMContext):
    file_id = None
    if message.video:
        file_id = message.video.file_id
    elif message.document:
        file_id = message.document.file_id
    elif message.text:
        file_id = message.text.strip()
        
    if not file_id:
        await message.answer("⚠️ Iltimos, video fayl yuboring:")
        return
        
    await state.update_data(quality_720_file_id=file_id)
    await state.set_state(AddMovieFSM.description)
    await message.answer("6-qadam: Kino haqida <b>qisqacha tavsif (sinopsis)</b> yozing yoki 'yoq' deb yuboring:")


@admin_router.message(AddMovieFSM.description)
async def fsm_movie_description(message: Message, state: FSMContext, bot: Bot):
    desc = message.text.strip()
    if desc.lower() in ["yoq", "yo'q", "none", "-"]:
        desc = "Ajoyib kino, maroqli tomosha tilaymiz!"
        
    data = await state.get_data()
    await state.clear()
    
    movie_dict = {
        "code": data["code"],
        "title": data["title"],
        "year": data["year"],
        "country": data.get("country", "AQSH"),
        "genres": data.get("genres", "Kino"),
        "quality_720_file_id": data["quality_720_file_id"],
        "description": desc,
        "language": "O'zbek tilida",
        "rating": 7.8,
        "duration": "1 soat 45 daqiqa"
    }
    
    movie_id = await add_movie(movie_dict)
    
    # Auto-post to Telegram channel if enabled
    await auto_post_movie_to_channel(bot, movie_dict)
    
    text = (
        "🎉 <b>KINO MUVAFFAQIYATLI QO'SHILDI!</b>\n\n"
        f"🎬 Nomi: <b>{movie_dict['title']}</b> ({movie_dict['year']})\n"
        f"🔢 Kodi: <code>{movie_dict['code']}</code>\n"
        f"🎭 Janr: {movie_dict['genres']}\n\n"
        "Foydalanuvchilar endi ushbu kod orqali kinoni bir zumda topa olishadi!"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Yana kino qo'shish", callback_data="add_movie_start")],
        [InlineKeyboardButton(text="◀️ Boshqaruv paneli", callback_data="admin_menu")]
    ])
    await message.answer(text, reply_markup=kb)


# --- Edit / Delete Movie ---

@admin_router.callback_query(F.data == "find_movie_edit")
async def cb_find_movie_edit(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FindMovieEditFSM.code)
    await callback.message.edit_text("🔍 Tahrirlamoqchi yoki o'chirmoqchi bo'lgan kino <b>kodini</b> yuboring:")


@admin_router.message(FindMovieEditFSM.code)
async def fsm_find_movie_code(message: Message, state: FSMContext):
    code = message.text.strip().upper()
    await state.clear()
    movie = await get_movie_by_code(code)
    if not movie:
        await message.answer(f"❌ <b>{code}</b> kodli kino topilmadi!", reply_markup=get_admin_main_kb())
        return
        
    text = (
        f"🎬 <b>KINO MA'LUMOTLARI: #{movie['id']}</b>\n\n"
        f"📌 Nomi: <b>{movie['title']}</b> ({movie['year']})\n"
        f"🔢 Kodi: <code>{movie['code']}</code>\n"
        f"🎭 Janrlari: {movie['genres']}\n"
        f"👁 Ko'rishlar: {movie['views_count']} | 📥 Yuklashlar: {movie['downloads_count']}\n"
        f"📝 Tavsif: {movie['description'][:100]}..."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📁 Qism Qo'shish (Serial)", callback_data=f"add_ep_start:{movie['id']}"),
            InlineKeyboardButton(text="🔗 Treyler Linki", callback_data=f"set_trailer_start:{movie['id']}")
        ],
        [InlineKeyboardButton(text="🗑 Kinoni O'chirish", callback_data=f"del_movie:{movie['id']}")],
        [InlineKeyboardButton(text="◀️ Kinolar menyusi", callback_data="admin_movies")]
    ])
    await message.answer(text, reply_markup=kb)


@admin_router.callback_query(F.data.startswith("del_movie:"))
async def cb_del_movie(callback: CallbackQuery):
    m_id = int(callback.data.split(":")[1])
    await delete_movie(m_id)
    await callback.answer("Kino butunlay o'chirildi!", show_alert=True)
    await cb_admin_movies(callback)


# --- Add Episode to Series ---
@admin_router.callback_query(F.data.startswith("add_ep_start:"))
async def cb_add_ep_start(callback: CallbackQuery, state: FSMContext):
    movie_id = int(callback.data.split(":")[1])
    await state.update_data(movie_id=movie_id)
    await state.set_state(AddEpisodeFSM.season)
    await callback.message.edit_text(
        "📁 <b>SERIAL QISMINI QO'SHISH</b>\n\n"
        "1-qadam: Fasl raqamini yozing (masalan: <code>1</code>):"
    )


@admin_router.message(AddEpisodeFSM.season)
async def fsm_ep_season(message: Message, state: FSMContext):
    try:
        season = int(message.text.strip())
    except ValueError:
        await message.answer("⚠️ Iltimos, faqat raqam kiriting (masalan: 1):")
        return
    await state.update_data(season=season)
    await state.set_state(AddEpisodeFSM.episode)
    await message.answer("2-qadam: Qism raqamini yozing (masalan: <code>1</code> yoki <code>2</code>):")


@admin_router.message(AddEpisodeFSM.episode)
async def fsm_ep_number(message: Message, state: FSMContext):
    try:
        episode = int(message.text.strip())
    except ValueError:
        await message.answer("⚠️ Iltimos, faqat raqam kiriting (masalan: 1):")
        return
    await state.update_data(episode=episode)
    await state.set_state(AddEpisodeFSM.file)
    await message.answer("3-qadam: Ushbu qism videosini yuboring (yoki Telegram video file_id sini yozing):")


@admin_router.message(AddEpisodeFSM.file)
async def fsm_ep_file(message: Message, state: FSMContext):
    file_id = ""
    if message.video:
        file_id = message.video.file_id
    elif message.document:
        file_id = message.document.file_id
    elif message.text:
        file_id = message.text.strip()

    if not file_id:
        await message.answer("⚠️ Iltimos, video fayl yuboring yoki file_id sini yozing:")
        return

    await state.update_data(file_id=file_id)
    await state.set_state(AddEpisodeFSM.title)
    await message.answer("4-qadam: Qism nomini yozing (ixtiyoriy, nom yo'q bo'lsa <code>-</code> deb yozing):")


@admin_router.message(AddEpisodeFSM.title)
async def fsm_ep_title(message: Message, state: FSMContext):
    ep_title = message.text.strip()
    if ep_title == "-":
        ep_title = ""
    data = await state.get_data()
    await state.clear()

    movie_id = data["movie_id"]
    season = data["season"]
    episode = data["episode"]
    file_id = data["file_id"]

    await add_episode(
        movie_id=movie_id,
        season_number=season,
        episode_number=episode,
        file_id=file_id,
        episode_title=ep_title,
        quality="720p"
    )
    # Mark movie as series
    await update_movie(movie_id, {"is_series": 1})

    movie = await get_movie_by_id(movie_id)
    title = movie["title"] if movie else f"#{movie_id}"
    await message.answer(
        f"✅ <b>{title}</b> serialiga <b>{season}-fasl, {episode}-qism</b> muvaffaqiyatli qo'shildi!",
        reply_markup=get_admin_main_kb()
    )


# --- Set Trailer URL ---
@admin_router.callback_query(F.data.startswith("set_trailer_start:"))
async def cb_set_trailer_start(callback: CallbackQuery, state: FSMContext):
    movie_id = int(callback.data.split(":")[1])
    await state.update_data(movie_id=movie_id)
    await state.set_state(SetTrailerFSM.trailer_url)
    await callback.message.edit_text(
        "🔗 <b>TREYLER LINKINI O'RNATISH</b>\n\n"
        "Rasmiy treyler uchun YouTube yoki Telegram video havolasini yuboring (masalan: <i>https://youtu.be/...</i>):"
    )


@admin_router.message(SetTrailerFSM.trailer_url)
async def fsm_trailer_url(message: Message, state: FSMContext):
    url = message.text.strip()
    data = await state.get_data()
    await state.clear()

    movie_id = data["movie_id"]
    await update_movie(movie_id, {"trailer_url": url})
    await message.answer(
        "✅ Treyler havolasi muvaffaqiyatli saqlandi!",
        reply_markup=get_admin_main_kb()
    )


# ===================== DYNAMIC SETTINGS =====================

@admin_router.callback_query(F.data == "admin_settings")
async def cb_admin_settings(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return
        
    settings_dict = await get_all_settings()
    maintenance_status = "🔴 O'chirilgan" if settings_dict.get("maintenance_mode") == "0" else "🟢 YOQILGAN (Sayt ta'mirda)"
    daily_limit = settings_dict.get("daily_download_limit", "10")
    card_number = settings_dict.get("payment_card_number", "8600 •••• •••• 1234")
    admin_contact = settings_dict.get("admin_contact", "@Odiljon_n3")
    
    text = (
        "⚙️ <b>BOTNING DINAMIK PARAMETRLARI:</b>\n\n"
        f"🛠 <b>Texnik ishlar rejimi:</b> {maintenance_status}\n"
        f"📥 <b>Kunlik bepul yuklash limiti:</b> {daily_limit} ta (0 = cheksiz)\n"
        f"💳 <b>VIP To'lov kartasi:</b> <code>{card_number}</code>\n"
        f"👨‍💻 <b>Admin aloqa:</b> <code>{admin_contact}</code>\n"
        f"⚡️ <b>Anti-flood himoyasi:</b> {settings_dict.get('anti_flood_rate', '2')} so'rov/sekund\n"
        f"📢 <b>Homiy reklama banneri:</b> {settings_dict.get('ad_banner_text', 'Yo''q')[:35]}...\n\n"
        "O'zgartirmoqchi bo'lgan parametrni tanlang:"
    )
    
    m_toggle_text = "🟢 Texnik rejimni YOQISH" if settings_dict.get("maintenance_mode") == "0" else "🔴 Texnik rejimni O'CHIRISH"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=m_toggle_text, callback_data="toggle_maintenance")],
        [InlineKeyboardButton(text="💳 VIP To'lov kartasini o'zgartirish", callback_data="edit_setting:payment_card_number")],
        [InlineKeyboardButton(text="👨‍💻 Admin kontaktini o'zgartirish", callback_data="edit_setting:admin_contact")],
        [InlineKeyboardButton(text="📝 Start xabarini o'zgartirish", callback_data="edit_setting:start_message")],
        [InlineKeyboardButton(text="🎨 Kino shablonini o'zgartirish", callback_data="edit_setting:caption_template")],
        [InlineKeyboardButton(text="📥 Kunlik limitni o'zgartirish", callback_data="edit_setting:daily_download_limit")],
        [InlineKeyboardButton(text="📢 Homiy reklama bannerini tahrirlash", callback_data="edit_setting:ad_banner_text")],
        [InlineKeyboardButton(text="◀️ Boshqaruv paneli", callback_data="admin_menu")]
    ])
    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except Exception:
        pass


@admin_router.callback_query(F.data == "toggle_maintenance")
async def cb_toggle_maintenance(callback: CallbackQuery):
    curr = await get_setting("maintenance_mode", "0")
    new_val = "1" if curr == "0" else "0"
    await set_setting("maintenance_mode", new_val)
    status_label = "yoqildi" if new_val == "1" else "o'chirildi"
    await callback.answer(f"Texnik ta'mirlash rejimi {status_label}!", show_alert=True)
    await cb_admin_settings(callback)


@admin_router.callback_query(F.data.startswith("edit_setting:"))
async def cb_edit_setting(callback: CallbackQuery, state: FSMContext):
    key = callback.data.split(":")[1]
    curr_val = await get_setting(key, "")
    await state.set_state(EditSettingFSM.new_value)
    await state.update_data(setting_key=key)
    
    text = (
        f"✏️ <b>SOZLAMANI O'ZGARTIRISH: <code>{key}</code></b>\n\n"
        f"Joriy qiymat:\n<code>{curr_val}</code>\n\n"
        "Yangi qiymatni yozib yuboring (yoki bekor qilish uchun /cancel):"
    )
    await callback.message.edit_text(text)


@admin_router.message(EditSettingFSM.new_value)
async def fsm_edit_setting_val(message: Message, state: FSMContext):
    data = await state.get_data()
    key = data["setting_key"]
    new_val = message.text.strip()
    await set_setting(key, new_val)
    await state.clear()
    
    await message.answer(
        f"✅ <b>{key}</b> sozlamasi muvaffaqiyatli saqlandi!",
        reply_markup=get_admin_main_kb()
    )


# ===================== BROADCAST =====================

@admin_router.callback_query(F.data == "admin_broadcast")
async def cb_admin_broadcast(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        return
        
    await state.set_state(BroadcastFSM.message_content)
    text = (
        "✉️ <b>HAMMAGA XABARNOMA YUBORISH (BROADCAST)</b>\n\n"
        "Barcha faol foydalanuvchilarga yubormoqchi bo'lgan xabaringizni (matn, rasm yoki video) yuboring:\n\n"
        "<i>Bekor qilish uchun /cancel deb yozing.</i>"
    )
    await callback.message.edit_text(text)


@admin_router.message(BroadcastFSM.message_content)
async def fsm_broadcast_content(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    status_msg = await message.answer("⏳ Xabarnoma yuborilmoqda, iltimos kuting...")
    
    text = message.caption or message.text or ""
    photo_id = message.photo[-1].file_id if message.photo else None
    video_id = message.video.file_id if message.video else None
    
    result = await broadcast_message(
        bot=bot,
        text=text if text else None,
        photo_file_id=photo_id,
        video_file_id=video_id
    )
    
    report = (
        "✅ <b>XABARNOMA YAKUNLANDI!</b>\n\n"
        f"👥 Jami foydalanuvchilar: {result['total']}\n"
        f"✅ Muvaffaqiyatli yetkazildi: {result['sent']}\n"
        f"🚫 Botni bloklaganlar: {result['blocked']}\n"
        f"❌ Xatoliklar: {result['failed']}"
    )
    await status_msg.edit_text(report, reply_markup=get_admin_main_kb())


# ===================== VIP & PROMOCODES =====================

@admin_router.callback_query(F.data == "admin_vip")
async def cb_admin_vip(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return
        
    text = (
        "💎 <b>VIP STATUS VA PROMOKODLAR BOSHQARUVI:</b>\n\n"
        "Foydalanuvchilarga cheksiz yuklash va reklamasiz foydalanish imkoniyatini taqdim etuvchi promokodlar yarating."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎟 Yangi Promokod Yaratish", callback_data="add_promo_start")],
        [InlineKeyboardButton(text="👤 Foydalanuvchiga VIP Berish", callback_data="grant_vip_start")],
        [InlineKeyboardButton(text="◀️ Boshqaruv paneli", callback_data="admin_menu")]
    ])
    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except Exception:
        pass


@admin_router.callback_query(F.data == "add_promo_start")
async def cb_add_promo_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CreatePromoFSM.code)
    await callback.message.edit_text("🎟 Promokod nomini yozing (masalan: <code>PREMYERA2026</code>):")


@admin_router.message(CreatePromoFSM.code)
async def fsm_promo_code(message: Message, state: FSMContext):
    await state.update_data(code=message.text.strip().upper())
    await state.set_state(CreatePromoFSM.days)
    await message.answer("VIP davomiyligi (kunlarda, masalan: <code>30</code>):")


@admin_router.message(CreatePromoFSM.days)
async def fsm_promo_days(message: Message, state: FSMContext):
    try:
        days = int(message.text.strip())
    except ValueError:
        days = 30
    await state.update_data(days=days)
    await state.set_state(CreatePromoFSM.max_uses)
    await message.answer("Ushbu promokoddan necha kishi foydalana olsin? (masalan: <code>50</code>):")


@admin_router.message(CreatePromoFSM.max_uses)
async def fsm_promo_max_uses(message: Message, state: FSMContext):
    try:
        max_uses = int(message.text.strip())
    except ValueError:
        max_uses = 1
    data = await state.get_data()
    await state.clear()
    
    await create_promocode(data["code"], data["days"], max_uses)
    text = (
        "🎉 <b>YANGI PROMOKOD YARATILDI!</b>\n\n"
        f"🎟 Kodi: <code>{data['code']}</code>\n"
        f"📅 Muddat: {data['days']} kun\n"
        f"👥 Maksimal ishlatish: {max_uses} marta"
    )
    await message.answer(text, reply_markup=get_admin_main_kb())


# ===================== DATABASE BACKUP =====================

@admin_router.callback_query(F.data == "admin_backup")
async def cb_admin_backup(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return
        
    if not os.path.exists(DB_PATH):
        await callback.answer("Baza fayli topilmadi!", show_alert=True)
        return
        
    await callback.answer("Zaxira nusxasi yuborilmoqda...")
    doc = FSInputFile(DB_PATH, filename="kinochi_backup.db")
    await callback.message.answer_document(
        document=doc,
        caption="💾 <b>Gala Kino</b> ma'lumotlar bazasining zaxira nusxasi (.db fayl)."
    )


# ===================== WEB DASHBOARD INFO =====================

@admin_router.callback_query(F.data == "admin_web_info")
async def cb_admin_web_info(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return
        
    text = (
        "🌐 <b>ZAMONAVIY WEB ADMIN DASHBOARD</b>\n\n"
        f"Host: <code>http://{settings.WEB_HOST}:{settings.WEB_PORT}</code> yoki <code>http://localhost:{settings.WEB_PORT}</code>\n"
        f"Login: <code>{settings.WEB_ADMIN_USERNAME}</code>\n"
        f"Parol: <code>{settings.WEB_ADMIN_PASSWORD}</code>\n\n"
        "Web panel orqali siz brauzerda qulay interfeysda kanallarni qo'shishingiz, "
        "taymerlarni slaydlar orqali boshqarishingiz va grafikalarni ko'rishingiz mumkin!"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="admin_menu")]
    ])
    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except Exception:
        pass


@admin_router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Cancel current FSM operation."""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Bekor qilinadigan faol amal yo'q.")
        return
    await state.clear()
    await message.answer("❌ Amal bekor qilindi.", reply_markup=get_admin_main_kb())
