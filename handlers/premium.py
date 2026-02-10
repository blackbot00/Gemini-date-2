import requests
import urllib.parse
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from database import db
from config import SHORTENER_URL

router = Router()

@router.message(Command("premium"))
@router.callback_query(F.data == "go_premium")
async def premium_menu(event: types.Message | types.CallbackQuery, state: FSMContext = None):
    if state:
        await state.clear()
        
    user_id = event.from_user.id
    user = await db.users.find_one({"user_id": user_id})
    
    if not user:
        user = {"ref_count": 0}

    bot_username = (await event.bot.get_me()).username
    unlock_payload = f"https://t.me/{bot_username}?start=unlock_{user_id}"
    
    # TNLinks documentation padi urlencode (quote) pannanum
    encoded_url = urllib.parse.quote(unlock_payload)
    
    # Default fallback (error vandha direct link)
    final_button_url = unlock_payload 
    
    try:
        # API request with TEXT format for easier result extraction
        api_request_url = f"{SHORTENER_URL}{encoded_url}"
        response = requests.get(api_request_url, timeout=10)
        
        # In TEXT format, response is just the shortened link string
        if response.status_code == 200 and response.text.startswith("http"):
            final_button_url = response.text.strip()
            print(f"Success! Shortened URL: {final_button_url}")
    except Exception as e:
        print(f"Shortener API Error: {e}")

    ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"

    text = (
        "💎 **CoupleDating Premium** 💖\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🚀 **Instant 1 Hour Access:**\n"
        "Keela irukura link-ah click panni ads skip pannunga, auto-va premium unlock aagum! ⚡\n\n"
        "👥 **Refer & Earn:**\n"
        "5 referrals = **1 Week Premium** 🎁\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 **Your Referrals:** {user.get('ref_count', 0)} / 5\n"
        f"🔗 **Your Link:** `{ref_link}`"
    )
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔓 Unlock 1 Hour Premium", url=final_button_url)],
        [types.InlineKeyboardButton(text="🔙 Back", callback_data="main_menu")]
    ])
    
    if isinstance(event, types.Message):
        await event.answer(text, reply_markup=kb)
    else:
        try:
            await event.message.edit_text(text, reply_markup=kb)
        except:
            await event.message.answer(text, reply_markup=kb)
    
