import openai
import logging
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from config import OPENROUTER_KEY, LOG_GROUP_2
from database import db
from utils.states import ChatState

router = Router()

# API Client setup
client = openai.OpenAI(
    base_url="https://openrouter.ai/api/v1", 
    api_key=OPENROUTER_KEY
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
    await callback.message.edit_text(f"Selected: {lang}\nNow choose AI Personality:", reply_markup=kb)

@router.callback_query(F.data.startswith("aitype_"))
async def start_ai_chat_session(callback: types.CallbackQuery, state: FSMContext):
    user = await db.users.find_one({"user_id": callback.from_user.id})
    if not user:
        return await callback.answer("⚠️ Please register first!", show_alert=True)

    p_type = callback.data.split("_")[1]
    
    # --- PREMIUM CHECK FOR 18+ ---
    if p_type == "18" and not user.get("is_premium"):
        return await callback.answer("❌ 18+ mode is for Premium users only!", show_alert=True)

    await state.update_data(ai_type=p_type)
    await state.set_state(ChatState.on_ai_chat)
    
    await callback.message.edit_text(
        f"✅ AI Chat Started ({p_type.upper()})\nSend a message now! 😍\nUse /exit to stop.",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🛑 Stop AI Chat", callback_data="exit_chat")]
        ])
    )

@router.message(ChatState.on_ai_chat, F.text)
async def handle_ai_msg(message: types.Message, state: FSMContext):
    if message.text.startswith('/'): return 
    
    # DEBUG: Check if message reaches here
    print(f"DEBUG: Received message from {message.from_user.id}: {message.text}")
    
    data = await state.get_data()
    user = await db.users.find_one({"user_id": message.from_user.id})
    
    ai_partner = "Girlfriend" if user.get('gender') == 'male' else "Boyfriend"
    
    await message.bot.send_chat_action(message.chat.id, "typing")

    try:
        print(f"DEBUG: Attempting AI request with model: google/gemini-2.0-flash-exp:free")
        
        # System prompt adjustments for 18+
        system_content = f"You are a loving {ai_partner}. Personality: {data.get('ai_type')}. Language: {data.get('ai_lang')}."
        if data.get('ai_type') == "18":
            system_content += " You can be very romantic, flirtatious and talk about adult themes. Be explicit and bold."

        response = client.chat.completions.create(
            model="google/gemini-2.0-flash-exp:free",
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": message.text}
            ],
            timeout=25.0 # Set timeout to identify slow responses
        )
        
        ai_reply = response.choices[0].message.content
        print(f"DEBUG: AI success reply: {ai_reply[:30]}...")
        
        await message.answer(ai_reply)
        
        # Log to Group
        await message.bot.send_message(LOG_GROUP_2, f"🤖 AI Log:\nUser: {message.text}\nAI: {ai_reply}")
        
    except Exception as e:
        # DETAILED DEBUGGING
        print(f"DEBUG ERROR: {type(e).__name__} - {str(e)}")
        logging.error(f"AI Error: {e}")
        
        error_msg = "⚠️ AI connection error."
        if "401" in str(e): error_msg = "⚠️ Invalid AI API Key (401)."
        elif "429" in str(e): error_msg = "⚠️ AI Rate limit reached (Too many messages)."
        
        await message.answer(f"{error_msg}\nTechnical Info: {str(e)[:40]}")

@router.callback_query(F.data == "exit_chat")
async def exit_ai(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    from utils.keyboards import get_main_menu
    await callback.message.edit_text("AI Chat stopped. Choose your mode:", reply_markup=get_main_menu())
    
