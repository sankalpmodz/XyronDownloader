from pyrogram import Client, filters
from config import Config
from xyrondownloader.core.database import get_total_users_count

@Client.on_message(filters.command("stats") & filters.user(Config.OWNER_ID))
async def stats_command(client, message):
    msg = await client.send_message(message.chat.id, "🔄 **Counting users...**", reply_to_message_id=message.id)
    count = await get_total_users_count()
    await msg.edit_text(f"📊 **Total Users:** `{count}`")