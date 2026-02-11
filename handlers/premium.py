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
    
    # 1. New 6-Digit Code generate
    activation_code = ''.join(random.choices(string.digits, k=6))
    full_code = f"CP-{activation_code}"
    
    # DB-la save pandrom
    await db.users.update_one(
        {"user_id": user_id}, 
        {"$set": {"pending_code": full_code}}, 
        upsert=True
    )
    
    # 2. Intha text thaan user-ku browser-la theriyanum
    # Simple-ah oru Google Search URL-a use pannuvom (Easy display)
    display_text = f"YOUR_PREMIUM_CODE_IS_{full_code}_COPY_THIS_AND_SEND_TO_BOT"
    target_url = f"https://www.google.com/search?q={display_text}"
    
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
        "💎 **Premium Activation** 💎\n\n"
        "1. Keela irukura link-ah click panni ads skip pannunga.\n"
        "2. Ads mudichu varra page-la (Google search bar-la) unga **Activation Code** theriyum.\n"
        "3. Andha code-ah copy panni inga type panni anuppunga! ✅"
    )
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔓 Get Activation Code", url=final_url)],
        [types.InlineKeyboardButton(text="🔙 Back", callback_data="main_menu")]
    ])
    
    if isinstance(event, types.Message):
        await event.answer(text, reply_markup=kb)
    else:
        await event.message.edit_text(text, reply_markup=kb)
              
