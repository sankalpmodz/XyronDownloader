import re
import os
import time
import shutil
import asyncio
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Callable, Dict, Any
from config import Config
from xyrondownloader import logger

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def get_video_id(url: str) -> Optional[str]:
    match = re.search(
        r"(?:v=|\/|youtu\.be\/|shorts\/|embed\/|live\/)([0-9A-Za-z_-]{11})",
        url,
    )
    return match.group(1) if match else None


def format_duration(seconds: int) -> str:
    if not seconds:
        return "Unknown"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def download_stream_range(
    url: str,
    dest_path: str,
    workers: int = 6,
    chunk_size_mb: int = 5,
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> int:
    """
    Downloads a stream using multi-threaded HTTP Range requests.
    Bypasses YouTube bandwidth throttling and delivers maximum download speed.
    """
    parent = os.path.dirname(dest_path)
    if parent:
        os.makedirs(parent, exist_ok=True)

    req = urllib.request.Request(
        url,
        headers={
            "Range": "bytes=0-0",
            "User-Agent": USER_AGENT,
        },
    )
    total_bytes = 0
    try:
        with urllib.request.urlopen(req, timeout=12.0) as resp:
            cr = resp.headers.get("Content-Range", "")
            if "/" in cr:
                total_bytes = int(cr.split("/")[-1])
            elif resp.headers.get("Content-Length"):
                total_bytes = int(resp.headers.get("Content-Length", 0))
    except Exception as e:
        logger.debug(f"Range probe error: {e}")

    if total_bytes <= 0:
        return download_stream_linear(url, dest_path, progress_callback)

    chunk_size = max(128 * 1024, chunk_size_mb * 1024 * 1024)
    chunks = []
    for start in range(0, total_bytes, chunk_size):
        end = min(start + chunk_size - 1, total_bytes - 1)
        chunks.append((start, end))

    fd = os.open(dest_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
    downloaded = 0
    t0 = time.time()

    def fetch_chunk(start: int, end: int) -> int:
        nonlocal downloaded
        chunk_req = urllib.request.Request(
            url,
            headers={
                "Range": f"bytes={start}-{end}",
                "User-Agent": USER_AGENT,
            },
        )
        for attempt in range(3):
            try:
                with urllib.request.urlopen(chunk_req, timeout=20.0) as resp:
                    data = resp.read()
                    os.pwrite(fd, data, start)
                    downloaded += len(data)
                    if progress_callback:
                        elapsed = max(time.time() - t0, 0.01)
                        pct = round((downloaded / total_bytes) * 100, 1)
                        speed = round((downloaded / (1024 * 1024)) / elapsed, 2)
                        progress_callback({
                            "downloaded_bytes": downloaded,
                            "total_bytes": total_bytes,
                            "percent": pct,
                            "speed_mbps": speed,
                        })
                    return len(data)
            except Exception as e:
                if attempt == 2:
                    raise e
                time.sleep(0.5 * (attempt + 1))
        return 0

    try:
        max_pool_workers = min(workers, 16, len(chunks) or 1)
        with ThreadPoolExecutor(max_workers=max_pool_workers) as pool:
            futures = [pool.submit(fetch_chunk, start, end) for start, end in chunks]
            for f in as_completed(futures):
                f.result()
    finally:
        os.close(fd)

    return downloaded


def download_stream_linear(
    url: str,
    dest_path: str,
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> int:
    parent = os.path.dirname(dest_path)
    if parent:
        os.makedirs(parent, exist_ok=True)

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Range": "bytes=0-",
        },
    )

    downloaded = 0
    t0 = time.time()

    with urllib.request.urlopen(req, timeout=20.0) as resp, open(dest_path, "wb") as f:
        total_bytes = int(resp.headers.get("Content-Length", 0))
        while True:
            chunk = resp.read(128 * 1024)
            if not chunk:
                break
            f.write(chunk)
            downloaded += len(chunk)
            if progress_callback and total_bytes > 0:
                elapsed = max(time.time() - t0, 0.01)
                pct = round((downloaded / total_bytes) * 100, 1)
                speed = round((downloaded / (1024 * 1024)) / elapsed, 2)
                progress_callback({
                    "downloaded_bytes": downloaded,
                    "total_bytes": total_bytes,
                    "percent": pct,
                    "speed_mbps": speed,
                })

    return downloaded


async def run_ffmpeg_merge(video_path: str, audio_path: str, output_path: str) -> bool:
    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        logger.warning("FFmpeg not found; cannot mux video and audio")
        return False

    cmd = [
        ffmpeg_bin,
        "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "copy",
        "-movflags", "+faststart",
        output_path,
    ]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
        if proc.returncode == 0 and os.path.exists(output_path):
            return True
        cmd_fallback = [
            ffmpeg_bin,
            "-y",
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            output_path,
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd_fallback,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
        return proc.returncode == 0 and os.path.exists(output_path)
    except Exception as e:
        logger.error(f"FFmpeg merge error: {e}")
        return False


async def convert_to_m4a(input_path: str, output_path: str) -> bool:
    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        return False

    cmd = [
        ffmpeg_bin,
        "-y",
        "-i", input_path,
        "-c:a", "aac",
        "-b:a", "192k",
        "-vn",
        output_path,
    ]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
        return proc.returncode == 0 and os.path.exists(output_path)
    except Exception as e:
        logger.error(f"FFmpeg audio convert error: {e}")
        return False
