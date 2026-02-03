import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token
API_TOKEN = os.getenv("BOT_TOKEN")

# Database URL
MONGO_URL = os.getenv("MONGO_URL")

# AI API Key (OpenRouter)
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")

# IDs
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
LOG_GROUP_1 = int(os.getenv("LOG_GROUP_1", 0)) # Registration & Admin Logs
LOG_GROUP_2 = int(os.getenv("LOG_GROUP_2", 0)) # Chat Logs

# --- CASHFREE CONFIGURATION (New) ---
# Intha variables thaan missing-nu error vanthuchi
CASHFREE_APP_ID = os.getenv("CASHFREE_APP_ID")
CASHFREE_SECRET_KEY = os.getenv("CASHFREE_SECRET_KEY")
