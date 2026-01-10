import certifi
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI

# Bypass SSL Verification
client = AsyncIOMotorClient(
    MONGO_URI,
    tls=True,
    tlsAllowInvalidCertificates=True,
    tlsCAFile=certifi.where()
)

db = client["career_gps_bot"]
collection = db["user_history"]

async def get_history(user_id):
    """Fetch chat history"""
    try:
        doc = await collection.find_one({"user_id": user_id})
        if doc and "history" in doc:
            return doc["history"]
    except Exception as e:
        print(f"DB Read Error: {e}")
    return []

async def add_history(user_id, user_text, model_text):
    """Save message"""
    try:
        new_entries = [
            {"role": "user", "parts": [user_text]},
            {"role": "model", "parts": [model_text]}
        ]
        await collection.update_one(
            {"user_id": user_id},
            {"$push": {"history": {"$each": new_entries}}},
            upsert=True
        )
    except Exception as e:
        print(f"DB Write Error: {e}")

async def clear_history(user_id):
    """Clear history"""
    try:
        await collection.delete_one({"user_id": user_id})
    except:
        pass
