"""
User handlers for Kinochi Bot Pro.
Includes deep-linking, code lookup, fuzzy search, genres catalog, random discovery,
top trending movies, VIP activation, and seamless timer-aware forced subscription.
"""
import logging
from aiogram import Router, F, Bot
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import settings
from database import (
    get_or_create_user,
    get_user,
    get_setting,
    get_movie_by_code,
    get_movie_by_id,
    search_movies,
    get_movies_by_genre,
    get_top_movies,
    get_random_movie,
    increment_movie_stats,
    increment_user_downloads,
    check_user_vip_status,
    redeem_promocode,
    log_search,
    add_referral,
    rate_movie
)
from services.subscription import check_all_subscriptions, build_subscription_keyboard
from services.template import format_caption, format_start_message

logger = logging.getLogger(__name__)
user_router = Router(name="user")


# ===================== FSM STATES =====================

class SearchTitleFSM(StatesGroup):
    query = State()

class EnterPromoFSM(StatesGroup):
    code = State()


# ===================== KEYBOARD HELPERS =====================

async def get_user_main_menu() -> ReplyKeyboardMarkup:
    """Main persistent navigation keyboard with real-time Mini App button."""
    from aiogram.types import WebAppInfo
    from database import get_web_app_url
    
    app_url = await get_web_app_url()
    kb_rows = []
    if app_url and app_url.startswith("https://"):
        kb_rows.append([KeyboardButton(text="📱 Gala Kino (Mini App)", web_app=WebAppInfo(url=app_url))])
        
    kb_rows.extend([
        [
            KeyboardButton(text="🔍 Nomi bo'yicha qidirish"),
            KeyboardButton(text="🎲 Tasodifiy kino")
        ],
        [
            KeyboardButton(text="🎭 Janrlar katalogi"),
            KeyboardButton(text="🏆 Top-10 kinolar")
        ],
        [
            KeyboardButton(text="👥 Do'stlarni taklif qilish"),
            KeyboardButton(text="📥 Kino buyurtma qilish")
        ],
        [
            KeyboardButton(text="💎 VIP Status"),
            KeyboardButton(text="📞 Aloqa & Yordam")
        ]
    ])
    return ReplyKeyboardMarkup(keyboard=kb_rows, resize_keyboard=True)


def get_genres_keyboard() -> InlineKeyboardMarkup:
    """Pre-configured genre filter buttons."""
    genres = [
        "Jangari", "Komediya", "Fantastika", "Qo'rqinchli",
        "Drama", "Melodrama", "Multfilm", "Kriminal",
        "Tarixiy", "Detektiv", "Anime", "Sarguzasht"
    ]
    buttons = []
    row = []
    for g in genres:
        row.append(InlineKeyboardButton(text=f"🎭 {g}", callback_data=f"genre:{g}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ===================== /START HANDLER =====================

@user_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    """Handle /start command with deep linking and forced subscription checks."""
    await state.clear()
    user_id = message.from_user.id
    user = await get_or_create_user(
        telegram_id=user_id,
        username=message.from_user.username,
        first_name=message.from_user.first_name
    )

    # 1. Check Maintenance Mode
    maintenance_mode = await get_setting("maintenance_mode", "0")
    if maintenance_mode == "1" and user.get("role") not in ["admin", "superadmin"]:
        m_text = await get_setting("maintenance_text")
        await message.answer(m_text)
        return

    # 2. Extract deep link movie code or referral if present
    args = message.text.split()
    target_code = ""
    if len(args) > 1:
        param = args[1].strip()
        if param.startswith("ref_"):
            try:
                referrer_id = int(param.replace("ref_", ""))
                success, ref_msg = await add_referral(referrer_id, user_id)
                if success:
                    try:
                        await bot.send_message(
                            chat_id=referrer_id,
                            text=f"🎉 <b>Yangi referal!</b>\nSizning taklif havolangiz orqali <b>{message.from_user.first_name}</b> botga qo'shildi.\n\n{ref_msg}"
                        )
                    except Exception:
                        pass
            except Exception as e:
                logger.warning(f"Referral parsing error: {e}")
        elif param == "buy_vip":
            from handlers.payment import send_vip_payment_screen
            await send_vip_payment_screen(message)
            return
        else:
            target_code = param.replace("movie_", "")

    # 3. Check Mandatory Subscription
    is_subscribed, unsubscribed_channels, remaining_timer = await check_all_subscriptions(
        bot=bot, telegram_id=user_id, user=user
    )

    if not is_subscribed:
        sub_text = await get_setting("force_sub_text")
        if remaining_timer > 0:
            sub_text += f"\n\n⏳ <b>Taymer:</b> Sizga {remaining_timer} soniyalik bepul ko'rish imkoni berilgan!"
            
        kb = build_subscription_keyboard(unsubscribed_channels, target_code, remaining_timer)
        await message.answer(sub_text, reply_markup=kb)
        return

    # 4. If deep link movie is specified, deliver directly
    if target_code:
        delivered = await deliver_movie_by_code(message, bot, target_code, user)
        if delivered:
            return

    # 5. Send Welcome Start Message
    welcome_text = await format_start_message(message.from_user.first_name, user_id)
    await message.answer(welcome_text, reply_markup=await get_user_main_menu())


@user_router.message(Command("app"))
async def cmd_app(message: Message):
    """Open Gala Kino Telegram Mini App."""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
    from database import get_web_app_url
    app_url = await get_web_app_url()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 Gala Kino Mini Appni Ochish", web_app=WebAppInfo(url=app_url))]
    ])
    await message.answer(
        "📱 <b>Gala Kino Telegram Mini App</b>\n\n"
        "Kinolar katalogi, janrlar va qulay qidiruv tizimidan foydalanish uchun quyidagi tugmani bosing:",
        reply_markup=kb
    )


