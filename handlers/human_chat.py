from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from database import db
from config import LOG_GROUP_2, LOG_GROUP_1
from utils.keyboards import get_main_menu
from utils.states import ChatState
import datetime
import asyncio

router = Router()

# --- HELPER: EXIT LOGIC ---
async def exit_logic(message, state, user_id=None):
    uid = user_id or (message.chat.id if hasattr(message, 'chat') else message.from_user.id)
    user = await db.users.find_one({"user_id": uid})
    
    if user and user.get("partner"):
        partner_id = user.get("partner")
        partner_data = await db.users.find_one({"user_id": partner_id})

        try:
            if user.get("conn_msg_id"):
                await message.bot.delete_message(uid, user["conn_msg_id"])
            if partner_data and partner_data.get("conn_msg_id"):
                await message.bot.delete_message(partner_id, partner_data["conn_msg_id"])
        except: pass

        await db.users.update_many({"user_id": {"$in": [uid, partner_id]}}, {"$set": {"status": "idle", "partner": None, "conn_msg_id": None}})
        
        report_kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🚫 Report Your Partner", callback_data=f"ask_rep_{partner_id}")]
        ])
        
        await message.bot.send_message(partner_id, "⚠️ Partner left the chat.", reply_markup=get_main_menu())
        m1 = await message.bot.send_message(partner_id, "Click below to report:", reply_markup=report_kb)
        
        final_text = "Chat ended. Hope you found someone special! ❤️"
        if isinstance(message, types.CallbackQuery):
            await message.message.answer(final_text, reply_markup=get_main_menu())
            m2 = await message.message.answer("Click below to report:", reply_markup=report_kb)
        else:
            await message.answer(final_text, reply_markup=get_main_menu())
            m2 = await message.answer("Click below to report:", reply_markup=report_kb)
        
        asyncio.create_task(delete_after(m1, 9))
        asyncio.create_task(delete_after(m2, 9))
    else:
        await db.users.update_one({"user_id": uid}, {"$set": {"status": "idle", "partner": None}})
        if isinstance(message, types.CallbackQuery):
            await message.message.answer("Chat ended.", reply_markup=get_main_menu())
        else:
            await message.answer("Chat ended.", reply_markup=get_main_menu())
    
    await state.clear()

# --- 2-STEP REPORT LOGIC ---
@router.callback_query(F.data.startswith("ask_rep_"))
async def ask_report_reason(callback: types.CallbackQuery):
    target_id = callback.data.split("_")[2]
    reason_kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🤬 Abuse", callback_data=f"final_rep_Abuse_{target_id}"),
         types.InlineKeyboardButton(text="💸 Scam", callback_data=f"final_rep_Scam_{target_id}")],
        [types.InlineKeyboardButton(text="🔞 Adult Content", callback_data=f"final_rep_Adult_{target_id}")]
    ])
    await callback.message.edit_text("Select the reason for reporting:", reply_markup=reason_kb)

@router.callback_query(F.data.startswith("final_rep_"))
async def final_report(callback: types.CallbackQuery):
    _, _, reason, target_id = callback.data.split("_")
    reported_user = await db.users.find_one({"user_id": int(target_id)})
    reported_name = reported_user['name'] if reported_user else "Unknown"

    report_log = (
        "🚷 **New Report Submitted** 🚷\n"
        "━━━━━━━━━━━━━━\n"
        f"Reporter: {callback.from_user.full_name} (`{callback.from_user.id}`)\n"
        f"Reported: {reported_name} (`{target_id}`)\n\n"
        f"Reason: **{reason}**"
    )
    
    await callback.bot.send_message(LOG_GROUP_1, report_log)
    await callback.answer("Report sent to Admin! ✅", show_alert=True)
    await callback.message.delete()

# --- SEARCH LOGIC ---
async def delete_after(message, delay: int):
    await asyncio.sleep(delay)
    try: await message.delete()
    except: pass

async def find_partner(user_id):
    return await db.users.find_one({"status": "searching", "user_id": {"$ne": user_id}})

@router.callback_query(F.data == "exit_chat")
async def exit_callback(callback: types.CallbackQuery, state: FSMContext):
    await exit_logic(callback, state, callback.from_user.id)

