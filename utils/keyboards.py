from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import types

def get_state_keyboard():
    builder = InlineKeyboardBuilder()
    states = [
        "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", 
        "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", 
        "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", 
        "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", 
        "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", 
        "Uttarakhand", "West Bengal"
    ]
    for state in states:
        builder.add(types.InlineKeyboardButton(text=state, callback_data=f"regstate_{state}"))
    builder.adjust(3)
    return builder.as_markup()

def get_main_menu():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="👫 Chat with Human", callback_data="chat_human"))
    builder.row(types.InlineKeyboardButton(text="🤖 Chat with AI", callback_data="chat_ai"))
    builder.row(
        types.InlineKeyboardButton(text="👤 Profile", callback_data="view_profile"),
        types.InlineKeyboardButton(text="💎 Premium", callback_data="go_premium")
    )
    return builder.as_markup()
