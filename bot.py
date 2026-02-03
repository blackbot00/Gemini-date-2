import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from config import API_TOKEN, LOG_GROUP_1
from handlers import registration, human_chat, chat_ai, common
from database import db

bot = Bot(token=API_TOKEN, parse_mode="Markdown")
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    user = await db.users.find_one({"user_id": message.from_user.id})
    
    if not user:
        # First time Log
        await bot.send_message(LOG_GROUP_1, f"🆕 New User Started: {message.from_user.full_name}")
        await registration.start_reg(message, state) # Trigger Registration
    else:
        # Returning user menu
        await message.answer(f"Welcome back, {user['name']}! Choose your mode:", 
                             reply_markup=keyboards.get_main_menu())

async def main():
    dp.include_routers(registration.router, human_chat.router, chat_ai.router, common.router)
    print("Bot is running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
                       
