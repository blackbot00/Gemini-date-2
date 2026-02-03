import os
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URL = os.getenv("MONGO_URL")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
LOG_GROUP_1 = int(os.getenv("LOG_GROUP_1")) # Registration & Admin Logs
LOG_GROUP_2 = int(os.getenv("LOG_GROUP_2")) # Chat Logs

