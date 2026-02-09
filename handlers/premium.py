from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from database import db
import datetime
import os
from config import SHORTENER_URL # .env la SHORTENER_URL="https://yourlink.com/api?api=KEY&url=" nu veiyunga

router = Router()

@router.message(Command("premium"))
@router.callback_query(F.data == "go_premium")
async def premium_menu(event: types.Message | types.CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = event.from_user.id if isinstance(event, types.Message) else event.from_user.id
    user = await db.users.find_one({"user_id": user_id})
    
    # Unique links
    bot_username = (await event.bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    # Shortener link: Bot redirect logic "start=unlock_userid"
    unlock_link = f"https://t.me/{bot_username}?start=unlock_{user_id}"
    final_short_url = f"{SHORTENER_URL}{unlock_link}"

    text = (
        "💎 **CoupleDating Premium** 💖\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🚀 **Instant Access:**\n"
        "Shortener link moolama 1 hour premium unlock pannunga! Safe & Fast. ⚡\n\n"
        "👥 **Refer & Earn:**\n"
        "Refer 5 new friends and get **1 Week Premium** for free! (One-time offer) 🎁\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 **Your Referrals:** {user.get('ref_count', 0)} / 5\n"
        f"🔗 **Your Link:** `{ref_link}`"
    )
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔓 Unlock 1 Hour Premium", url=final_short_url)],
        [types.InlineKeyboardButton(text="📢 Share Referral Link", url=f"https://t.me/share/url?url={ref_link}&text=Join%20this%20amazing%20dating%20bot!%20❤️")],
        [types.InlineKeyboardButton(text="🔙 Back", callback_data="main_menu")]
    ])
    
    if isinstance(event, types.Message):
        await event.answer(text, reply_markup=kb)
    else:
        try: await event.message.edit_text(text, reply_markup=kb)
        except: await event.message.answer(text, reply_markup=kb)
            
