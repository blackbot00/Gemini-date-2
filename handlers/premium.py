from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import db
from utils.keyboards import get_main_menu
import datetime
import urllib.parse
from config import ADMIN_ID, UPI_ID

router = Router()

# State handling for screenshot
class PaymentState(StatesGroup):
    waiting_for_screenshot = State()

PLANS = {
    "29": {"name": "1 Week", "days": 7},
    "79": {"name": "1 Month", "days": 30},
    "149": {"name": "3 Months", "days": 90}
}

@router.message(Command("premium"))
@router.callback_query(F.data == "go_premium")
async def premium_menu(event: types.Message | types.CallbackQuery, state: FSMContext):
    await state.clear() # Clear any previous states
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
        # Check if the current message has a caption (is a photo) or text
        if event.message.photo:
            await event.message.delete()
            await event.message.answer(text, reply_markup=kb)
        else:
            await event.message.edit_text(text, reply_markup=kb)

@router.callback_query(F.data.startswith("payup_"))
async def process_direct_pay(callback: types.CallbackQuery, state: FSMContext):
    amount = callback.data.split("_")[1]
    plan = PLANS[amount]
    
    upi_payload = f"upi://pay?pa={UPI_ID}&pn=CoupleDating&am={amount}&cu=INR"
    encoded_upi = urllib.parse.quote(upi_payload)
    qr_api_url = f"https://quickchart.io/qr?text={encoded_upi}&size=300"
    
    caption = (
        f"✨ **Plan: {plan['name']}**\n"
        f"💰 **Amount: ₹{amount}**\n\n"
        f"📍 **UPI ID:** `{UPI_ID}`\n\n"
        f"📸 **Step 1:** Intha QR code-ah scan panni ₹{amount} pay pannunga.\n"
        f"📤 **Step 2:** Pay panni mudichuttu **Screenshot**-ah keela anupunga.\n\n"
        f"⏳ Admin verify panna udanae active aagidum."
    )
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔙 Back", callback_data="go_premium")]
    ])
    
    await callback.answer()
    await callback.message.delete()
    
    # Send QR and set state
    await callback.bot.send_photo(
        chat_id=callback.message.chat.id,
        photo=qr_api_url,
        caption=caption,
        reply_markup=kb,
        parse_mode="Markdown"
    )
    await state.set_state(PaymentState.waiting_for_screenshot)
    await state.update_data(plan_amount=amount)

# --- Screenshot Handling with State ---

@router.message(PaymentState.waiting_for_screenshot, F.photo)
async def handle_payment_screenshot(message: types.Message, state: FSMContext):
    data = await state.get_data()
    amount = data.get("plan_amount", "Unknown")
    
    await message.answer("✅ Screenshot received! Admin check panniட்டு activate pannuvanga. Please wait.")
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="✅ Approve", callback_data=f"approve_{message.from_user.id}_{amount}")],
        [types.InlineKeyboardButton(text="❌ Reject", callback_data=f"reject_{message.from_user.id}")]
    ])
    
    # Send to Admin
    await message.bot.send_photo(
        ADMIN_ID, 
        message.photo[-1].file_id, 
        caption=f"💰 **New Payment Proof!**\n\n👤 User: {message.from_user.full_name}\n🆔 ID: `{message.from_user.id}`\n💵 Plan: ₹{amount}",
        reply_markup=kb
    )
    await state.clear()

# --- Approval Logic ---

@router.callback_query(F.data.startswith("approve_"))
async def approve_payment(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    user_id = int(parts[1])
    amount = parts[2]
    
    # Logic for days based on amount
    days = 30
    if amount == "29": days = 7
    elif amount == "149": days = 90

    expiry = datetime.datetime.now() + datetime.timedelta(days=days)
    
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"is_premium": True, "expiry_date": expiry.strftime("%Y-%m-%d")}}
    )
    
    try:
        await callback.bot.send_message(user_id, f"🎉 **Premium Activated!**\n\nPlan: ₹{amount}\nExpiry: {expiry.strftime('%Y-%m-%d')}\n🔥 Enjoy your features!")
    except:
        pass
        
    await callback.message.edit_caption(caption=callback.message.caption + "\n\n✅ **APPROVED**")
    await callback.answer("Premium Activated!")

@router.callback_query(F.data.startswith("reject_"))
async def reject_payment(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    try:
        await callback.bot.send_message(user_id, "❌ **Payment Rejected!**\nPlease check the screenshot and try again.")
    except:
        pass
    await callback.message.edit_caption(caption=callback.message.caption + "\n\n❌ **REJECTED**")
    await callback.answer("Rejected.")
    
