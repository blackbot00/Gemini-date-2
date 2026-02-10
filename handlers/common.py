from aiogram import Router, types
from aiogram.filters import Command, CommandObject
from utils.keyboards import get_main_menu
from database import db
import datetime

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message, command: CommandObject):
    user_id = message.from_user.id
    args = command.args
    user_exists = await db.users.find_one({"user_id": user_id})

    # Token verification from Shortener
    if args and args.startswith("verify_"):
        token = args.split("_")[1]
        user = await db.users.find_one({"user_id": user_id})
        
        if user and user.get("last_token") == token:
            kb = types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="✅ Complete Activation", callback_data=f"activate_{token}")]
            ])
            return await message.answer("🔒 **Link Verified!**\nClick below to finish activation:", reply_markup=kb)
        else:
            return await message.answer("❌ Token mismatch! Please use the latest link from /premium.")

    if not user_exists:
        await db.users.insert_one({
            "user_id": user_id,
            "name": message.from_user.full_name,
            "is_premium": False,
            "last_token": None,
            "joined_date": datetime.datetime.now().strftime("%Y-%m-%d")
        })

    await message.answer(f"✨ **Welcome {message.from_user.first_name}!**", reply_markup=get_main_menu())
# ... (help, about, privacy matha commands-ah keela sethukonga)

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
        "/editprofile - Edit your info\n"
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

# --- 6. PREMIUM COMMAND (Redirect to premium handler) ---
@router.message(Command("premium"))
async def cmd_premium(message: types.Message):
    from handlers.premium import premium_menu
    await premium_menu(message)
    
