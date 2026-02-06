import asyncio
import logging
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
    await web.TCPSite(runner, "0.0.0.0", 8000).start()

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="Markdown"))
dp = Dispatcher()

# GLOBAL BAN CHECK
@dp.message(F.chat.type == "private")
async def check_ban_global(message: types.Message):
    user = await db.users.find_one({"user_id": message.from_user.id})
    if user and user.get("is_banned"):
        return # Blocked users don't get a response

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear() 
    user = await db.users.find_one({"user_id": message.from_user.id})
    if not user:
        # DB-la basic fields initialize pandrom
        await db.users.insert_one({
            "user_id": message.from_user.id,
            "name": message.from_user.full_name,
            "joined_date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "is_premium": False,
            "is_banned": False
        })
        await bot.send_message(LOG_GROUP_1, f"🆕 New User: {message.from_user.full_name}")
        await state.set_state(states.Registration.state)
        await message.answer("Welcome! Select your State:", reply_markup=keyboards.get_state_keyboard())
    else:
        await message.answer(f"Welcome back, {user['name']}! ❤️", reply_markup=keyboards.get_main_menu())

async def main():
    asyncio.create_task(start_health_server()) 
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
    
