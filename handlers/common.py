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

    # Deep Link Logic
    if args:
        if args.startswith("unlock_"):
            # Same user check logic
            target_id = int(args.split("_")[1])
            if target_id == user_id:
                expiry = datetime.datetime.now() + datetime.timedelta(hours=1)
                await db.users.update_one(
                    {"user_id": user_id}, 
                    {"$set": {"is_premium": True, "expiry_date": expiry.strftime("%Y-%m-%d %H:%M")}},
                    upsert=True
                )
                return await message.answer("✅ **1 Hour Premium Unlocked!** 💎\nIppo neenga unlimited-ah chat pannalaam!")

        if args.startswith("ref_") and not user_exists:
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
                        await message.bot.send_message(referrer_id, "🎉 5 Referrals Completed! **1 Week Premium** Activated! 💎")
                    except: pass

    # Basic Registration
    if not user_exists:
        await db.users.insert_one({
            "user_id": user_id,
            "name": message.from_user.full_name,
            "ref_count": 0,
            "is_premium": False,
            "joined_date": datetime.datetime.now().strftime("%Y-%m-%d")
        })

    await message.answer(f"Hi {message.from_user.first_name}! ❤️ Welcome back.", reply_markup=get_main_menu())

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer("❓ **Commands:**\n/chat - Start Match\n/premium - Get Access\n/about - Join Group")

@router.message(Command("about"))
async def cmd_about(message: types.Message):
    await message.answer("✨ Join @Blackheartmain for updates!", disable_web_page_preview=True)

# Important: premium command direct handler
@router.message(Command("premium"))
async def cmd_premium_handle(message: types.Message):
    from handlers.premium import premium_menu
    await premium_menu(message)
                
