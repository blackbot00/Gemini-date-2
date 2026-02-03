from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from database import db
from config import LOG_GROUP_2
import datetime

router = Router()

# Simple Queue System using MongoDB
async def find_partner(user_id, gender_pref=None):
    # Search for someone who is 'searching' and not 'me'
    query = {"status": "searching", "user_id": {"$ne": user_id}}
    if gender_pref:
        query["gender"] = gender_pref
    
    partner = await db.users.find_one(query)
    return partner

@router.callback_query(F.data == "chat_human")
async def start_human_search(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_data = await db.users.find_one({"user_id": user_id})

    # Check Daily Limit
    if not user_data.get("is_premium") and user_data.get("daily_chats", 0) >= 11:
        await callback.answer("Daily limit reached! Upgrade to Premium 💎", show_alert=True)
        return

    await db.users.update_one({"user_id": user_id}, {"$set": {"status": "searching"}})
    await callback.message.edit_text("🔍 Searching for a partner...", 
                                     reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                                         [types.InlineKeyboardButton(text="❌ Cancel", callback_data="exit_chat")]
                                     ]))

    partner = await find_partner(user_id)
    if partner:
        # Connect them
        await db.users.update_one({"user_id": user_id}, {"$set": {"status": "chatting", "partner": partner['user_id']}})
        await db.users.update_one({"user_id": partner['user_id']}, {"$set": {"status": "chatting", "partner": user_id}})
        
        # Send Notification to both
        msg = "❤️ **Partner Found!**\n\nGender: {}\nAge: {}\n\nType message to start...".format(partner['gender'], partner['age'])
        await callback.message.edit_text(msg, reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🛑 Exit Chat", callback_data="exit_chat")]
        ]))
        await callback.bot.send_message(partner['user_id'], "❤️ **Partner Found!**\n\nType message to start...")

# Handling Messages between Users
@router.message(F.text & ~F.text.startswith('/'))
async def relay_message(message: types.Message):
    user = await db.users.find_one({"user_id": message.from_user.id})
    if user and user.get("status") == "chatting":
        partner_id = user.get("partner")
        
        # Link Filter (Free Users)
        if not user.get("is_premium") and ("http" in message.text or ".com" in message.text):
            await message.answer("⚠️ Links are not allowed for free users!")
            return

        # Log to Group 2
        time_str = datetime.datetime.now().strftime("%I:%M %p")
        log_text = f"[{time_str}] {message.from_user.first_name}({message.from_user.id}) ➜ Partner\n💬 {message.text}"
        await message.bot.send_message(LOG_GROUP_2, log_text)

        await message.bot.send_message(partner_id, message.text)
      
