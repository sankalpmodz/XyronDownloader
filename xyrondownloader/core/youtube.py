import os
import asyncio
import urllib.request
import urllib.parse
import json
from typing import Optional, List, Dict, Any
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import Config
from xyrondownloader import logger
from xyrondownloader.helpers.utils import sanitize_title
from xyrondownloader.helpers.youtube import (
    get_video_id,
    format_duration,
    download_stream_range,
    run_ffmpeg_merge,
    convert_to_m4a,
)

_tt_client = None


class _FallbackTypeTubeClient:
    def __init__(self, endpoint="https://typetube.xysushi.in", api_key=""):
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key or "public"

    async def resolve_async(self, query: str) -> Dict[str, Any]:
        url = f"{self.endpoint}/v1/resolve?q={urllib.parse.quote(query)}"
        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "X-API-Key": self.api_key,
                "User-Agent": "TypeTube-Xyron/1.0",
            },
        )
        loop = asyncio.get_event_loop()
        def _fetch():
            with urllib.request.urlopen(req, timeout=15.0) as resp:
                return json.loads(resp.read().decode("utf-8"))
        return await loop.run_in_executor(None, _fetch)


def get_typetube_client():
    global _tt_client
    if _tt_client is None:
        endpoint = getattr(Config, "TYPETUBE_ENDPOINT", "https://typetube.xysushi.in")
        api_key = getattr(Config, "TYPETUBE_API_KEY", "") or None
        try:
            from typetube import create_client
            _tt_client = create_client(endpoint=endpoint, api_key=api_key)
        except ImportError:
            _tt_client = _FallbackTypeTubeClient(endpoint=endpoint, api_key=api_key or "")
    return _tt_client


def _video_caption(title: str, quality: str) -> str:
    title = sanitize_title(title)
    return (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"  ✦ **@MysticDownloaderBot** ✦\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📹 **{title[:45]}**\n\n"
        f"📐 __Quality:__ **{quality}**\n"
        f"🌐 __Platform:__ **YouTube (TypeTube)**"
    )


def _audio_caption(title: str, quality: str = "Best Audio (M4A)") -> str:
    title = sanitize_title(title)
    return (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"  ✦ **@MysticDownloaderBot** ✦\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🎵 **{title[:45]}**\n\n"
        f"📐 __Quality:__ **{quality}**\n"
        f"🌐 __Platform:__ **YouTube (TypeTube)**"
    )


def _extract_clen(url: str) -> Optional[int]:
    try:
        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)
        if "clen" in params and params["clen"]:
            return int(params["clen"][0])
    except Exception:
        pass
    return None


async def _resolve_track(vid_id: str):
    client = get_typetube_client()
    if hasattr(client, "resolve_async"):
        data = await client.resolve_async(vid_id)
        if hasattr(data, "title"):
            return data
        return data
    else:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: client.resolve(vid_id))


