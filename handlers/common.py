from aiogram import Router, F, types
from aiogram.filters import Command  # Intha line thaan missing!
from aiogram.fsm.context import FSMContext
from database import db
from utils.keyboards import get_main_menu

router = Router()

@router.message(Command("privacy"))
async def cmd_privacy(message: types.Message):
    privacy_text = (
        "🔐 **Privacy Policy**\n\n"
        "1️⃣ 🛡️ Safety First — We take user safety seriously.\n"
        "2️⃣ 😇 Don't be Misbehave — Respect others and chat politely.\n"
        "3️⃣ 🚫 No Personal Info — Never share phone, OTP, address, bank details.\n"
        "4️⃣ 🚩 Report Option — Use Report button if someone abuses.\n"
        "5️⃣ 🔒 Data Use — Registration info used only for matching."
    )
    await message.answer(privacy_text)

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = (
        "❓ **How to use this bot?**\n\n"
        "• Use /start to register or open menu.\n"
        "• Select Human or AI chat.\n"
        "• Use /exit to stop any conversation.\n"
        "• Use /premium to check plans."
    )
    await message.answer(help_text)

@router.message(Command("about"))
async def cmd_about(message: types.Message):
    about_text = (
        "🤖 **About CoupleDatingbot AI**\n"
        "━━━━━━━━━━━━━━━\n"
        "LoveMate AI is a smart AI-powered dating assistant.\n"
        "Chat freely, safely, and without pressure.\n\n"
        "✨ **Features**\n"
        "• 🤖 AI Dating Chat\n"
        "• 🔐 Moderated Conversations\n"
        "• 💎 Premium Exclusive AI Modes"
    )
    await message.answer(about_text)

@router.callback_query(F.data == "go_premium")
@router.message(Command("premium"))
async def show_premium(event: types.Message | types.CallbackQuery):
    premium_text = (
        "💎 **PREMIUM PLANS**\n"
        "━━━━━━━━━━━━━━\n"
        "• Unlimited AI Chats\n"
        "• 18+ Romantic AI Mode\n"
        "• Filter partners by Gender\n"
        "• Priority Connection\n\n"
        "🎟 **Pricing:**\n"
        "• 1 Week: ₹29\n"
        "• 1 Month: ₹79\n"
        "• 3 Months: ₹149"
    )
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Buy Now (UPI/Card)", callback_data="buy_premium")],
        [types.InlineKeyboardButton(text="🔙 Back", callback_data="main_menu")]
    ])
    
    if isinstance(event, types.Message):
        await event.answer(premium_text, reply_markup=kb)
    else:
        await event.message.edit_text(premium_text, reply_markup=kb)

@router.callback_query(F.data == "main_menu")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Welcome back! Choose your mode:", reply_markup=get_main_menu())
        
