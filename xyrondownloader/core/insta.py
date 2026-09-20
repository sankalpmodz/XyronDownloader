import os, glob, asyncio, subprocess, urllib.request, yt_dlp
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, InputMediaVideo
from config import Config
from xyrondownloader.helpers.insta import (
    run_gallery_dl,
    get_insta_extract_options,
    get_insta_download_options,
)
from xyrondownloader.helpers.utils import sanitize_title
from xyrondownloader import logger


def _video_caption(title, quality, platform="Instagram"):
    title = sanitize_title(title)
    return (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"  ✦ **@MysticDownloaderBot** ✦\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📹 **{title[:45]}**\n\n"
        f"📐 __Quality:__ **{quality}**\n"
        f"🌐 __Platform:__ **{platform}**"
    )


def _photo_caption():
    return (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"  ✦ **@MysticDownloaderBot** ✦\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📷 **Instagram Photo**"
    )


async def insta_logic(client, message, url, is_insta=True):
    chat_id = message.chat.id
    user_msg_id = message.id
    platform = "Instagram" if is_insta else "Pinterest"

    status_msg = await client.send_message(
        chat_id,
        f"⏳ __Processing your {platform} link...__",
        reply_to_message_id=user_msg_id,
    )

    if not is_insta:
        await _gallery_dl_flow(client, status_msg, url, chat_id, user_msg_id)
        return

    if "/p/" in url.lower():
        await _gallery_dl_flow(client, status_msg, url, chat_id, user_msg_id)
        return

    try:
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(get_insta_extract_options()) as ydl:
            info = await loop.run_in_executor(
                None, lambda: ydl.extract_info(url, download=False)
            )

        if info is None:
            raise Exception("No info returned")

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

        formats = info.get("formats", [])
        valid_formats = [
            f for f in formats
            if f.get("height")
            and f.get("vcodec")
            and f.get("vcodec") != "none"
        ]

        if not valid_formats:
            raise Exception("No video formats found")

        title = sanitize_title(info.get("title", "Instagram Video"))
        thumb = info.get("thumbnail")
        duration = info.get("duration_string", "")

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
            best_audio_size = int((128 * 1000 / 8) * duration_secs)

        valid_formats.sort(key=lambda x: x["height"], reverse=True)

        available = []
        buttons = []
        for f in valid_formats:
            h = f["height"]
            f_id = f["format_id"]
            if h not in available:
                if max_bytes:
                    f_size = est_filesize(f) + best_audio_size
                    if f_size > max_bytes:
                        continue
                available.append(h)
                buttons.append(
                    InlineKeyboardButton(
                        f"🎬 {h}p",
                        callback_data=f"dl|ig|{f_id}|{h}|{user_msg_id}",
                    )
                )
                if len(available) >= 4:
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
            if len(buttons) <= 2:
                rows.append(buttons)
            else:
                rows.append(buttons[:2])
                rows.append(buttons[2:])

        if audio_allowed:
            rows.append(
                [
                    InlineKeyboardButton(
                        "🎵 Audio Only",
                        callback_data=f"dl|ig|audio|mp3|{user_msg_id}",
                    )
                ]
            )

        await status_msg.delete()

        dur_text = f"\n⏳ __Duration:__ **{duration}**" if duration else ""
        caption = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"  ✦ **@MysticDownloaderBot** ✦\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📹 **{title[:42]}**\n"
            f"🌐 __Platform:__ **Instagram**{dur_text}\n\n"
            f"📐 **Select Quality:**"
        )

        try:
            await client.send_photo(
                chat_id,
                photo=thumb,
                caption=caption,
                reply_markup=InlineKeyboardMarkup(rows),
                reply_to_message_id=user_msg_id,
            )
        except Exception:
            await client.send_message(
                chat_id,
                text=caption,
                reply_markup=InlineKeyboardMarkup(rows),
                reply_to_message_id=user_msg_id,
            )
        return

    except Exception as e:
        logger.info(f"yt-dlp failed, falling back to gallery-dl: {e}")
        await _gallery_dl_flow(client, status_msg, url, chat_id, user_msg_id)


