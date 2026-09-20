from pyrogram import Client, filters
from config import Config
from xyrondownloader.core.database import ban_user, unban_user

@Client.on_message(filters.command("ban") & filters.user(Config.OWNER_ID))
async def ban_command(client, message):
    try:
        user_id = int(message.command[1])
        await ban_user(user_id)
        await message.reply_text(f"🚫 User {user_id} banned.", quote=True)
    except: await message.reply_text("Invalid ID", quote=True)

@Client.on_message(filters.command("unban") & filters.user(Config.OWNER_ID))
async def unban_command(client, message):
    try:
        user_id = int(message.command[1])
        await unban_user(user_id)
        await message.reply_text(f"✅ User {user_id} unbanned.", quote=True)
    except: await message.reply_text("Invalid ID", quote=True)