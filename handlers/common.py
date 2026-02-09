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
    
    # --- Logic: Handle Deep Links ---
    if args:
        # 1. Shortener Unlock (1 Hour)
        if args.startswith("unlock_"):
            target_id = int(args.split("_")[1])
            if target_id == user_id:
                expiry = datetime.datetime.now() + datetime.timedelta(hours=1)
                await db.users.update_one({"user_id": user_id}, {"$set": {"is_premium": True, "expiry_date": expiry.strftime("%Y-%m-%d %H:%M")}})
                return await message.answer("✅ **1 Hour Premium Unlocked!**\nEnjoy unlimited AI & Human chats baby! 💎🔥")

        # 2. Referral System (Only for NEW users)
        if args.startswith("ref_") and not user_exists:
            referrer_id = int(args.split("_")[1])
            if referrer_id != user_id:
                # Add count to referrer
                await db.users.update_one({"user_id": referrer_id}, {"$inc": {"ref_count": 1}})
                
                # Check for reward
                referrer = await db.users.find_one({"user_id": referrer_id})
                if referrer.get("ref_count") == 5 and not referrer.get("ref_reward_claimed"):
                    expiry = datetime.datetime.now() + datetime.timedelta(days=7)
                    await db.users.update_one({"user_id": referrer_id}, {
                        "$set": {"is_premium": True, "expiry_date": expiry.strftime("%Y-%m-%d"), "ref_reward_claimed": True}
                    })
                    try: await message.bot.send_message(referrer_id, "🎉 **Congratulations!**\nYou referred 5 members. **1 Week Premium** activated! 💎💖")
                    except: pass

    # Normal registration/start
    if not user_exists:
        # Unga registration logic inga podunga (db.users.insert_one...)
        pass

    await message.answer(
        "✨ **Welcome to CoupleDatingBot!** ❤️\n\nFind your perfect match or chat with our smart AI. Use the menu below to start!",
        reply_markup=get_main_menu()
    )

# --- 2. PRIVACY, ABOUT, HELP, CHAT ---
@router.message(Command("privacy"))
async def cmd_privacy(message: types.Message):
    await message.answer("🔐 **Privacy Policy**\n\n1️⃣ Safety First.\n2️⃣ No misbehaving.\n3️⃣ Don't share personal info.\n4️⃣ Use Report button for abuse.")

@router.message(Command("about"))
async def cmd_about(message: types.Message):
    await message.answer("✨ **About This Bot**\n\nMain Group: @Blackheartmain\nJoin for updates!", disable_web_page_preview=True)

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "❓ **Need Help?**\n\n"
        "/chat - Start matching\n"
        "/premium - Unlock features\n"
        "/edit_profile - Change info\n\n"
        "Issues? Contact Admin in the discussion group! ❤️"
    )

@router.message(Command("chat"))
async def cmd_chat_manual(message: types.Message):
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🤖 Chat with AI", callback_data="chat_ai")],
        [types.InlineKeyboardButton(text="👥 Chat with Human", callback_data="chat_human")]
    ])
    await message.answer("✨ **Start Chatting**", reply_markup=kb)
        
