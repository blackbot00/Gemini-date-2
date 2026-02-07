from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from database import db
from config import LOG_GROUP_2, LOG_GROUP_1
from utils.keyboards import get_main_menu
import datetime
import asyncio

router = Router()

# --- HELPER: EXIT LOGIC ---
async def exit_logic(message, state, user_id=None):
    uid = user_id or (message.chat.id if hasattr(message, 'chat') else message.from_user.id)
    user = await db.users.find_one({"user_id": uid})
    
    if user and user.get("partner"):
        partner_id = user.get("partner")
        # Clear DB for both
        await db.users.update_many({"user_id": {"$in": [uid, partner_id]}}, {"$set": {"status": "idle", "partner": None}})
        
        kb = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🚫 Report Partner", callback_data=f"report_{partner_id}")]])
        
        # Notify Partner
        await message.bot.send_message(partner_id, "⚠️ Partner left the chat.", reply_markup=get_main_menu())
        m1 = await message.bot.send_message(partner_id, "Report if needed (9s):", reply_markup=kb)
        
        # Notify User
        if isinstance(message, types.CallbackQuery):
            await message.message.answer("Chat ended.", reply_markup=get_main_menu())
            m2 = await message.message.answer("Report if needed (9s):", reply_markup=kb)
        else:
            await message.answer("Chat ended.", reply_markup=get_main_menu())
            m2 = await message.answer("Report if needed (9s):", reply_markup=kb)
        
        # Auto Delete Report Buttons
        asyncio.create_task(delete_after(m1, 9))
        asyncio.create_task(delete_after(m2, 9))
    else:
        await db.users.update_one({"user_id": uid}, {"$set": {"status": "idle", "partner": None}})
        if isinstance(message, types.CallbackQuery):
            await message.message.answer("Chat ended.", reply_markup=get_main_menu())
        else:
            await message.answer("Chat ended.", reply_markup=get_main_menu())
    
    await state.clear()

async def delete_after(message: types.Message, delay: int):
    await asyncio.sleep(delay)
    try: await message.delete()
    except: pass

async def find_partner(user_id):
    return await db.users.find_one({"status": "searching", "user_id": {"$ne": user_id}})

# --- 1. EXIT BUTTON FIX ---
@router.callback_query(F.data == "exit_chat")
async def exit_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("Ending chat...")
    await exit_logic(callback, state, callback.from_user.id)

# --- SEARCH LOGIC ---
@router.callback_query(F.data == "chat_human")
async def start_human_search(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_data = await db.users.find_one({"user_id": user_id})
    if not user_data: return await callback.answer("⚠️ Register first!", show_alert=True)

    is_premium = user_data.get("is_premium", False)
    partner = await find_partner(user_id)
    now = datetime.datetime.now()
    
    if partner:
        await db.users.update_one({"user_id": user_id}, {"$set": {"status": "chatting", "partner": partner['user_id'], "chat_start": now}, "$inc": {"daily_chats": 1}})
        await db.users.update_one({"user_id": partner['user_id']}, {"$set": {"status": "chatting", "partner": user_id, "chat_start": now}, "$inc": {"daily_chats": 1}})
        
        def partner_info(p, viewer_is_premium):
            gender_text = p['gender'] if viewer_is_premium else "🔒 Locked (Premium Required) 💎"
            return f"💌 **Partner Details**\n━━━━━━━━━━━━━━\n👤 Gender: {gender_text}\n🎂 Age: {p['age']}\n📍 State: {p['state']}"

        # Delete search msg and show details
        await callback.message.edit_text(f"{partner_info(partner, is_premium)}\n\nConnected! Start chatting!", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🛑 Exit Chat", callback_data="exit_chat")]]))
        await callback.bot.send_message(partner['user_id'], f"{partner_info(user_data, partner.get('is_premium'))}\n\nConnected! Start chatting!", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🛑 Exit Chat", callback_data="exit_chat")]]))
    else:
        await db.users.update_one({"user_id": user_id}, {"$set": {"status": "searching"}})
        await callback.message.edit_text("🔍 Searching for a partner...", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="❌ Cancel", callback_data="exit_chat")]]))

# --- MESSAGE RELAY & LOGS ---
@router.message(F.chat.type == "private")
async def relay_handler(message: types.Message, state: FSMContext):
    # Ignore commands
    if message.text and message.text.startswith("/"):
        if message.text == "/exit": return await exit_logic(message, state)
        return

    user = await db.users.find_one({"user_id": message.from_user.id})
    
    # 3. FIX: Not connected message
    if not user or user.get("status") != "chatting":
        # Don't reply to random media if not in state
        if message.text or message.photo or message.video:
            return await message.answer("⚠️ **Not Connected!**\nPlease click 'Chat with Human' first to find a partner. ❤️")
        return

    partner_id = user.get("partner")
    is_premium = user.get("is_premium", False)
    partner_data = await db.users.find_one({"user_id": partner_id})

    # 2. LOGGING HEADER
    log_header = f"📤({user['name']})[`{user['user_id']}`] ➜ ({partner_data['name']})[`{partner_id}`] 📩"

    try:
        if message.text:
            # Link check for free users
            if not is_premium:
                forbidden = ["http", ".com", ".in", "@", "t.me"]
                if any(x in message.text.lower() for x in forbidden):
                    return await message.answer("⚠️ Links/Usernames are blocked for Free users! 💎")
            
            await message.bot.send_message(partner_id, message.text)
            await message.bot.send_message(LOG_GROUP_2, f"{log_header}\n💬 {message.text}")
        
        else:
            # Media logic
            if not is_premium:
                elapsed = (datetime.datetime.now() - user.get("chat_start")).total_seconds()
                if elapsed < 180:
                    return await message.answer(f"⏳ Media enabled in {int(180 - elapsed)}s.")

            # Send to partner & Log
            await message.bot.send_message(LOG_GROUP_2, log_header)
            await message.forward(LOG_GROUP_2) # Media log

            if message.photo: await message.bot.send_photo(partner_id, message.photo[-1].file_id, caption=message.caption)
            elif message.video: await message.bot.send_video(partner_id, message.video.file_id, caption=message.caption)
            elif message.document: await message.bot.send_document(partner_id, message.document.file_id, caption=message.caption)
            elif message.animation: await message.bot.send_animation(partner_id, message.animation.file_id)
    except: pass
        
