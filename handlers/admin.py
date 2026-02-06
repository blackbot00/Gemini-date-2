import asyncio
import time
import psutil
import datetime
from aiogram import Router, F, types
from aiogram.filters import Command
from config import ADMIN_ID
from database import db

router = Router()
start_time = time.time()

async def is_admin(user_id):
    return user_id == ADMIN_ID

@router.message(Command("status"))
async def admin_status(message: types.Message):
    if not await is_admin(message.from_user.id):
        return await message.reply("Heyy 😌💕\nThat command is only for admins, okay? 😘")

    uptime = str(datetime.timedelta(seconds=int(time.time() - start_time)))
    total_users = await db.users.count_documents({})
    premium_users = await db.users.count_documents({"is_premium": True})
    
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory()
    
    status_msg = (
        "━━━━ 🟢 Bot: Online\n"
        f"⏱ Uptime: {uptime}\n"
        f"• Total Users: {total_users}\n"
        f"• Premium Users: {premium_users}\n"
        f"• CPU Load: {cpu}%\n"
        f"• RAM Usage: {ram.percent}%"
    )
    await message.answer(status_msg)

@router.message(Command("id"))
async def get_id_info(message: types.Message):
    if not await is_admin(message.from_user.id): return
    try:
        args = message.text.split()
        target_id = int(args[1])
        user = await db.users.find_one({"user_id": target_id})
        
        if not user: return await message.answer("❌ User not found.")
        
        info = (
            f"👤 **USER PROFILE**\n"
            f"ID: `{user['user_id']}`\n"
            f"Name: {user.get('name')}\n"
            f"Premium: {user.get('is_premium')}\n"
            f"Joined: {user.get('joined_date')}"
        )
        await message.answer(info)
    except: await message.answer("Usage: /id <userid>")

@router.message(Command("giveaway"))
async def giveaway(message: types.Message):
    if not await is_admin(message.from_user.id): return
    try:
        args = message.text.split()
        target_id, days = int(args[1]), int(args[2])
        expiry = (datetime.datetime.now() + datetime.timedelta(days=days)).strftime("%Y-%m-%d")
        
        await db.users.update_one({"user_id": target_id}, {"$set": {
            "is_premium": True, 
            "expiry_date": expiry,
            "premium_start": datetime.datetime.now().strftime("%Y-%m-%d")
        }})
        await message.bot.send_message(target_id, f"🎁 Premium Gifted: {days} days! Enjoy! 💎")
        await message.answer(f"✅ Success! ID {target_id} is now Premium.")
    except: await message.answer("Usage: /giveaway <id> <days>")
