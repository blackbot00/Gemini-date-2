import openai
import logging
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from config import OPENROUTER_KEY, LOG_GROUP_2
from database import db
from utils.states import ChatState
from utils.keyboards import get_main_menu

router = Router()

client = openai.OpenAI(
    base_url="https://openrouter.ai/api/v1", 
    api_key=OPENROUTER_KEY
)

# List of free models to try if one fails
MODELS = [
    "google/gemini-2.0-flash-lite-preview-02-05:free",
    "google/gemini-2.0-pro-exp-02-05:free",
    "mistralai/mistral-7b-instruct:free",
    "deepseek/deepseek-chat:free"
]

@router.callback_query(F.data == "chat_ai")
async def ai_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Tamil 🇮🇳", callback_data="ailang_Tamil"),
         types.InlineKeyboardButton(text="English 🇺🇸", callback_data="ailang_English")],
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
    if message.text and message.text.startswith('/'):
        if message.text in ["/exit", "/stop"]:
            await state.clear()
            return await message.answer("AI Chat stopped.", reply_markup=get_main_menu())
        return

    data = await state.get_data()
    user = await db.users.find_one({"user_id": message.from_user.id})
    ai_role = "Girlfriend" if user.get('gender') == 'male' else "Boyfriend"
    
    await message.bot.send_chat_action(message.chat.id, "typing")

    system_content = f"You are a human {ai_role}. Personality: {data.get('ai_type')}. Language: {data.get('ai_lang')}. Concise."
    if data.get('ai_type') == "18":
        system_content += " Act bold and use adult-themed romantic language."

    # --- LOOP THROUGH MODELS IF 404 OCCURS ---
    ai_reply = None
    for model_id in MODELS:
        try:
            print(f"DEBUG: Trying model {model_id}")
            response = client.chat.completions.create(
                model=model_id,
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": message.text}
                ],
                timeout=20
            )
            ai_reply = response.choices[0].message.content
            if ai_reply:
                break # Success! Exit loop
        except Exception as e:
            print(f"DEBUG: Model {model_id} failed with: {str(e)}")
            continue # Try next model

    if ai_reply:
        await message.answer(ai_reply)
        await message.bot.send_message(LOG_GROUP_2, f"🤖 AI Log:\nUser: {message.text}\nAI: {ai_reply}")
    else:
        await message.answer("⚠️ Ellaa AI models-um busy-aa iruku. OpenRouter Dashboard-la models active-aa irukannu check pannunga.")

@router.callback_query(F.data == "exit_ai")
async def exit_ai_btn(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("AI Chat stopped.", reply_markup=get_main_menu())
    
