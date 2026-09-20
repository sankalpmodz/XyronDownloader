from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from xyrondownloader.core.database import is_banned, add_user, check_and_increment_limit
from xyrondownloader.plugins.forcesub import check_subscription, send_log
from xyrondownloader.core.youtube import youtube_logic
from xyrondownloader.helpers.utils import sanitize_html


@Client.on_message(filters.command("start"))
async def start(client, message):
    if await is_banned(message.from_user.id):
        return await client.send_message(
            message.chat.id,
            "🚫 **You are banned from using this bot**",
        )

    if not await check_subscription(client, message):
        return

    if await add_user(message.from_user.id):
        await send_log(
            client,
            f"📝 <b>New User Log</b>\n\n"
            f"👤 <b>Name:</b> {sanitize_html(message.from_user.first_name)}\n"
            f"🆔 <b>ID:</b> <code>{message.from_user.id}</code>\n"
            f"🔗 <b>Username:</b> @{message.from_user.username or 'None'}",
        )

    parts = message.text.split()
    if len(parts) > 1 and parts[1].startswith("dl_"):
        vid_id = parts[1][3:]
        url = f"https://www.youtube.com/watch?v={vid_id}"
        user_id = message.from_user.id

        if not await check_and_increment_limit(user_id, Config.DAILY_DOWNLOAD_LIMIT):
            return await client.send_message(
                message.chat.id,
                "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "    ⚠️ **Daily Limit Reached!**\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "__You have exhausted your daily download limit.__\n"
                "__Please come back tomorrow!__ 🔄",
                reply_to_message_id=message.id,
            )

        await send_log(
            client,
            f"📥 <b>Download Log</b> (Inline)\n\n"
            f"👤 <b>User:</b> {sanitize_html(message.from_user.first_name)} (<code>{user_id}</code>)\n"
            f"🌐 <b>Platform:</b> YouTube\n"
            f"🔗 <b>Link:</b> {url}",
        )

        await youtube_logic(client, message, url)
        return

    name = message.from_user.first_name or "User"

    welcome_text = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"    ⚡ **Mystic X Downloader** ⚡\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"**Hey** {name}! 👋\n\n"
        f"__**Multi-Platform Media Downloader**__\n\n"
        f"**Supported Platforms:**\n"
        f"  ▸ **YouTube**\n"
        f"  ▸ **Instagram**\n"
        f"  ▸ **Pinterest**\n"
        f"  ▸ **TikTok**\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 **Just send a link to download!**\n"
        f"🔍 __Type__ `@{client.me.username} <name>` __to search YouTube__\n\n"
        f"✨ **@MysticDownloaderBot** ✨"
    )

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📢 Updates", url="https://t.me/XyronUpdates"),
                InlineKeyboardButton("💬 Support", url="https://t.me/+LFpYFn1t2utmYWM8"),
            ],
        ]
    )

    await client.send_message(
        chat_id=message.chat.id,
        text=welcome_text,
        reply_markup=buttons,
        reply_to_message_id=message.id,
    )