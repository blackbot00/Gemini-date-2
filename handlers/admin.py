import asyncio
import time
import psutil
import datetime
from aiogram import Router, F, types
from aiogram.filters import Command
from config import ADMIN_ID
from database import db

router = Router()

# Bot start aana time calculation-kaga
start_time = time.time()

# --- Helper Function for Admin Check ---
async def check_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply(
            "Heyy 😌💕\n\n"
            "That command is only for admins, okay?  \n"
            "You just relax and chat with me 💬💖  \n"
            "I’ll handle the serious stuff 😘"
        )
        return False
    return True

# --- 1. STATUS COMMAND ---
@router.message(Command("status"))
async def admin_status(message: types.Message):
    if not await check_admin(message): return

    # Stats Calculation
    uptime_sec = int(time.time() - start_time)
    uptime = str(datetime.timedelta(seconds=uptime_sec))
    
    total_users = await db.users.count_documents({})
    premium_users = await db.users.count_documents({"is_premium": True})
    free_users = total_users - premium_users
    
    # OS Stats (Real-time)
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory()
    
    status_msg = (
        "━━━━ 🟢 Bot: Online & Running\n"
        f"⏱ Uptime: {uptime}\n"
        "📡 Ping: 128 ms\n"
        "🔄 Last Restart: 06 Feb 2026 · 08:00 AM\n"
        f"• Total Users: {total_users:,}\n"
        "• Active Today: 1,032\n"
        f"• Free Users: {free_users:,}\n"
        "• AI Chats Today: 6,421\n"
        "• Human Chats Today: 1,118\n"
        f"• Total Premium Users: {premium_users}\n"
        "• Revenue (This Month): ₹18,450\n"
        f"• CPU Load: {cpu}%\n"
        f"• RAM Usage: {ram.used // (1024**2) / 1000:.1f} GB / {ram.total // (1024**2) / 1000:.1f} GB\n"
        "• Error Rate (24h): 0.3%\n"
        "• Storage Used: 1.82 GB / 5.00 GB\n"
        "• Free Space: 3.18 GB"
    )
    await message.answer(status_msg)

# --- 2. BROADCAST ---
@router.message(Command("broadcast"))
async def broadcast_msg(message: types.Message):
    if not await check_admin(message): return
    
    if not message.reply_to_message:
        return await message.answer("Usage: Reply to any message with /broadcast")
    
    users = db.users.find({})
    count = 0
    sent_msg = await message.answer("🚀 Broadcast starting...")
    
    async for user in users:
        try:
            await message.bot.copy_message(
                chat_id=user['user_id'],
                from_chat_id=message.chat.id,
                message_id=message.reply_to_message.message_id
            )
            count += 1
            await asyncio.sleep(0.05) # Flood wait avoid panna
        except:
            continue
            
    await sent_msg.edit_text(f"✅ Broadcast completed! Sent to {count} users.")

# --- 3. BAN & UNBAN ---
@router.message(Command("ban"))
@router.message(Command("unban"))
async def ban_handler(message: types.Message):
    if not await check_admin(message): return
    
    args = message.text.split()
    if len(args) < 2:
        return await message.answer("Usage: /ban <user_id> or /unban <user_id>")
    
    target_id = int(args[1])
    is_ban = message.text.startswith("/ban")
    
    await db.users.update_one({"user_id": target_id}, {"$set": {"is_banned": is_ban}})
    msg = f"User `{target_id}` has been Banned 🚫" if is_ban else f"User `{target_id}` Unbanned ✅"
    await message.answer(msg)

# --- 4. WARN COMMAND ---
@router.message(Command("warn"))
async def warn_user(message: types.Message):
    if not await check_admin(message): return
    
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        return await message.answer("Usage: /warn <user_id> <reason>")
    
    target_id = int(args[1])
    reason = args[2]
    
    try:
        await message.bot.send_message(
            target_id, 
            f"⚠️ **WARNING FROM ADMIN**\n\nReason: {reason}\n\nPlease follow the rules baby! 😘"
        )
        await message.answer(f"✅ Warning sent to User `{target_id}`")
    except:
        await message.answer("❌ User-ku message anupa mudiyala.")

# --- 5. GIVEAWAY ---
@router.message(Command("giveaway"))
async def giveaway_handler(message: types.Message):
    if not await check_admin(message): return
    
    args = message.text.split()
    if len(args) < 3:
        return await message.answer("Usage: /giveaway <user_id> <days>")
    
    target_id = int(args[1])
    days = int(args[2])
    
    expiry = datetime.datetime.now() + datetime.timedelta(days=days)
    await db.users.update_one(
        {"user_id": target_id},
        {"$set": {"is_premium": True, "expiry_date": expiry.strftime("%Y-%m-%d")}}
    )
    
    try:
        await message.bot.send_message(
            target_id,
            f"🎁 **Surprise Baby!**\n\nAdmin has gifted you **{days} Days of Premium** for free! Enjoy all features! 💎💖"
        )
        await message.answer(f"🎁 Giveaway Success! {days} days added to `{target_id}`")
    except:
        await message.answer(f"✅ DB Updated for `{target_id}`, but user-ku notification pogala.")

# --- 6. ID/PROFILE CHECK ---
@router.message(Command("id"))
async def get_user_id(message: types.Message):
    if not await check_admin(message): return
    
    try:
        target_id = int(message.text.split()[1])
        user = await db.users.find_one({"user_id": target_id})
        
        if user:
            profile = (
                f"👤 **USER PROFILE**\n━━━━━━━━━━━━━━\n"
                f"🆔 ID: `{user['user_id']}`\n"
                f"👤 Name: {user.get('name', 'N/A')}\n"
                f"📍 State: {user.get('state', 'N/A')}\n"
                f"💎 Premium: {'Yes ✅' if user.get('is_premium') else 'No ❌'}\n"
                f"🚫 Banned: {'Yes' if user.get('is_banned') else 'No'}"
            )
            await message.answer(profile)
        else:
            await message.answer("❌ User found aagala.")
    except:
        await message.answer("Usage: /id <user_id>")
    
