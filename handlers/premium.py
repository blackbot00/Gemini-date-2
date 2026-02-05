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
        "✅ Unlimited Human Chats\n"
        "✅ Instant Media Sharing\n"
        "✅ Gender & State Reveal\n"
        "✅ 18+ AI Mode Unlocked\n"
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
    
    # User-ku feedback kudukka oru loading message
    await callback.message.edit_text("⏳ Processing your payment link...")
    
    # utils/payment.py-la irukura function-ah call pandrom
    checkout_url, order_id = await create_cashfree_order(user_id, 29, user_name)
    
    if checkout_url:
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🚀 Click to Pay", url=checkout_url)],
            [types.InlineKeyboardButton(text="✅ Check Payment Status", callback_data=f"verify_{order_id}")]
        ])
        await callback.message.edit_text(
            "✅ **Payment Link Ready!**\n\n1️⃣ Keela irukura button-ah click panni pay pannunga.\n"
            "2️⃣ Pay panni mudichuttu 'Check Payment Status' click pannunga.",
            reply_markup=kb
        )
    else:
        await callback.message.edit_text("❌ Failed to generate link. Try again later or contact Admin.")

@router.callback_query(F.data.startswith("verify_"))
async def verify_payment(callback: types.CallbackQuery):
    order_id = callback.data.split("_")[1]
    
    # Cashfree Production API endpoint
    url = f"https://api.cashfree.com/pg/orders/{order_id}"
    headers = {
        "x-client-id": CASHFREE_APP_ID,
        "x-client-secret": CASHFREE_SECRET_KEY,
        "x-api-version": "2023-08-01"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            data = response.json()
            
            # Order success-ah nu check pandrom
            if data.get("order_status") == "PAID":
                user_id = callback.from_user.id
                # Database-la premium activate pandrom
                await db.users.update_one(
                    {"user_id": user_id},
                    {"$set": {"is_premium": True, "premium_since": str(datetime.datetime.now())}}
                )
                await callback.message.edit_text(
                    "🎉 **Premium Activated!**\n\nUnlimited access ippo ungalukku kidaichurichi. Enjoy! 🔥",
                    reply_markup=get_main_menu()
                )
            else:
                current_status = data.get("order_status", "UNKNOWN")
                await callback.answer(f"⚠️ Status: {current_status}. Please complete the payment first!", show_alert=True)
        except Exception as e:
            await callback.answer("⚠️ Connection error while verifying. Try again.", show_alert=True)
    
