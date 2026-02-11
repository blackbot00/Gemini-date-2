from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from database import db
import datetime
import random

router = Router()

# --- 1. ADS MUDICHU VARUMBODHU CODE ANUPPURA LOGIC ---
@router.message(Command("start"))
async def cmd_start(message: types.Message, command: CommandObject):
    user_id = int(message.from_user.id)
    args = command.args
    
    # User ads skip panni vandha args-la 'verify_' irukkum
    if args and args.startswith("verify_"):
        token = args.split("_")[1]
        user = await db.users.find_one({"user_id": user_id})
        
        if user and user.get("last_token") == token:
            # Code generate panni save pandrom
            new_code = f"CP-{random.randint(100000, 999999)}"
            await db.users.update_one(
                {"user_id": user_id}, 
                {"$set": {"pending_code": new_code, "last_token": None}}
            )
            
            return await message.answer(
                f"✅ **Ads Verified!**\n\n"
                f"Unga Activation Code: `{new_code}`\n\n"
                "Mela irukura code-ah **Copy panni ippo anuppunga**, premium active aydum! ✨"
            )

    # Normal Start Logic
    user_exists = await db.users.find_one({"user_id": user_id})
    if not user_exists:
        await db.users.insert_one({
            "user_id": user_id,
            "name": message.from_user.full_name,
            "is_premium": False,
            "pending_code": None,
            "joined_date": datetime.datetime.now().strftime("%Y-%m-%d")
        })
    await message.answer(f"✨ Welcome {message.from_user.first_name}! ❤️")

# --- 2. USER CODE ANUPUNA VERIFY PANDRA LOGIC ---
@router.message(F.text.startswith("CP-"))
async def verify_manual_code(message: types.Message):
    user_id = int(message.from_user.id)
    received_code = message.text.strip()
    
    user = await db.users.find_one({"user_id": user_id})
    
    if user and user.get("pending_code") == received_code:
        expiry = datetime.datetime.now() + datetime.timedelta(hours=1)
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"is_premium": True, "expiry_date": expiry.strftime("%Y-%m-%d %H:%M:%S"), "pending_code": None}}
        )
        await message.answer(f"🎊 **Premium Activated!** ❤️\nValid until: `{expiry.strftime('%I:%M %p')}`")
    else:
        await message.answer("❌ **Invalid Code!**\nGet a new link from /premium.")
        
