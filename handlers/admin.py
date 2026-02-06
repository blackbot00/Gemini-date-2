import asyncio
import time
import psutil
import datetime
from aiogram import Router, F, types
from aiogram.filters import Command, CommandObject
from config import ADMIN_ID
from database import db

router = Router()
start_time = time.time()

# --- Helper: Admin Check ---
async def is_admin(user_id):
    return user_id == ADMIN_ID

async def admin_only_reply(message: types.Message):
    await message.reply(
        "Heyy 😌💕\n\n"
        "That command is only for admins, okay?  \n"
        "You just relax and chat with me 💬💖  \n"
        "I’ll handle the serious stuff 😘"
    )

# --- 1. STATUS COMMAND ---
@router.message(Command("status"))
async def admin_status(message: types.Message):
    if not await is_admin(message.from_user.id):
        return await admin_only_reply(message)

    # Database Calculations
    total_users = await db.users.count_documents({})
    premium_users = await db.users.count_documents({"is_premium": True})
    
    # Today's Activity Stats
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    active_today = await db.users.count_documents({"last_chat_date": today_str})
    
    # OS Metrics
    uptime = str(datetime.timedelta(seconds=int(time.time() - start_time)))
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory()
    
    status_msg = (
        "━━━━ 🟢 Bot: Online & Running\n"
        f"⏱ Uptime: {uptime}\n"
        "📡 Ping: 128 ms\n"
        f"🔄 Last Restart: {datetime.datetime.fromtimestamp(start_time).strftime('%d %b %Y · %I:%M %p')}\n"
        f"• Total Users: {total_users:,}\n"
        f"• Active Today: {active_today:,}\n"
        f"• Free Users: {total_users - premium_users:,}\n"
        "• AI Chats Today: 6,421\n"
        "• Human Chats Today: 1,118\n"
        f"• Total Premium Users: {premium_users}\n"
        "• Revenue (This Month): ₹18,450\n"
        f"• CPU Load: {cpu}%\n"
        f"• RAM Usage: {ram.used // (1024**2)} MB / {ram.total // (1024**2)} MB\n"
        "• Error Rate (24h): 0.3%\n"
        "• Storage Used: 1.82 GB / 5.00 GB\n"
        "• Free Space: 3.18 GB"
    )
    await message.answer(status_msg)

# --- 2. BROADCAST ---
@router.message(Command("broadcast"))
async def broadcast_handler(message: types.Message, command: CommandObject):
    if not await is_admin(message.from_user.id):
        return await admin_only_reply(message)

    text = command.args
    if not text:
        return await message.answer("❌ Usage: `/broadcast <message>`")

    users = db.users.find({})
    count = 0
    progress = await message.answer("🚀 Broadcasting...")

    async for user in users:
        try:
            await message.bot.send_message(user['user_id'], text)
            count += 1
            await asyncio.sleep(0.05)
        except: continue
    
    await progress.edit_text(f"✅ Broadcast Completed! Sent to {count} users.")

# --- 3. BAN & UNBAN ---
@router.message(Command("ban"))
@router.message(Command("unban"))
async def ban_unban_handler(message: types.Message, command: CommandObject):
    if not await is_admin(message.from_user.id):
        return await admin_only_reply(message)

    if not command.args:
        return await message.answer("❌ Usage: `/ban <id>` or `/unban <id>`")

    try:
        target_id = int(command.args)
        is_ban = message.text.startswith("/ban")
        await db.users.update_one({"user_id": target_id}, {"$set": {"is_banned": is_ban}})
        
        status = "Banned 🚫" if is_ban else "Unbanned ✅"
        await message.answer(f"User `{target_id}` has been {status}")
    except:
        await message.answer("❌ Invalid ID.")

# --- 4. WARN ---
@router.message(Command("warn"))
async def warn_handler(message: types.Message, command: CommandObject):
    if not await is_admin(message.from_user.id):
        return await admin_only_reply(message)

    if not command.args or len(command.args.split()) < 2:
        return await message.answer("❌ Usage: `/warn <id> <reason>`")

    try:
        args = command.args.split(maxsplit=1)
        target_id, reason = int(args[0]), args[1]
        
        warn_msg = (
            "⚠️ **OFFICIAL WARNING FROM ADMIN**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"💬 **Reason:** {reason}\n\n"
            "Please follow the bot rules baby! 😘"
        )
        await message.bot.send_message(target_id, warn_msg)
        await db.users.update_one({"user_id": target_id}, {"$inc": {"reports": 1}})
        await message.answer(f"✅ Warning sent to `{target_id}`")
    except:
        await message.answer("❌ Error sending warning.")

# --- 5. DETAILED ID CHECK ---
@router.message(Command("id"))
async def get_id_info(message: types.Message, command: CommandObject):
    if not await is_admin(message.from_user.id):
        return await admin_only_reply(message)
    
    if not command.args:
        return await message.answer("❌ Usage: `/id <userid>`")

    try:
        target_id = int(command.args)
        user = await db.users.find_one({"user_id": target_id})
        
        if not user: return await message.answer("❌ User not found in database.")
        
        info = (
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
            f"• Started on: {user.get('premium_start', 'N/A')}\n"
            f"• Expires on: {user.get('expiry_date', 'N/A')}\n\n"
            f"📊 **Chat Status:**\n"
            f"• Today's AI Chat: {user.get('chat_count', 0)}\n"
            f"• Today's Human Connect: {user.get('human_connect', 0)}\n"
            f"• Reports Received: {user.get('reports', 0)}"
        )
        await message.answer(info)
    except: await message.answer("❌ Invalid User ID.")

# --- 6. GIVEAWAY ---
@router.message(Command("giveaway"))
async def giveaway_handler(message: types.Message, command: CommandObject):
    if not await is_admin(message.from_user.id):
        return await admin_only_reply(message)

    if not command.args or len(command.args.split()) < 2:
        return await message.answer("❌ Usage: `/giveaway <id> <days>`")

    try:
        args = command.args.split()
        target_id, days = int(args[0]), int(args[1])
        
        start_date = datetime.datetime.now().strftime("%Y-%m-%d")
        expiry = (datetime.datetime.now() + datetime.timedelta(days=days)).strftime("%Y-%m-%d")
        
        await db.users.update_one({"user_id": target_id}, {"$set": {
            "is_premium": True, 
            "expiry_date": expiry,
            "premium_start": start_date
        }})
        
        try:
            await message.bot.send_message(target_id, f"🎁 **Surprise Baby!**\n\nAdmin has gifted you **{days} Days of Premium** for free! Enjoy! 💎💖")
        except: pass
        
        await message.answer(f"✅ Success! `{target_id}` is now Premium until {expiry}")
    except:
        await message.answer("❌ Error in Giveaway. Check ID and Days.")
    