@user_router.message(F.web_app_data)
async def handle_miniapp_data(message: Message, bot: Bot):
    """Handle movie selection directly from Telegram Mini App."""
    code = message.web_app_data.data.strip().upper()
    user = await get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    await deliver_movie_by_code(message, bot, code, user)


# ===================== SUBSCRIPTION CALLBACKS =====================

@user_router.callback_query(F.data.startswith("check_sub:"))
async def cb_check_subscription(callback: CallbackQuery, bot: Bot):
    """Re-check subscription when user clicks '✅ Obunani tekshirish'."""
    user_id = callback.from_user.id
    user = await get_user(user_id)
    target_code = callback.data.split(":")[1]
    if target_code == "none":
        target_code = ""

    is_subscribed, unsubscribed_channels, remaining_timer = await check_all_subscriptions(
        bot=bot, telegram_id=user_id, user=user
    )

    if not is_subscribed:
        await callback.answer("⚠️ Hali barcha kanallarga a'zo bo'lmadingiz!", show_alert=True)
        sub_text = await get_setting("force_sub_text")
        kb = build_subscription_keyboard(unsubscribed_channels, target_code, remaining_timer)
        try:
            await callback.message.edit_text(sub_text, reply_markup=kb)
        except Exception:
            pass
        return

    await callback.answer("🎉 Obunangiz tasdiqlandi! Xush kelibsiz.")
    try:
        await callback.message.delete()
    except Exception:
        pass

    # Deliver movie if was waiting for one
    if target_code:
        await deliver_movie_by_code(callback.message, bot, target_code, user)
    else:
        welcome_text = await format_start_message(callback.from_user.first_name, user_id)
        await callback.message.answer(welcome_text, reply_markup=await get_user_main_menu())


@user_router.callback_query(F.data.startswith("refresh_sub:"))
async def cb_refresh_subscription(callback: CallbackQuery, bot: Bot):
    """Update countdown timer display."""
    user_id = callback.from_user.id
    user = await get_user(user_id)
    target_code = callback.data.split(":")[1]

    is_subscribed, unsubscribed_channels, remaining_timer = await check_all_subscriptions(
        bot=bot, telegram_id=user_id, user=user
    )

    if is_subscribed:
        await cb_check_subscription(callback, bot)
        return

    sub_text = await get_setting("force_sub_text")
    kb = build_subscription_keyboard(unsubscribed_channels, target_code, remaining_timer)
    try:
        await callback.message.edit_reply_markup(reply_markup=kb)
        await callback.answer(f"Taymer: {remaining_timer} soniya qoldi")
    except Exception:
        await callback.answer()


