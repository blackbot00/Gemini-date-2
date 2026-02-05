from aiogram import Router, F, types
from aiogram.filters import Command
from database import db
from utils.keyboards import get_main_menu
import datetime
import urllib.parse
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
        "✅ QR Code scan panni pay pannunga.\n"
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
    
    # UPI Link Generation
    upi_payload = f"upi://pay?pa={UPI_ID}&pn=CoupleDating&am={amount}&cu=INR"
    
    # URL Encoding for Google API
    encoded_upi = urllib.parse.quote(upi_payload)
    qr_api_url = f"https://chart.googleapis.com/chart?chs=300x300&cht=qr&chl={encoded_upi}&choe=UTF-8"
    
    caption = (
        f"✨ **Plan: {plan['name']}**\n"
        f"💰 **Amount: ₹{amount}**\n\n"
        f"📍 **UPI ID:** `{UPI_ID}`\n\n"
        f"📸 **Step 1:** Intha QR code-ah scan panni ₹{amount} pay pannunga.\n"
        f"📤 **Step 2:** Pay panni mudichuttu **Screenshot**-ah inga anupunga.\n\n"
        f"⏳ Admin verify panna udanae premium active aagidum."
    )
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔙 Back", callback_data="go_premium")]
    ])
    
    await callback.answer()
    # Message-ah delete panniட்டு photo-voda puthu message anupuvom
    try:
        await callback.message.delete()
    except:
        pass

    await callback.bot.send_photo(
        chat_id=callback.message.chat.id,
        photo=qr_api_url,
        caption=caption,
        reply_markup=kb,
        parse_mode="Markdown"
    )

# --- SCREENSHOT HANDLING & APPROVAL (SAME LOGIC) ---

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
    
