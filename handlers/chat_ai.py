import openai
from aiogram import Router, F, types
from config import OPENROUTER_KEY, LOG_GROUP_2
from database import db

router = Router()
client = openai.OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_KEY)

@router.callback_query(F.data == "chat_ai")
async def ai_menu(callback: types.CallbackQuery):
    # Language Selection Keyboard
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Tamil", callback_data="ailang_Tamil"),
         types.InlineKeyboardButton(text="English", callback_data="ailang_English")],
        [types.InlineKeyboardButton(text="Tanglish", callback_data="ailang_Tanglish")]
    ])
    await callback.message.edit_text("Choose AI Language:", reply_markup=kb)

@router.callback_query(F.data.startswith("ailang_"))
async def ai_personality(callback: types.CallbackQuery):
    # Personality Selection
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Sweet 😊", callback_data="aitype_sweet"),
         types.InlineKeyboardButton(text="Romantic ❤️", callback_data="aitype_romantic")],
        [types.InlineKeyboardButton(text="18+ 🔥 (Premium)", callback_data="aitype_18")]
    ])
    await callback.message.edit_text("Choose AI Personality:", reply_markup=kb)

@router.message(F.text, ChatState.on_ai_chat)
async def handle_ai_msg(message: types.Message, state: FSMContext):
    user = await db.users.find_one({"user_id": message.from_user.id})
    
    # Gender Swap Logic for AI Roleplay
    ai_role = "Girlfriend" if user['gender'] == "male" else "Boyfriend"
    if user['gender'] == "transgender": ai_role = "Neutral Partner"

    # AI API Call
    response = client.chat.completions.create(
        model="google/gemini-2.0-flash-exp:free",
        messages=[
            {"role": "system", "content": f"You are a {ai_role}. Act {user['ai_type']} in {user['ai_lang']}."},
            {"role": "user", "content": message.text}
        ]
    )
    ai_text = response.choices[0].message.content
    
    # Log to Group 2
    log_text = f"👤 {user['name']} ↔ 🤖 AI\n{message.text}\nAI: {ai_text}"
    await message.bot.send_message(LOG_GROUP_2, log_text)
    
    await message.answer(ai_text)
