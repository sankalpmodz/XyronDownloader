from pyrogram import Client
from pyrogram.enums import ChatType
from pyrogram.types import (
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from xyrondownloader.core.search import youtube_search
from xyrondownloader.helpers.utils import sanitize_title
from xyrondownloader import logger


@Client.on_inline_query()
async def inline_youtube_search(client, inline_query):
    query = inline_query.query.strip()
    bot_username = client.me.username

    if not query:
        await inline_query.answer(
            results=[],
            switch_pm_text="🔍 Type a video name to search YouTube",
            switch_pm_parameter="search_help",
            cache_time=5,
        )
        return

    try:
        results = await youtube_search(query, max_results=50)

        if not results:
            await inline_query.answer(
                results=[],
                switch_pm_text="❌ No results found. Try different keywords.",
                switch_pm_parameter="search_help",
                cache_time=10,
            )
            return

        is_bot_dm = False
        try:
            ct = inline_query.chat_type
            if ct is not None:
                for attr in ("SENDER", "BOT"):
                    if hasattr(ChatType, attr) and ct == getattr(ChatType, attr):
                        is_bot_dm = True
                        break
                if not is_bot_dm:
                    raw = str(ct).lower()
                    if "sender" in raw or "bot" in raw:
                        is_bot_dm = True
        except Exception:
            pass

        articles = []
        for r in results:
            vid_id = r["id"]
            title = r["title"]
            channel = r["channel"][:30]
            duration = r["duration"]
            description = f"🎤 {channel}  •  ⏳ {duration}"
            url = r["url"]

            if is_bot_dm:
                articles.append(
                    InlineQueryResultArticle(
                        id=f"yt_{vid_id}",
                        title=title,
                        description=description,
                        thumb_url=r["thumb"],
                        input_message_content=InputTextMessageContent(
                            message_text=url,
                        ),
                    )
                )
            else:
                safe_title = sanitize_title(title)
                card_text = (
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"  ✦ **@{bot_username}** ✦\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"🎬 **{safe_title[:42]}**\n"
                    f"🎤 __{channel}__ • ⏳ __{duration}__\n\n"
                    f"📥 __Tap the button below to download__"
                )

                deep_link = f"https://t.me/{bot_username}?start=dl_{vid_id}"

                articles.append(
                    InlineQueryResultArticle(
                        id=f"yt_{vid_id}",
                        title=title,
                        description=description,
                        thumb_url=r["thumb"],
                        input_message_content=InputTextMessageContent(
                            message_text=card_text,
                        ),
                        reply_markup=InlineKeyboardMarkup(
                            [
                                [
                                    InlineKeyboardButton(
                                        "📥 Download in Bot PM",
                                        url=deep_link,
                                    )
                                ]
                            ]
                        ),
                    )
                )

        await inline_query.answer(
            results=articles,
            cache_time=300,
            is_personal=True,
        )

    except Exception as e:
        logger.error(f"Inline search error: {e}")
        await inline_query.answer(
            results=[],
            switch_pm_text="⚠️ Search failed. Try again.",
            switch_pm_parameter="search_help",
            cache_time=5,
        )
