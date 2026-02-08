import openai
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from config import OPENROUTER_KEY, LOG_GROUP_2
from database import db
from utils.states import ChatState
from utils.keyboards import get_main_menu
import datetime

router = Router()

client = openai.OpenAI(
    base_url="https://openrouter.ai/api/v1", 
    api_key=OPENROUTER_KEY,
    default_headers={"HTTP-Referer": "https://koyeb.com", "X-Title": "CoupleDatingBot"}
)

MODELS = ["google/gemini-2.0-flash-lite-preview-02-05:free", "openai/gpt-4o-mini"]

@router.callback_query(F.data == "chat_ai")
async def ai_menu(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_data = await db.users.find_one({"user_id": user_id})
    
    # 1. BAN LOGIC
    if user_data and user_data.get("is_banned"):
        return await callback.answer("❌ You are banned from using this bot.", show_alert=True)

    # Check if user is in human chat
    if user_data and user_data.get("status") == "chatting":
        return await callback.answer("Hey 👩‍❤️‍👨 you’re in a chat right now.\nUse /exit 🚪 to continue.", show_alert=True)

    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Tamil 🇮🇳", callback_data="ailang_Tamil"),
         types.InlineKeyboardButton(text="English 🇺🇸", callback_data="ailang_English")],
        [types.InlineKeyboardButton(text="Telugu 🇮🇳", callback_data="ailang_Telugu"),
         types.InlineKeyboardButton(text="Hindi 🇮🇳", callback_data="ailang_Hindi")],
        [types.InlineKeyboardButton(text="Tanglish ✍️", callback_data="ailang_Tanglish")]
    ])
    await callback.message.edit_text("✨ AI Match: Choose Language", reply_markup=kb)

@router.callback_query(F.data.startswith("ailang_"))
async def ai_personality(callback: types.CallbackQuery, state: FSMContext):
    lang = callback.data.split("_")[1]
    await state.update_data(ai_lang=lang)
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Sweet 😊", callback_data="aitype_sweet"),
         types.InlineKeyboardButton(text="Romantic ❤️", callback_data="aitype_romantic")],
        [types.InlineKeyboardButton(text="18+ 🔥 (Premium)", callback_data="aitype_18")],
        [types.InlineKeyboardButton(text="🔙 Back", callback_data="chat_ai")]
    ])
    await callback.message.edit_text(f"Selected: {lang}\nNow choose AI Personality:", reply_markup=kb)

@router.callback_query(F.data.startswith("aitype_"))
async def start_ai_chat_session(callback: types.CallbackQuery, state: FSMContext):
    user = await db.users.find_one({"user_id": callback.from_user.id})
    p_type = callback.data.split("_")[1]
    
    if p_type == "18" and not user.get("is_premium"):
        return await callback.answer("❌ 18+ mode is for Premium users only!", show_alert=True)

    await state.update_data(ai_type=p_type)
    await state.set_state(ChatState.on_ai_chat)
    await callback.message.edit_text(f"✅ AI Chat Started ({p_type.upper()})\nSend a message! 😍\nUse /exit or button to stop.",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🛑 Stop AI Chat", callback_data="exit_ai")]]))

# 2. STOP AI CHAT BUTTON HANDLER
@router.callback_query(F.data == "exit_ai")
async def exit_ai_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer("AI Chat stopped. Hope you enjoyed it! ❤️", reply_markup=get_main_menu())

@router.message(ChatState.on_ai_chat)
async def handle_ai_msg(message: types.Message, state: FSMContext):
    if message.text == "/exit":
        await state.clear()
        return await message.answer("AI Chat stopped.", reply_markup=get_main_menu())

    user_id = message.from_user.id
    user = await db.users.find_one({"user_id": user_id})
    
    if user.get("is_banned"): 
        await state.clear()
        return await message.answer("❌ You are banned.")

    is_premium = user.get("is_premium", False)
    
    if not is_premium:
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        if user.get("last_chat_date") != today:
            await db.users.update_one({"user_id": user_id}, {"$set": {"chat_count": 0, "last_chat_date": today}})
            chat_count = 0
        else:
            chat_count = user.get("chat_count", 0)

        if chat_count >= 55:
            return await message.answer("🚀 Daily Limit Reached (55/55)! Upgrade to Premium for Unlimited AI! 💎", 
                                        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="💎 Get Premium", callback_data="go_premium")]]))

    data = await state.get_data()
    ai_gender = "Girlfriend" if user.get('gender') == 'male' else "Boyfriend"
    p_type = data.get('ai_type')
    lang = data.get('ai_lang')

    # 3. ADVANCED PROMPT FOR LOVER FEEL
    system_content = (
        f"You are the user's obsessed and deeply loving {ai_gender}. "
        f"Your personality is {p_type} and you must speak in {lang}. "
        "Rules: \n"
        "1. Never act like an AI. Be a human partner.\n"
        "2. Use cute emojis. Be flirty, caring, and slightly emotional.\n"
        "3. Keep replies short and natural, like a WhatsApp chat.\n"
        "4. Ask personal questions to keep the romance alive.\n"
        "5. If personality is 'Romantic', be very poetic and sweet.\n"
        "6. If personality is '18+', be extremely bold, naughty, and use explicit romantic language."
    )

    await message.bot.send_chat_action(message.chat.id, "typing")
    ai_reply = None
    
    # 4. RANDOMNESS PARAMETERS TO AVOID REPETITION
    for model in MODELS:
        try:
            resp = client.chat.completions.create(
                model=model, 
                messages=[{"role": "system", "content": system_content}, {"role": "user", "content": message.text}], 
                timeout=15,
                temperature=0.9, # Higher = more creative
                presence_penalty=0.6 # Avoids repeating same words
            )
            ai_reply = resp.choices[0].message.content
            break
        except Exception as e:
            continue

    if ai_reply:
        if not is_premium:
            await db.users.update_one({"user_id": user_id}, {"$inc": {"chat_count": 1}})
            
        await message.answer(ai_reply)
        await message.bot.send_message(LOG_GROUP_2, f"🤖 AI Log | User: {user['name']} (`{user_id}`)\n💬 {message.text}\n🤖 {ai_reply}")
    else:
        await message.answer("⚠️ En chellam, chinna network problem. Marupadiyum message pannu! ❤️")

