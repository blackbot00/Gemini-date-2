import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from config import API_TOKEN, LOG_GROUP_1
from handlers import registration, human_chat, chat_ai, common
from utils import keyboards, states
from database import db

# Enable Logging
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN, parse_mode="Markdown")
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    user = await db.users.find_one({"user_id": message.from_user.id})
    
    if not user:
        # First time Log to Admin Group
        await bot.send_message(LOG_GROUP_1, f"🆕 New User Started: {message.from_user.full_name} (@{message.from_user.username})")
        
        # Trigger Registration Flow
        await state.set_state(states.Registration.state)
        await message.answer("Welcome! Let's register first.\n\nSelect your State:", 
                             reply_markup=keyboards.get_state_keyboard())
    else:
        # Already registered - Show Main Menu
        await message.answer(f"Welcome back, {user['name']}! ❤️\nWhat would you like to do today?", 
                             reply_markup=keyboards.get_main_menu())

@dp.callback_query(F.data == "exit_chat")
async def global_exit(callback: types.CallbackQuery, state: FSMContext):
    # Reset user status in DB
    await db.users.update_one({"user_id": callback.from_user.id}, {"$set": {"status": "idle"}})
    await state.clear()
    await callback.message.edit_text("Chat ended. Choose again:", reply_markup=keyboards.get_main_menu())

async def main():
    # Include all routers
    dp.include_router(registration.router)
    dp.include_router(human_chat.router)
    dp.include_router(chat_ai.router)
    dp.include_router(common.router)
    
    print("🚀 Bot is live on Koyeb!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
                                    
