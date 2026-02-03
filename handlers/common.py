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
        "1️⃣ 🛡️ Safety First — We take user safety seriously.\n"
        "2️⃣ 😇 Don't be Misbehave — Respect others.\n"
        "3️⃣ 🚫 No Personal Info — Never share phone/address.\n"
        "4️⃣ 🚩 Report Option — Use Report button for abuse."
    )
    await message.answer(privacy_text)

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
        "🎟 **Select a plan to continue:**"
    )
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="1 Week - ₹29", callback_data="buy_29")],
        [types.InlineKeyboardButton(text="1 Month - ₹79", callback_data="buy_79")],
        [types.InlineKeyboardButton(text="3 Months - ₹149", callback_data="buy_149")],
        [types.InlineKeyboardButton(text="🔙 Back", callback_data="main_menu")]
    ])
    
    if isinstance(event, types.Message):
        await event.answer(premium_text, reply_markup=kb)
    else:
        await event.message.edit_text(premium_text, reply_markup=kb)

@router.callback_query(F.data.startswith("buy_"))
async def process_buy_button(callback: types.CallbackQuery):
    amount = callback.data.split("_")[1]
    # Inga thaan Cashfree link create panna vendum. 
    # For now confirmation message:
    await callback.answer(f"Processing ₹{amount} plan...", show_alert=False)
    
    pay_kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="💳 Pay Now", url="https://t.me/your_admin_username")], # Replace with real link later
        [types.InlineKeyboardButton(text="🔙 Back", callback_data="go_premium")]
    ])
    
    await callback.message.edit_text(
        f"💎 **Premium Plan: ₹{amount}**\n\n"
        "Click the button below to pay via UPI or Card. Once payment is done, send the screenshot to Admin.",
        reply_markup=pay_kb
    )

@router.callback_query(F.data == "main_menu")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Welcome back! Choose your mode:", reply_markup=get_main_menu())
    
