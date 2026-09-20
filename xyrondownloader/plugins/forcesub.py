import aiohttp
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from xyrondownloader.core.database import get_fsub_settings
from xyrondownloader import logger


async def send_log(client, text):
    if Config.ENABLE_LOGGER and getattr(Config, "LOG_GROUP_ID", 0) != 0:
        url = f"https://api.telegram.org/bot{Config.BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": Config.LOG_GROUP_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        async with aiohttp.ClientSession() as session:
            try:
                await session.post(url, json=payload)
            except Exception as e:
                logger.error(f"Failed to send log via API: {e}")


async def check_subscription(client, message):
    user_id = message.from_user.id
    if user_id == Config.OWNER_ID:
        return True

    fsub_data = await get_fsub_settings()
    checks = []
    if fsub_data.get("channel_id", 0) != 0:
        checks.append(
            (fsub_data["channel_id"], fsub_data["channel_link"], "Channel")
        )
    if fsub_data.get("group_id", 0) != 0:
        checks.append(
            (fsub_data["group_id"], fsub_data["group_link"], "Group")
        )
    if not checks:
        return True

    buttons, not_joined = [], False
    async with aiohttp.ClientSession() as session:
        for chat_id, chat_link, chat_type in checks:
            try:
                async with session.get(
                    f"https://api.telegram.org/bot{Config.BOT_TOKEN}/getChatMember",
                    params={"chat_id": chat_id, "user_id": user_id},
                ) as resp:
                    if resp.status == 200 and (await resp.json()).get(
                        "result", {}
                    ).get("status") in ["left", "kicked"]:
                        not_joined = True
                        buttons.append(
                            [
                                InlineKeyboardButton(
                                    f"{'📢' if chat_type == 'Channel' else '💬'} Join {chat_type}",
                                    url=chat_link,
                                )
                            ]
                        )
                    elif resp.status != 200:
                        not_joined = True
                        buttons.append(
                            [
                                InlineKeyboardButton(
                                    f"{'📢' if chat_type == 'Channel' else '💬'} Join {chat_type}",
                                    url=chat_link,
                                )
                            ]
                        )
            except Exception:
                pass

    if not_joined:
        buttons.append(
            [
                InlineKeyboardButton(
                    "✅ Try Again",
                    url=f"https://t.me/{client.me.username}?start=start",
                )
            ]
        )

        fsub_text = (
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "      🔒 **Access Restricted**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "__Join our channel & group to use this bot in private chat.__\n\n"
            "📌 **Join below and tap** __**Try Again**__ **to continue.**"
        )

        await client.send_message(
            message.chat.id,
            fsub_text,
            reply_markup=InlineKeyboardMarkup(buttons),
            reply_to_message_id=message.id,
        )
        return False

    return True