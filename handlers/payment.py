"""
VIP Payment and Receipt Verification System for Gala Kino Bot.
Handles manual card payments, automated receipt processing, and instant 1-click admin approval.
"""
import logging
from datetime import datetime
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from config import settings
from database import (
    get_user,
    set_user_vip,
    get_setting,
    get_or_create_user
)

logger = logging.getLogger(__name__)
payment_router = Router(name="payment")


class PaymentReceiptFSM(StatesGroup):
    waiting_receipt = State()


async def send_vip_payment_screen(message: Message):
    """Send VIP payment options and card details directly to chat."""
    card_number = await get_setting("payment_card_number", "8600 •••• •••• 1234 (Odiljon N.)")
    admin_contact = await get_setting("admin_contact", "@Odiljon_n3")
    
    text = (
        "💎 <b>VIP STATUS SOTIB OLISH</b>\n\n"
        "💳 <b>To'lov uchun karta raqami:</b>\n"
        f"<code>{card_number}</code>\n\n"
        "💰 <b>Tariflar:</b>\n"
        "• 1 oy: <b>15,000 so'm</b>\n"
        "• 3 oy: <b>35,000 so'm</b>\n"
        "• 1 yil: <b>99,000 so'm</b>\n\n"
        "📌 <b>To'lov qilish tartibi:</b>\n"
        "1. Yuqoridagi kartaga to'lovni bajaring.\n"
        "2. To'lov chekini (skrinshotini) saqlab oling.\n"
        "3. Pastdagi <b>«📸 Chekni yuborish»</b> tugmasini bosing va chekni botga jo'nating.\n\n"
        "<i>To'lovingiz admin tomonidan bir necha daqiqada tasdiqlanadi va VIP avtomatik yoqiladi!</i>"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📸 Chekni yuborish", callback_data="send_receipt_start")],
        [InlineKeyboardButton(text="👨‍💻 Adminga yozish", url=f"https://t.me/{admin_contact.replace('@', '')}")],
        [InlineKeyboardButton(text="◀️ Bosh sahifa", callback_data="vip_status_back")]
    ])
    await message.answer(text, reply_markup=kb)


@payment_router.callback_query(F.data == "buy_vip")
async def cb_buy_vip_options(callback: CallbackQuery, state: FSMContext):
    """Show payment methods and card credentials."""
    card_number = await get_setting("payment_card_number", "8600 •••• •••• 1234 (Odiljon N.)")
    admin_contact = await get_setting("admin_contact", "@Odiljon_n3")
    
    text = (
        "💎 <b>VIP STATUS SOTIB OLISH</b>\n\n"
        "💳 <b>To'lov uchun karta raqami:</b>\n"
        f"<code>{card_number}</code>\n\n"
        "💰 <b>Tariflar:</b>\n"
        "• 1 oy: <b>15,000 so'm</b>\n"
        "• 3 oy: <b>35,000 so'm</b>\n"
        "• 1 yil: <b>99,000 so'm</b>\n\n"
        "📌 <b>To'lov qilish tartibi:</b>\n"
        "1. Yuqoridagi kartaga to'lovni bajaring.\n"
        "2. To'lov chekini (skrinshotini) saqlab oling.\n"
        "3. Pastdagi <b>«📸 Chekni yuborish»</b> tugmasini bosing va chekni botga jo'nating.\n\n"
        "<i>To'lovingiz admin tomonidan bir necha daqiqada tasdiqlanadi va VIP avtomatik yoqiladi!</i>"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📸 Chekni yuborish", callback_data="send_receipt_start")],
        [InlineKeyboardButton(text="👨‍💻 Adminga yozish", url=f"https://t.me/{admin_contact.replace('@', '')}")],
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="vip_status_back")]
    ])
    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except Exception:
        await callback.message.answer(text, reply_markup=kb)
    await callback.answer()


@payment_router.callback_query(F.data == "send_receipt_start")
async def cb_send_receipt_start(callback: CallbackQuery, state: FSMContext):
    """Prompt user to upload receipt photo."""
    await state.set_state(PaymentReceiptFSM.waiting_receipt)
    text = (
        "📸 <b>TO'LOV CHEKINI YUBORISH</b>\n\n"
        "Iltimos, to'lov chekingizning skrinshotini (rasmini) shu yerga yuboring:\n\n"
        "<i>Bekor qilish uchun /cancel deb yozing.</i>"
    )
    await callback.message.answer(text)
    await callback.answer()


