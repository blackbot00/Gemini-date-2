from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from utils.keyboards import get_main_menu
from database import db
import datetime

router = Router()

# --- 1. START COMMAND (Handles Referral & Unlock) ---
@router.message(Command("start"))
async def cmd_start(message: types.Message, command: CommandObject):
    user_id = message.from_user.id
    args = command.args
    user_exists = await db.users.find_one({"user_id": user_id})

    # Deep Link Logic (Referral & Unlock)
    if args:
        # Shortener Unlock (1 Hour)
        if args.startswith("unlock_"):
            target_id = int(args.split("_")[1])
            if target_id == user_id:
                expiry = datetime.datetime.now() + datetime.timedelta(hours=1)
                await db.users.update_one(
                    {"user_id": user_id}, 
                    {"$set": {"is_premium": True, "expiry_date": expiry.strftime("%Y-%m-%d %H:%M")}}
                )
                return await message.answer("✅ **1 Hour Premium Unlocked!** 💎\nEnjoy unlimited AI & Human chats baby! 🔥")

        # Referral System
        if args.startswith("ref_") and not user_exists:
            referrer_id = int(args.split("_")[1])
            if referrer_id != user_id:
                await db.users.update_one({"user_id": referrer_id}, {"$inc": {"ref_count": 1}})
                
                referrer = await db.users.find_one({"user_id": referrer_id})
                if referrer.get("ref_count") == 5 and not referrer.get("ref_reward_claimed"):
                    expiry = datetime.datetime.now() + datetime.timedelta(days=7)
                    await db.users.update_one({"user_id": referrer_id}, {
                        "$set": {"is_premium": True, "expiry_date": expiry.strftime("%Y-%m-%d"), "ref_reward_claimed": True}
                    })
                    try:
                        await message.bot.send_message(referrer_id, "🎉 **Congratulations!**\n5 members referred! **1 Week Premium** Active! 💎💖")
                    except: pass

    # New User Registration
    if not user_exists:
        await db.users.insert_one({
            "user_id": user_id,
            "name": message.from_user.full_name,
            "username": message.from_user.username,
            "ref_count": 0,
            "is_premium": False,
            "joined_date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "chat_count": 0,
            "reports": 0
        })

    await message.answer(
        f"✨ **Welcome {message.from_user.first_name}!** ❤️\n\n"
        "Find your soulmate or chat with our smart AI Lover. Use the menu below to start your journey!",
        reply_markup=get_main_menu()
    )

# --- 2. HELP COMMAND ---
@router.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = (
        "❓ **Need Help? Here are the Commands:**\n\n"
        "🚀 `/chat` - Start AI or Human matching\n"
        "💎 `/premium` - Unlock premium features\n"
        "👤 `/edit_profile` - Update your info\n"
        "ℹ️ `/about` - Community groups\n"
        "🔐 `/privacy` - Bot rules & safety\n\n"
        "💡 **Tip:** Facing issues? Join our discussion group via /about!"
    )
    await message.answer(help_text)

# --- 3. ABOUT COMMAND ---
@router.message(Command("about"))
async def cmd_about(message: types.Message):
    about_text = (
        "✨ **About CoupleDatingBot**\n\n"
        "The most advanced AI Dating companion and Human matching bot. ❤️\n\n"
        "📢 **Main Group:** @Blackheartmain\n"
        "💬 **Support:** Join our discussion group for help!"
    )
    await message.answer(about_text, disable_web_page_preview=True)

# --- 4. PRIVACY COMMAND ---
@router.message(Command("privacy"))
async def cmd_privacy(message: types.Message):
    privacy_text = (
        "🔐 **Privacy & Safety Rules**\n\n"
        "1️⃣ **Respect:** Misbehavior will lead to a permanent ban.\n"
        "2️⃣ **Security:** Never share OTP or personal bank details.\n"
        "3️⃣ **Data:** Your info is only used for better matching.\n"
        "4️⃣ **Reports:** Use the report button if someone bothers you."
    )
    await message.answer(privacy_text)

# --- 5. CHAT COMMAND ---
@router.message(Command("chat"))
async def cmd_chat_manual(message: types.Message):
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🤖 Chat with AI", callback_data="chat_ai")],
        [types.InlineKeyboardButton(text="👥 Chat with Human", callback_data="chat_human")]
    ])
    await message.answer("✨ **Select Chat Type:**\n\nWho do you want to talk to right now?", reply_markup=kb)

# --- 6. PREMIUM COMMAND REDIRECT ---
@router.message(Command("premium"))
async def cmd_premium_redirect(message: types.Message):
    # This will trigger the same logic as the premium menu
    from handlers.premium import premium_menu
    await premium_menu(message, None)
            
