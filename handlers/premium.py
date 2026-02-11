import requests
import urllib.parse
import uuid
from aiogram import Router, F, types
from aiogram.filters import Command
from database import db
from config import SHORTENER_URL

router = Router()

@router.message(Command("premium"))
@router.callback_query(F.data == "go_premium")
async def premium_menu(event: types.Message | types.CallbackQuery):
    user_id = int(event.from_user.id)
    bot_username = (await event.bot.get_me()).username
    
    # Unique token generate panni DB-la save pandrom
    verify_token = str(uuid.uuid4())[:8]
    await db.users.update_one(
        {"user_id": user_id}, 
        {"$set": {"last_token": verify_token}}, 
        upsert=True
    )
    
    # Telegram bot deep link
    unlock_payload = f"https://t.me/{bot_username}?start=verify_{verify_token}"
    encoded_url = urllib.parse.quote(unlock_payload)
    
    # API Link build pandrom
    # Check: SHORTENER_URL should be like 'https://tnlinks.in/api?api=YOUR_KEY&url='
    api_url = f"{SHORTENER_URL}{encoded_url}&format=text"
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    final_url = unlock_payload # Fail aana direct link varum

    try:
        # API-kitta irundhu shortened link-ah edukuroam
        response = requests.get(api_url, headers=headers, timeout=10)
        if response.status_code == 200 and response.text.startswith("http"):
            final_url = response.text.strip()
    except Exception as e:
        print(f"Shortener API Error: {e}")

    text = (
        "💎 **CoupleDating Premium** 💖\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🚀 **1 Hour Premium Unlock:**\n"
        "Keela irukura link-ah click panni ads skip pannunga. Mudichu thirumba varumbothu activation button varum! ⚡"
    )
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔓 Unlock 1 Hour Premium", url=final_url)],
        [types.InlineKeyboardButton(text="🔙 Back", callback_data="main_menu")]
    ])
    
    if isinstance(event, types.Message):
        await event.answer(text, reply_markup=kb)
    else:
        await event.message.edit_text(text, reply_markup=kb)
    
