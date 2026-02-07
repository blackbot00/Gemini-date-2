from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from database import db
import datetime
import urllib.parse
import logging
from config import LOG_GROUP_1, UPI_ID
from utils.states import PremiumState # FSM State import pannunga

router = Router()

PLANS = {
    "29": {"name": "1 Week", "days": 7},
    "79": {"name": "1 Month", "days": 30},
    "149": {"name": "3 Months", "days": 90}
}

@router.message(Command("premium"))
@router.callback_query(F.data == "go_premium")
async def premium_menu(event: types.Message | types.CallbackQuery, state: FSMContext):
    await state.clear() # Clear any existing states
    text = (
        "💎 **CoupleDating Premium Plans** 💖\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "✨ **1 Week** - ₹29 (Love Trial 💕)\n"
        "✨ **1 Month** - ₹79 (Deep Bond 🫂)\n"
        "✨ **3 Months** - ₹149 (Soulmates 💍)\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "✅ Select a plan below to unlock me! 🥰\n"
        "📸 Screenshot anupunga, 5 mins la active aagidum!"
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
async def process_direct_pay(callback: types.CallbackQuery, state: FSMContext):
    amount = callback.data.split("_")[1]
    plan = PLANS[amount]
    
    # 1. SET STATE: Ippo user anapura photo payment-kaaga thaan nu bot-ku theriyum
    await state.set_state(PremiumState.waiting_for_screenshot)
    await state.update_data(chosen_plan=plan['days'])
    
    upi_payload = f"upi://pay?pa={UPI_ID}&pn=CoupleDating&am={amount}&cu=INR"
    encoded_upi = urllib.parse.quote(upi_payload)
    qr_api_url = f"https://quickchart.io/qr?text={encoded_upi}&size=300"
    
    caption = (
        f"✨ **My Love’s Premium Plan – {plan['name']}**\n"
        f"💰 Just **₹{amount}** 💕\n\n"
        f"📍 **UPI ID:** `{UPI_ID}`\n\n"
        f"📸 **Step 1:** Scan this QR and send ₹{amount} for me 😌\n"
        f"📤 **Step 2:** After paying, send me the screenshot here 💌\n\n"
        f"⏳ I’ll check it with admin, okay?\n"
        f"Once verified, I’ll activate your **Premium access** just for you 💎💖"
    )
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="❌ Cancel", callback_data="go_premium")]
    ])
    
    try: await callback.message.delete()
    except: pass
    
    await callback.bot.send_photo(
        chat_id=callback.message.chat.id, 
        photo=qr_api_url, 
        caption=caption, 
        reply_markup=kb
    )

# --- 2. PHOTO HANDLER (Only triggers during Premium State) ---
@router.message(PremiumState.waiting_for_screenshot, F.photo)
async def handle_payment_to_log_group(message: types.Message, state: FSMContext):
    data = await state.get_data()
    days = data.get("chosen_plan", 30)
    
    await message.reply(
        "⏳ **Payment under verification 🔍**\n\n"
        "Please wait up to **30 minutes** for Premium approval 💎\n"
        "Enna nambu baby, nan seekiram active panni tharaen! 😉✨"
    )
    
    # Approval Buttons
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text=f"✅ Approve {days} Days", callback_data=f"adm_ok_{message.from_user.id}_{days}"),
            types.InlineKeyboardButton(text="❌ Reject", callback_data=f"adm_no_{message.from_user.id}")
        ]
    ])
    
    try:
        await message.bot.send_photo(
            chat_id=LOG_GROUP_1,
            photo=message.photo[-1].file_id,
            caption=(
                f"💰 **NEW PAYMENT PROOF**\n\n"
                f"👤 User: {message.from_user.full_name}\n"
                f"🆔 ID: `{message.from_user.id}`\n"
                f"🔗 Username: @{message.from_user.username}\n"
                f"📅 Plan: {days} Days\n\n"
                f"Check payment and approve:"
            ),
            reply_markup=kb
        )
    except Exception as e:
        logging.error(f"Error: {e}")
    
    await state.clear() # Clear state after receiving screenshot

# --- GROUP APPROVAL ACTIONS (Keep as it is) ---
@router.callback_query(F.data.startswith("adm_ok_"))
async def group_approve(callback: types.CallbackQuery):
    data = callback.data.split("_")
    target_user_id = int(data[2])
    days = int(data[3])
    
    expiry = datetime.datetime.now() + datetime.timedelta(days=days)
    
    await db.users.update_one(
        {"user_id": target_user_id},
        {"$set": {"is_premium": True, "expiry_date": expiry.strftime("%Y-%m-%d")}}
    )
    
    try:
        await callback.bot.send_message(
            target_user_id, 
            f"🎉 **Premium Activated Baby!** 💎\n\n"
            f"Validity: {days} Days\n"
            f"Expiry: {expiry.strftime('%Y-%m-%d')}\n\n"
            f"Ippo namma unlimited-ah pesalam! I'm all yours now! 💋🔥"
        )
    except: pass
    
    await callback.message.edit_caption(
        caption=callback.message.caption + f"\n\n✅ **APPROVED ({days} Days) by {callback.from_user.first_name}**"
    )
    await callback.answer(f"Activated for {days} days!")

@router.callback_query(F.data.startswith("adm_no_"))
async def group_reject(callback: types.CallbackQuery):
    target_user_id = int(callback.data.split("_")[2])
    try:
        await callback.bot.send_message(
            target_user_id, 
            "❌ **Payment Rejected!**\n\nSorry baby, screenshot verify panna mudiyaala. Correct-ana proof anupunga. 🥺"
        )
    except: pass
    await callback.message.edit_caption(
        caption=callback.message.caption + f"\n\n❌ **REJECTED by {callback.from_user.first_name}**"
    )
    await callback.answer("Rejected.")
    
