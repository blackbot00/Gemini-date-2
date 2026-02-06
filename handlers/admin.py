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

async def check_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("Heyy 😌💕\n\nThat command is only for admins, okay? \nYou just relax and chat with me 💬💖\nI’ll handle the serious stuff 😘")
        return False
    return True

@router.message(Command("status"))
async def admin_status(message: types.Message):
    if not await check_admin(message): return

    uptime = str(datetime.timedelta(seconds=int(time.time() - start_time)))
    total_users = await db.users.count_documents({})
    premium_users = await db.users.count_documents({"is_premium": True})
    
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    active_today = await db.users.count_documents({"last_chat_date": today})
    
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory()
    
    status_msg = (
        "━━━━ 🟢 Bot: Online & Running\n"
        f"⏱ Uptime: {uptime}\n"
        f"📡 DB Status: Connected ✅\n"
        f"🔄 Last Restart: {datetime.datetime.fromtimestamp(start_time).strftime('%d %b %Y · %I:%M %p')}\n"
        f"• Total Users: {total_users}\n"
        f"• Active Today: {active_today}\n"
        f"• Free Users: {total_users - premium_users}\n"
        f"• Total Premium Users: {premium_users}\n"
        f"• CPU Load: {cpu}%\n"
        f"• RAM Usage: {ram.used // (1024**2) / 1024:.1f} GB / {ram.total // (1024**2) / 1024:.1f} GB"
    )
    await message.answer(status_msg)

@router.message(Command("id"))
async def get_detailed_id(message: types.Message):
    if not await check_admin(message): return
    try:
        target_id = int(message.text.split()[1])
        user = await db.users.find_one({"user_id": target_id})
        if not user: return await message.answer("❌ User found aagala.")

        profile = (
            f"👤 **USER PROFILE**\n━━━━━━━━━━━━━━\n"
            f"📛 Name: {user.get('name', 'N/A')}\n"
            f"🔗 Username: @{user.get('username', 'N/A')}\n"
            f"🆔 ID: `{user['user_id']}`\n"
            f"📅 Joined: {user.get('joined_date', 'N/A')}\n"
            f"📍 State: {user.get('state', 'N/A')}\n"
            f"🎂 Age: {user.get('age', 'N/A')}\n"
            f"👫 Gender: {user.get('gender', 'N/A')}\n\n"
            f"💎 **Premium Status:**\n"
            f"• Status: {'Active ✅' if user.get('is_premium') else 'Inactive ❌'}\n"
            f"• Started: {user.get('premium_start', 'N/A')}\n"
            f"• Expires: {user.get('expiry_date', 'N/A')}\n\n"
            f"📊 **Chat Status:**\n"
            f"• Today's AI Chat: {user.get('chat_count', 0)}\n"
            f"• Reports Received: {user.get('reports', 0)}"
        )
        await message.answer(profile)
    except: await message.answer("Usage: /id <user_id>")

@router.message(Command("ban"))
@router.message(Command("unban"))
async def ban_handler(message: types.Message):
    if not await check_admin(message): return
    try:
        target_id = int(message.text.split()[1])
        is_ban = message.text.startswith("/ban")
        await db.users.update_one({"user_id": target_id}, {"$set": {"is_banned": is_ban}})
        await message.answer(f"✅ User `{target_id}` {'Banned 🚫' if is_ban else 'Unbanned ✅'}")
    except: await message.answer("Usage: /ban <id>")

@router.message(Command("giveaway"))
async def giveaway_handler(message: types.Message):
    if not await check_admin(message): return
    try:
        args = message.text.split()
        target_id, days = int(args[1]), int(args[2])
        expiry = (datetime.datetime.now() + datetime.timedelta(days=days)).strftime("%Y-%m-%d")
        await db.users.update_one({"user_id": target_id}, {"$set": {
            "is_premium": True, 
            "expiry_date": expiry,
            "premium_start": datetime.datetime.now().strftime("%Y-%m-%d")
        }})
        await message.bot.send_message(target_id, f"🎁 Surprise Baby! Admin gifted you {days} days of Premium! Enjoy! 💎💖")
        await message.answer(f"✅ Giveaway Success to `{target_id}` till {expiry}")
    except: await message.answer("Usage: /giveaway <id> <days>")

@router.message(Command("broadcast"))
async def broadcast_handler(message: types.Message):
    if not await check_admin(message): return
    if not message.reply_to_message: return await message.answer("Reply to a message with /broadcast")
    users = db.users.find({})
    count = 0
    async for user in users:
        try:
            await message.bot.copy_message(user['user_id'], message.chat.id, message.reply_to_message.message_id)
            count += 1
            await asyncio.sleep(0.05)
        except: continue
    await message.answer(f"✅ Sent to {count} users.")
        
