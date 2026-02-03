from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from database import db
from config import LOG_GROUP_2
import datetime

router = Router()

async def find_partner(user_id, gender_pref=None):
    query = {"status": "searching", "user_id": {"$ne": user_id}}
    if gender_pref: query["gender"] = gender_pref
    return await db.users.find_one(query)

@router.callback_query(F.data == "chat_human")
async def start_human_search(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_data = await db.users.find_one({"user_id": user_id})

    if not user_data:
        return await callback.answer("⚠️ Please register first with /start", show_alert=True)

    if not user_data.get("is_premium", False) and user_data.get("daily_chats", 0) >= 11:
        return await callback.answer("Daily limit reached! Upgrade to Premium 💎", show_alert=True)

    await db.users.update_one({"user_id": user_id}, {"$set": {"status": "searching"}})
    await callback.message.edit_text("🔍 Searching for a partner...", 
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="❌ Cancel", callback_data="exit_chat")]
        ]))

    partner = await find_partner(user_id)
    if partner:
        await db.users.update_one({"user_id": user_id}, {"$set": {"status": "chatting", "partner": partner['user_id']}})
        await db.users.update_one({"user_id": partner['user_id']}, {"$set": {"status": "chatting", "partner": user_id}})
        
        await callback.message.edit_text(f"❤️ **Partner Found!**\nAge: {partner['age']}\n\nStart chatting!", 
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🛑 Exit", callback_data="exit_chat")]]))
        await callback.bot.send_message(partner['user_id'], "❤️ **Partner Found!**\nStart chatting!")

@router.message(F.text & ~F.text.startswith('/'))
async def relay_message(message: types.Message):
    user = await db.users.find_one({"user_id": message.from_user.id})
    if user and user.get("status") == "chatting":
        partner_id = user.get("partner")
        if not user.get("is_premium") and ("http" in message.text or ".com" in message.text):
            return await message.answer("⚠️ Links blocked for Free users!")

        log_text = f"[{datetime.datetime.now().strftime('%I:%M %p')}] {user['name']} ➜ Partner\n💬 {message.text}"
        await message.bot.send_message(LOG_GROUP_2, log_text)
        await message.bot.send_message(partner_id, message.text)
        
