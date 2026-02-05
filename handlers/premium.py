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

# --- PREMIUM MENU & QR CODE (Same as before) ---
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
        try: await event.message.delete()
        except: pass
        await event.message.answer(text, reply_markup=kb)

@router.callback_query(F.data.startswith("payup_"))
async def process_direct_pay(callback: types.CallbackQuery):
    amount = callback.data.split("_")[1]
    plan = PLANS[amount]
    upi_payload = f"upi://pay?pa={UPI_ID}&pn=CoupleDating&am={amount}&cu=INR"
    encoded_upi = urllib.parse.quote(upi_payload)
    qr_api_url = f"https://quickchart.io/qr?text={encoded_upi}&size=300"
    
    caption = f"✨ **Plan: {plan['name']}**\n💰 **Amount: ₹{amount}**\n\n📍 **UPI ID:** `{UPI_ID}`\n\n📸 Screenshot-ah inga anupunga."
    kb = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🔙 Back", callback_data="go_premium")]])
    
    await callback.answer()
    try: await callback.message.delete()
    except: pass
    await callback.bot.send_photo(chat_id=callback.message.chat.id, photo=qr_api_url, caption=caption, reply_markup=kb)

# --- PHOTO HANDLER WITH SPECIAL FILTER ---
# Indha message-la "Payment" illa "Premium" nu caption irundha mattum filter pannalam nu patha, user chumma anupuvanga.
# So direct-ah ellame LOG_GROUP_1-ku anupa solrom.

@router.message(F.photo)
async def handle_payment_to_log_group(message: types.Message):
    # LOG_GROUP_1 check
    if not LOG_GROUP_1:
        return await message.answer("❌ Error: Log Group ID not set in Config!")

    await message.reply("✅ **Proof Received!**\nAdmin team check panni 5-10 mins-la active pannuvanga.")
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="✅ Approve 7D", callback_data=f"adm_ok_{message.from_user.id}_7"),
            types.InlineKeyboardButton(text="✅ Approve 30D", callback_data=f"adm_ok_{message.from_user.id}_30")
        ],
        [
            types.InlineKeyboardButton(text="✅ Approve 90D", callback_data=f"adm_ok_{message.from_user.id}_90"),
            types.InlineKeyboardButton(text="❌ Reject", callback_data=f"adm_no_{message.from_user.id}")
        ]
    ])
    
    await message.bot.send_photo(
        chat_id=LOG_GROUP_1,
        photo=message.photo[-1].file_id,
        caption=f"💰 **PAYMENT PROOF**\n\n👤 User: {message.from_user.full_name}\n🆔 ID: `{message.from_user.id}`\n🔗 @{message.from_user.username}",
        reply_markup=kb
    )

# --- CALLBACKS (Approve/Reject) ---
@router.callback_query(F.data.startswith("adm_ok_"))
async def group_approve(callback: types.CallbackQuery):
    data = callback.data.split("_")
    uid, days = int(data[2]), int(data[3])
    exp = (datetime.datetime.now() + datetime.timedelta(days=days)).strftime("%Y-%m-%d")
    await db.users.update_one({"user_id": uid}, {"$set": {"is_premium": True, "expiry_date": exp}})
    try: await callback.bot.send_message(uid, f"🎉 **Premium Active!**\nExpiry: {exp}")
    except: pass
    await callback.message.edit_caption(caption=callback.message.caption + f"\n\n✅ Approved {days}D")

@router.callback_query(F.data.startswith("adm_no_"))
async def group_reject(callback: types.CallbackQuery):
    uid = int(callback.data.split("_")[2])
    try: await callback.bot.send_message(uid, "❌ Payment Rejected!")
    except: pass
    await callback.message.edit_caption(caption=callback.message.caption + "\n\n❌ Rejected")
    
