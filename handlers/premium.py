from aiogram import Router, F, types
from database import db
from utils.payment import create_cashfree_order
from utils.keyboards import get_main_menu
import httpx
import datetime
from config import CASHFREE_APP_ID, CASHFREE_SECRET_KEY

router = Router()

# Premium main menu showing plans
@router.callback_query(F.data == "go_premium")
async def premium_menu(callback: types.CallbackQuery):
    text = (
        "💎 **CoupleDating Premium Plans**\n"
        "━━━━━━━━━━━━━━\n"
        "1️⃣ **1 Week** - ₹29\n"
        "2️⃣ **1 Month** - ₹79\n"
        "3️⃣ **3 Months** - ₹149\n"
        "━━━━━━━━━━━━━━\n"
        "✅ Unlimited Human Chats\n"
        "✅ Instant Media Sharing\n"
        "✅ Reveal Partner Details\n"
        "✅ 18+ AI Personality Mode"
    )
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🎟️ 1 Week - ₹29", callback_data="buy_29")],
        [types.InlineKeyboardButton(text="🎟️ 1 Month - ₹79", callback_data="buy_79")],
        [types.InlineKeyboardButton(text="🎟️ 3 Months - ₹149", callback_data="buy_149")],
        [types.InlineKeyboardButton(text="🔙 Back", callback_data="main_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=kb)

# Handling plan selection and link generation
@router.callback_query(F.data.startswith("buy_"))
async def process_plan_selection(callback: types.CallbackQuery):
    amount = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    user_name = callback.from_user.first_name
    
    plan_name = "1 Week" if amount == 29 else "1 Month" if amount == 79 else "3 Months"
    
    await callback.message.edit_text(f"⏳ Generating link for {plan_name} plan...")
    
    link_url, link_id = await create_cashfree_order(user_id, amount, user_name)
    
    if link_url:
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text=f"🚀 Pay ₹{amount} Now", url=link_url)],
            [types.InlineKeyboardButton(text="✅ Check Status", callback_data=f"vlnk_{link_id}_{amount}")]
        ])
        await callback.message.edit_text(
            f"✅ **{plan_name} Plan Link Ready!**\n\nPay panni mudichuttu 'Check Status' click pannunga.",
            reply_markup=kb
        )
    else:
        await callback.message.edit_text("❌ Error generating link. Please try again.")

# Verification and Activation
@router.callback_query(F.data.startswith("vlnk_"))
async def verify_link_payment(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    link_id = parts[1]
    amount = int(parts[2])
    
    url = f"https://api.cashfree.com/pg/links/{link_id}"
    headers = {
        "x-client-id": CASHFREE_APP_ID,
        "x-client-secret": CASHFREE_SECRET_KEY,
        "x-api-version": "2025-01-01"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        data = response.json()
        
        if data.get("link_status") == "PAID":
            # Duration logic
            days = 7 if amount == 29 else 30 if amount == 79 else 90
            expiry_date = datetime.datetime.now() + datetime.timedelta(days=days)
            
            await db.users.update_one(
                {"user_id": callback.from_user.id},
                {"$set": {
                    "is_premium": True, 
                    "plan_amount": amount,
                    "expiry_date": expiry_date.strftime("%Y-%m-%d %H:%M")
                }}
            )
            await callback.message.edit_text(
                f"🎉 **Premium Active!**\n\nPlan: {days} Days\nExpires on: {expiry_date.strftime('%d %b %Y')}\n\nEnjoy unlimited features! 🔥",
                reply_markup=get_main_menu()
            )
        else:
            await callback.answer("⚠️ Payment innum receive aagala. Pay pannittu try pannunga!", show_alert=True)
    
