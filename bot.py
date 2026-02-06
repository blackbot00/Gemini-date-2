import asyncio
import logging
import datetime  # MUKKIYAM!
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.client.default import DefaultBotProperties
from aiohttp import web
from config import API_TOKEN, LOG_GROUP_1
from handlers import registration, human_chat, chat_ai, common, profile, premium, admin
from utils import keyboards, states
from database import db

logging.basicConfig(level=logging.INFO)

async def handle_health(request): return web.Response(text="Bot is live!")

async def start_health_server():
    app = web.Application()
    app.router.add_get("/", handle_health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8000)
    await site.start()

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="Markdown"))
dp = Dispatcher()

# --- FIXED GLOBAL CHECK ---
@dp.message(F.chat.type == "private")
async def check_user_status(message: types.Message, state: FSMContext):
    user = await db.users.find_one({"user_id": message.from_user.id})
    
    # Ban Check
    if user and user.get("is_banned"):
        return 

    # Continue to next handler
    await dp.propagate_event(message)

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear() 
    user_id = message.from_user.id
    user = await db.users.find_one({"user_id": user_id})
    
    if not user:
        new_user = {
            "user_id": user_id,
            "name": message.from_user.full_name,
            "username": message.from_user.username,
            "joined_date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "is_premium": False,
            "is_banned": False,
            "chat_count": 0
        }
        await db.users.insert_one(new_user)
        await bot.send_message(LOG_GROUP_1, f"🆕 New User: {message.from_user.full_name}")
        await state.set_state(states.Registration.state)
        await message.answer("Welcome! Select your State:", reply_markup=keyboards.get_state_keyboard())
    else:
        await message.answer(f"Welcome back, {user['name']}! ❤️", reply_markup=keyboards.get_main_menu())

async def main():
    asyncio.create_task(start_health_server()) 
    
    # Order matters
    dp.include_router(admin.router)
    dp.include_router(premium.router)
    dp.include_router(registration.router)
    dp.include_router(chat_ai.router)
    dp.include_router(profile.router)
    dp.include_router(human_chat.router)
    dp.include_router(common.router) 
    
    print("🚀 Bot is live on Koyeb!")
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
    
