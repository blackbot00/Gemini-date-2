from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from utils.keyboards import get_main_menu
from database import db
import datetime
import random

router = Router()

# --- 1. MANUAL CODE VERIFICATION ---
@router.message(F.text.startswith("CP-"))
async def verify_manual_code(message: types.Message):
    user_id = int(message.from_user.id)
    received_code = message.text.strip()
    
    user = await db.users.find_one({"user_id": user_id})
    
    if user and user.get("pending_code") == received_code:
        expiry = datetime.datetime.now() + datetime.timedelta(hours=1)
        
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {
                "is_premium": True, 
                "expiry_date": expiry.strftime("%Y-%m-%d %H:%M:%S"),
                "pending_code": None 
            }}
        )
        await message.answer(
            f"🎊 **Premium Activated Successfully!** 🎊\n\n"
            f"Enjoy your premium features until: `{expiry.strftime('%I:%M %p')}` ❤️"
        )
    else:
        await message.answer("❌ **Invalid Code!**\nPlease get a new code from /premium.")

# --- 2. START COMMAND (With Auto-Code Logic) ---
@router.message(Command("start"))
async def cmd_start(message: types.Message, command: CommandObject):
    user_id = int(message.from_user.id)
    args = command.args
    user_exists = await db.users.find_one({"user_id": user_id})

    # --- ADS SKIP PANNI VANDHA INGA VARUM ---
    if args and "showcode_" in args:
        try:
            token = args.split("_")[1]
            user = await db.users.find_one({"user_id": user_id})
            
            if user and user.get("last_token") == token:
                # Code generate panni DB-la update pandrom
                new_code = f"CP-{random.randint(100000, 999999)}"
                await db.users.update_one(
                    {"user_id": user_id}, 
                    {"$set": {"pending_code": new_code, "last_token": None}}
                )
                
                return await message.answer(
                    f"✅ **Ads Verified!**\n\n"
                    f"Your Activation Code is: `{new_code}`\n\n"
                    "Intha code-ah copy panni chat-la thirumba anuppunga. Premium instant-ah activate aydum! ✨"
                )
        except Exception as e:
            print(f"Start Args Error: {e}")

    # --- NORMAL REGISTRATION ---
    if not user_exists:
        await db.users.insert_one({
            "user_id": user_id,
            "name": message.from_user.full_name,
            "username": message.from_user.username,
            "is_premium": False,
            "pending_code": None,
            "last_token": None,
            "ref_count": 0,
            "joined_date": datetime.datetime.now().strftime("%Y-%m-%d")
        })
        welcome_text = f"✨ **Welcome {message.from_user.first_name}!** ❤️\n\nFind your soulmate or chat with AI. Use the menu below to start!"
    else:
        welcome_text = f"✨ **Welcome back {message.from_user.first_name}!** ❤️"

    await message.answer(welcome_text, reply_markup=get_main_menu())

# --- 3. OTHER COMMANDS (Privacy, About, Help, Chat) ---
@router.message(Command("privacy"))
async def cmd_privacy(message: types.Message):
    await message.answer("🔐 **Privacy Policy**\n\n1️⃣ Safety First\n2️⃣ Respect Others\n3️⃣ No Personal Info Share.")

@router.message(Command("about"))
async def cmd_about(message: types.Message):
    await message.answer("✨ **About Bot**\nJoin our group: @Blackheartmain", disable_web_page_preview=True)

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer("❓ **Help**\nUse /chat for matching\nUse /premium for extras.")

@router.message(Command("chat"))
async def cmd_chat_manual(message: types.Message):
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🤖 AI Chat", callback_data="chat_ai")],
        [types.InlineKeyboardButton(text="👥 Human Chat", callback_data="chat_human")]
    ])
    await message.answer("✨ Choose chat type:", reply_markup=kb)

@router.message(Command("premium"))
async def cmd_premium(message: types.Message):
    from handlers.premium import premium_menu
    await premium_menu(message)
        
