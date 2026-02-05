from aiogram import Router, F, types
from database import db
from utils.keyboards import get_main_menu
import datetime

router = Router()

# Admin ID (Unga ID inga podunga)
ADMIN_ID = 123456789  

# Plan details with your manual links
PLANS = {
    "29": {"name": "1 Week", "link": "https://cashfree.com/your_manual_link_29", "days": 7},
    "79": {"name": "1 Month", "link": "https://cashfree.com/your_manual_link_79", "days": 30},
    "149": {"name": "3 Months", "link": "https://cashfree.com/your_manual_link_149", "days": 90}
}

@router.callback_query(F.data == "go_premium")
async def premium_menu(callback: types.CallbackQuery):
    text = (
        "💎 **CoupleDating Premium Plans**\n"
        "━━━━━━━━━━━━━━\n"
        "1️⃣ **1 Week** - ₹29\n"
        "2️⃣ **1 Month** - ₹79\n"
        "3️⃣ **3 Months** - ₹149\n"
        "━━━━━━━━━━━━━━\n"
        "✅ Pay panni mudichu screenshot anupunga, 5 mins la activate aagidum!"
    )
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🎟️ 1 Week - ₹29", callback_data="manual_29")],
        [types.InlineKeyboardButton(text="🎟️ 1 Month - ₹79", callback_data="manual_79")],
        [types.InlineKeyboardButton(text="🎟️ 3 Months - ₹149", callback_data="manual_149")],
        [types.InlineKeyboardButton(text="🔙 Back", callback_data="main_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=kb)

@router.callback_query(F.data.startswith("manual_"))
async def process_manual_pay(callback: types.CallbackQuery):
    amount = callback.data.split("_")[1]
    plan = PLANS[amount]
    
    text = (
        f"✨ **Plan: {plan['name']}**\n"
        f"💰 **Amount: ₹{amount}**\n\n"
        f"1️⃣ Keela ulla link-ah click panni pay pannunga.\n"
        f"2️⃣ Payment successful screenshot-ah inga anuppunga.\n\n"
        f"🔗 [CLICK HERE TO PAY]({plan['link']})"
    )
    
    await callback.message.edit_text(text, parse_mode="Markdown")

# Handle Screenshot from User
@router.message(F.photo)
async def handle_payment_screenshot(message: types.Message):
    user = await db.users.find_one({"user_id": message.from_user.id})
    # Check if user is in idle or payment state (Optional)
    
    await message.answer("✅ Screenshot received! Admin verification-ku appuram premium activate aagum. Please wait (5-10 mins).")
    
    # Forward to Admin
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="✅ Approve", callback_data=f"approve_{message.from_user.id}")],
        [types.InlineKeyboardButton(text="❌ Reject", callback_data=f"reject_{message.from_user.id}")]
    ])
    
    await message.bot.send_photo(
        ADMIN_ID, 
        message.photo[-1].file_id, 
        caption=f"💰 **New Payment Proof!**\nUser: {message.from_user.full_name}\nID: `{message.from_user.id}`",
        reply_markup=kb
    )

# Admin Approval Logic
@router.callback_query(F.data.startswith("approve_"))
async def approve_payment(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    
    # Default-ah 30 days active pannuvom (illana logic complex aagum)
    expiry = datetime.datetime.now() + datetime.timedelta(days=30)
    
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"is_premium": True, "expiry_date": expiry.strftime("%Y-%m-%d")}}
    )
    
    await callback.bot.send_message(user_id, "🎉 **Premium Activated!** Ungaluku premium features ippo unlock aagidichi. Enjoy!")
    await callback.message.edit_caption(caption=callback.message.caption + "\n\n✅ **APPROVED**")

@router.callback_query(F.data.startswith("reject_"))
async def reject_payment(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    await callback.bot.send_message(user_id, "❌ Unga payment proof reject seiyapattathu. Please contact admin if this is a mistake.")
    await callback.message.edit_caption(caption=callback.message.caption + "\n\n❌ **REJECTED**")
    
