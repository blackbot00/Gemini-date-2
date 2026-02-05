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
# Koyeb-la ADMIN_ID variable correct-ah numeric-ah irukanum
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
LOG_GROUP_1 = int(os.getenv("LOG_GROUP_1", 0)) 
LOG_GROUP_2 = int(os.getenv("LOG_GROUP_2", 0)) 

# Payment Config
UPI_ID = os.getenv("UPI_ID", "yourname@okicici") # Koyeb-la UPI_ID-nu set pannunga
