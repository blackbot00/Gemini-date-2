# handlers/premium.py
from aiogram import Router, F, types
from aiogram.filters import Command # Add this
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

# Inga Command add pannirukaen, so /premium nu type pannaalum idhu work aagum
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

# Indha function dhaan 29, 79 buttons-ah handle pannum
@router.callback_query(F.data.startswith("payup_"))
async def process_direct_pay(callback: types.CallbackQuery):
    amount = callback.data.split("_")[1]
    plan = PLANS[amount]
    upi_link = f"upi://pay?pa={UPI_ID}&pn=CoupleDating&am={amount}&cu=INR"
    
    text = (
        f"✨ **Plan: {plan['name']}**\n"
        f"💰 **Amount: ₹{amount}**\n\n"
        f"📍 **UPI ID:** `{UPI_ID}`\n\n"
        f"1️⃣ Keela ulla button click panni pay pannunga.\n"
        f"2️⃣ Pay panni mudichuttu **Screenshot** anupunga.\n"
        f"3️⃣ Admin verify panna udanae active aagidum."
    )
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="📱 Open Payment App", url=upi_link)],
        [types.InlineKeyboardButton(text="🔙 Back", callback_data="go_premium")]
    ])
    
    # Adhellam correct-ah work aagudhanu check panna answer callback kudukrom
    await callback.answer() 
    await callback.message.edit_text(text, reply_markup=kb)

# ... (rest of the handle_payment_screenshot and approval logic remains same)
