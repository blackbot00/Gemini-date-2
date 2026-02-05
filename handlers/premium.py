from aiogram import Router, F, types
from aiogram.filters import Command
from database import db
import datetime
import urllib.parse
from config import LOG_GROUP_1, UPI_ID

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
    try:
        await callback.message.delete()
    except: pass
    
    await callback.bot.send_photo(
        chat_id=callback.message.chat.id, 
        photo=qr_api_url, 
        caption=caption, 
        reply_markup=kb
    )

# --- SEND TO LOG GROUP 1 ---
@router.message(F.photo)
async def handle_payment_to_log_group(message: types.Message):
    # User-ku message
    await message.reply("✅ **Screenshot Received!**\nAdmin team verify panni active pannuvanga. Please wait.")
    
    # Approval Buttons for Log Group 1
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="✅ 30 Days", callback_data=f"adm_ok_{message.from_user.id}_30"),
            types.InlineKeyboardButton(text="✅ 7 Days", callback_data=f"adm_ok_{message.from_user.id}_7")
        ],
        [
            types.InlineKeyboardButton(text="✅ 90 Days", callback_data=f"adm_ok_{message.from_user.id}_90"),
            types.InlineKeyboardButton(text="❌ Reject", callback_data=f"adm_no_{message.from_user.id}")
        ]
    ])
    
    # Sending to LOG_GROUP_1
    await message.bot.send_photo(
        chat_id=LOG_GROUP_1,
        photo=message.photo[-1].file_id,
        caption=(
            f"💰 **NEW PAYMENT PROOF**\n\n"
            f"👤 User: {message.from_user.full_name}\n"
            f"🆔 ID: `{message.from_user.id}`\n"
            f"🔗 User: @{message.from_user.username if message.from_user.username else 'N/A'}\n\n"
            f"Verify and click a button below:"
        ),
        reply_markup=kb
    )

# --- GROUP APPROVAL ACTIONS ---

@router.callback_query(F.data.startswith("adm_ok_"))
async def group_approve(callback: types.CallbackQuery):
    data = callback.data.split("_")
    target_user_id = int(data[2])
    days = int(data[3])
    
    expiry = datetime.datetime.now() + datetime.timedelta(days=days)
    
    # Update Database
    await db.users.update_one(
        {"user_id": target_user_id},
        {"$set": {"is_premium": True, "expiry_date": expiry.strftime("%Y-%m-%d")}}
    )
    
    # Notify User in DM
    try:
        await callback.bot.send_message(
            target_user_id, 
            f"🎉 **Premium Activated!**\n\nValidity: {days} Days\nExpiry: {expiry.strftime('%Y-%m-%d')}\n🔥 Unlimited access start aagidichi!"
        )
    except: pass
    
    # Update Group Message
    await callback.message.edit_caption(
        caption=callback.message.caption + f"\n\n✅ **APPROVED ({days} Days) by {callback.from_user.first_name}**"
    )
    await callback.answer(f"User {target_user_id} is now Premium!")

@router.callback_query(F.data.startswith("adm_no_"))
async def group_reject(callback: types.CallbackQuery):
    target_user_id = int(callback.data.split("_")[2])
    
    try:
        await callback.bot.send_message(
            target_user_id, 
            "❌ **Payment Rejected!**\n\nProper-ana proof illai. Correct-ana screenshot anupunga."
        )
    except: pass
    
    await callback.message.edit_caption(
        caption=callback.message.caption + f"\n\n❌ **REJECTED by {callback.from_user.first_name}**"
    )
    await callback.answer("Rejected.")
    
