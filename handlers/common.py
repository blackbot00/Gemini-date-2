from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from utils.keyboards import get_main_menu
from database import db
import datetime

router = Router()

# --- 1. MANUAL CODE VERIFICATION (New Idea Implementation) ---
# User 'CP-123456' nu message anupuna idhu trigger aagum
@router.message(F.text.startswith("CP-"))
async def verify_manual_code(message: types.Message):
    user_id = int(message.from_user.id)
    received_code = message.text.strip()
    
    user = await db.users.find_one({"user_id": user_id})
    
    if user and user.get("pending_code") == received_code:
        # 1 Hour Premium calculate pandrom
        expiry = datetime.datetime.now() + datetime.timedelta(hours=1)
        
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {
                "is_premium": True, 
                "expiry_date": expiry.strftime("%Y-%m-%d %H:%M:%S"),
                "pending_code": None # Code-ah use panniyaachu, so reset
            }}
        )
        await message.answer(
            f"🎊 **Jackpot Baby! Premium Activated!** 🎊\n\n"
            f"Code verified successfully! Enjooy unlimited access until `{expiry.strftime('%I:%M %p')}`. ❤️"
        )
    else:
        await message.answer("❌ **Invalid or Expired Code!**\nPlease use the latest code from the unlock link in /premium.")

# --- 2. START COMMAND (Simplified Registration) ---
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = int(message.from_user.id)
    user_exists = await db.users.find_one({"user_id": user_id})

    # Basic Registration
    if not user_exists:
        await db.users.insert_one({
            "user_id": user_id,
            "name": message.from_user.full_name,
            "username": message.from_user.username,
            "is_premium": False,
            "pending_code": None,
            "ref_count": 0,
            "joined_date": datetime.datetime.now().strftime("%Y-%m-%d")
        })
        welcome_text = f"✨ **Welcome {message.from_user.first_name}!** ❤️\n\nFind your soulmate or chat with AI. Use the menu below to start!"
    else:
        welcome_text = f"✨ **Welcome back {message.from_user.first_name}!** ❤️"

    await message.answer(welcome_text, reply_markup=get_main_menu())

# --- 3. PRIVACY COMMAND ---
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

# --- 4. ABOUT COMMAND ---
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

# --- 5. HELP COMMAND ---
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

# --- 6. CHAT COMMAND ---
@router.message(Command("chat"))
async def cmd_chat_manual(message: types.Message):
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🤖 Chat with AI", callback_data="chat_ai")],
        [types.InlineKeyboardButton(text="👥 Chat with Human", callback_data="chat_human")]
    ])
    await message.answer("✨ **Start Chatting**\n\nWho would you like to talk to today? Choose below:", reply_markup=kb)

# --- 7. PREMIUM COMMAND ---
@router.message(Command("premium"))
async def cmd_premium(message: types.Message):
    from handlers.premium import premium_menu
    await premium_menu(message)
    
