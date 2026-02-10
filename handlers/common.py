from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from utils.keyboards import get_main_menu
from database import db
import datetime

router = Router()

# --- 1. START COMMAND (Referral & Unlock Fixed) ---
@router.message(Command("start"))
async def cmd_start(message: types.Message, command: CommandObject):
    user_id = message.from_user.id
    args = command.args
    user_exists = await db.users.find_one({"user_id": user_id})

    if args:
        # Fixed: Using 'in' instead of 'startswith' for better reliability
        if "unlock_" in args:
            try:
                # Extracting ID from unlock_12345 format
                target_id = int(args.split("_")[1])
                if target_id == user_id:
                    # Current time + 1 hour with seconds for accuracy
                    expiry = datetime.datetime.now() + datetime.timedelta(hours=1)
                    await db.users.update_one(
                        {"user_id": user_id}, 
                        {"$set": {
                            "is_premium": True, 
                            "expiry_date": expiry.strftime("%Y-%m-%d %H:%M:%S")
                        }},
                        upsert=True
                    )
                    return await message.answer(f"✅ **1 Hour Premium Unlocked!** 💎\n\nExpiry: {expiry.strftime('%I:%M %p')}\nEnjoy your unlimited access!")
            except: pass

        # Referral Logic
        elif "ref_" in args and not user_exists:
            try:
                referrer_id = int(args.split("_")[1])
                if referrer_id != user_id:
                    await db.users.update_one({"user_id": referrer_id}, {"$inc": {"ref_count": 1}})
                    referrer = await db.users.find_one({"user_id": referrer_id})
                    if referrer and referrer.get("ref_count") == 5 and not referrer.get("ref_reward_claimed"):
                        expiry = datetime.datetime.now() + datetime.timedelta(days=7)
                        await db.users.update_one({"user_id": referrer_id}, {
                            "$set": {"is_premium": True, "expiry_date": expiry.strftime("%Y-%m-%d"), "ref_reward_claimed": True}
                        })
                        try:
                            await message.bot.send_message(referrer_id, "🎉 **Congratulations!**\n5 referrals reached. **1 Week Premium** active! 💎")
                        except: pass
            except: pass

    # Register user if not exists
    if not user_exists:
        await db.users.insert_one({
            "user_id": user_id,
            "name": message.from_user.full_name,
            "ref_count": 0,
            "is_premium": False,
            "joined_date": datetime.datetime.now().strftime("%Y-%m-%d")
        })

    await message.answer(f"✨ **Welcome {message.from_user.first_name}!** ❤️", reply_markup=get_main_menu())

# --- 2. PRIVACY COMMAND ---
@router.message(Command("privacy"))
async def cmd_privacy(message: types.Message):
    privacy_text = (
        "🔐 **Privacy Policy**\n\n"
        "1️⃣ 🛡️ **Safety First** — We take user safety seriously.\n"
        "2️⃣ 😇 **Don't be Misbehave** — Respect others and chat politely.\n"
        "3️⃣ 🚫 **No Personal Info** — Never share phone, OTP, address, bank details.\n"
        "4️⃣ 🚩 **Report Option** — Use Report button if someone abuses.\n"
        "5️⃣ 🔒 **Data Use** — Registration info used only for matching."
    )
    await message.answer(privacy_text)

# --- 3. ABOUT COMMAND ---
@router.message(Command("about"))
async def cmd_about(message: types.Message):
    about_text = (
        "✨ **About This Bot**\n\n"
        "Welcome to the ultimate place for fun, friendship, and romance! ❤️\n\n"
        "📢 **Main Group:** [Join Here](https://t.me/Blackheartmain)\n"
        "💬 **Discussion Group:** [Join Here](https://t.me/+liSMeNJ-2GQ4NzA9)\n\n"
        "Any doubts ask 👆🏼"
    )
    await message.answer(about_text, disable_web_page_preview=True)

# --- 4. HELP COMMAND ---
@router.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = (
        "❓ **Need Help?**\n\n"
        "🎮 **Commands:**\n"
        "/chat - Start matching with AI or Human\n"
        "/edit_profile - Edit your info\n"
        "/about - Join our groups\n"
        "/privacy - Read our rules\n"
        "/premium - Get extra features\n\n"
        "💡 **Tip:** If you find any issues, contact admin through the discussion group!"
    )
    await message.answer(help_text)

# --- 5. CHAT COMMAND ---
@router.message(Command("chat"))
async def cmd_chat_manual(message: types.Message):
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🤖 Chat with AI", callback_data="chat_ai")],
        [types.InlineKeyboardButton(text="👥 Chat with Human", callback_data="chat_human")]
    ])
    await message.answer("✨ **Start Chatting**\n\nWho would you like to talk to today? Choose below:", reply_markup=kb)

# --- 6. PREMIUM COMMAND ---
@router.message(Command("premium"))
async def cmd_premium(message: types.Message):
    from handlers.premium import premium_menu
    await premium_menu(message)
                        
