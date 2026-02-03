from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from database import db
from utils.keyboards import get_main_menu
from utils.payment import create_cashfree_order # Import matching the function above

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

@router.callback_query(F.data == "go_premium")
@router.message(Command("premium"))
async def show_premium(event: types.Message | types.CallbackQuery):
    premium_text = (
        "💎 **PREMIUM PLANS**\n"
        "━━━━━━━━━━━━━━\n"
        "• Unlimited AI Chats\n"
        "• 18+ Romantic AI Mode\n"
        "• Filter partners by Gender\n\n"
        "🎟 **Select a plan to pay via UPI/Card:**"
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
    user_id = callback.from_user.id
    
    # User name for Cashfree
    user_data = await db.users.find_one({"user_id": user_id})
    name = user_data.get("name", "User") if user_data else "User"

    await callback.message.edit_text(f"⏳ Generating secure payment link for ₹{amount}...")

    # Generate real session from Cashfree
    session_id, order_id = await create_cashfree_order(user_id, amount, name)

    if session_id:
        # Construct the official Checkout URL
        checkout_url = f"https://payments.cashfree.com/order/#/{session_id}"
        
        pay_kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="💳 Pay Now (UPI/Card)", url=checkout_url)],
            [types.InlineKeyboardButton(text="🔙 Back", callback_data="go_premium")]
        ])
        
        await callback.message.edit_text(
            f"✅ **Order Generated!**\n\nPlan: ₹{amount}\nOrder ID: `{order_id}`\n\nClick below to complete the payment. After payment, your premium will be active soon.",
            reply_markup=pay_kb
        )
    else:
        await callback.message.edit_text(
            "❌ **Gateway Error!**\n\nCould not generate payment link. Please try again later or contact Admin.",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="🔙 Back", callback_data="go_premium")]
            ])
        )

@router.callback_query(F.data == "main_menu")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Welcome back! Choose your mode:", reply_markup=get_main_menu())
    
