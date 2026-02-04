from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from database import db
from utils.keyboards import get_main_menu
from utils.states import Registration # Reuse registration states for editing

router = Router()

@router.callback_query(F.data == "view_profile")
async def show_profile(callback: types.CallbackQuery):
    user = await db.users.find_one({"user_id": callback.from_user.id})
    
    premium_status = "💎 Premium Member" if user.get("is_premium") else "🆓 Free User"
    
    text = (
        f"👤 **YOUR PROFILE**\n"
        f"━━━━━━━━━━━━━━\n"
        f"📛 Name: {user['name']}\n"
        f"👫 Gender: {user['gender']}\n"
        f"🎂 Age: {user['age']}\n"
        f"📍 State: {user['state']}\n"
        f"🌟 Status: {premium_status}\n"
        f"━━━━━━━━━━━━━━\n"
        f"Edit option is only for Premium users! ✨"
    )
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="✍️ Edit Profile", callback_data="edit_profile")],
        [types.InlineKeyboardButton(text="🔙 Back", callback_data="main_menu")]
    ])
    
    await callback.message.edit_text(text, reply_markup=kb)

@router.callback_query(F.data == "edit_profile")
async def edit_profile_check(callback: types.CallbackQuery, state: FSMContext):
    user = await db.users.find_one({"user_id": callback.from_user.id})
    
    if not user.get("is_premium"):
        return await callback.answer("❌ Edit option only for Premium users!", show_alert=True)
    
    # Start re-registration flow for editing
    await state.set_state(Registration.state) # Or create a dedicated EditState
    from utils.keyboards import get_state_keyboard
    await callback.message.edit_text("🔄 **Editing Profile**\nSelect your State again:", reply_markup=get_state_keyboard())

@router.message(F.text == "/edit_profile")
async def edit_profile_cmd(message: types.Message, state: FSMContext):
    user = await db.users.find_one({"user_id": message.from_user.id})
    
    if not user.get("is_premium"):
        return await message.answer("❌ This command is only for Premium users! 💎")
    
    await state.set_state(Registration.state)
    from utils.keyboards import get_state_keyboard
    await message.answer("🔄 **Editing Profile**\nSelect your State:", reply_markup=get_state_keyboard())

@router.callback_query(F.data == "main_menu")
async def back_to_main(callback: types.CallbackQuery):
    await callback.message.edit_text("Main Menu:", reply_markup=get_main_menu())
  