# ===================== MOVIE DELIVERY ENGINE =====================

async def deliver_movie_by_code(message: Message, bot: Bot, code: str, user: dict) -> bool:
    """Deliver movie video and dynamic caption to user with limit check."""
    movie = await get_movie_by_code(code)
    if not movie:
        await message.answer(
            f"❌ <b>{code}</b> kodli kino topilmadi.\n"
            "Iltimos, kodni to'g'ri kiritganingizni tekshiring yoki nomi bo'yicha qidiring."
        )
        return False

    # Check VIP only movie
    if movie.get("is_vip_only") and not await check_user_vip_status(user):
        vip_text = (
            "🔒 <b>Ushbu kino faqat VIP foydalanuvchilar uchun!</b>\n\n"
            "Ushbu eksklyuziv premyerani tomosha qilish uchun VIP statusni faollashtiring."
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💎 VIP Status Olish", callback_data="buy_vip")]
        ])
        await message.answer(vip_text, reply_markup=kb)
        return False

    # Check Daily Download Limit
    daily_limit = int(await get_setting("daily_download_limit", "10"))
    if daily_limit > 0 and not await check_user_vip_status(user):
        current_downloads = user.get("daily_downloads", 0)
        if current_downloads >= daily_limit:
            limit_msg = await get_setting("limit_exceeded_text")
            limit_msg = limit_msg.replace("{limit}", str(daily_limit))
            await message.answer(limit_msg)
            return False

    # Build movie caption
    caption = await format_caption(movie)

    # Action buttons (Share, like, dislike)
    bot_user = settings.BOT_USERNAME.replace("@", "")
    share_url = f"https://t.me/share/url?url=https://t.me/{bot_user}?start={movie['code']}&text={movie['title']}%20kinosini%20ko'ring!"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⭐ 1", callback_data=f"rate:{movie['id']}:1"),
            InlineKeyboardButton(text="⭐ 2", callback_data=f"rate:{movie['id']}:2"),
            InlineKeyboardButton(text="⭐ 3", callback_data=f"rate:{movie['id']}:3"),
            InlineKeyboardButton(text="⭐ 4", callback_data=f"rate:{movie['id']}:4"),
            InlineKeyboardButton(text="⭐ 5", callback_data=f"rate:{movie['id']}:5")
        ],
        [
            InlineKeyboardButton(text="↗️ Do'stlarga ulashish", url=share_url)
        ]
    ])

    # Send movie file
    file_id = movie.get("quality_720_file_id") or movie.get("quality_1080_file_id") or movie.get("quality_480_file_id")
    if file_id:
        try:
            await bot.send_video(
                chat_id=message.chat.id,
                video=file_id,
                caption=caption,
                reply_markup=kb
            )
        except Exception as e:
            logger.error(f"Failed to send video: {e}")
            # Fallback to text message with caption
            await message.answer(caption, reply_markup=kb)
    else:
        await message.answer(caption, reply_markup=kb)

    # Increment statistics
    await increment_movie_stats(movie["id"], views=1, downloads=1)
    await increment_user_downloads(user["telegram_id"])
    return True


# ===================== TEXT INPUT & CODE SEARCH =====================

@user_router.message(F.text == "🔍 Nomi bo'yicha qidirish")
async def btn_search_title(message: Message, state: FSMContext):
    await state.set_state(SearchTitleFSM.query)
    await message.answer("🔍 Qidirmoqchi bo'lgan kino <b>nomini</b> yozing (masalan: <i>Forsaj</i> yoki <i>Avatar</i>):")


