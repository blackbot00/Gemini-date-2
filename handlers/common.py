from aiogram import Router, F, types
from utils.keyboards import get_main_menu

router = Router()

@router.message(Command("privacy"))
async def cmd_privacy(message: types.Message):
    privacy_text = (
        "🔐 **Privacy Policy**\n\n"
        "1️⃣ 🛡️ Safety First — We take user safety seriously.\n"
        "2️⃣ 😇 Don't be Misbehave — Respect others.\n"
        "3️⃣ 🚫 No Personal Info — Never share phone/address.\n"
        "4️⃣ 🚩 Report Option — Use Report button for abuse."
    )
    await message.answer(privacy_text)

@router.callback_query(F.data == "edit_profile")
async def edit_profile(callback: types.CallbackQuery):
    user = await db.users.find_one({"user_id": callback.from_user.id})
    if not user.get("is_premium"):
        return await callback.answer("⭐ Only for Premium Users!", show_alert=True)
    
    # Logic to restart FSM for editing
    await callback.message.edit_text("🔄 Update your profile. Choose what to change:", 
                                     reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                                         [types.InlineKeyboardButton(text="State", callback_data="reg_start")],
                                         [types.InlineKeyboardButton(text="Back", callback_data="main_menu")]
                                     ]))
  
