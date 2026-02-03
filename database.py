import motor.motor_asyncio
from config import MONGO_URL

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client.dating_bot

async def add_user(user_id, data):
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": data},
        upsert=True
    )

async def is_premium(user_id):
    user = await db.users.find_one({"user_id": user_id})
    return user.get("is_premium", False) if user else False
  
