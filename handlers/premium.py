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
        "💎 **Premium Plans**\n"
        "━━━━━━━━━━━━━━\n"
        "1️⃣ **1 Week** - ₹29\n"
        "2️⃣ **1 Month** - ₹79\n"
        "3️⃣ **3 Months** - ₹149\n\n"
        "✅ QR Code scan panni pay pannunga.\n"
        "📸 Pay panna apram **Screenshot**-ah inga anupunga!"
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
        # Photo message-ah edit panna mudiyaadhu, so delete & send
        try:
            await event.message.delete()
        except: pass
        await event.message.answer(text, reply_markup=kb)

@router.callback_query(F.data.startswith("payup_"))
async def process_direct_pay(callback: types.CallbackQuery):
    amount = callback.data.split("_")[1]
    plan = PLANS[amount]
    
    upi_payload = f"upi://pay?pa={UPI_ID}&pn=CoupleDating&am={amount}&cu=INR"
    encoded_upi = urllib.parse.quote(upi_payload)
    qr_api_url = f"https://quickchart.io/qr?text={encoded_upi}&size=300"
    
    caption = (
        f"✨ **Plan: {plan['name']}**\n"
        f"💰 **Amount: ₹{amount}**\n\n"
        f"📍 **UPI ID:** `{UPI_ID}`\n\n"
        f"📸 **Instructions:**\n"
        f"1. QR code scan panni pay pannunga.\n"
        f"2. Screenshot-ah indha chat-laye anupunga.\n"
        f"3. Admin verify panni 5 mins-la active pannuvanga."
    )
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔙 Back", callback_data="go_premium")]
    ])
    
    await callback.answer()
    await callback.message.delete()
    await callback.bot.send_photo(callback.message.chat.id, photo=qr_api_url, caption=caption, reply_markup=kb)

# --- GLOBAL PHOTO HANDLER ---
# User eppo photo anupunaalum admin-ku proof-ah pogum
@router.message(F.photo)
async def handle_any_photo(message: types.Message):
    # User-ku reply
    await message.reply("✅ **Proof Received!**\nAdmin check panni premium active pannuvaaru. Please wait 5-10 mins.")
    
    # Admin-ku anupa vendiya buttons
    # Note: callback_data length limit 64 characters, so keep it short
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="✅ Approve (30 Days)", callback_data=f"adm_ok_{message.from_user.id}_30"),
            types.InlineKeyboardButton(text="✅ Approve (7 Days)", callback_data=f"adm_ok_{message.from_user.id}_7")
        ],
        [types.InlineKeyboardButton(text="❌ Reject", callback_data=f"adm_no_{message.from_user.id}")]
    ])
    
    # Admin-ku photo-voda details anupuradhu
    await message.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=message.photo[-1].file_id,
        caption=f"💰 **New Payment Proof!**\n\n👤 User: {message.from_user.full_name}\n🆔 ID: `{message.from_user.id}`\n\nCheck payment & click button below:",
        reply_markup=kb
    )

# --- ADMIN ACTIONS ---

@router.callback_query(F.data.startswith("adm_ok_"))
async def admin_approve(callback: types.CallbackQuery):
    # data format: adm_ok_USERID_DAYS
    data = callback.data.split("_")
    target_user_id = int(data[2])
    days = int(data[3])
    
    expiry = datetime.datetime.now() + datetime.timedelta(days=days)
    
    # DB Update
    await db.users.update_one(
        {"user_id": target_user_id},
        {"$set": {"is_premium": True, "expiry_date": expiry.strftime("%Y-%m-%d")}}
    )
    
    # Notify User
    try:
        await callback.bot.send_message(
            target_user_id, 
            f"🎉 **Premium Activated!**\n\nPlan: {days} Days\nExpiry: {expiry.strftime('%Y-%m-%d')}\n🔥 Unlimited features access unlocked!"
        )
    except: pass
    
    await callback.message.edit_caption(caption=callback.message.caption + f"\n\n✅ **APPROVED ({days} Days)**")
    await callback.answer("Premium Activated!")

@router.callback_query(F.data.startswith("adm_no_"))
async def admin_reject(callback: types.CallbackQuery):
    target_user_id = int(callback.data.split("_")[2])
    
    try:
        await callback.bot.send_message(target_user_id, "❌ **Payment Rejected!**\n\nUngal screenshot verify panna mudiyaala. Proper-ana proof anupunga.")
    except: pass
    
    await callback.message.edit_caption(caption=callback.message.caption + "\n\n❌ **REJECTED**")
    await callback.answer("Rejected.")
            
