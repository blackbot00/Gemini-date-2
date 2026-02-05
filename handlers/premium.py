from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from database import db
from utils.payment import create_cashfree_order
from utils.keyboards import get_main_menu
import httpx
from config import CASHFREE_APP_ID, CASHFREE_SECRET_KEY

router = Router()

@router.callback_query(F.data == "go_premium")
async def premium_menu(callback: types.CallbackQuery):
    text = (
        "💎 **CoupleDating Premium**\n"
        "━━━━━━━━━━━━━━\n"
        "✅ Unlimited Human Chats (No 50/day limit)\n"
        "✅ Instant Media Sharing (No 3-min wait)\n"
        "✅ Reveal Partner Gender & Details\n"
        "✅ Edit Your Profile anytime\n"
        "✅ Bold 18+ AI Personality Mode\n"
        "━━━━━━━━━━━━━━\n"
        "💰 **Special Offer: ₹29 Only!**"
    )
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="💳 Pay ₹29 & Upgrade", callback_data="pay_now")],
        [types.InlineKeyboardButton(text="🔙 Back", callback_data="main_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=kb)

@router.callback_query(F.data == "pay_now")
async def process_payment(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_name = callback.from_user.first_name
    
    await callback.message.edit_text("⏳ Generating secure payment link...")
    
    # Amount ₹29 for example
    checkout_url, order_id = await create_cashfree_order(user_id, 29, user_name)
    
    if checkout_url:
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🚀 Click to Pay", url=checkout_url)],
            [types.InlineKeyboardButton(text="✅ Check Status", callback_data=f"verify_{order_id}")]
        ])
        await callback.message.edit_text(
            "✅ **Order Created!**\n\n1️⃣ Click the button below to pay.\n2️⃣ After payment, click 'Check Status'.",
            reply_markup=kb
        )
    else:
        await callback.message.edit_text("❌ Payment Gateway busy. Please try again later.")

@router.callback_query(F.data.startswith("verify_"))
async def verify_payment(callback: types.CallbackQuery):
    order_id = callback.data.split("_")[1]
    
    # Cashfree API to check order status
    url = f"https://api.cashfree.com/pg/orders/{order_id}"
    headers = {
        "x-client-id": CASHFREE_APP_ID,
        "x-client-secret": CASHFREE_SECRET_KEY,
        "x-api-version": "2023-08-01"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        data = response.json()
        
        # Check if order status is PAID
        if data.get("order_status") == "PAID":
            user_id = callback.from_user.id
            # Activate Premium in Database
            await db.users.update_one(
                {"user_id": user_id},
                {"$set": {"is_premium": True, "premium_date": str(callback.message.date)}}
            )
            await callback.message.edit_text(
                "🎉 **Congratulations!**\n\nYour Premium is now active. Enjoy unlimited features! 🔥",
                reply_markup=get_main_menu()
            )
        else:
            await callback.answer("⚠️ Payment not received yet. If you paid, wait 2 mins and check again.", show_alert=True)
