import os, asyncio, yt_dlp, glob, urllib.request
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from xyrondownloader.helpers.tiktok import get_extract_options, get_download_options
from xyrondownloader.helpers.utils import sanitize_title
from xyrondownloader import logger


def _video_caption(title):
    title = sanitize_title(title)
    return (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"  ✦ **@MysticDownloaderBot** ✦\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📹 **{title[:45]}**\n\n"
        f"📐 __Quality:__ **Best**\n"
        f"🌐 __Platform:__ **TikTok**"
    )


async def tiktok_logic(client, message, url):
    chat_id, user_msg_id = message.chat.id, message.id
    status_msg = await client.send_message(
        chat_id,
        "⏳ __Analyzing TikTok link...__",
        reply_to_message_id=user_msg_id,
    )

    try:
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(get_extract_options()) as ydl:
            info = await loop.run_in_executor(
                None, lambda: ydl.extract_info(url, download=False)
            )

        title = info.get("title", "TikTok Video")
        thumb = info.get("thumbnail")

        is_live = info.get("is_live") or info.get("live_status") == "is_live"
        if is_live:
            return await status_msg.edit_text(
                "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "    🔴 **Live Video Detected**\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "❌ __Downloading live videos is not allowed in this bot__"
            )

        duration_secs = info.get("duration") or 0
        if Config.MAX_DURATION and duration_secs:
            max_secs = Config.MAX_DURATION * 60
            if duration_secs > max_secs:
                dur_str = info.get("duration_string", "Unknown")
                return await status_msg.edit_text(
                    "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "    ⏱️ **Duration Limit Exceeded**\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"❌ __Max allowed duration is__ **{Config.MAX_DURATION} min**\n"
                    f"📹 __This video is__ **{dur_str}**"
                )

        if Config.MAX_FILE_SIZE:
            max_bytes = Config.MAX_FILE_SIZE * 1024 * 1024
            formats = info.get("formats", [])

            def est_filesize(f):
                size = f.get("filesize") or f.get("filesize_approx")
                if size:
                    return size
                tbr = f.get("tbr") or (f.get("vbr", 0) + (f.get("abr", 0) or 128))
                if tbr and duration_secs:
                    return int((tbr * 1000 / 8) * duration_secs)
                return 0

            est_size = 0
            if formats:
                est_size = max((est_filesize(f) for f in formats), default=0)
            elif info.get("filesize") or info.get("filesize_approx"):
                est_size = info.get("filesize") or info.get("filesize_approx")

            if est_size and est_size > max_bytes:
                return await status_msg.edit_text(
                    "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "    📦 **File Size Limit Exceeded**\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"❌ __This video exceeds the maximum allowed file size of__ **{Config.MAX_FILE_SIZE} MB**"
                )

        buttons = [
            [
                InlineKeyboardButton(
                    "📥 Download Video",
                    callback_data=f"dl|tt|best|{user_msg_id}",
                )
            ]
        ]

        caption = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"  ✦ **@MysticDownloaderBot** ✦\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📹 **{title[:42]}**\n"
            f"🌐 __Platform:__ **TikTok**\n\n"
            f"__Tap below to download__"
        )

        await status_msg.delete()

        try:
            await client.send_photo(
                chat_id,
                photo=thumb,
                caption=caption,
                reply_markup=InlineKeyboardMarkup(buttons),
                reply_to_message_id=user_msg_id,
            )
        except Exception:
            await client.send_message(
                chat_id,
                text=caption,
                reply_markup=InlineKeyboardMarkup(buttons),
                reply_to_message_id=user_msg_id,
            )

    except Exception as e:
        logger.error(e)
        await status_msg.edit_text("❌ **TikTok analysis failed** • __Try again__")


async def tiktok_download(client, callback_query):
    data = callback_query.data.split("|")
    original_msg_id = int(data[3])
    chat_id = callback_query.message.chat.id
    quality_msg = callback_query.message

    original_msg = await client.get_messages(chat_id, original_msg_id)
    if not original_msg or not original_msg.text:
        return await callback_query.answer("❌ Link expired.", show_alert=True)
    url = original_msg.text.strip()

    wait_msg = (
        await client.send_message(
            chat_id,
            "⏳ __Waiting for download slot...__",
            reply_to_message_id=original_msg_id,
        )
        if client.download_semaphore.locked()
        else None
    )

    async with client.download_semaphore:
        if wait_msg:
            await wait_msg.delete()

        status_msg = await client.send_message(
            chat_id,
            "📥 __Downloading__ • **Best** • __TikTok__",
            reply_to_message_id=original_msg_id,
        )

        try:
            loop = asyncio.get_event_loop()
            opts = get_download_options()
            opts["format"] = "best"

            with yt_dlp.YoutubeDL(opts) as ydl:
                info = await loop.run_in_executor(
                    None, lambda: ydl.extract_info(url, download=True)
                )
                file_path = ydl.prepare_filename(info)

            base, _ = os.path.splitext(file_path)
            if opts.get("merge_output_format") == "mp4":
                file_path = (
                    base + ".mp4"
                    if os.path.exists(base + ".mp4")
                    else (
                        base + ".mkv"
                        if os.path.exists(base + ".mkv")
                        else file_path
                    )
                )
            if not os.path.exists(file_path) and glob.glob(f"{base}.*"):
                file_path = glob.glob(f"{base}.*")[0]

            title = info.get("title", "TikTok Video")
            thumb_url = info.get("thumbnail")
            local_thumb = None

            if thumb_url:
                local_thumb = os.path.join(
                    Config.DOWNLOAD_DIR, f"tt_thumb_{original_msg_id}.jpg"
                )
                try:
                    await loop.run_in_executor(
                        None,
                        lambda: urllib.request.urlretrieve(thumb_url, local_thumb),
                    )
                except Exception:
                    local_thumb = None

            await status_msg.edit_text("📤 __Uploading to Telegram...__")

            if Config.MAX_FILE_SIZE and os.path.exists(file_path):
                file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                if file_size_mb > Config.MAX_FILE_SIZE:
                    os.remove(file_path)
                    if local_thumb and os.path.exists(local_thumb):
                        os.remove(local_thumb)
                    return await status_msg.edit_text(
                        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        "    📦 **File Size Limit Exceeded**\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                        f"❌ __Max allowed size is__ **{Config.MAX_FILE_SIZE} MB**\n"
                        f"📁 __This file is__ **{int(file_size_mb)} MB**"
                    )

            await client.send_video(
                chat_id,
                video=file_path,
                caption=_video_caption(title),
                thumb=local_thumb,
                reply_to_message_id=original_msg_id,
            )

            await status_msg.delete()
            try:
                await quality_msg.delete()
            except Exception:
                pass

            for f in [file_path, local_thumb]:
                if f and os.path.exists(f):
                    try:
                        os.remove(f)
                    except Exception:
                        pass

        except Exception as e:
            logger.error(e)
            err_str = str(e).lower()
            if "larger than" in err_str or "max-filesize" in err_str or "max_filesize" in err_str:
                await status_msg.edit_text(
                    "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "    📦 **File Size Limit Exceeded**\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"❌ __Max allowed size is__ **{Config.MAX_FILE_SIZE} MB**"
                )
            else:
                await status_msg.edit_text("❌ **Download failed** • __Try again__")