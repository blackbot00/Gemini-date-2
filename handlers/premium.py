import aiohttp # Asynchronous request-ku
import urllib.parse
import uuid
from aiogram import Router, F, types
from aiogram.filters import Command
from database import db

router = Router()

@router.message(Command("premium"))
@router.callback_query(F.data == "go_premium")
async def premium_menu(event: types.Message | types.CallbackQuery):
    user_id = int(event.from_user.id)
    bot_username = (await event.bot.get_me()).username
    
    # 1. Unique token generate panni DB-la save pandrom
    verify_token = str(uuid.uuid4())[:8]
    await db.users.update_one(
        {"user_id": user_id}, 
        {"$set": {"last_token": verify_token}}, 
        upsert=True
    )
    
    # 2. Telegram deep link format
    unlock_payload = f"https://t.me/{bot_username}?start=verify_{verify_token}"
    encoded_url = urllib.parse.quote(unlock_payload)
    
    # API Settings
    api_token = "03d52a6cae2e4b2fce67525b7a0ff4b26ad8eee2"
    api_url = f"https://tnlinks.in/api?api={api_token}&url={encoded_url}"
    
    final_url = unlock_payload # Fallback if API fails
    
    # 3. Server-side shortening (JSON-ah Python-la handle pandrom)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "success":
                        # JSON-la irundhu link-ah edukuroam
                        # Browser-la JSON kaatama, link-ah mattum button-la vaippom
                        final_url = data.get("shortenedUrl").replace("\\", "")
                        print(f"Success: {final_url}")
    except Exception as e:
        print(f"Shortener Error: {e}")

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
    
