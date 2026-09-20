from pyrogram import Client, filters
from pyrogram.enums import ChatType
from config import Config
from xyrondownloader.core.database import is_banned, add_user, add_chat, check_and_increment_limit
from xyrondownloader.plugins.forcesub import check_subscription, send_log
from xyrondownloader.core.youtube import youtube_logic, youtube_download
from xyrondownloader.core.tiktok import tiktok_logic, tiktok_download
from xyrondownloader.core.pinterest import pinterest_logic
from xyrondownloader.core.insta import insta_logic, insta_download
from xyrondownloader.helpers.utils import sanitize_html


@Client.on_message(filters.regex(r"http"))
async def router_handler(client, message):
    if message.chat.id == getattr(Config, "LOG_GROUP_ID", 0):
        return
    if not message.from_user or message.from_user.is_bot:
        return

    url_raw = message.text or message.caption
    if not url_raw:
        return
    url = url_raw.strip()
    url_lower = url.lower()
    user_id, chat_id = message.from_user.id, message.chat.id

    if await is_banned(user_id):
        return await client.send_message(
            chat_id,
            "🚫 **You are banned from using this bot**",
            reply_to_message_id=message.id,
        )

    if not await check_subscription(client, message):
        return

    if await add_user(user_id):
        await send_log(
            client,
            f"📝 <b>New User Log</b>\n\n"
            f"👤 <b>Name:</b> {sanitize_html(message.from_user.first_name)}\n"
            f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
            f"🔗 <b>Username:</b> @{message.from_user.username or 'None'}",
        )

    if message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP] and await add_chat(chat_id):
        await send_log(
            client,
            f"📝 <b>New Chat Log</b>\n\n"
            f"💬 <b>Group Name:</b> {sanitize_html(message.chat.title)}\n"
            f"🆔 <b>Chat ID:</b> <code>{chat_id}</code>",
        )

    platform = (
        "YouTube"
        if "youtube.com" in url_lower or "youtu.be" in url_lower
        else "Instagram"
        if "instagram.com" in url_lower
        or "ig.me" in url_lower
        or "instagr.am" in url_lower
        else "Pinterest"
        if "pinterest.com" in url_lower or "pin.it" in url_lower
        else "TikTok"
        if "tiktok.com" in url_lower or "vt.tiktok.com" in url_lower
        else None
    )

    if not platform:
        return

    if not await check_and_increment_limit(user_id, Config.DAILY_DOWNLOAD_LIMIT):
        return await client.send_message(
            chat_id,
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "    ⚠️ **Daily Limit Reached!**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "__You have exhausted your daily download limit.__\n"
            "__Please come back tomorrow!__ 🔄",
            reply_to_message_id=message.id,
        )

    await send_log(
        client,
        f"📥 <b>Download Log</b>\n\n"
        f"👤 <b>User:</b> {sanitize_html(message.from_user.first_name)} (<code>{user_id}</code>)\n"
        f"🌐 <b>Platform:</b> {platform}\n"
        f"🔗 <b>Link:</b> {url}",
    )

    if platform == "YouTube":
        await youtube_logic(client, message, url)
    elif platform == "Instagram":
        await insta_logic(client, message, url, is_insta=True)
    elif platform == "Pinterest":
        await pinterest_logic(client, message, url)
    elif platform == "TikTok":
        await tiktok_logic(client, message, url)


@Client.on_callback_query(filters.regex(r"^dl\|"))
async def download_handler(client, callback_query):
    data = callback_query.data.split("|")
    await callback_query.message.edit_reply_markup(None)

    if data[1] == "yt":
        await youtube_download(client, callback_query)
    elif data[1] == "tt":
        await tiktok_download(client, callback_query)
    elif data[1] == "ig":
        await insta_download(client, callback_query)