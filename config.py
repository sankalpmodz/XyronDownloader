import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    API_ID = int(os.getenv("API_ID", "0"))
    API_HASH = os.getenv("API_HASH", "")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")

    OWNER_ID = int(os.getenv("OWNER_ID", "0"))

    MONGO_DB_URI = os.getenv("MONGO_DB_URI", "")

    ENABLE_LOGGER = os.getenv("ENABLE_LOGGER", "True").lower() in ["true", "1", "yes"]
    LOG_GROUP_ID = int(os.getenv("LOG_GROUP_ID", "0")) 

    DAILY_DOWNLOAD_LIMIT = int(os.getenv("DAILY_DOWNLOAD_LIMIT", "0"))
    MAX_DURATION = int(os.getenv("MAX_DURATION", "0"))
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "2000"))

    FORCE_SUB_CHANNEL_ID = int(os.getenv("FORCE_SUB_CHANNEL_ID", "0")) 
    FORCE_SUB_CHANNEL_LINK = os.getenv("FORCE_SUB_CHANNEL_LINK", "")
    FORCE_SUB_GROUP_ID = int(os.getenv("FORCE_SUB_GROUP_ID", "0")) 
    FORCE_SUB_GROUP_LINK = os.getenv("FORCE_SUB_GROUP_LINK", "")

    USE_PROXY = os.getenv("USE_PROXY", "False").lower() in ["true", "1", "yes"]
    PROXIES = [p.strip() for p in os.getenv("PROXIES", "").split(",") if p.strip()]

    USE_COOKIES = os.getenv("USE_COOKIES", "True").lower() in ["true", "1", "yes"]
    COOKIES_FILE_PATH = os.getenv("COOKIES_FILE_PATH", "xyrondownloader/cookies/cookies.txt")
    INSTA_COOKIES_FILE = os.getenv("INSTA_COOKIES_FILE", "xyrondownloader/cookies/insta.txt")

    DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "downloads")