from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from database import db
from config import LOG_GROUP_2
from utils.keyboards import get_main_menu
import datetime
import asyncio

router = Router()

# --- HELPER FUNCTIONS ---
async def find_partner(user_id):
    return await db.users.find_one({"status": "searching", "user_id": {"$ne": user_id}})

async def exit_logic(message, state, user_id=None):
    uid = user_id or message.chat.id
    user = await db.users.find_one({"user_id": uid})
    
    if user and user.get("partner"):
        partner_id = user.get("partner")
        await db.users.update_many({"user_id": {"$in": [uid, partner_id]}}, {"$set": {"status": "idle", "partner": None}})
        
        # Report Buttons for both users
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🚫 Report Partner", callback_data=f"report_{partner_id}")]
        ])
        
        await message.bot.send_message(partner_id, "⚠️ Partner left the chat.", reply_markup=get_main_menu())
        await message.bot.send_message(partner_id, "Did something go wrong? Report if needed:", reply_markup=kb)
        
        kb_self = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🚫 Report Partner", callback_data=f"report_{partner_id}")]
        ])
        await message.answer("Chat ended.", reply_markup=get_main_menu())
        await message.answer("Report if your partner was abusive:", reply_markup=kb_self)
    else:
        await db.users.update_one({"user_id": uid}, {"$set": {"status": "idle", "partner": None}})
        await message.answer("Chat ended.", reply_markup=get_main_menu())
    await state.clear()

# --- SEARCH LOGIC ---
@router.callback_query(F.data == "chat_human")
async def start_human_search(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_data = await db.users.find_one({"user_id": user_id})

    if not user_data.get("is_premium", False) and user_data.get("daily_chats", 0) >= 11:
        return await callback.answer("Daily limit reached! Upgrade to Premium 💎", show_alert=True)

    partner = await find_partner(user_id)
    now = datetime.datetime.now()
    
    if partner:
        await db.users.update_one({"user_id": user_id}, {"$set": {"status": "chatting", "partner": partner['user_id'], "chat_start": now}})
        await db.users.update_one({"user_id": partner['user_id']}, {"$set": {"status": "chatting", "partner": user_id, "chat_start": now}})
        
        # Details Reveal Logic
        def partner_info(p, viewer_is_premium):
            gender_text = p['gender'] if viewer_is_premium else "🔒 Premium Required 💎"
            return f"💌 **Partner Details**\n👤 Gender: {gender_text}\n🎂 Age: {p['age']}\n📍 State: {p['state']}"

        await callback.message.edit_text(f"{partner_info(partner, user_data.get('is_premium'))}\n\nConnected! Start chatting!", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🛑 Exit", callback_data="exit_chat")]]))
        await callback.bot.send_message(partner['user_id'], f"{partner_info(user_data, partner.get('is_premium'))}\n\nConnected! Start chatting!", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🛑 Exit", callback_data="exit_chat")]]))
    else:
        await db.users.update_one({"user_id": user_id}, {"$set": {"status": "searching"}})
        await callback.message.edit_text("🔍 Searching...", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="❌ Cancel", callback_data="exit_chat")]]))

# --- MESSAGE RELAY (TEXT & MEDIA) ---
@router.message(F.chat.type == "private")
async def relay_handler(message: types.Message, state: FSMContext):
    if message.text == "/exit": return await exit_logic(message, state)
    
    user = await db.users.find_one({"user_id": message.from_user.id})
    if not user or user.get("status") != "chatting": return

    partner_id = user.get("partner")
    partner_data = await db.users.find_one({"user_id": partner_id})
    
    # 1. LINK & USERNAME BLOCK
    if message.text:
        forbidden = ["http", ".com", ".in", "@", "t.me", "/", ".net"]
        if not user.get("is_premium") and any(x in message.text.lower() for x in forbidden):
            return await message.answer("⚠️ Links and Usernames are blocked for Free users!")

    # 2. MEDIA TIMER CHECK (3 MINS)
    if not message.text: # If it's photo, video, etc.
        if not user.get("is_premium"):
            start_time = user.get("chat_start")
            elapsed = (datetime.datetime.now() - start_time).total_seconds()
            if elapsed < 180: # 3 minutes
                wait = int(180 - elapsed)
                return await message.answer(f"⏳ Media sharing enabled in {wait} seconds. Upgrade to Premium for instant share! 💎")

    # 3. LOGGING & RELAYING
    log_header = f"📤({user['name']})[{user['user_id']}] ➜ ({partner_data['name']})[{partner_id}]📩"
    
    try:
        if message.text:
            await message.bot.send_message(partner_id, message.text)
            await message.bot.send_message(LOG_GROUP_2, f"{log_header}\n💬 {message.text}")
        elif message.photo:
            await message.bot.send_photo(partner_id, message.photo[-1].file_id, caption=message.caption)
            await message.bot.send_message(LOG_GROUP_2, f"{log_header}\n🖼 [Photo]")
        elif message.video:
            await message.bot.send_video(partner_id, message.video.file_id, caption=message.caption)
            await message.bot.send_message(LOG_GROUP_2, f"{log_header}\n📹 [Video]")
        elif message.document:
            await message.bot.send_document(partner_id, message.document.file_id, caption=message.caption)
            await message.bot.send_message(LOG_GROUP_2, f"{log_header}\n📄 [Document]")
        elif message.animation: # GIF
            await message.bot.send_animation(partner_id, message.animation.file_id)
            await message.bot.send_message(LOG_GROUP_2, f"{log_header}\n👾 [GIF]")
    except Exception as e:
        print(f"Relay Error: {e}")

# --- REPORT SYSTEM ---
@router.callback_query(F.data.startswith("report_"))
async def report_user_menu(callback: types.CallbackQuery):
    target_id = callback.data.split("_")[1]
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Abuse 🤬", callback_data=f"confirmreport_Abuse_{target_id}")],
        [types.InlineKeyboardButton(text="Scam 💸", callback_data=f"confirmreport_Scam_{target_id}")],
        [types.InlineKeyboardButton(text="Adult 🔞", callback_data=f"confirmreport_Adult_{target_id}")]
    ])
    await callback.message.edit_text("Select Reason for Reporting:", reply_markup=kb)

@router.callback_query(F.data.startswith("confirmreport_"))
async def submit_report(callback: types.CallbackQuery):
    _, reason, target_id = callback.data.split("_")
    reporter = callback.from_user
    target = await db.users.find_one({"user_id": int(target_id)})
    
    report_msg = (
        f"🚷 **New Report Submitted** 🚷\n"
        f"━━━━━━━━━━━━━━\n"
        f"Reporter: {reporter.full_name} ({reporter.id})\n"
        f"Reported: {target['name']} ({target_id})\n\n"
        f"Reason: {reason}"
    )
    
    from config import LOG_GROUP_1 # Send to admin group
    await callback.bot.send_message(LOG_GROUP_1, report_msg)
    await callback.message.edit_text("✅ Report submitted to admins. Thank you!")

@router.callback_query(F.data == "exit_chat")
async def exit_callback(callback: types.CallbackQuery, state: FSMContext):
    await exit_logic(callback.message, state, callback.from_user.id)
        
