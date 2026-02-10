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
    
    # documentation-la sonna maari URL encoding
    encoded_url = urllib.parse.quote(unlock_payload)
    
    # Fallback to direct link if API fails
    final_button_url = unlock_payload 
    
    # headers add pannuraen - idhu real browser maari TNLinks-ah namba veykkum
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        # JSON response logic (standard format)
        # Note: .env la SHORTENER_URL=https://tnlinks.in/api?api=YOUR_KEY&url= mattum irukunu pathukonga
        # format=text-ah remove pannidunga (if exists)
        api_request_url = f"{SHORTENER_URL}{encoded_url}"
        
        response = requests.get(api_request_url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                final_button_url = data.get("shortenedUrl")
            else:
                print(f"API Error Message: {data.get('message')}")
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
            
