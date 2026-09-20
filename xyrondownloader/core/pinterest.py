import os, glob, asyncio, subprocess
from config import Config
from xyrondownloader.helpers.pinterest import run_gallery_dl
from xyrondownloader import logger


def _media_caption(is_video=False):
    media_type = "📹 **Video**" if is_video else "📷 **Photo**"
    return (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"  ✦ **@MysticDownloaderBot** ✦\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{media_type}\n"
        f"🌐 __Platform:__ **Pinterest**"
    )


async def pinterest_logic(client, message, url):
    chat_id, user_msg_id = message.chat.id, message.id
    status_msg = await client.send_message(
        chat_id,
        "⏳ __Processing your Pinterest link...__",
        reply_to_message_id=user_msg_id,
    )

    success, result = await run_gallery_dl(url, chat_id, user_msg_id)
    if not success:
        return await status_msg.edit_text(
            "❌ **Download Failed** • __Could not fetch media__"
        )

    files_found = sorted(
        glob.glob(f"{Config.DOWNLOAD_DIR}/**/dl_{result}_*", recursive=True)
    )
    if not files_found:
        return await status_msg.edit_text(
            "❌ **Downloaded but file not found**"
        )

    await status_msg.edit_text(
        f"📤 __Uploading {len(files_found)} file(s)...__"
    )

    for file_path in files_found:
        try:
            if Config.MAX_FILE_SIZE and os.path.exists(file_path):
                file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                if file_size_mb > Config.MAX_FILE_SIZE:
                    os.remove(file_path)
                    await client.send_message(
                        chat_id,
                        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        "    📦 **File Size Limit Exceeded**\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                        f"❌ __Max allowed size is__ **{Config.MAX_FILE_SIZE} MB**\n"
                        f"📁 __This file is__ **{int(file_size_mb)} MB**",
                        reply_to_message_id=user_msg_id,
                    )
                    continue

            ext = os.path.splitext(file_path)[1].lower()
            if ext in [".mp4", ".webm", ".mov"]:
                await client.send_video(
                    chat_id,
                    video=file_path,
                    caption=_media_caption(is_video=True),
                    reply_to_message_id=user_msg_id,
                )
            elif ext in [".jpg", ".jpeg", ".png"]:
                await client.send_photo(
                    chat_id,
                    photo=file_path,
                    caption=_media_caption(is_video=False),
                    reply_to_message_id=user_msg_id,
                )
            elif ext == ".webp":
                jpg_path = file_path.rsplit(".", 1)[0] + ".jpg"
                try:
                    subprocess.run(
                        ["ffmpeg", "-i", file_path, "-y", jpg_path],
                        capture_output=True, timeout=30,
                    )
                    if os.path.exists(jpg_path):
                        await client.send_photo(
                            chat_id,
                            photo=jpg_path,
                            caption=_media_caption(is_video=False),
                            reply_to_message_id=user_msg_id,
                        )
                        os.remove(jpg_path)
                    else:
                        raise Exception("Conversion failed")
                except Exception:
                    await client.send_document(
                        chat_id,
                        document=file_path,
                        caption=_media_caption(is_video=False),
                        reply_to_message_id=user_msg_id,
                    )
            if os.path.exists(file_path):
                os.remove(file_path)
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.error(f"Upload Error: {e}")

    await status_msg.delete()
    try:
        subprocess.run(
            f"find {Config.DOWNLOAD_DIR} -type d -empty -delete", shell=True
        )
    except Exception:
        pass