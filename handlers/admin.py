from aiogram import Router, F, types
from aiogram.filters import Command
from config import ADMIN_ID, LOG_GROUP_1
from database import db
import time

router = Router()

@router.message(Command("status"))
async def admin_status(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("❌ This command is only for Admin")
    
    total_users = await db.users.count_documents({})
    premium_users = await db.users.count_documents({"is_premium": True})
    
    status_msg = (
        "🤖 **BOT STATUS — ADMIN**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🟢 Bot: Online\n"
        f"👥 Total Users: {total_users}\n"
        f"💎 Premium Users: {premium_users}\n"
        "📡 DB Status: Connected ✅\n"
        "━━━━━━━━━━━━━━━━━━"
    )
    await message.answer(status_msg)

@router.message(Command("id"))
async def get_user_id(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    # Syntax: /id 123456789
    target_id = int(message.text.split()[1])
    user = await db.users.find_one({"user_id": target_id})
    
    if user:
        profile = (
            f"👤 **USER PROFILE**\n━━━━━━━━━━━━━━\n"
            f"🆔 ID: `{user['user_id']}`\n"
            f"👤 Name: {user['name']}\n"
            f"📍 State: {user['state']}\n"
            f"💎 Premium: {'Yes ✅' if user['is_premium'] else 'No ❌'}"
        )
        await message.answer(profile)
  
