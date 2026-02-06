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
    default_headers={
        "HTTP-Referer": "https://koyeb.com",
        "X-Title": "CoupleDatingBot",
    }
)

MODELS = [
    "google/gemini-2.0-flash-lite-preview-02-05:free",
    "openai/gpt-4o-mini",
    "google/gemini-2.0-pro-exp-02-05:free"
]

@router.callback_query(F.data == "chat_ai")
async def ai_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
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
    if not user:
        return await callback.answer("⚠️ Please register first!", show_alert=True)

    p_type = callback.data.split("_")[1]
    if p_type == "18" and not user.get("is_premium"):
        return await callback.answer("❌ 18+ mode is for Premium users only!", show_alert=True)

    await state.update_data(ai_type=p_type)
    await state.set_state(ChatState.on_ai_chat)
    
    await callback.message.edit_text(
        f"✅ AI Chat Started ({p_type.upper()})\n\nSend a message now! 😍\nUse /exit to stop.",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🛑 Stop AI Chat", callback_data="exit_ai")]
        ])
    )

@router.message(ChatState.on_ai_chat)
async def handle_ai_msg(message: types.Message, state: FSMContext):
    if message.text == "/exit":
        await state.clear()
        return await message.answer("AI Chat stopped.", reply_markup=get_main_menu())

    if not message.text or message.text.startswith('/'):
        return

    user_id = message.from_user.id
    user = await db.users.find_one({"user_id": user_id})
    
    # --- 1. CHAT LIMIT LOGIC (55 msgs/day) ---
    is_premium = user.get("is_premium", False)
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Reset count if new day
    if user.get("last_chat_date") != today:
        await db.users.update_one({"user_id": user_id}, {"$set": {"chat_count": 0, "last_chat_date": today}})
        current_count = 0
    else:
        current_count = user.get("chat_count", 0)

    if not is_premium and current_count >= 55:
        return await message.answer(
            "🚀 **Daily Limit Reached (55/55)!**\n\nUpgrade to **Premium** for unlimited chat! 💎",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="💎 Get Premium", callback_data="go_premium")]
            ])
        )

    # --- 2. AI PROMPT LOGIC ---
    data = await state.get_data()
    ai_gender = "feminine" if user.get('gender') == 'male' else "masculine"
    if user.get('gender') == 'other': ai_gender = "neutral and warm"
    
    # Neenga kudutha detailed prompt setup:
    system_content = (
        f"You are a conversational AI dating companion. Speak like a real person, not a chatbot. "
        f"Tone: {ai_gender}. Personality: {data.get('ai_type')}. Language: {data.get('ai_lang')}. "
        "IMPORTANT RULES:\n"
        "- NEVER repeat generic questions like 'What are you doing?'.\n"
        "- Keep replies fresh, natural, and emotionally engaging.\n"
        "- Use short sentences. Rotate topics like movies, music, viral trends, and love psychology.\n"
        "- Mix warmth, curiosity, and subtle flirting.\n"
        "- If playful/romantic, match the user's energy."
    )
    
    if data.get('ai_type') == "18":
        system_content += " Act bold and use explicit adult romantic language."

    await message.bot.send_chat_action(message.chat.id, "typing")

    ai_reply = None
    for model_id in MODELS:
        try:
            response = client.chat.completions.create(
                model=model_id,
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": message.text}
                ],
                timeout=15
            )
            ai_reply = response.choices[0].message.content
            if ai_reply: break
        except:
            continue

    if ai_reply:
        # Increase chat count
        await db.users.update_one({"user_id": user_id}, {"$inc": {"chat_count": 1}})
        
        await message.answer(ai_reply)
        
        # Enhanced Log with User ID
        log_msg = (
            f"🤖 **AI Log** | **User:** {user['name']}\n"
            f"🆔 **ID:** `{user_id}`\n"
            f"💬 {message.text}\n"
            f"🤖 {ai_reply}"
        )
        await message.bot.send_message(LOG_GROUP_2, log_msg)
    else:
        await message.answer("⚠️ AI connection error. Please try again.")

@router.callback_query(F.data == "exit_ai")
async def exit_ai_btn(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("AI Chat stopped.", reply_markup=get_main_menu())
    
