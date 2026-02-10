import requests
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from database import db
import datetime
from config import SHORTENER_URL

router = Router()

@router.message(Command("premium"))
@router.callback_query(F.data == "go_premium")
async def premium_menu(event: types.Message | types.CallbackQuery, state: FSMContext = None):
    if state:
        await state.clear()
        
    user_id = event.from_user.id
    user = await db.users.find_one({"user_id": user_id})
    
    # User register aagala na basic data create pannidalaam
    if not user:
        user = {"ref_count": 0}

    bot_username = (await event.bot.get_me()).username
    unlock_link = f"https://t.me/{bot_username}?start=unlock_{user_id}"
    
    # Shortening Logic
    final_short_url = unlock_link # Default
    try:
        response = requests.get(f"{SHORTENER_URL}{unlock_link}", timeout=5)
        data = response.json()
        if data.get("status") == "success":
            final_short_url = data.get("shortenedUrl")
    except:
        pass

    ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"

    text = (
        "💎 **CoupleDating Premium** 💖\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🚀 **Instant 1 Hour Access:**\n"
        "Keela irukura link-ah click panni ads skip pannunga, auto-va premium unlock aagum! ⚡\n\n"
        "👥 **Refer & Earn:**\n"
        "5 referrals = **1 Week Premium** 🎁\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 **Your Referrals:** {user.get('ref_count', 0)} / 5\n"
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
    
