import aiohttp
import urllib.parse
import random
import string
from aiogram import Router, F, types
from aiogram.filters import Command
from database import db

router = Router()

@router.message(Command("premium"))
@router.callback_query(F.data == "go_premium")
async def premium_menu(event: types.Message | types.CallbackQuery):
    user_id = int(event.from_user.id)
    
    # 1. Generate unique 6-digit Activation Code
    activation_code = ''.join(random.choices(string.digits, k=6))
    full_code = f"CP-{activation_code}"
    
    # Save to DB
    await db.users.update_one(
        {"user_id": user_id}, 
        {"$set": {"pending_code": full_code}}, 
        upsert=True
    )
    
    # 2. Simple Display Page (Rentry use pannuvom, adhu stable)
    # User ads skip panna indha page open aagi code-ah kaatum
    display_text = f"✅ YOUR ACTIVATION CODE IS: {full_code}"
    
    # Target URL: Rentry or Just a raw text display
    # TNLinks API-ku target URL format venum, so namma raw text display site use pannuvom
    target_url = f"https://txt.fyi/+/raw?text={urllib.parse.quote(display_text)}"
    
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
        print(f"Shortener Error: {e}")

    text = (
        "💎 **CoupleDating Premium** 💎\n\n"
        "1. Click the button and skip ads. ⚡\n"
        "2. The final page will show your **Code**. 🔑\n"
        "3. Copy and send it here to activate! ✅"
    )
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔓 Get Activation Code", url=final_url)],
        [types.InlineKeyboardButton(text="🔙 Back", callback_data="main_menu")]
    ])
    
    if isinstance(event, types.Message):
        await event.answer(text, reply_markup=kb)
    else:
        await event.message.edit_text(text, reply_markup=kb)
        
