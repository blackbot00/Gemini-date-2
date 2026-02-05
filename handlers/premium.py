from aiogram import Router, F, types
from database import db
from utils.payment import create_cashfree_order
from utils.keyboards import get_main_menu
import httpx
import datetime
from config import CASHFREE_APP_ID, CASHFREE_SECRET_KEY

router = Router()

@router.callback_query(F.data == "pay_now")
async def process_payment(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_name = callback.from_user.first_name
    
    await callback.message.edit_text("⏳ Generating payment link...")
    
    # Amount ₹29
    link_url, link_id = await create_cashfree_order(user_id, 29, user_name)
    
    if link_url:
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🚀 Click to Pay ₹29", url=link_url)],
            [types.InlineKeyboardButton(text="✅ Check Payment Status", callback_data=f"vlnk_{link_id}")]
        ])
        await callback.message.edit_text(
            "✅ **Link Ready!**\n\nPay panni mudichuttu 'Check Payment Status' click pannunga.",
            reply_markup=kb
        )
    else:
        await callback.message.edit_text("❌ Error. Try again later.")

@router.callback_query(F.data.startswith("vlnk_"))
async def verify_link_payment(callback: types.CallbackQuery):
    link_id = callback.data.split("_")[1]
    
    # Payment Link status check panna API
    url = f"https://api.cashfree.com/pg/links/{link_id}"
    headers = {
        "x-client-id": CASHFREE_APP_ID,
        "x-client-secret": CASHFREE_SECRET_KEY,
        "x-api-version": "2025-01-01"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        data = response.json()
        
        # Link status 'PAID' ah nu check pannuvom
        if data.get("link_status") == "PAID":
            await db.users.update_one(
                {"user_id": callback.from_user.id},
                {"$set": {"is_premium": True, "premium_since": str(datetime.datetime.now())}}
            )
            await callback.message.edit_text("🎉 **Premium Active!** Enjoy unlimited chats!", reply_markup=get_main_menu())
        else:
            await callback.answer("⚠️ Payment innum mudikala. Pay pannittu try pannunga!", show_alert=True)
    
