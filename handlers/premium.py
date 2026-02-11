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
    
    # 1. New 6-Digit Code generate pandrom (Manual activation-ku)
    activation_code = ''.join(random.choices(string.digits, k=6))
    full_code = f"CP-{activation_code}"
    
    # DB-la save pandrom
    await db.users.update_one(
        {"user_id": user_id}, 
        {"$set": {"pending_code": full_code}}, 
        upsert=True
    )
    
    # 2. Intha message thaan user-ku browser-la theriyanum
    # "Unlock link" skip panna apram intha text kaatum
    browser_msg = f"SUCCESS! Your Activation Code is: {full_code}. Copy this code and send it to the bot."
    encoded_msg = urllib.parse.quote(browser_msg)
    
    # API Settings
    api_token = "03d52a6cae2e4b2fce67525b7a0ff4b26ad8eee2"
    api_url = f"https://tnlinks.in/api?api={api_token}&url={encoded_msg}"
    
    final_url = "#" # Fallback

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "success":
                        final_url = data.get("shortenedUrl").replace("\\", "")
    except Exception as e:
        print(f"Shortener Error: {e}")

    text = (
        "💎 **Manual Premium Unlock** 💎\n\n"
        "1. Keela irukura link-ah click panni ads skip pannunga.\n"
        "2. Ads mudichu varra page-la oru **Activation Code** theriyum.\n"
        "3. Andha code-ah inga type panni anuppunga! ✅"
    )
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔓 Get Activation Code", url=final_url)],
        [types.InlineKeyboardButton(text="🔙 Back", callback_data="main_menu")]
    ])
    
    if isinstance(event, types.Message):
        await event.answer(text, reply_markup=kb)
    else:
        await event.message.edit_text(text, reply_markup=kb)
    
