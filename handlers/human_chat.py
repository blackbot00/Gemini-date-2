from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from database import db
from config import LOG_GROUP_2, LOG_GROUP_1
from utils.keyboards import get_main_menu
import datetime
import asyncio

router = Router()

# --- HELPER FUNCTIONS ---
async def find_partner(user_id):
    return await db.users.find_one({"status": "searching", "user_id": {"$ne": user_id}})

async def delete_after(message: types.Message, delay: int):
    await asyncio.sleep(delay)
    try: await message.delete()
    except: pass

async def exit_logic(message, state, user_id=None):
    uid = user_id or message.chat.id
    user = await db.users.find_one({"user_id": uid})
    
    if user and user.get("partner"):
        partner_id = user.get("partner")
        await db.users.update_many({"user_id": {"$in": [uid, partner_id]}}, {"$set": {"status": "idle", "partner": None}})
        
        # Partner details-ah delete panna, edit_text use pannalam or namma kaila irukura message-ah delete pannalam
        kb = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🚫 Report Partner", callback_data=f"report_{partner_id}")]])
        
        # Partner details auto-delete logic: Partner details msg replace aayidum
        await message.bot.send_message(partner_id, "⚠️ Partner left the chat.", reply_markup=get_main_menu())
        m1 = await message.bot.send_message(partner_id, "Report if needed (9s):", reply_markup=kb)
        
        await message.answer("Chat ended.", reply_markup=get_main_menu())
        m2 = await message.answer("Report if needed (9s):", reply_markup=kb)
        
        asyncio.create_task(delete_after(m1, 9))
        asyncio.create_task(delete_after(m2, 9))
    else:
        await db.users.update_one({"user_id": uid}, {"$set": {"status": "idle", "partner": None}})
        await message.answer("Chat ended.", reply_markup=get_main_menu())
    await state.clear()

# --- SEARCH LOGIC ---
@router.callback_query(F.data == "chat_human")
async def start_human_search(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_data = await db.users.find_one({"user_id": user_id})
    is_premium = user_data.get("is_premium", False)

    if not user_data: return await callback.answer("⚠️ Register first!", show_alert=True)

    # Daily Limit Check
    if not is_premium:
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        if user_data.get("last_search_date") != today:
            await db.users.update_one({"user_id": user_id}, {"$set": {"daily_chats": 0, "last_search_date": today}})
            current_chats = 0
        else:
            current_chats = user_data.get("daily_chats", 0)
        if current_chats >= 50:
            return await callback.answer("Daily limit (50) reached! Upgrade to Premium 💎", show_alert=True)

    partner = await find_partner(user_id)
    now = datetime.datetime.now()
    
    if partner:
        # 1. FIX: Auto Delete "Searching..." message by editing it to partner details
        await db.users.update_one({"user_id": user_id}, {"$set": {"status": "chatting", "partner": partner['user_id'], "chat_start": now}, "$inc": {"daily_chats": 1}})
        await db.users.update_one({"user_id": partner['user_id']}, {"$set": {"status": "chatting", "partner": user_id, "chat_start": now}, "$inc": {"daily_chats": 1}})
        
        def partner_info(p, viewer_is_premium):
            gender_text = p['gender'] if viewer_is_premium else "🔒 Locked (Premium Required) 💎"
            return f"💌 **Partner Details**\n━━━━━━━━━━━━━━\n👤 Gender: {gender_text}\n🎂 Age: {p['age']}\n📍 State: {p['state']}"

        # Current user-ku "Searching" message-ah edit panni details kaattum
        await callback.message.edit_text(f"{partner_info(partner, is_premium)}\n\nConnected! Start chatting!", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🛑 Exit", callback_data="exit_chat")]]))
        
        # Partner-ku "Searching" message irukaathu, so fresh message anupalam
        # Note: If partner was also searching, you might need their message_id to edit, but sending a new one is safer.
        await callback.bot.send_message(partner['user_id'], f"{partner_info(user_data, partner.get('is_premium'))}\n\nConnected! Start chatting!", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🛑 Exit", callback_data="exit_chat")]]))
    else:
        await db.users.update_one({"user_id": user_id}, {"$set": {"status": "searching"}})
        await callback.message.edit_text("🔍 Searching for a partner...", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="❌ Cancel", callback_data="exit_chat")]]))

# --- MESSAGE RELAY ---
@router.message(F.chat.type == "private")
async def relay_handler(message: types.Message, state: FSMContext):
    if message.text == "/exit": return await exit_logic(message, state)
    
    # Check if user is in a state (like waiting for payment screenshot)
    # If state is NOT None, don't relay (let premium.py handle it)
    current_state = await state.get_state()
    if current_state is not None and not str(current_state).endswith("on_human_chat"): 
        return # Indha line payment screenshot process-ah interfere panna vidaathu

    user = await db.users.find_one({"user_id": message.from_user.id})
    
    # 3. FIX: Check if connected or not
    if not user or user.get("status") != "chatting":
        if not message.text.startswith("/"): # Don't trigger for commands
             return await message.answer("⚠️ **Not Connected!**\nPlease click 'Chat with Human' first to find a partner. ❤️")
        return

    partner_id = user.get("partner")
    is_premium = user.get("is_premium", False)
    
    # 2. FIX: Media and Payment Screenshot Logic
    # Relay media ONLY if chatting. Payment logic unga premium.py-la state based-ah irukanum.
    if not message.text:
        # Check if it's for human chat or payment
        if current_state is None: # Chatting but no special state
            if not is_premium:
                elapsed = (datetime.datetime.now() - user.get("chat_start")).total_seconds()
                if elapsed < 180:
                    return await message.answer(f"⏳ Media enabled in {int(180 - elapsed)}s. Upgrade to Premium for instant share! 💎")
            
            # Relay logic
            try:
                if message.photo: await message.bot.send_photo(partner_id, message.photo[-1].file_id, caption=message.caption)
                elif message.video: await message.bot.send_video(partner_id, message.video.file_id, caption=message.caption)
                elif message.document: await message.bot.send_document(partner_id, message.document.file_id, caption=message.caption)
                elif message.animation: await message.bot.send_animation(partner_id, message.animation.file_id)
            except: pass
    else:
        # Text Relay
        forbidden = ["http", ".com", ".in", "@", "t.me", ".net"]
        if not is_premium and any(x in message.text.lower() for x in forbidden):
            return await message.answer("⚠️ Links are blocked for Free users! 💎")
        
        try: await message.bot.send_message(partner_id, message.text)
        except: pass
        
