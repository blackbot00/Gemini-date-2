import requests
import urllib.parse
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
    user_id = event.from_user.id
    bot_username = (await event.bot.get_me()).username
    
    # URL-ah encode panni direct-ah oru simple verification link generate pannuvom
    unlock_payload = f"https://t.me/{bot_username}?start=verify"
    encoded_url = urllib.parse.quote(unlock_payload)
    
    final_url = unlock_payload
    try:
        api_request_url = f"{SHORTENER_URL}{encoded_url}"
        response = requests.get(api_request_url, timeout=10)
        if response.status_code == 200:
            # JSON response logic
            data = response.json()
            if data.get("status") == "success":
                final_url = data.get("shortenedUrl")
    except: pass

    text = (
        "💎 **Premium Unlock System** 💎\n\n"
        "1. Keela irukura link-ah click panni ads skip pannunga.\n"
        "2. Ads mudichu 'Start' kudutha apram, intha message-la irukura **Verify** button-ah click pannunga.\n\n"
        "⚠️ **Note:** Verify click pannaale 1 Hour premium activate aagum!"
    )
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔓 1. Unlock Link", url=final_url)],
        [types.InlineKeyboardButton(text="✅ 2. Verify Activation", callback_data="verify_now")],
        [types.InlineKeyboardButton(text="🔙 Back", callback_data="main_menu")]
    ])
    
    if isinstance(event, types.Message):
        await event.answer(text, reply_markup=kb)
    else:
        await event.message.edit_text(text, reply_markup=kb)

# --- VERIFICATION HANDLER ---
@router.callback_query(F.data == "verify_now")
async def process_verification(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    # Time update
    expiry = datetime.datetime.now() + datetime.timedelta(hours=1)
    
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"is_premium": True, "expiry_date": expiry.strftime("%Y-%m-%d %H:%M:%S")}},
        upsert=True
    )
    
    await callback.answer("✅ Premium Activated for 1 Hour!", show_alert=True)
    await callback.message.edit_text(
        f"🎉 **Success!**\n\nYour premium is active until `{expiry.strftime('%I:%M %p')}`.\n"
        "Enjoy unlimited features now! ❤️"
    )
    
