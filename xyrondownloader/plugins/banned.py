import aiohttp
from pyrogram import Client, filters
from config import Config
from xyrondownloader.core.database import get_banned_users

async def post_to_pastebin(text):
    url = "https://batbin.me"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json={"content": text, "extension": "txt"}) as response:
                res = await response.json()
                if response.status == 201: return f"https://batbin.me/{res['payload']['id']}"
                else: return None
        except Exception: return None

@Client.on_message(filters.command("banned") & filters.user(Config.OWNER_ID))
async def banned_list_command(client, message):
    msg = await client.send_message(message.chat.id, "🔄 **Fetching banned users...**", reply_to_message_id=message.id)
    banned_ids = await get_banned_users()
    if not banned_ids: return await msg.edit_text("✅ **No users are currently banned.**")

    count = len(banned_ids)
    text_content = f"Total Banned Users: {count}\n\n"
    for uid in banned_ids: text_content += f"ID: {uid}\n"

    link = await post_to_pastebin(text_content)
    if link: await msg.edit_text(f"🚫 **Banned List**\n👥 Total: `{count}`\n📄 List: [Click Here]({link})", disable_web_page_preview=True)
    else: await msg.edit_text(f"🚫 Total: {count}\n(Pastebin Error)")