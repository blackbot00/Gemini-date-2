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
    
    # 1. Generate random 6-digit code
    activation_code = ''.join(random.choices(string.digits, k=6))
    full_code = f"CP-{activation_code}"
    
    # 2. DB-la pending_code save pandrom
    await db.users.update_one(
        {"user_id": user_id}, 
        {"$set": {"pending_code": full_code}}, 
        upsert=True
    )
    
    # 3. User-ku browser-la enna message kaatanum-nu decide pandrom
    # TNLinks API-ku target-ah oru dummy URL kuduthu, andha URL-laye code-ah vaikuroam
    display_msg = f"SUCCESS!_Your_Activation_Code_is_{full_code}_Copy_and_Send_to_Bot"
    target_url = f"https://www.google.com/search?q={display_msg}"
    
    # API Settings
    api_token = "03d52a6cae2e4b2fce67525b7a0ff4b26ad8eee2"
    # Inga dhaan munnadi encoded_url-nu thappa kuduthuttaen. Ippo fix panniyaachu:
    api_url = f"https://tnlinks.in/api?api={api_token}&url={urllib.parse.quote(target_url)}"
    
    final_url = api_url # Link generate aagalana idhu fallback

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
        "2. Kadasila oru page open aagum, adhula unga **Activation Code** kaatum. 🔑\n"
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
    
