import asyncio
import time
import psutil
import datetime
import shutil
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

    total_users = await db.users.count_documents({})
    premium_users = await db.users.count_documents({"is_premium": True})
    free_users = total_users - premium_users
    
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    active_today = await db.users.count_documents({"last_chat_date": today_str})
    
    # Calculate Total AI Chats for Today
    total_ai_today = 0
    async for user in db.users.find({"last_chat_date": today_str}):
        total_ai_today += user.get("chat_count", 0)
    
    uptime = str(datetime.timedelta(seconds=int(time.time() - start_time)))
    ram = psutil.virtual_memory()
    disk = shutil.disk_usage("/")
    monthly_rev = premium_users * 150 

    status_msg = (
        "📊 **BOT SYSTEM STATUS**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"⏱ **Uptime:** {uptime}\n"
        f"📡 **Ping:** Checking...\n"
        f"🔄 **Last Restart:** {datetime.datetime.fromtimestamp(start_time).strftime('%d %b %Y | %I:%M %p')}\n\n"
        "👥 **User Statistics:**\n"
        f"• Total Users: {total_users:,}\n"
        f"• Active Today: {active_today:,}\n"
        f"• Free Users: {free_users:,}\n"
        f"• Premium Users: {premium_users:,}\n\n"
        "💬 **Daily Traffic:**\n"
        f"• Today AI Chats: {total_ai_today:,}\n"
        f"• Today Human Chats: {active_today:,} sessions\n\n"
        "💰 **Finance:**\n"
        f"• Monthly Revenue: ₹{monthly_rev:,}\n\n"
        "🖥 **Server Usage:**\n"
        f"• RAM Usage: {ram.used // (1024**2)}MB / {ram.total // (1024**2)}MB\n"
        f"• Storage Used: {disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB\n"
        f"• Free Space: {disk.free // (1024**3)}GB"
    )
    
    start_ping = time.time()
    msg = await message.answer(status_msg)
    end_ping = time.time()
    ping_ms = round((end_ping - start_ping) * 1000)
    await msg.edit_text(status_msg.replace("Checking...", f"{ping_ms}ms"))

# --- 2. BROADCAST BY REPLY ---
@router.message(Command("broadcast"))
async def cmd_broadcast(message: types.Message):
    if not await is_admin(message.from_user.id):
        return await admin_only_reply(message)

    if not message.reply_to_message:
        return await message.answer("⚠️ **Reply to a message** with `/broadcast` to send it to all users.")

    broadcast_msg = message.reply_to_message
    cursor = db.users.find({})
    success, blocked = 0, 0
    status_msg = await message.answer("🚀 **Broadcast started...**")

    async for user in cursor:
        try:
            await broadcast_msg.copy_to(user['user_id'])
            success += 1
            await asyncio.sleep(0.05)
        except:
            blocked += 1
            continue

    await status_msg.edit_text(f"✅ **Broadcast Completed!**\n\n✅ Sent: {success}\n❌ Failed: {blocked}")

# --- 3. WARN USER ---
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
            "Please follow the bot rules, sweetie! 😘"
        )
        await message.bot.send_message(target_id, warn_msg)
        # Reports count incremented in DB
        await db.users.update_one({"user_id": target_id}, {"$inc": {"reports": 1}})
        await message.answer(f"✅ Warning sent to `{target_id}` and report count increased.")
    except Exception as e:
        await message.answer(f"❌ Error: {str(e)}")

# --- 4. DETAILED ID CHECK ---
@router.message(Command("id"))
async def get_id_info(message: types.Message, command: CommandObject):
    if not await is_admin(message.from_user.id):
        return await admin_only_reply(message)
    
    if not command.args:
        return await message.answer("❌ Usage: `/id <userid>`")

    try:
        target_id = int(command.args)
        user = await db.users.find_one({"user_id": target_id})
        if not user: return await message.answer("❌ User not found.")
        
        info = (
            f"👤 **USER PROFILE INFO**\n"
            "━━━━━━━━━━━━━━\n"
            f"📛 **Name:** {user.get('name', 'N/A')}\n"
            f"🔗 **Username:** @{user.get('username', 'N/A')}\n"
            f"🆔 **User ID:** `{user['user_id']}`\n"
            f"📍 **State:** {user.get('state', 'N/A')}\n"
            f"🎂 **Age:** {user.get('age', 'N/A')}\n"
            f"👫 **Gender:** {user.get('gender', 'N/A')}\n\n"
            f"🛡 **Account Status:**\n"
            f"• Tier: {'💎 Premium User' if user.get('is_premium') else '🆓 Free User'}\n"
            f"• Banned: {'Yes 🚫' if user.get('is_banned') else 'No ✅'}\n\n"
            f"🚩 **Report History:**\n"
            f"• Reports Received: {user.get('reports', 0)}\n"
            f"• Reports Sent to others: {user.get('reports_sent_count', 0)}"
        )
        await message.answer(info)
    except: await message.answer("❌ Invalid User ID.")

# --- 5. BAN & UNBAN ---
@router.message(Command("ban"))
@router.message(Command("unban"))
async def ban_unban_handler(message: types.Message, command: CommandObject):
    if not await is_admin(message.from_user.id):
        return await admin_only_reply(message)
    if not command.args: return await message.answer("❌ Usage: `/ban <id>`")
    try:
        target_id = int(command.args)
        is_ban = message.text.startswith("/ban")
        await db.users.update_one({"user_id": target_id}, {"$set": {"is_banned": is_ban}})
        await message.answer(f"User `{target_id}` {'Banned 🚫' if is_ban else 'Unbanned ✅'}")
    except: await message.answer("❌ Invalid ID.")

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
        expiry = (datetime.datetime.now() + datetime.timedelta(days=days)).strftime("%Y-%m-%d")
        await db.users.update_one({"user_id": target_id}, {"$set": {"is_premium": True, "expiry_date": expiry}})
        await message.bot.send_message(target_id, f"🎁 Admin has gifted you **{days} Days of Premium**! Enjoy! 💎")
        await message.answer(f"✅ Success! `{target_id}` is Premium until {expiry}")
    except: await message.answer("❌ Error.")
                       
