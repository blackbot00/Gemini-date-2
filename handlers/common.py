from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from utils.keyboards import get_main_menu
from database import db
import datetime
import random

router = Router()

# --- 1. MANUAL CODE VERIFICATION ---
# User 'CP-123456' nu manual-ah type panni anupunaal idhu trigger aagum
@router.message(F.text.startswith("CP-"))
async def verify_manual_code(message: types.Message):
    user_id = int(message.from_user.id)
    received_code = message.text.strip()
    
    # Database-la andha user-oda pending_code-ah check pandrom
    user = await db.users.find_one({"user_id": user_id})
    
    if user and user.get("pending_code") == received_code:
        # 1 Hour Premium Time calculate pandrom
        expiry = datetime.datetime.now() + datetime.timedelta(hours=1)
        
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {
                "is_premium": True, 
                "expiry_date": expiry.strftime("%Y-%m-%d %H:%M:%S"),
                "pending_code": None # Oru vaati use panna apram code-ah thookiduvom
            }}
        )
        await message.answer(
            f"🎊 **Premium Activated Successfully!** 🎊\n\n"
            f"Enjoy your premium features until: `{expiry.strftime('%I:%M %p')}` ❤️\n"
            "Keep using our bot for more matches!"
        )
    else:
        await message.answer(
            "❌ **Invalid or Expired Code!**\n\n"
            "Please make sure you copied the code correctly from the link. "
            "Get a new code from /premium if needed."
        )

# common.py la cmd_start-ah mattum replace pannunga:

@router.message(Command("start"))
async def cmd_start(message: types.Message, command: CommandObject):
    user_id = int(message.from_user.id)
    args = command.args
    user_exists = await db.users.find_one({"user_id": user_id})

    # --- ADS SKIP PANNI VANDHA INGA VARUM ---
    if args and args.startswith("showcode_"):
        token = args.split("_")[1]
        user = await db.users.find_one({"user_id": user_id})
        
        if user and user.get("last_token") == token:
            # Code generate panni DB-la save pandrom
            new_code = f"CP-{random.randint(100000, 999999)}"
            await db.users.update_one(
                {"user_id": user_id}, 
                {"$set": {"pending_code": new_code, "last_token": None}}
            )
            
            return await message.answer(
                f"✅ **Ads Verified!**\n\n"
                f"Your Activation Code is: `{new_code}`\n\n"
                "Intha code-ah copy panni chat-la anuppunga. Premium instant-ah activate aydum! ✨"
            )
        else:
            return await message.answer("❌ **Link Expired!**\nPlease get a new link from /premium.")

    # ... Normal Start Registration logic (Munnadi kudutha maari) ...
    if not user_exists:
        # (Unga pazhaya registration code inga irukanum)
        pass

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
    
