import openai
import logging
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from config import OPENROUTER_KEY, LOG_GROUP_2
from database import db
from utils.states import ChatState

router = Router()

# Updated Client with timeout to prevent hanging
client = openai.OpenAI(
    base_url="https://openrouter.ai/api/v1", 
    api_key=OPENROUTER_KEY,
    timeout=20.0 
)

@router.callback_query(F.data == "chat_ai")
async def ai_menu(callback: types.CallbackQuery, state: FSMContext):
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Tamil 🇮🇳", callback_data="ailang_Tamil"),
         types.InlineKeyboardButton(text="English 🇺🇸", callback_data="ailang_English")],
        [types.InlineKeyboardButton(text="Tanglish ✍️", callback_data="ailang_Tanglish")]
    ])
    await callback.message.edit_text("✨ Choose AI Language:", reply_markup=kb)

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
    await callback.message.edit_text(f"Language: {lang}\nNow choose AI Personality:", reply_markup=kb)

@router.callback_query(F.data.startswith("aitype_"))
async def start_ai_chat_session(callback: types.CallbackQuery, state: FSMContext):
    user = await db.users.find_one({"user_id": callback.from_user.id})
    if not user:
        return await callback.answer("⚠️ Please register first!", show_alert=True)

    p_type = callback.data.split("_")[1]
    if p_type == "18" and not user.get("is_premium"):
        return await callback.answer("❌ 18+ is Premium only!", show_alert=True)

    await state.update_data(ai_type=p_type)
    await state.set_state(ChatState.on_ai_chat)
    
    await callback.message.edit_text(
        f"✅ AI Chat Started ({p_type.upper()})\n\nSend a message to start. Use /exit to stop.",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🛑 Exit Chat", callback_data="exit_chat")]
        ])
    )

@router.message(ChatState.on_ai_chat, F.text)
async def handle_ai_msg(message: types.Message, state: FSMContext):
    if message.text.startswith('/'): return 
    
    data = await state.get_data()
    user = await db.users.find_one({"user_id": message.from_user.id})
    
    ai_role = "Girlfriend" if user.get('gender') == "male" else "Boyfriend"
    lang = data.get('ai_lang', 'Tamil')
    personality = data.get('ai_type', 'sweet')

    await message.bot.send_chat_action(message.chat.id, "typing")

    try:
        # Using a more stable free model name
        response = client.chat.completions.create(
            model="google/gemini-2.0-flash-lite-preview-02-05:free", 
            messages=[
                {"role": "system", "content": f"You are a human {ai_role}. Personality: {personality}. Language: {lang}. Be concise."},
                {"role": "user", "content": message.text}
            ],
            extra_headers={
                "HTTP-Referer": "https://koyeb.com",
                "X-Title": "CoupleDatingBot"
            }
        )
        ai_text = response.choices[0].message.content
        
        # Log Chat
        log_text = f"👤 {user.get('name')} ↔ 🤖 AI\nIn: {message.text}\nOut: {ai_text}"
        await message.bot.send_message(LOG_GROUP_2, log_text)
        
        await message.answer(ai_text)

    except Exception as e:
        logging.error(f"AI ERROR: {str(e)}")
        # Intha error message ippo unga bot-laye varum, so kandupudikalaam
        await message.answer(f"⚠️ AI is busy. Error: {str(e)[:50]}...")