@router.callback_query(F.data == "chat_human")
async def start_human_search(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_data = await db.users.find_one({"user_id": user_id})
    
    # --- ADDED BAN CHECK HERE ---
    if user_data and user_data.get("is_banned"):
        return await callback.answer("❌ You are banned from using this bot.", show_alert=True)
    
    if user_data and user_data.get("status") == "chatting":
        return await callback.answer("Hey 👩‍❤️‍👨 you’re in a chat right now.\nUse /exit 🚪 to continue.", show_alert=True)
    
    if not user_data: return await callback.answer("⚠️ Register first!", show_alert=True)
    is_premium = user_data.get("is_premium", False)
    partner = await find_partner(user_id)
    now = datetime.datetime.now()
    if partner:
        await db.users.update_one({"user_id": user_id}, {"$set": {"status": "chatting", "partner": partner['user_id'], "chat_start": now}, "$inc": {"daily_chats": 1}})
        await db.users.update_one({"user_id": partner['user_id']}, {"$set": {"status": "chatting", "partner": user_id, "chat_start": now}, "$inc": {"daily_chats": 1}})
        if partner.get("last_search_msg_id"):
            try: await callback.bot.delete_message(partner['user_id'], partner['last_search_msg_id'])
            except: pass
        def p_info(p, prem):
            g = p['gender'] if prem else "🔒 Locked 💎 Premium Only"
            return f"💌 **Partner Details**\n━━━━━━━━━━━━━━\n👤 Gender: {g}\n🎂 Age: {p['age']}\n📍 State: {p['state']}"
        
        u_m = await callback.message.edit_text(f"{p_info(partner, is_premium)}\n\nConnected! Start chatting!", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🛑 Exit Chat", callback_data="exit_chat")]]))
        await db.users.update_one({"user_id": user_id}, {"$set": {"conn_msg_id": u_m.message_id}})
        p_m = await callback.bot.send_message(partner['user_id'], f"{p_info(user_data, partner.get('is_premium'))}\n\nConnected! Start chatting!", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🛑 Exit Chat", callback_data="exit_chat")]]))
        await db.users.update_one({"user_id": partner['user_id']}, {"$set": {"conn_msg_id": p_m.message_id}})
    else:
        await db.users.update_one({"user_id": user_id}, {"$set": {"status": "searching", "last_search_msg_id": callback.message.message_id}})
        await callback.message.edit_text("🔍 Searching for a partner...", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_search")]]))

@router.callback_query(F.data == "cancel_search")
async def cancel_search(callback: types.CallbackQuery, state: FSMContext):
    await db.users.update_one({"user_id": callback.from_user.id}, {"$set": {"status": "idle"}})
    await callback.message.delete()
    await callback.message.answer("Search cancelled.", reply_markup=get_main_menu())

# --- MESSAGE RELAY (FIXED) ---
@router.message(F.chat.type == "private")
async def relay_handler(message: types.Message, state: FSMContext):
    # 1. AI Chat check
    current_state = await state.get_state()
    if current_state == ChatState.on_ai_chat: 
        return

    # 2. Command check
    if message.text and message.text.startswith("/"):
        if message.text == "/exit":
            return await exit_logic(message, state)
        return 

    user = await db.users.find_one({"user_id": message.from_user.id})
    
    # 3. Ban Check in Relay
    if user and user.get("is_banned"):
        return

    is_chatting = user and user.get("status") == "chatting"

    # 4. Connection check (Non-commands only)
    if not is_chatting:
        if message.text or message.photo or message.video:
            return await message.answer("⚠️ **Not Connected!**\nPlease click 'Chat with Human' first to find a partner. ❤️")
        return

    partner_id = user.get("partner")
    is_premium = user.get("is_premium", False)
    partner_data = await db.users.find_one({"user_id": partner_id})
    
    log_header = f"📤 **{user['name']}** (`{user['user_id']}`) ➜ **{partner_data['name']}** (`{partner_id}`) 📩"

    try:
        if message.text:
            if not is_premium and any(x in message.text.lower() for x in ["http", ".com", ".in", "@", "t.me"]):
                return await message.answer("⚠️ Links/Usernames are blocked! for free users 💎")
            await message.bot.send_message(partner_id, message.text)
            await message.bot.send_message(LOG_GROUP_2, f"{log_header}\n💬 {message.text}")
        else:
            if not is_premium:
                elapsed = (datetime.datetime.now() - user.get("chat_start")).total_seconds()
                if elapsed < 180: return await message.answer(f"⏳ Media enabled in {int(180 - elapsed)}s. 💎upgrade to premium to instant share media 💖")
            await message.bot.send_message(LOG_GROUP_2, log_header)
            await message.forward(LOG_GROUP_2)
            if message.photo: await message.bot.send_photo(partner_id, message.photo[-1].file_id, caption=message.caption)
            elif message.video: await message.bot.send_video(partner_id, message.video.file_id, caption=message.caption)
            elif message.document: await message.bot.send_document(partner_id, message.document.file_id, caption=message.caption)
            elif message.animation: await message.bot.send_animation(partner_id, message.animation.file_id)
    except: pass
            
