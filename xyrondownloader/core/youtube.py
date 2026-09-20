import os, asyncio, urllib.request, yt_dlp
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from xyrondownloader.helpers.youtube import get_video_id, get_yt_analyze_options, get_ytdl_options
from xyrondownloader.helpers.utils import sanitize_title
from xyrondownloader import logger


def _video_caption(title, quality):
    title = sanitize_title(title)
    return (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"  ✦ **@MysticDownloaderBot** ✦\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📹 **{title[:45]}**\n\n"
        f"📐 __Quality:__ **{quality}**\n"
        f"🌐 __Platform:__ **YouTube**"
    )


def _audio_caption(title, quality="Best Audio (M4A)"):
    title = sanitize_title(title)
    return (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"  ✦ **@MysticDownloaderBot** ✦\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🎵 **{title[:45]}**\n\n"
        f"📐 __Quality:__ **{quality}**\n"
        f"🌐 __Platform:__ **YouTube**"
    )


async def youtube_logic(client, message, url):
    chat_id, user_msg_id = message.chat.id, message.id
    vid_id = get_video_id(url)
    if not vid_id:
        return await client.send_message(
            chat_id,
            "❌ **Invalid YouTube link**",
            reply_to_message_id=user_msg_id,
        )

    status_msg = await client.send_message(
        chat_id,
        "⏳ __Analyzing available qualities...__",
        reply_to_message_id=user_msg_id,
    )

    try:
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(get_yt_analyze_options()) as ydl:
            info = await loop.run_in_executor(
                None, lambda: ydl.extract_info(url, download=False)
            )

        title = sanitize_title(info.get("title", "Unknown"))
        thumb = info.get("thumbnail")
        duration = info.get("duration_string")
        duration_secs = info.get("duration") or 0
        formats = info.get("formats", [])
        is_live = info.get("is_live") or info.get("live_status") == "is_live"

        if is_live:
            return await status_msg.edit_text(
                "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "    🔴 **Live Video Detected**\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "❌ __Downloading live videos is not allowed in this bot__"
            )

        if Config.MAX_DURATION and duration_secs:
            max_secs = Config.MAX_DURATION * 60
            if duration_secs > max_secs:
                return await status_msg.edit_text(
                    "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "    ⏱️ **Duration Limit Exceeded**\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"❌ __Max allowed duration is__ **{Config.MAX_DURATION} min**\n"
                    f"📹 __This video is__ **{duration}**"
                )
        max_bytes = (Config.MAX_FILE_SIZE * 1024 * 1024) if Config.MAX_FILE_SIZE else 0

        def est_filesize(f):
            size = f.get("filesize") or f.get("filesize_approx")
            if size:
                return size
            tbr = f.get("tbr") or (f.get("vbr", 0) + (f.get("abr", 0) or 128))
            if tbr and duration_secs:
                return int((tbr * 1000 / 8) * duration_secs)
            return 0

        audio_formats = [
            f for f in formats if f.get("acodec") != "none" and f.get("vcodec") == "none"
        ]
        best_audio_size = 0
        if audio_formats:
            best_audio_size = max(est_filesize(f) for f in audio_formats)
        elif duration_secs:
            best_audio_size = int((256 * 1000 / 8) * duration_secs)

        valid_formats = [
            f
            for f in formats
            if f.get("height") and f.get("vcodec") != "none"
        ]
        valid_formats.sort(key=lambda x: x["height"], reverse=True)

        available_resolutions = []
        buttons = []
        for f in valid_formats:
            h = f["height"]
            f_id = f["format_id"]
            if h not in available_resolutions:
                if max_bytes:
                    f_size = est_filesize(f) + best_audio_size
                    if f_size > max_bytes:
                        continue
                available_resolutions.append(h)
                buttons.append(
                    InlineKeyboardButton(
                        f"🎬 {h}p",
                        callback_data=f"dl|yt|{vid_id}|{f_id}|{h}|{user_msg_id}",
                    )
                )
                if len(available_resolutions) >= 3:
                    break

        audio_allowed = True
        if max_bytes and best_audio_size > max_bytes:
            audio_allowed = False

        if max_bytes and not buttons and not audio_allowed:
            return await status_msg.edit_text(
                "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "    📦 **File Size Limit Exceeded**\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"❌ __This video exceeds the maximum allowed file size of__ **{Config.MAX_FILE_SIZE} MB**"
            )

        rows = []
        if buttons:
            if len(buttons) == 2:
                rows.append(buttons)
            else:
                rows.append(buttons[:2])
                if len(buttons) > 2:
                    rows.append(buttons[2:])

        if audio_allowed:
            rows.append(
                [
                    InlineKeyboardButton(
                        "🎵 Best Audio (M4A)",
                        callback_data=f"dl|yt|{vid_id}|audio|m4a|{user_msg_id}",
                    )
                ]
            )

        if not rows:
            return await status_msg.edit_text("❌ **No downloadable formats found** • __Try again__")

        await status_msg.delete()

        caption = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"  ✦ **@MysticDownloaderBot** ✦\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🎥 **{title[:42]}**\n"
            f"⏳ __Duration:__ **{duration}**\n"
            f"🌐 __Platform:__ **YouTube**\n\n"
            f"📐 **Select Quality:**"
        )

        await client.send_photo(
            chat_id,
            photo=thumb,
            caption=caption,
            reply_markup=InlineKeyboardMarkup(rows),
            reply_to_message_id=user_msg_id,
        )

    except Exception as e:
        logger.error(e)
        await status_msg.edit_text("❌ **YouTube analysis failed** • __Try again__")


