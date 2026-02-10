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
    user_id = event.from_user.id
    bot_username = (await event.bot.get_me()).username
    
    # Session-ku oru unique token
    verify_token = str(uuid.uuid4())[:8]
    await db.users.update_one({"user_id": user_id}, {"$set": {"last_token": verify_token}})
    
    # Telegram start link
    unlock_payload = f"https://t.me/{bot_username}?start=verify_{verify_token}"
    encoded_url = urllib.parse.quote(unlock_payload)
    
    # Headers to bypass bot detection
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    final_url = unlock_payload # Fallback
    
    try:
        # TEXT format-la request anupuroam (Innum safe)
        # Check: .env la SHORTENER_URL=https://tnlinks.in/api?api=YOUR_KEY&url= mattum irukanum
        api_url = f"{SHORTENER_URL}{encoded_url}&format=text"
        response = requests.get(api_url, headers=headers, timeout=15)
        
        if response.status_code == 200 and "http" in response.text:
            final_url = response.text.strip()
    except Exception as e:
        print(f"Shortener Error: {e}")

    text = (
        "💎 **CoupleDating Premium** 💖\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🚀 **1 Hour Instant Access:**\n"
        "Keela irukura link-ah click panni ads skip pannunga. Mudichu thirumba varumbothu activation option varum! ⚡\n\n"
        "⚠️ **Note:** Direct-ah verify panna mudiyaathu, link skip panniye aaganum."
    )
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔓 Unlock 1 Hour Premium", url=final_url)],
        [types.InlineKeyboardButton(text="🔙 Back", callback_data="main_menu")]
    ])
    
    if isinstance(event, types.Message):
        await event.answer(text, reply_markup=kb)
    else:
        await event.message.edit_text(text, reply_markup=kb)

# Activation handler
@router.callback_query(F.data.startswith("activate_"))
async def activate_premium(callback: types.CallbackQuery):
    token_received = callback.data.split("_")[1]
    user_id = callback.from_user.id
    user = await db.users.find_one({"user_id": user_id})
    
    if user and user.get("last_token") == token_received:
        import datetime
        expiry = datetime.datetime.now() + datetime.timedelta(hours=1)
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"is_premium": True, "expiry_date": expiry.strftime("%Y-%m-%d %H:%M:%S"), "last_token": None}}
        )
        await callback.message.edit_text(f"✅ **Premium Activated!** 💎\nValid until: `{expiry.strftime('%I:%M %p')}`")
    else:
        await callback.answer("❌ Verification Failed! Please click the link again.", show_alert=True)
    
