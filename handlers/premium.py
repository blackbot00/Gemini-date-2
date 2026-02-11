import aiohttp
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
    
    # 1. Unique Token generate pandrom (Ads skip pannadharkku proof)
    verify_token = str(uuid.uuid4())[:8]
    await db.users.update_one(
        {"user_id": user_id}, 
        {"$set": {"last_token": verify_token}}, 
        upsert=True
    )
    
    # 2. Target URL: Ads mudichu 'Open' kudutha indha link thaan open aagum
    target_url = f"https://t.me/{bot_username}?start=verify_{verify_token}"
    
    # API Settings
    api_token = "03d52a6cae2e4b2fce67525b7a0ff4b26ad8eee2"
    api_url = f"https://tnlinks.in/api?api={api_token}&url={urllib.parse.quote(target_url)}"
    
    final_url = api_url 

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "success":
                        short_link = data.get("shortenedUrl").replace("\\", "")
                        if "http" in short_link:
                            final_url = short_link
    except Exception as e:
        print(f"API Error: {e}")

    text = (
        "💎 **CoupleDating Premium** 💖\n\n"
        "1. Keela irukura link-ah click panni ads skip pannunga. ⚡\n"
        "2. Ads mudichu 'Open' kudutha, **Bot automatic-ah Activation Code anuppum**. 🔑\n"
        "3. Andha code-ah copy panni thirumba type panni anuppunga! ✅"
    )
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔓 Unlock Activation Code", url=final_url)],
        [types.InlineKeyboardButton(text="🔙 Back", callback_data="main_menu")]
    ])
    
    if isinstance(event, types.Message):
        await event.answer(text, reply_markup=kb)
    else:
        await event.message.edit_text(text, reply_markup=kb)
    