@user_router.message(SearchTitleFSM.query)
async def fsm_search_title(message: Message, state: FSMContext):
    query = message.text.strip()
    await state.clear()
    
    results = await search_movies(query, limit=10)
    await log_search(message.from_user.id, query, len(results))

    if not results:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📥 Ushbu kinoni adminga buyurtma qilish", callback_data=f"req_movie:{query[:30]}")]
        ])
        await message.answer(
            f"😔 <b>'{query}'</b> bo'yicha hech qanday kino topilmadi.\n"
            "Boshqa so'z bilan qidirib ko'ring yoki ushbu kinoni adminga buyurtma qiling:",
            reply_markup=kb
        )
        return

    buttons = []
    for m in results:
        btn_label = f"🎬 {m['title']} ({m['year']}) — [{m['code']}]"
        buttons.append([InlineKeyboardButton(text=btn_label, callback_data=f"view_movie:{m['id']}")])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(f"🔍 <b>'{query}'</b> bo'yicha topilgan kinolar:", reply_markup=kb)


@user_router.message(F.text == "🎲 Tasodifiy kino")
async def btn_random_movie(message: Message, bot: Bot):
    user = await get_user(message.from_user.id)
    is_subscribed, unsubscribed, rem = await check_all_subscriptions(bot, message.from_user.id, user)
    if not is_subscribed:
        sub_text = await get_setting("force_sub_text")
        await message.answer(sub_text, reply_markup=build_subscription_keyboard(unsubscribed, "", rem))
        return

    movie = await get_random_movie()
    if not movie:
        await message.answer("Bazada hozircha kinolar yo'q.")
        return

    await deliver_movie_by_code(message, bot, movie["code"], user)


@user_router.message(F.text == "🏆 Top-10 kinolar")
async def btn_top_movies(message: Message):
    top_list = await get_top_movies(limit=10)
    if not top_list:
        await message.answer("Hozircha top kinolar ro'yxati shakllanmagan.")
        return

    buttons = []
    for idx, m in enumerate(top_list, 1):
        btn_label = f"{idx}. {m['title']} (👁 {m['views_count']}) — [{m['code']}]"
        buttons.append([InlineKeyboardButton(text=btn_label, callback_data=f"view_movie:{m['id']}")])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("🏆 <b>ENG KO'P KO'RILGAN TOP-10 KINOLAR:</b>", reply_markup=kb)


@user_router.message(F.text == "🎭 Janrlar katalogi")
async def btn_genres_catalog(message: Message):
    await message.answer(
        "🎭 <b>KINO JANRLARI KATALOGI:</b>\n\nO'zingizga yoqqan janrni tanlang:",
        reply_markup=get_genres_keyboard()
    )


@user_router.message(F.text == "💎 VIP Status")
async def btn_vip_status(message: Message):
    user = await get_user(message.from_user.id)
    is_vip = await check_user_vip_status(user)
    vip_text = await get_setting("vip_info_text")
    admin_contact = await get_setting("admin_contact", "@Odiljon_n3")
    vip_text = vip_text.replace("{admin_contact}", admin_contact)

    status_str = f"🟢 <b>Faol!</b> (Muddati: {user.get('vip_until', 'Cheksiz')})" if is_vip else "🔴 <b>Faol emas</b>"
    text = f"Sizning holatingiz: {status_str}\n\n{vip_text}"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 VIP Sotib Olish (Karta orqali)", callback_data="buy_vip")],
        [InlineKeyboardButton(text="🎟 Promokod kiritish", callback_data="enter_promo")],
        [InlineKeyboardButton(text="💬 Adminga yozish", url=f"https://t.me/{admin_contact.replace('@', '')}")]
    ])
    await message.answer(text, reply_markup=kb)


@user_router.message(F.text == "📞 Aloqa & Yordam")
async def btn_support(message: Message):
    contact = await get_setting("admin_contact", "@Odiljon_n3")
    text = (
        "📞 <b>ALOQA VA YORDAM MARKAZI</b>\n\n"
        "Savollar, takliflar yoki reklama masalalari bo'yicha biz bilan bog'laning:\n"
        f"👨‍💻 Administrator: {contact}\n\n"
        "<i>Kino kodini botga to'g'ridan-to'g'ri yuborsangiz, bot kinoni darhol topib beradi!</i>"
    )
    await message.answer(text)


# ===================== GENRES & VIEW CALLBACKS =====================

