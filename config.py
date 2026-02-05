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
LOG_GROUP_1 = int(os.getenv("LOG_GROUP_1", 0)) 
LOG_GROUP_2 = int(os.getenv("LOG_GROUP_2", 0)) 

# --- PAYMENT CONFIG (New) ---
# Cashfree thevaiyillai, athunala remove pannidunga.
# Direct-ah UPI ID-ah inga set pannunga.
UPI_ID = os.getenv("UPI_ID", "yourname@okicici") # Koyeb-la UPI_ID nu variable set pannunga
