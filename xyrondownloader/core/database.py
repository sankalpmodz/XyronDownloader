from motor.motor_asyncio import AsyncIOMotorClient
from config import Config
from datetime import datetime

cli = AsyncIOMotorClient(Config.MONGO_DB_URI)
db = cli.BotDatabase

users_collection = db.users
banned_collection = db.banned_users
settings_collection = db.settings
chats_collection = db.chats 

async def add_user(user_id: int):
    user = await users_collection.find_one({"_id": user_id})
    if not user:
        await users_collection.insert_one({
            "_id": user_id,
            "daily_downloads": 0,
            "last_download_date": datetime.now().strftime("%Y-%m-%d")
        })
        return True 
    return False

async def get_all_users():
    return users_collection.find({})

async def add_chat(chat_id: int):
    chat = await chats_collection.find_one({"_id": chat_id})
    if not chat:
        await chats_collection.insert_one({"_id": chat_id})
        return True 
    return False

async def check_and_increment_limit(user_id: int, limit: int):
    if limit == 0:
        return True

    today = datetime.now().strftime("%Y-%m-%d")
    user = await users_collection.find_one({"_id": user_id})

    current_downloads = user.get("daily_downloads", 0) if user else 0
    last_date = user.get("last_download_date", "") if user else ""

    if last_date != today:
        current_downloads = 0
        last_date = today

    if current_downloads >= limit:
        return False

    await users_collection.update_one(
        {"_id": user_id},
        {"$set": {"daily_downloads": current_downloads + 1, "last_download_date": last_date}},
        upsert=True
    )
    return True

async def ban_user(user_id: int):
    is_banned = await banned_collection.find_one({"_id": user_id})
    if not is_banned:
        await banned_collection.insert_one({"_id": user_id})

async def unban_user(user_id: int):
    await banned_collection.delete_one({"_id": user_id})

async def is_banned(user_id: int):
    user = await banned_collection.find_one({"_id": user_id})
    return True if user else False
    
async def get_banned_users():
    banned_list = []
    async for user in banned_collection.find({}):
        banned_list.append(user["_id"])
    return banned_list

async def get_total_users_count():
    return await users_collection.count_documents({})

async def get_fsub_settings():
    settings = await settings_collection.find_one({"_id": "fsub_data"})
    if not settings:
        return {"channel_id": 0, "channel_link": "", "group_id": 0, "group_link": ""}
    return settings

async def sync_fsub_with_config():
    db_settings = await get_fsub_settings()
    c_id = Config.FORCE_SUB_CHANNEL_ID
    c_link = Config.FORCE_SUB_CHANNEL_LINK
    g_id = Config.FORCE_SUB_GROUP_ID
    g_link = Config.FORCE_SUB_GROUP_LINK
    
    new_c_id = 0 if c_id == 0 else c_id
    new_g_id = 0 if g_id == 0 else g_id
    
    await settings_collection.update_one(
        {"_id": "fsub_data"},
        {"$set": {
            "channel_id": new_c_id,
            "channel_link": c_link,
            "group_id": new_g_id,
            "group_link": g_link
        }},
        upsert=True
    )

async def get_all_chats():
    return chats_collection.find({})