@user_router.callback_query(F.data.startswith("genre:"))
async def cb_genre_selected(callback: CallbackQuery):
    genre_name = callback.data.split(":")[1]
    movies = await get_movies_by_genre(genre_name, limit=10)
    if not movies:
        await callback.answer(f"'{genre_name}' janrida hali kinolar mavjud emas.", show_alert=True)
        return

    buttons = []
    for m in movies:
        btn_label = f"🎬 {m['title']} ({m['year']}) — [{m['code']}]"
        buttons.append([InlineKeyboardButton(text=btn_label, callback_data=f"view_movie:{m['id']}")])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(f"🎭 <b>'{genre_name}' janridagi kinolar:</b>", reply_markup=kb)


@user_router.callback_query(F.data.startswith("view_movie:"))
async def cb_view_movie(callback: CallbackQuery, bot: Bot):
    movie_id = int(callback.data.split(":")[1])
    movie = await get_movie_by_id(movie_id)
    if not movie:
        await callback.answer("Kino topilmadi!", show_alert=True)
        return

    user = await get_user(callback.from_user.id)
    is_subscribed, unsubscribed, rem = await check_all_subscriptions(bot, callback.from_user.id, user)
    if not is_subscribed:
        sub_text = await get_setting("force_sub_text")
        await callback.message.answer(sub_text, reply_markup=build_subscription_keyboard(unsubscribed, movie["code"], rem))
        return

    await deliver_movie_by_code(callback.message, bot, movie["code"], user)
    await callback.answer()


@user_router.callback_query(F.data.startswith("rate:"))
async def cb_rate_movie(callback: CallbackQuery):
    parts = callback.data.split(":")
    movie_id = int(parts[1])
    stars = int(parts[2])
    new_avg = await rate_movie(movie_id, callback.from_user.id, stars)
    await callback.answer(f"Rahmat! Siz {stars} ta yulduz berdingiz. ⭐ Yangi reyting: {new_avg}/10", show_alert=True)


@user_router.callback_query(F.data.startswith("like:"))
async def cb_like_movie(callback: CallbackQuery):
    await callback.answer("Rahmat! Bahoyingiz qabul qilindi. 👍")


@user_router.callback_query(F.data.startswith("dislike:"))
async def cb_dislike_movie(callback: CallbackQuery):
    await callback.answer("Fikringiz uchun rahmat! 👎")


# ===================== PROMOCODE FSM =====================

@user_router.callback_query(F.data == "enter_promo")
async def cb_enter_promo(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EnterPromoFSM.code)
    await callback.message.answer("🎟 VIP promokodni kiriting:")
    await callback.answer()


@user_router.message(EnterPromoFSM.code)
async def fsm_promo_entered(message: Message, state: FSMContext):
    code = message.text.strip()
    await state.clear()
    success, res_text = await redeem_promocode(code, message.from_user.id)
    await message.answer(res_text, reply_markup=await get_user_main_menu())


# ===================== CATCH-ALL TEXT (CODE LOOKUP) =====================

@user_router.message(F.text)
async def handle_direct_code(message: Message, bot: Bot):
    """Handle direct code input from user (e.g. 101, 102, AVATAR)."""
    text = message.text.strip()
    user = await get_user(message.from_user.id)
    
    # 1. Check Mandatory Subscription
    is_subscribed, unsubscribed, rem = await check_all_subscriptions(bot, message.from_user.id, user)
    if not is_subscribed:
        sub_text = await get_setting("force_sub_text")
        await message.answer(sub_text, reply_markup=build_subscription_keyboard(unsubscribed, text, rem))
        return

    # 2. Try Deliver by Code
    delivered = await deliver_movie_by_code(message, bot, text, user)
    if not delivered:
        # Fallback: search movies
        results = await search_movies(text, limit=5)
        if results:
            buttons = [
                [InlineKeyboardButton(text=f"🎬 {m['title']} ({m['year']})", callback_data=f"view_movie:{m['id']}")]
                for m in results
            ]
            await message.answer(
                f"Kino kodi topilmadi, lekin shunga o'xshash kinolar mavjud:",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
            )
