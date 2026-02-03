import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.client.default import DefaultBotProperties
from aiohttp import web
from config import API_TOKEN, LOG_GROUP_1
from handlers import registration, human_chat, chat_ai, common
from utils import keyboards, states
from database import db

logging.basicConfig(level=logging.INFO)

# --- KOYEB HEALTH CHECK ---
async def handle_health(request):
    return web.Response(text="Bot is live!")

async def start_health_server():
    app = web.Application()
    app.router.add_get("/", handle_health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8000)
    await site.start()

# --- BOT SETUP ---
bot = Bot(
    token=API_TOKEN, 
    default=DefaultBotProperties(parse_mode="Markdown")
)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    user = await db.users.find_one({"user_id": message.from_user.id})
    if not user:
        await bot.send_message(LOG_GROUP_1, f"🆕 New User Started: {message.from_user.full_name}")
        await state.set_state(states.Registration.state)
        await message.answer("Welcome! Let's register first.\n\nSelect your State:", 
                             reply_markup=keyboards.get_state_keyboard())
    else:
        await message.answer(f"Welcome back, {user['name']}! ❤️", reply_markup=keyboards.get_main_menu())

@dp.callback_query(F.data == "exit_chat")
async def global_exit(callback: types.CallbackQuery, state: FSMContext):
    await db.users.update_one({"user_id": callback.from_user.id}, {"$set": {"status": "idle"}})
    await state.clear()
    await callback.message.edit_text("Chat ended. Choose again:", reply_markup=keyboards.get_main_menu())

async def main():
    asyncio.create_task(start_health_server()) # Starts the 8000 port server
    dp.include_routers(registration.router, human_chat.router, chat_ai.router, common.router)
    print("🚀 Bot is live on Koyeb!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