async def youtube_download(client, callback_query):
    data = callback_query.data.split("|")
    vid_id, format_id, quality_label, original_msg_id = (
        data[2],
        data[3],
        data[4],
        int(data[5]),
    )
    chat_id = callback_query.message.chat.id
    quality_msg = callback_query.message
    url = f"https://www.youtube.com/watch?v={vid_id}"
    display_text = "Audio" if format_id == "audio" else f"{quality_label}p"

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
            f"📥 __Downloading__ • **{display_text}** • __YouTube__",
            reply_to_message_id=original_msg_id,
        )

        try:
            loop = asyncio.get_event_loop()

            if format_id == "audio":
                audio_fmt = "bestaudio[ext=m4a]/bestaudio[acodec^=mp4a]/bestaudio/best"
                opts = get_ytdl_options(audio_fmt)
                opts["postprocessors"] = [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "m4a",
                        "preferredquality": "0",
                    }
                ]
            else:
                fmt_str = f"{format_id}+bestaudio/best"
                opts = get_ytdl_options(fmt_str)
                opts["merge_output_format"] = "mp4"

            with yt_dlp.YoutubeDL(opts) as ydl:
                info = await loop.run_in_executor(
                    None, lambda: ydl.extract_info(url, download=True)
                )
                file_path = ydl.prepare_filename(info)

                if format_id == "audio":
                    base, _ = os.path.splitext(file_path)
                    file_path = base + ".m4a"
                elif opts.get("merge_output_format") == "mp4":
                    base, _ = os.path.splitext(file_path)
                    file_path = base + ".mp4"

                if not os.path.exists(file_path):
                    base, _ = os.path.splitext(file_path)
                    for ext in [".m4a", ".mp4", ".mkv", ".webm", ".opus", ".mp3"]:
                        if os.path.exists(base + ext):
                            file_path = base + ext
                            break

            title = info.get("title", "YouTube Video")
            thumb_url = info.get("thumbnail")
            local_thumb = None

            if thumb_url:
                local_thumb = os.path.join(
                    Config.DOWNLOAD_DIR, f"thumb_{vid_id}.jpg"
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

            if format_id == "audio":
                abr = info.get("abr") or info.get("tbr")
                if abr:
                    audio_quality = f"Best Audio ({int(abr)}kbps M4A)"
                else:
                    audio_quality = "Best Audio (M4A)"
                await client.send_audio(
                    chat_id,
                    audio=file_path,
                    title=title,
                    performer=info.get("uploader"),
                    thumb=local_thumb,
                    caption=_audio_caption(title, audio_quality),
                    reply_to_message_id=original_msg_id,
                )
            else:
                await client.send_video(
                    chat_id,
                    video=file_path,
                    caption=_video_caption(title, f"{quality_label}p"),
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
