from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from database import db
import datetime
from config import SHORTENER_URL

router = Router()

@router.message(Command("premium"))
@router.callback_query(F.data == "go_premium")
async def premium_menu(event: types.Message | types.CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = event.from_user.id
    user = await db.users.find_one({"user_id": user_id})
    
    bot_username = (await event.bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    # URL structure fix
    unlock_link = f"https://t.me/{bot_username}?start=unlock_{user_id}"
    final_short_url = f"{SHORTENER_URL}{unlock_link}"

    text = (
        "💎 **CoupleDating Premium** 💖\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🚀 **Instant Access:**\n"
        "Unlock 1 hour premium safely via shortener link! ⚡\n\n"
        "👥 **Refer & Earn:**\n"
        "Refer 5 new friends and get **1 Week Premium**! 🎁\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 **Referrals:** {user.get('ref_count', 0)} / 5\n"
        f"🔗 **Your Link:** `{ref_link}`"
    )
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔓 Unlock 1 Hour Premium", url=final_short_url)],
        [types.InlineKeyboardButton(text="🔙 Back", callback_data="main_menu")]
    ])
    
    if isinstance(event, types.Message):
        await event.answer(text, reply_markup=kb)
    else:
        await event.message.edit_text(text, reply_markup=kb)
        
