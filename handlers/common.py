from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from database import db
from utils.keyboards import get_main_menu

router = Router()

@router.message(Command("privacy"))
async def cmd_privacy(message: types.Message):
    privacy_text = (
        "🔐 **Privacy Policy**\n\n"
        "1️⃣ 🛡️ Safety First — User safety is our priority.\n"
        "2️⃣ 😇 Don't be Misbehave — Respect others.\n"
        "3️⃣ 🚫 No Personal Info — Don't share private data.\n"
        "4️⃣ 🚩 Report Option — Use Report button if needed."
    )
    await message.answer(privacy_text)

@router.callback_query(F.data == "main_menu")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Welcome back! Choose your mode:", reply_markup=get_main_menu())
    