@payment_router.message(PaymentReceiptFSM.waiting_receipt, F.photo)
async def process_payment_receipt(message: Message, state: FSMContext, bot: Bot):
    """Forward user's payment receipt to admins for 1-click approval."""
    await state.clear()
    photo_file_id = message.photo[-1].file_id
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    username = f"@{message.from_user.username}" if message.from_user.username else "Mavjud emas"
    
    # Confirm to user
    await message.answer(
        "✅ <b>To'lov chekingiz adminga yetkazildi!</b>\n\n"
        "Tekshiruvdan so'ng VIP statusingiz avtomatik faollashtiriladi va sizga xabar yuboriladi."
    )
    
    # Send to admins
    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ 1 oy (30 kun)", callback_data=f"approve_vip:{user_id}:30"),
            InlineKeyboardButton(text="✅ 3 oy (90 kun)", callback_data=f"approve_vip:{user_id}:90")
        ],
        [
            InlineKeyboardButton(text="✅ 1 yil (365 kun)", callback_data=f"approve_vip:{user_id}:365")
        ],
        [
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_vip:{user_id}")
        ]
    ])
    
    admin_caption = (
        "💳 <b>YANGI VIP TO'LOV CHEKI KELDI!</b>\n\n"
        f"👤 <b>Foydalanuvchi:</b> {user_name} ({username})\n"
        f"🆔 <b>Telegram ID:</b> <code>{user_id}</code>\n"
        f"⏱ <b>Vaqt:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        "Kerakli muddatni tanlab, bir bosishda VIP bering:"
    )
    
    for admin_id in settings.ADMIN_IDS:
        try:
            await bot.send_photo(
                chat_id=admin_id,
                photo=photo_file_id,
                caption=admin_caption,
                reply_markup=admin_kb
            )
        except Exception as e:
            logger.error(f"Failed to forward receipt to admin {admin_id}: {e}")


@payment_router.message(PaymentReceiptFSM.waiting_receipt)
async def invalid_receipt_input(message: Message):
    """Handle non-photo receipt submissions."""
    if message.text and message.text.startswith("/"):
        return
    await message.answer("⚠️ Iltimos, to'lov chekini <b>rasm (skrinshot)</b> shaklida yuboring.")


# ===================== ADMIN APPROVAL HANDLERS =====================

@payment_router.callback_query(F.data.startswith("approve_vip:"))
async def cb_admin_approve_vip(callback: CallbackQuery, bot: Bot):
    """Admin approves VIP and user receives instant notification."""
    parts = callback.data.split(":")
    target_user_id = int(parts[1])
    days = int(parts[2])
    
    success = await set_user_vip(target_user_id, days)
    if success:
        admin_text = callback.message.caption or ""
        admin_text += f"\n\n🟢 <b>TASDIQLANDI!</b> ({days} kunlik VIP berildi)"
        try:
            await callback.message.edit_caption(caption=admin_text, reply_markup=None)
        except Exception:
            pass
            
        # Notify user
        user_msg = (
            "🎉 <b>TABRIKLAYMIZ!</b>\n\n"
            f"Sizning to'lovingiz admin tomonidan tasdiqlandi va hisobingizga <b>{days} kunlik VIP STATUS</b> faollashtirildi! 💎✨\n\n"
            "Endi siz barcha kinolarni:\n"
            "• Reklamasiz va majburiy obunasiz\n"
            "• Cheksiz yuklab olishingiz mumkin!\n\n"
            "Maroqli tomosha tilaymiz!"
        )
        try:
            await bot.send_message(chat_id=target_user_id, text=user_msg)
        except Exception as e:
            logger.warning(f"Could not notify user {target_user_id} of VIP approval: {e}")
            
        await callback.answer(f"Foydalanuvchiga {days} kunlik VIP berildi!", show_alert=True)
    else:
        await callback.answer("Xatolik: VIP berish muvaffaqiyatsiz bo'ldi.", show_alert=True)


@payment_router.callback_query(F.data.startswith("reject_vip:"))
async def cb_admin_reject_vip(callback: CallbackQuery, bot: Bot):
    """Admin rejects invalid VIP receipt."""
    target_user_id = int(callback.data.split(":")[1])
    admin_contact = await get_setting("admin_contact", "@Odiljon_n3")
    
    admin_text = callback.message.caption or ""
    admin_text += "\n\n🔴 <b>RAD ETILDI!</b>"
    try:
        await callback.message.edit_caption(caption=admin_text, reply_markup=None)
    except Exception:
        pass
        
    user_msg = (
        "❌ <b>To'lov tasdiqlanmadi</b>\n\n"
        "Kechirasiz, siz yuborgan to'lov cheki admin tomonidan qabul qilinmadi. "
        "Iltimos, ma'lumotlarni tekshirib qayta to'lov qiling yoki administratorga murojaat qiling:\n\n"
        f"👨‍💻 Administrator: {admin_contact}"
    )
    try:
        await bot.send_message(chat_id=target_user_id, text=user_msg)
    except Exception:
        pass
        
    await callback.answer("To'lov rad etildi.", show_alert=True)
