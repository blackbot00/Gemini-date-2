from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from database import db
from config import LOG_GROUP_2, LOG_GROUP_1
from utils.keyboards import get_main_menu
import datetime
import asyncio

router = Router()

# --- HELPER FUNCTIONS ---
async def find_partner(user_id):
    return await db.users.find_one({"status": "searching", "user_id": {"$ne": user_id}})

async def delete_message_after(message: types.Message, delay: int):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except:
        pass

async def exit_logic(message, state, user_id=None):
    uid = user_id or message.chat.id
    user = await db.users.find_one({"user_id": uid})
    
    if user and user.get("partner"):
        partner_id = user.get("partner")
        await db.users.update_many({"user_id": {"$in": [uid, partner_id]}}, {"$set": {"status": "idle", "partner": None}})
        
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🚫 Report Partner", callback_data=f"report_{partner_id}")]
        ])
        
        m1 = await message.bot.send_message(partner_id, "⚠️ Partner left the chat.", reply_markup=get_main_menu())
        m2 = await message.bot.send_message(partner_id, "Report if needed (9s):", reply_markup=kb)
        
        await message.answer("Chat ended.", reply_markup=get_main_menu())
        m3 = await message.answer("Report if needed (9s):", reply_markup=kb)
        
        # Auto-delete report buttons (Point 3)
        asyncio.create_task(delete_message_after(m2, 9))
        asyncio.create_task(delete_message_after(m3, 9))
    else:
        await db.users.update_one({"user_id": uid}, {"$set": {"status": "idle", "partner": None}})
        await message.answer("Chat ended.", reply_markup=get_main_menu())
    await state.clear()

# --- SEARCH LOGIC ---
@router.callback_query(F.data == "chat_human")
async def start_human_search(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_data = await db.users.find_one({"user_id": user_id})

    # Daily Limit (Point 2)
    daily_limit = 50
    if not user_data.get("is_premium", False) and user_data.get("daily_chats", 0) >= daily_limit:
        return await callback.answer(f"❌ Daily limit {daily_limit} chats reached! Upgrade to Premium for Unlimited. 💎", show_alert=True)

    partner = await find_partner(user_id)
    now = datetime.datetime.now()
    
    if partner:
        await db.users.update_one({"user_id": user_id}, {"$set": {"status": "chatting", "partner": partner['user_id'], "chat_start": now}, "$inc": {"daily_chats": 1}})
        await db.users.update_one({"user_id": partner['user_id']}, {"$set": {"status": "chatting", "partner": user_id, "chat_start": now}, "$inc": {"daily_chats": 1}})
        
        def partner_info(p, viewer_is_premium):
            gender_text = p['gender'] if viewer_is_premium else "🔒 Premium Required 💎"
            return f"💌 **Partner Details**\n👤 Gender: {gender_text}\n🎂 Age: {p['age']}\n📍 State: {p['state']}"

        await callback.message.edit_text(f"{partner_info(partner, user_data.get('is_premium'))}\n\nConnected! Start chatting!", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🛑 Exit", callback_data="exit_chat")]]))
        await callback.bot.send_message(partner['user_id'], f"{partner_info(user_data, partner.get('is_premium'))}\n\nConnected! Start chatting!", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🛑 Exit", callback_data="exit_chat")]]))
    else:
        await db.users.update_one({"user_id": user_id}, {"$set": {"status": "searching"}})
        await callback.message.edit_text("🔍 Searching...", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="❌ Cancel", callback_data="exit_chat")]]))

# --- MESSAGE RELAY & FORWARD LOGGING ---
@router.message(F.chat.type == "private")
async def relay_handler(message: types.Message, state: FSMContext):
    if message.text == "/exit": return await exit_logic(message, state)
    
    user = await db.users.find_one({"user_id": message.from_user.id})
    if not user or user.get("status") != "chatting": return

    partner_id = user.get("partner")
    partner_data = await db.users.find_one({"user_id": partner_id})
    
    # Strict Blocking
    if message.text:
        forbidden = ["http", ".com", ".in", "@", "t.me", "/", ".net"]
        if not user.get("is_premium") and any(x in message.text.lower() for x in forbidden):
            return await message.answer("⚠️ Links and Usernames are blocked!")

    # Media Timer
    if not message.text and not user.get("is_premium"):
        elapsed = (datetime.datetime.now() - user.get("chat_start")).total_seconds()
        if elapsed < 180:
            return await message.answer(f"⏳ Media sharing enabled in {int(180 - elapsed)}s.")

    # LOGGING & RELAYING (Point 1: Full Forwarding)
    log_header = f"📤({user['name']})[{user['user_id']}] ➜ ({partner_data['name']})[{partner_id}]📩"
    await message.bot.send_message(LOG_GROUP_2, log_header)

    try:
        # Forward everything to log channel
        await message.forward(LOG_GROUP_2)
        
        # Relay to partner
        if message.text:
            await message.bot.send_message(partner_id, message.text)
        elif message.photo:
            await message.bot.send_photo(partner_id, message.photo[-1].file_id, caption=message.caption)
        elif message.video:
            await message.bot.send_video(partner_id, message.video.file_id, caption=message.caption)
        elif message.document:
            await message.bot.send_document(partner_id, message.document.file_id, caption=message.caption)
        elif message.animation:
            await message.bot.send_animation(partner_id, message.animation.file_id)
    except:
        pass

# --- REPORT SYSTEM ---
@router.callback_query(F.data.startswith("report_"))
async def report_user_menu(callback: types.CallbackQuery):
    target_id = callback.data.split("_")[1]
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Abuse 🤬", callback_data=f"confirmreport_Abuse_{target_id}")],
        [types.InlineKeyboardButton(text="Scam 💸", callback_data=f"confirmreport_Scam_{target_id}")],
        [types.InlineKeyboardButton(text="Adult 🔞", callback_data=f"confirmreport_Adult_{target_id}")]
    ])
    await callback.message.edit_text("Select Reason:", reply_markup=kb)

@router.callback_query(F.data.startswith("confirmreport_"))
async def submit_report(callback: types.CallbackQuery):
    _, reason, target_id = callback.data.split("_")
    target = await db.users.find_one({"user_id": int(target_id)})
    
    report_msg = f"🚷 **Report**\nReporter: {callback.from_user.id}\nTarget: {target['name']} ({target_id})\nReason: {reason}"
    await callback.bot.send_message(LOG_GROUP_1, report_msg)
    await callback.message.edit_text("✅ Reported.")

@router.callback_query(F.data == "exit_chat")
async def exit_callback(callback: types.CallbackQuery, state: FSMContext):
    await exit_logic(callback.message, state, callback.from_user.id)
    