async def _gallery_dl_flow(client, status_msg, url, chat_id, user_msg_id):
    success, result = await run_gallery_dl(url, chat_id, user_msg_id)
    if not success:
        if "401" in str(result):
            return await status_msg.edit_text("❌ **Authentication Failed** • __Cookies expired__")
        return await status_msg.edit_text("❌ **Download Failed** • __Could not fetch media__")

    files_found = sorted(
        glob.glob(f"{Config.DOWNLOAD_DIR}/**/dl_{result}_*", recursive=True)
    )
    if not files_found:
        return await status_msg.edit_text("❌ **Downloaded but file not found**")

    await status_msg.edit_text(f"📤 __Uploading {len(files_found)} file(s)...__")

    photo_caption = _photo_caption()
    video_caption = _video_caption("Instagram Media", "Best", "Instagram")

    media_items = []
    for file_path in files_found:
        ext = os.path.splitext(file_path)[1].lower()
        if ext in [".mp4", ".webm", ".mov"]:
            media_items.append(("video", file_path, False))
        elif ext in [".jpg", ".jpeg", ".png"]:
            media_items.append(("photo", file_path, False))
        elif ext == ".webp":
            jpg_path = file_path.rsplit(".", 1)[0] + ".jpg"
            try:
                subprocess.run(
                    ["ffmpeg", "-i", file_path, "-y", jpg_path],
                    capture_output=True, timeout=30,
                )
                if os.path.exists(jpg_path):
                    media_items.append(("photo", jpg_path, True))
                else:
                    media_items.append(("document", file_path, False))
            except Exception:
                media_items.append(("document", file_path, False))

    if len(media_items) == 1:
        mtype, mpath, is_temp = media_items[0]
        try:
            if mtype == "photo":
                await client.send_photo(
                    chat_id, photo=mpath, caption=photo_caption,
                    reply_to_message_id=user_msg_id,
                )
            elif mtype == "video":
                await client.send_video(
                    chat_id, video=mpath, caption=video_caption,
                    reply_to_message_id=user_msg_id,
                )
            else:
                await client.send_document(
                    chat_id, document=mpath, caption=photo_caption,
                    reply_to_message_id=user_msg_id,
                )
        except Exception as e:
            logger.error(f"Upload Error: {e}")

    elif len(media_items) > 1:
        groupable = [(mt, mp, it) for mt, mp, it in media_items if mt != "document"]
        documents = [(mt, mp, it) for mt, mp, it in media_items if mt == "document"]

        for i in range(0, len(groupable), 10):
            chunk = groupable[i:i + 10]
            group = []
            for j, (mtype, mpath, _) in enumerate(chunk):
                cap = photo_caption if (i == 0 and j == 0) else None
                if mtype == "photo":
                    group.append(InputMediaPhoto(mpath, caption=cap))
                elif mtype == "video":
                    group.append(InputMediaVideo(mpath, caption=cap))

            if len(group) >= 2:
                try:
                    await client.send_media_group(
                        chat_id, group, reply_to_message_id=user_msg_id,
                    )
                except Exception as e:
                    logger.error(f"Media group error: {e}")
                    for mtype, mpath, _ in chunk:
                        try:
                            if mtype == "photo":
                                await client.send_photo(
                                    chat_id, photo=mpath, caption=photo_caption,
                                    reply_to_message_id=user_msg_id,
                                )
                            else:
                                await client.send_video(
                                    chat_id, video=mpath, caption=video_caption,
                                    reply_to_message_id=user_msg_id,
                                )
                        except Exception:
                            pass
            elif len(group) == 1:
                mtype, mpath, _ = chunk[0]
                try:
                    if mtype == "photo":
                        await client.send_photo(
                            chat_id, photo=mpath, caption=photo_caption,
                            reply_to_message_id=user_msg_id,
                        )
                    else:
                        await client.send_video(
                            chat_id, video=mpath, caption=video_caption,
                            reply_to_message_id=user_msg_id,
                        )
                except Exception:
                    pass
            await asyncio.sleep(0.5)

        for _, mpath, _ in documents:
            try:
                await client.send_document(
                    chat_id, document=mpath, caption=photo_caption,
                    reply_to_message_id=user_msg_id,
                )
            except Exception:
                pass

    for _, mpath, is_temp in media_items:
        if os.path.exists(mpath):
            try:
                os.remove(mpath)
            except Exception:
                pass
    for file_path in files_found:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

    await status_msg.delete()
    try:
        subprocess.run(
            f"find {Config.DOWNLOAD_DIR} -type d -empty -delete", shell=True
        )
    except Exception:
        pass


async def insta_download(client, callback_query):
    data = callback_query.data.split("|")
    format_id = data[2]
    quality_label = data[3]
    original_msg_id = int(data[4])
    chat_id = callback_query.message.chat.id
    quality_msg = callback_query.message

    original_msg = await client.get_messages(chat_id, original_msg_id)
    if not original_msg or not original_msg.text:
        return await callback_query.answer("❌ Link expired.", show_alert=True)
    url = original_msg.text.strip()

    is_audio = format_id == "audio"
    display_text = "Audio" if is_audio else f"{quality_label}p"

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
            f"📥 __Downloading__ • **{display_text}** • __Instagram__",
            reply_to_message_id=original_msg_id,
        )

        try:
            loop = asyncio.get_event_loop()

            if is_audio:
                opts = get_insta_download_options("bestaudio/best")
                opts['postprocessors'] = [
                    {
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'm4a',
                        'preferredquality': '0',
                    }
                ]
                if 'merge_output_format' in opts:
                    del opts['merge_output_format']
            else:
                fmt_str = f"{format_id}+bestaudio/best"
                opts = get_insta_download_options(fmt_str)

            with yt_dlp.YoutubeDL(opts) as ydl:
                info = await loop.run_in_executor(
                    None, lambda: ydl.extract_info(url, download=True)
                )
                file_path = ydl.prepare_filename(info)

                if is_audio:
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

            title = info.get("title", "Instagram")
            thumb_url = info.get("thumbnail")
            local_thumb = None

            if thumb_url:
                local_thumb = os.path.join(
                    Config.DOWNLOAD_DIR,
                    f"ig_thumb_{original_msg_id}.jpg",
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

            if is_audio:
                abr = info.get("abr") or info.get("tbr")
                if abr:
                    audio_quality = f"Best Audio ({int(abr)}kbps M4A)"
                else:
                    audio_quality = "Best Audio (M4A)"
                await client.send_audio(
                    chat_id,
                    audio=file_path,
                    title=title,
                    performer=info.get("uploader", "Unknown"),
                    thumb=local_thumb,
                    caption=_video_caption(title, audio_quality, "Instagram"),
                    reply_to_message_id=original_msg_id,
                )
            else:
                await client.send_video(
                    chat_id,
                    video=file_path,
                    caption=_video_caption(title, f"{quality_label}p", "Instagram"),
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
            logger.error(f"Instagram download failed: {e}")
            err_str = str(e).lower()
            if "larger than" in err_str or "max-filesize" in err_str or "max_filesize" in err_str:
                await status_msg.edit_text(
                    "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "    📦 **File Size Limit Exceeded**\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"❌ __Max allowed size is__ **{Config.MAX_FILE_SIZE} MB**"
                )
            else:
                await status_msg.edit_text("❌ **Download Failed** • __Try another link__")