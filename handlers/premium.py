from aiogram import Router, F, types
from aiogram.filters import Command
from database import db
from utils.keyboards import get_main_menu
import datetime
from config import ADMIN_ID, UPI_ID

router = Router()

PLANS = {
    "29": {"name": "1 Week", "days": 7},
    "79": {"name": "1 Month", "days": 30},
    "149": {"name": "3 Months", "days": 90}
}

@router.message(Command("premium"))
@router.callback_query(F.data == "go_premium")
async def premium_menu(event: types.Message | types.CallbackQuery):
    text = (
        "💎 **CoupleDating Premium Plans**\n"
        "━━━━━━━━━━━━━━\n"
        "1️⃣ **1 Week** - ₹29\n"
        "2️⃣ **1 Month** - ₹79\n"
        "3️⃣ **3 Months** - ₹149\n"
        "━━━━━━━━━━━━━━\n"
        "✅ Direct G-Pay/PhonePe (0% Fees)\n"
        "✅ Screenshot anupunga, 5 mins la active aagum!"
    )
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🎟️ 1 Week - ₹29", callback_data="payup_29")],
        [types.InlineKeyboardButton(text="🎟️ 1 Month - ₹79", callback_data="payup_79")],
        [types.InlineKeyboardButton(text="🎟️ 3 Months - ₹149", callback_data="payup_149")],
        [types.InlineKeyboardButton(text="🔙 Back", callback_data="main_menu")]
    ])
    
    if isinstance(event, types.Message):
        await event.answer(text, reply_markup=kb)
    else:
        await event.message.edit_text(text, reply_markup=kb)

@router.callback_query(F.data.startswith("payup_"))
async def process_direct_pay(callback: types.CallbackQuery):
    amount = callback.data.split("_")[1]
    plan = PLANS[amount]
    
    # Telegram inline buttons don't support upi:// links. 
    # So we show the link in text for the user to click.
    upi_link = f"upi://pay?pa={UPI_ID}&pn=CoupleDating&am={amount}&cu=INR"
    
    text = (
        f"✨ **Plan: {plan['name']}**\n"
        f"💰 **Amount: ₹{amount}**\n\n"
        f"📍 **UPI ID:** `{UPI_ID}` (Click to copy)\n\n"
        f"🚀 **Step 1:** Click the link below to pay:\n"
        f"👉 {upi_link}\n\n"
        f"📸 **Step 2:** Pay panni mudichuttu **Screenshot**-ah inga anupunga.\n"
        f"⏳ Admin verify panna udanae premium active aagidum."
    )
    
    # We removed the URL button to fix the "Unsupported URL protocol" error
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔙 Back to Plans", callback_data="go_premium")]
    ])
    
    await callback.answer()
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

# Handle Screenshot & Approval (remains the same)
@router.message(F.photo)
async def handle_payment_screenshot(message: types.Message):
    await message.answer("✅ Screenshot received! Admin check panniட்டு activate pannuvanga. Please wait.")
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="✅ Approve", callback_data=f"approve_{message.from_user.id}")],
        [types.InlineKeyboardButton(text="❌ Reject", callback_data=f"reject_{message.from_user.id}")]
    ])
    
    await message.bot.send_photo(
        ADMIN_ID, 
        message.photo[-1].file_id, 
        caption=f"💰 **New Payment Proof!**\n\n👤 User: {message.from_user.full_name}\n🆔 ID: `{message.from_user.id}`",
        reply_markup=kb
    )

@router.callback_query(F.data.startswith("approve_"))
async def approve_payment(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    expiry = datetime.datetime.now() + datetime.timedelta(days=30)
    
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"is_premium": True, "expiry_date": expiry.strftime("%Y-%m-%d")}}
    )
    
    try:
        await callback.bot.send_message(user_id, "🎉 **Premium Activated!**\n\nUnlimited features unlock aagidichi! 🔥")
    except:
        pass
    await callback.message.edit_caption(caption=callback.message.caption + "\n\n✅ **APPROVED**")

@router.callback_query(F.data.startswith("reject_"))
async def reject_payment(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    try:
        await callback.bot.send_message(user_id, "❌ **Payment Rejected!**\nPlease check the screenshot and try again.")
    except:
        pass
    await callback.message.edit_caption(caption=callback.message.caption + "\n\n❌ **REJECTED**")
        
