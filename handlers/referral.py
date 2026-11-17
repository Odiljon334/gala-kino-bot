"""
Referral system handler for Kinochi Bot Pro.
Manages personal referral links, rewards, and the top referrers leaderboard.
"""
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database import (
    get_user_referrals_count,
    get_top_referrers,
    get_setting,
    get_user
)
from config import settings

referral_router = Router(name="referral")


@referral_router.message(F.text == "👥 Do'stlarni taklif qilish")
async def btn_referral_menu(message: Message):
    """Show referral status, link, and reward rules."""
    user_id = message.from_user.id
    bot_username = settings.BOT_USERNAME.replace("@", "")
    ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    count = await get_user_referrals_count(user_id)
    friends_for_vip = await get_setting("referral_friends_for_vip", "5")
    vip_days = await get_setting("referral_reward_vip_days", "7")
    reward_downloads = await get_setting("referral_reward_downloads", "3")
    
    text = (
        "👥 <b>DO'STARNI TAKLIF QILING VA BEPUL VIP YUTIB OLING!</b>\n\n"
        f"📊 Siz taklif qilgan do'stlar soni: <b>{count} ta</b>\n\n"
        "🎁 <b>Mukofot shartlari:</b>\n"
        f"• Har bir qo'shilgan do'stingiz uchun: <b>+{reward_downloads} ta</b> bepul kino yuklash imkoni!\n"
        f"• Har <b>{friends_for_vip} ta</b> do'stingiz uchun: <b>{vip_days} kunlik VIP</b> status avtomatik sovg'a qilinadi!\n\n"
        "🔗 <b>Sizning shaxsiy taklif havolangiz:</b>\n"
        f"<code>{ref_link}</code>\n\n"
        "Ushbu havolani do'stlaringizga, guruhlarga yoki kanallarga tarqating!"
    )
    
    share_text = f"🔥 Eng zo'r tarjima kinolar va premyeralarni shu botda tomosha qiling: {ref_link}"
    share_url = f"https://t.me/share/url?url={ref_link}&text=Zo'r%20kino%20boti!%20Kiring:"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="↗️ Do'stlarga ulashish", url=share_url)],
        [InlineKeyboardButton(text="🏆 Top taklif qiluvchilar", callback_data="top_referrers")]
    ])
    await message.answer(text, reply_markup=kb)


@referral_router.callback_query(F.data == "top_referrers")
async def cb_top_referrers(callback: CallbackQuery):
    """Show top 10 referrers."""
    top_list = await get_top_referrers(limit=10)
    if not top_list:
        await callback.answer("Hozircha referallar reytingi shakllanmagan.", show_alert=True)
        return

    text = "🏆 <b>ENG KO'P DO'ST TAKLIF QILGAN FOYDALANUVCHILAR:</b>\n\n"
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    
    for idx, r in enumerate(top_list):
        medal = medals[idx] if idx < len(medals) else "👤"
        name = r.get("first_name") or r.get("username") or "Foydalanuvchi"
        text += f"{medal} <b>{name}</b> — <b>{r['ref_count']} ta</b> do'st\n"
        
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_to_ref_info")]
    ])
    await callback.message.edit_text(text, reply_markup=kb)


@referral_router.callback_query(F.data == "back_to_ref_info")
async def cb_back_to_ref_info(callback: CallbackQuery):
    await callback.message.delete()
    await btn_referral_menu(callback.message)
