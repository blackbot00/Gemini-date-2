from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

def get_state_keyboard():
    builder = InlineKeyboardBuilder()
    states = ["Tamil Nadu", "Kerala", "Karnataka", "Mumbai", "Delhi", "Others"] # Add more
    for s in states:
        builder.add(InlineKeyboardButton(text=s, callback_data=f"reg_state_{s}"))
    builder.adjust(3)
    return builder.as_markup()

def get_main_menu():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="👤 Human Chat", callback_data="chat_human"),
                InlineKeyboardButton(text="🤖 AI Chat", callback_data="chat_ai"))
    builder.row(InlineKeyboardButton(text="💎 Get Premium", callback_data="go_premium"))
    return builder.as_markup()

def get_ai_lang_kb():
    builder = InlineKeyboardBuilder()
    langs = ["Tamil", "English", "Hindi", "Telugu", "Tanglish"]
    for l in langs:
        builder.add(InlineKeyboardButton(text=l, callback_data=f"ai_lang_{l}"))
    builder.adjust(2)
    return builder.as_markup()
