import openai
import logging
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from config import OPENROUTER_KEY, LOG_GROUP_2
from database import db
from utils.states import ChatState

router = Router()
client = openai.OpenAI(
    base_url="https://openrouter.ai/api/v1", 
    api_key=OPENROUTER_KEY
)

@router.message(ChatState.on_ai_chat, F.text)
async def handle_ai_msg(message: types.Message, state: FSMContext):
    if message.text.startswith('/'): return 
    
    data = await state.get_data()
    user = await db.users.find_one({"user_id": message.from_user.id})
    
    # User gender-ku yetha mathiri AI partner set panrom
    ai_partner = "Girlfriend" if user.get('gender') == 'male' else "Boyfriend"
    
    await message.bot.send_chat_action(message.chat.id, "typing")

    try:
        response = client.chat.completions.create(
            model="google/gemini-2.0-flash-exp:free",
            messages=[
                {"role": "system", "content": f"You are a loving {ai_partner}. Act {data.get('ai_type')} in {data.get('ai_lang')}. Keep it short and romantic."},
                {"role": "user", "content": message.text}
            ]
        )
        ai_reply = response.choices[0].message.content
        await message.answer(ai_reply)
        
        # Log to your group
        await message.bot.send_message(LOG_GROUP_2, f"🤖 AI Chat Log:\nUser: {message.text}\nAI: {ai_reply}")
        
    except Exception as e:
        logging.error(f"AI Error: {e}")
        await message.answer("⚠️ AI processing late-aaguthu. Oru 10 seconds kazhithu message pannunga.")
                
