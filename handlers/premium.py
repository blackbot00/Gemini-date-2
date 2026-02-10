import requests
import urllib.parse
import uuid # Token generate panna
from aiogram import Router, F, types
from aiogram.filters import Command
from database import db
import datetime
from config import SHORTENER_URL

router = Router()

@router.message(Command("premium"))
@router.callback_query(F.data == "go_premium")
async def premium_menu(event: types.Message | types.CallbackQuery):
    user_id = event.from_user.id
    bot_username = (await event.bot.get_me()).username
    
    # Generate unique token for this session
    verify_token = str(uuid.uuid4())[:8]
    await db.users.update_one({"user_id": user_id}, {"$set": {"last_token": verify_token}})
    
    # Intha link-ah skip panna dhaan verify command trigger aagum
    unlock_payload = f"https://t.me/{bot_username}?start=verify_{verify_token}"
    encoded_url = urllib.parse.quote(unlock_payload)
    
    final_url = unlock_payload
    try:
        api_request_url = f"{SHORTENER_URL}{encoded_url}"
        response = requests.get(api_request_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                final_url = data.get("shortenedUrl")
    except: pass

    text = (
        "💎 **Premium Unlock System** 💎\n\n"
        "1. Keela irukura **Unlock Link** click panni ads skip pannunga.\n"
        "2. Ads mudichu bot-kulla varumbothu automatic-ah **Verify** option varum.\n\n"
        "⚠️ Link skip pannaama activate panna mudiyaadhu!"
    )
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔓 Unlock 1 Hour Premium", url=final_url)],
        [types.InlineKeyboardButton(text="🔙 Back", callback_data="main_menu")]
    ])
    
    if isinstance(event, types.Message):
        await event.answer(text, reply_markup=kb)
    else:
        await event.message.edit_text(text, reply_markup=kb)

# Intha callback ippo /start moolama varum
@router.callback_query(F.data.startswith("activate_"))
async def activate_premium(callback: types.CallbackQuery):
    token_received = callback.data.split("_")[1]
    user_id = callback.from_user.id
    
    user = await db.users.find_one({"user_id": user_id})
    
    if user and user.get("last_token") == token_received:
        expiry = datetime.datetime.now() + datetime.timedelta(hours=1)
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"is_premium": True, "expiry_date": expiry.strftime("%Y-%m-%d %H:%M:%S"), "last_token": None}}
        )
        await callback.message.edit_text(f"✅ **Premium Activated!**\nValid until: {expiry.strftime('%I:%M %p')}")
    else:
        await callback.answer("❌ Invalid or Expired Token! Please click the link again.", show_alert=True)
    
