import openai
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from config import OPENROUTER_KEY, LOG_GROUP_2
from database import db
from utils.states import ChatState

router = Router()
client = openai.OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_KEY)

@router.callback_query(F.data == "chat_ai")
async def ai_menu(callback: types.CallbackQuery, state: FSMContext):
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Tamil 🇮🇳", callback_data="ailang_Tamil"),
         types.InlineKeyboardButton(text="English 🇺🇸", callback_data="ailang_English")]
    ])
    await callback.message.edit_text("✨ Choose AI Language:", reply_markup=kb)

@router.callback_query(F.data.startswith("ailang_"))
async def ai_personality(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(ai_lang=callback.data.split("_")[1])
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Sweet 😊", callback_data="aitype_sweet"),
         types.InlineKeyboardButton(text="Romantic ❤️", callback_data="aitype_romantic")],
        [types.InlineKeyboardButton(text="18+ 🔥 (Premium)", callback_data="aitype_18")]
    ])
    await callback.message.edit_text("Choose AI Personality:", reply_markup=kb)

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
    await callback.message.edit_text(f"✅ AI Chat Started ({p_type})\nSend a message to start!", 
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🛑 Exit", callback_data="exit_chat")]]))

@router.message(ChatState.on_ai_chat, F.text)
async def handle_ai_msg(message: types.Message, state: FSMContext):
    if message.text.startswith('/'): return
    data = await state.get_data()
    user = await db.users.find_one({"user_id": message.from_user.id})
    
    ai_role = "Girlfriend" if user['gender'] == "male" else "Boyfriend"
    try:
        response = client.chat.completions.create(
            model="google/gemini-2.0-flash-exp:free",
            messages=[{"role": "system", "content": f"You are a {ai_role}. Act {data.get('ai_type')} in {data.get('ai_lang')}"},
                      {"role": "user", "content": message.text}]
        )
        ai_text = response.choices[0].message.content
        await message.bot.send_message(LOG_GROUP_2, f"👤 {user['name']} ↔ 🤖 AI\n{message.text}\nAI: {ai_text}")
        await message.answer(ai_text)
    except:
        await message.answer("⚠️ AI connection lost.")
    