async def youtube_logic(client, message, url: str):
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
        "⚡ __Resolving with TypeTube (Cookie-Free)...__",
        reply_to_message_id=user_msg_id,
    )

    try:
        track = await _resolve_track(vid_id)
        
        if isinstance(track, dict):
            if not track.get("success", False):
                raise Exception("TypeTube resolution failed")
            title = sanitize_title(track.get("title", "Unknown"))
            duration_secs = track.get("durationSeconds", 0)
            thumb = track.get("thumbnail") or f"https://i.ytimg.com/vi/{vid_id}/maxresdefault.jpg"
            video_streams = track.get("videoStreams", [])
            audio_streams = track.get("audioStreams", [])
            best_audio = track.get("bestAudio")
        else:
            if not track.success:
                raise Exception("TypeTube resolution failed")
            title = sanitize_title(track.title or "Unknown")
            duration_secs = track.duration_seconds or 0
            thumb = track.thumbnail or f"https://i.ytimg.com/vi/{vid_id}/maxresdefault.jpg"
            video_streams = [
                {
                    "itag": s.itag,
                    "quality": s.quality,
                    "resolution": s.resolution,
                    "mimeType": s.mime_type,
                    "url": s.url,
                    "clen": _extract_clen(s.url),
                }
                for s in track.video_streams
            ]
            audio_streams = [
                {
                    "itag": s.itag,
                    "quality": s.quality,
                    "bitrate": s.bitrate,
                    "mimeType": s.mime_type,
                    "url": s.url,
                    "clen": _extract_clen(s.url),
                }
                for s in track.audio_streams
            ]
            best_audio = {
                "itag": track.best_audio.itag,
                "url": track.best_audio.url,
                "mimeType": track.best_audio.mime_type,
                "bitrate": track.best_audio.bitrate,
            } if track.best_audio else (audio_streams[0] if audio_streams else None)

        duration_str = format_duration(duration_secs)

        if duration_secs == 0:
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
                    f"📹 __This video is__ **{duration_str}**"
                )

        max_bytes = (Config.MAX_FILE_SIZE * 1024 * 1024) if Config.MAX_FILE_SIZE else 0

        def _stream_sort(s):
            q_str = s.get("quality", "") or ""
            q_num = int("".join(filter(str.isdigit, q_str))) if any(c.isdigit() for c in q_str) else 0
            is_mp4 = 1 if "mp4" in s.get("mimeType", "").lower() else 0
            return (is_mp4, q_num)

        sorted_streams = sorted(video_streams, key=_stream_sort, reverse=True)

        available_resolutions = []
        buttons = []
        for s in sorted_streams:
            q_str = s.get("quality", "") or ""
            q_num = "".join(filter(str.isdigit, q_str))
            if not q_num:
                res = s.get("resolution", "")
                if res and "x" in res:
                    q_num = res.split("x")[-1]
            if not q_num:
                continue

            q_label = f"{q_num}p"
            if q_label in available_resolutions:
                continue

            s_clen = s.get("clen") or _extract_clen(s.get("url", ""))
            if max_bytes and s_clen and s_clen > max_bytes:
                continue

            available_resolutions.append(q_label)
            buttons.append(
                InlineKeyboardButton(
                    f"🎬 {q_label}",
                    callback_data=f"dl|yt|{vid_id}|{s.get('itag', 0)}|{q_num}|{user_msg_id}",
                )
            )
            if len(available_resolutions) >= 3:
                break

        audio_allowed = True
        if max_bytes and best_audio:
            a_clen = best_audio.get("clen") or _extract_clen(best_audio.get("url", ""))
            if a_clen and a_clen > max_bytes:
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
            rows.append([
                InlineKeyboardButton(
                    "🎵 Best Audio (M4A)",
                    callback_data=f"dl|yt|{vid_id}|audio|m4a|{user_msg_id}",
                )
            ])

        if not rows:
            return await status_msg.edit_text("❌ **No downloadable formats found** • __Try again__")

        await status_msg.delete()

        caption = (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"  ✦ **@MysticDownloaderBot** ✦\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🎥 **{title[:42]}**\n"
            f"⏳ __Duration:__ **{duration_str}**\n"
            f"⚡ __Engine:__ **TypeTube (Cookie-Free)**\n\n"
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
        logger.error(f"TypeTube logic error: {e}")
        await status_msg.edit_text("❌ **YouTube resolution failed** • __Try again__")


async def youtube_download(client, callback_query):
    data = callback_query.data.split("|")
    vid_id = data[2]
    format_id = data[3]
    quality_label = data[4]
    original_msg_id = int(data[5])

    chat_id = callback_query.message.chat.id
    quality_msg = callback_query.message
    display_text = "Audio" if format_id == "audio" else f"{quality_label}p"

    wait_msg = (
        await client.send_message(
            chat_id,
            "⏳ __Waiting for download slot...__",
            reply_to_message_id=original_msg_id,
        )
        if hasattr(client, "download_semaphore") and client.download_semaphore.locked()
        else None
    )

    semaphore = getattr(client, "download_semaphore", asyncio.Semaphore(5))

    async with semaphore:
        if wait_msg:
            try:
                await wait_msg.delete()
            except Exception:
                pass

        status_msg = await client.send_message(
            chat_id,
            f"📥 __Downloading__ • **{display_text}** • __TypeTube__",
            reply_to_message_id=original_msg_id,
        )

        temp_files = []
        try:
            loop = asyncio.get_event_loop()
            workers = getattr(Config, "TYPETUBE_WORKERS", 6)
            download_dir = getattr(Config, "DOWNLOAD_DIR", "downloads")
            os.makedirs(download_dir, exist_ok=True)

            track = await _resolve_track(vid_id)
            if isinstance(track, dict):
                title = sanitize_title(track.get("title", "YouTube Video"))
                author = track.get("author") or track.get("uploader") or "YouTube"
                duration_secs = track.get("durationSeconds", 0)
                thumb_url = track.get("thumbnail")
                video_streams = track.get("videoStreams", [])
                audio_streams = track.get("audioStreams", [])
                best_audio = track.get("bestAudio")
            else:
                title = sanitize_title(track.title or "YouTube Video")
                author = track.author or track.uploader or "YouTube"
                duration_secs = track.duration_seconds or 0
                thumb_url = track.thumbnail
                video_streams = [
                    {"itag": s.itag, "quality": s.quality, "url": s.url, "mimeType": s.mime_type}
                    for s in track.video_streams
                ]
                audio_streams = [
                    {"itag": s.itag, "quality": s.quality, "url": s.url, "mimeType": s.mime_type, "bitrate": s.bitrate}
                    for s in track.audio_streams
                ]
                best_audio = {
                    "itag": track.best_audio.itag,
                    "url": track.best_audio.url,
                    "mimeType": track.best_audio.mime_type,
                } if track.best_audio else None

            final_file_path = None

            if format_id == "audio":
                target_audio = next(
                    (s for s in audio_streams if s.get("itag") == 140 and s.get("url")),
                    None
                ) or best_audio or (audio_streams[0] if audio_streams else None)

                if not target_audio or not target_audio.get("url"):
                    raise Exception("No audio stream available")

                raw_audio_path = os.path.join(download_dir, f"audio_{vid_id}_{target_audio.get('itag')}.tmp")
                temp_files.append(raw_audio_path)

                await loop.run_in_executor(
                    None,
                    lambda: download_stream_range(
                        target_audio["url"],
                        raw_audio_path,
                        workers=workers,
                    ),
                )

                final_m4a = os.path.join(download_dir, f"{vid_id}.m4a")
                temp_files.append(final_m4a)

                if target_audio.get("itag") == 140 or "mp4" in target_audio.get("mimeType", "").lower():
                    if os.path.exists(raw_audio_path):
                        os.replace(raw_audio_path, final_m4a)
                    final_file_path = final_m4a
                else:
                    converted = await convert_to_m4a(raw_audio_path, final_m4a)
                    final_file_path = final_m4a if (converted and os.path.exists(final_m4a)) else raw_audio_path

            else:
                target_video = None
                if format_id.isdigit():
                    target_video = next((s for s in video_streams if s.get("itag") == int(format_id)), None)

                if not target_video:
                    target_video = next(
                        (s for s in video_streams if quality_label in s.get("quality", "")),
                        None
                    ) or (video_streams[0] if video_streams else None)

                if not target_video or not target_video.get("url"):
                    raise Exception("Target video stream not found")

                mux_audio = next(
                    (s for s in audio_streams if s.get("itag") == 140 and s.get("url")),
                    None
                ) or best_audio or (audio_streams[0] if audio_streams else None)

                raw_video_path = os.path.join(download_dir, f"vid_{vid_id}_{target_video.get('itag')}.mp4")
                temp_files.append(raw_video_path)

                await loop.run_in_executor(
                    None,
                    lambda: download_stream_range(
                        target_video["url"],
                        raw_video_path,
                        workers=workers,
                    ),
                )

                if mux_audio and mux_audio.get("url"):
                    raw_audio_path = os.path.join(download_dir, f"aud_{vid_id}_{mux_audio.get('itag')}.m4a")
                    temp_files.append(raw_audio_path)

                    await loop.run_in_executor(
                        None,
                        lambda: download_stream_range(
                            mux_audio["url"],
                            raw_audio_path,
                            workers=workers,
                        ),
                    )

                    merged_path = os.path.join(download_dir, f"{vid_id}_{quality_label}p.mp4")
                    temp_files.append(merged_path)

                    merge_ok = await run_ffmpeg_merge(raw_video_path, raw_audio_path, merged_path)
                    final_file_path = merged_path if (merge_ok and os.path.exists(merged_path)) else raw_video_path
                else:
                    final_file_path = raw_video_path

            local_thumb = os.path.join(download_dir, f"thumb_{vid_id}.jpg")
            if thumb_url:
                temp_files.append(local_thumb)
                try:
                    await loop.run_in_executor(
                        None,
                        lambda: urllib.request.urlretrieve(thumb_url, local_thumb),
                    )
                except Exception:
                    local_thumb = None
            else:
                local_thumb = None

            if Config.MAX_FILE_SIZE and final_file_path and os.path.exists(final_file_path):
                file_size_mb = os.path.getsize(final_file_path) / (1024 * 1024)
                if file_size_mb > Config.MAX_FILE_SIZE:
                    return await status_msg.edit_text(
                        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        "    📦 **File Size Limit Exceeded**\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                        f"❌ __Max allowed size is__ **{Config.MAX_FILE_SIZE} MB**\n"
                        f"📁 __This file is__ **{int(file_size_mb)} MB**"
                    )

            await status_msg.edit_text("📤 __Uploading to Telegram...__")

            if format_id == "audio":
                await client.send_audio(
                    chat_id,
                    audio=final_file_path,
                    title=title,
                    performer=author,
                    duration=duration_secs,
                    thumb=local_thumb if (local_thumb and os.path.exists(local_thumb)) else None,
                    caption=_audio_caption(title, "Best Audio (M4A)"),
                    reply_to_message_id=original_msg_id,
                )
            else:
                await client.send_video(
                    chat_id,
                    video=final_file_path,
                    duration=duration_secs,
                    caption=_video_caption(title, f"{quality_label}p"),
                    thumb=local_thumb if (local_thumb and os.path.exists(local_thumb)) else None,
                    reply_to_message_id=original_msg_id,
                )

            await status_msg.delete()
            try:
                await quality_msg.delete()
            except Exception:
                pass

        except Exception as e:
            logger.error(f"TypeTube download error: {e}")
            await status_msg.edit_text("❌ **Download failed** • __Try again__")
        finally:
            for f in temp_files:
                if f and os.path.exists(f):
                    try:
                        os.remove(f)
                    except Exception:
                        pass
