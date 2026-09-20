import os
import time
import asyncio
from pyrogram import Client, idle
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import Config
from xyrondownloader import logger
from xyrondownloader.core.database import sync_fsub_with_config 

app = Client(
    "MysticDownloader",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    plugins=dict(root="xyrondownloader.plugins") 
)

app.download_semaphore = asyncio.Semaphore(5)

async def delete_old_files():
    now = time.time()
    for root, dirs, files in os.walk(Config.DOWNLOAD_DIR):
        for f in files:
            f_path = os.path.join(root, f)
            if os.stat(f_path).st_mtime < now - 86400:
                os.remove(f_path)

async def start_bot():
    if not os.path.exists(Config.DOWNLOAD_DIR):
        os.makedirs(Config.DOWNLOAD_DIR)
        
    await sync_fsub_with_config()
    logger.info("✅ Force Sub Data Synced with Config/Env")
        
    scheduler = AsyncIOScheduler()
    scheduler.add_job(delete_old_files, "interval", minutes=60)
    scheduler.start()
    logger.info("✅ Scheduler Started")
    
    await app.start()
    logger.info(f"✅ Bot Started as @{app.me.username}")
    
    await idle()
    await app.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop_policy().get_event_loop()
    loop.run_until_complete(start_bot())