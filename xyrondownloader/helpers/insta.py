import asyncio, os, random
from config import Config


class _SilentLogger:
    def debug(self, msg): pass
    def info(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass


async def run_gallery_dl(url, chat_id, msg_id):
    unique_id = f"{chat_id}_{msg_id}"
    cmd = [
        "gallery-dl",
        "--destination", Config.DOWNLOAD_DIR,
        "--filename", f"dl_{unique_id}_{{num}}.{{extension}}",
        "--no-mtime",
        url
    ]

    if os.path.exists(Config.INSTA_COOKIES_FILE):
        cmd.extend(["--cookies", Config.INSTA_COOKIES_FILE])

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        return False, stderr.decode()
    return True, unique_id


def get_insta_extract_options():
    opts = {
        'format': 'best',
        'geo_bypass': True,
        'nocheckcertificate': True,
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'extract_flat': False,
        'ignoreerrors': True,
        'source_address': '0.0.0.0',
        'logger': _SilentLogger(),
    }

    if Config.USE_PROXY and Config.PROXIES:
        opts['proxy'] = random.choice(Config.PROXIES)

    if Config.USE_COOKIES and os.path.exists(Config.INSTA_COOKIES_FILE):
        opts['cookiefile'] = Config.INSTA_COOKIES_FILE

    return opts


def get_insta_download_options(format_str=None):
    opts = {
        'format': format_str if format_str else 'bestvideo+bestaudio/best',
        'outtmpl': f'{Config.DOWNLOAD_DIR}/%(title)s_%(id)s.%(ext)s',
        'merge_output_format': 'mp4',
        'geo_bypass': True,
        'nocheckcertificate': True,
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'ignoreerrors': True,
        'source_address': '0.0.0.0',
        'logger': _SilentLogger(),
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
    }

    if Config.USE_PROXY and Config.PROXIES:
        proxy = random.choice(Config.PROXIES)
        opts['proxy'] = proxy

    if Config.USE_COOKIES and os.path.exists(Config.INSTA_COOKIES_FILE):
        opts['cookiefile'] = Config.INSTA_COOKIES_FILE

    if Config.MAX_FILE_SIZE:
        opts['max_filesize'] = Config.MAX_FILE_SIZE * 1024 * 1024

    return opts