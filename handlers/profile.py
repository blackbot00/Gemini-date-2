from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from database import db
from utils.keyboards import get_main_menu, get_state_keyboard
from utils.states import Registration

router = Router()

@router.callback_query(F.data == "view_profile")
async def show_profile(callback: types.CallbackQuery):
    user = await db.users.find_one({"user_id": callback.from_user.id})
    
    is_premium = user.get("is_premium", False)
    premium_status = "💎 Premium Member" if is_premium else "🆓 Free User"
    expiry_info = f"\n📅 Expires: {user.get('expiry_date')}" if is_premium else ""
    
    text = (
        f"👤 **YOUR PROFILE**\n"
        f"━━━━━━━━━━━━━━\n"
        f"📛 Name: {user.get('name')}\n"
        f"👫 Gender: {user.get('gender')}\n"
        f"🎂 Age: {user.get('age')}\n"
        f"📍 State: {user.get('state')}\n"
        f"🌟 Status: {premium_status}{expiry_info}\n"
        f"━━━━━━━━━━━━━━\n"
    )
    
    if not is_premium:
        text += "💡 *Tip: Upgrade to Premium to edit your profile anytime!* ✨"
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="✍️ Edit Profile", callback_data="edit_profile")],
        [types.InlineKeyboardButton(text="🔙 Back", callback_data="main_menu")]
    ])
    
    await callback.message.edit_text(text, reply_markup=kb)

@router.callback_query(F.data == "edit_profile")
async def edit_profile_check(callback: types.CallbackQuery, state: FSMContext):
    user = await db.users.find_one({"user_id": callback.from_user.id})
    
    if not user.get("is_premium"):
        return await callback.answer("❌ Profile editing is for Premium users only! 💎", show_alert=True)
    
    await state.set_state(Registration.state)
    await callback.message.edit_text("🔄 **Editing Profile**\nSelect your State again:", reply_markup=get_state_keyboard())

@router.message(Command("edit_profile")) # Changed to proper filter
async def edit_profile_cmd(message: types.Message, state: FSMContext):
    user = await db.users.find_one({"user_id": message.from_user.id})
    
    if not user.get("is_premium"):
        return await message.answer("❌ This command is only for Premium users! 💎")
    
    await state.set_state(Registration.state)
    await message.answer("🔄 **Editing Profile**\nSelect your State:", reply_markup=get_state_keyboard())

@router.callback_query(F.data == "main_menu")
async def back_to_main(callback: types.CallbackQuery):
    await callback.message.edit_text("✨ *Main Menu*", reply_markup=get_main_menu())
    
