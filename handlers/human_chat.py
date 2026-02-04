from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from database import db
from config import LOG_GROUP_2
from utils.keyboards import get_main_menu
import datetime

router = Router()

async def find_partner(user_id):
    # Find the oldest searching user to avoid shuffle (First-in-First-out)
    return await db.users.find_one({"status": "searching", "user_id": {"$ne": user_id}})

@router.callback_query(F.data == "chat_human")
async def start_human_search(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_data = await db.users.find_one({"user_id": user_id})

    if not user_data:
        return await callback.answer("⚠️ Please register first with /start", show_alert=True)

    if not user_data.get("is_premium", False) and user_data.get("daily_chats", 0) >= 11:
        return await callback.answer("Daily limit reached! Upgrade to Premium 💎", show_alert=True)

    # First, check if someone is already searching
    partner = await find_partner(user_id)
    
    if partner:
        # Match found - Lock both immediately
        await db.users.update_one({"user_id": user_id}, {"$set": {"status": "chatting", "partner": partner['user_id']}})
        await db.users.update_one({"user_id": partner['user_id']}, {"$set": {"status": "chatting", "partner": user_id}})
        
        # Details Reveal Logic
        def partner_info(p, viewer_is_premium):
            gender_text = p['gender'] if viewer_is_premium else "🔒 Available with Premium 💎"
            return (
                f"💌 **Your Partner Details**\n"
                f"━━━━━━━━━━━━━━\n"
                f"👤 Gender: {gender_text}\n"
                f"🎂 Age: {p['age']}\n"
                f"📍 State: {p['state']}\n\n"
                f"✨ Unlock Premium to see the complete picture 💖"
            )

        # Send to User 1
        await callback.message.edit_text(
            f"{partner_info(partner, user_data.get('is_premium'))}\n\nConnected! Start chatting! 😍\nUse /exit to stop.",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🛑 Exit", callback_data="exit_chat")]])
        )
        
        # Send to User 2 (Partner)
        await callback.bot.send_message(
            partner['user_id'], 
            f"{partner_info(user_data, partner.get('is_premium'))}\n\nConnected! Start chatting! 😍\nUse /exit to stop.",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🛑 Exit", callback_data="exit_chat")]])
        )
    else:
        # No partner, set status to searching
        await db.users.update_one({"user_id": user_id}, {"$set": {"status": "searching"}})
        await callback.message.edit_text("🔍 Searching for a partner...", 
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="❌ Cancel", callback_data="exit_chat")]
            ]))

@router.message(F.text)
async def relay_message(message: types.Message, state: FSMContext):
    # Handle /exit command
    if message.text == "/exit":
        return await exit_logic(message, state)

    user = await db.users.find_one({"user_id": message.from_user.id})
    if user and user.get("status") == "chatting":
        partner_id = user.get("partner")
        
        # Block links for free users
        if not user.get("is_premium") and ("http" in message.text.lower() or ".com" in message.text.lower()):
            return await message.answer("⚠️ Links blocked for Free users!")

        partner_data = await db.users.find_one({"user_id": partner_id})
        
        # NEW LOG FORMAT: 📤(Name)[Id]➜ (name)[id]📩
        log_text = (
            f"📤({user['name']})[{user['user_id']}] ➜ ({partner_data['name']})[{partner_id}]📩\n"
            f"💬 {message.text}"
        )
        await message.bot.send_message(LOG_GROUP_2, log_text)
        
        # Relay message
        try:
            await message.bot.send_message(partner_id, message.text)
        except:
            await exit_logic(message, state)

@router.callback_query(F.data == "exit_chat")
async def exit_callback(callback: types.CallbackQuery, state: FSMContext):
    await exit_logic(callback.message, state, callback.from_user.id)
    await callback.answer()

async def exit_logic(message, state, user_id=None):
    uid = user_id or message.chat.id
    user = await db.users.find_one({"user_id": uid})
    
    if user and user.get("partner"):
        partner_id = user.get("partner")
        # Reset both
        await db.users.update_many({"user_id": {"$in": [uid, partner_id]}}, {"$set": {"status": "idle", "partner": None}})
        await message.bot.send_message(partner_id, "⚠️ Partner left the chat.", reply_markup=get_main_menu())
        
    await db.users.update_one({"user_id": uid}, {"$set": {"status": "idle", "partner": None}})
    await message.answer("Chat ended.", reply_markup=get_main_menu())
    await state.clear()
            
