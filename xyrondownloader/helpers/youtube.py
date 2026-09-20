import re, random, os
from config import Config

def get_video_id(url):
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    return match.group(1) if match else None

def get_yt_analyze_options():
    opts = {
        'format': 'best',
        'geo_bypass': True,
        'nocheckcertificate': True,
        'quiet': True,
        'no_warnings': True,
        'source_address': '0.0.0.0',
    }
    
    if Config.USE_PROXY and Config.PROXIES:
        opts['proxy'] = random.choice(Config.PROXIES)
        
    if Config.USE_COOKIES and os.path.exists(Config.COOKIES_FILE_PATH):
        opts['cookiefile'] = Config.COOKIES_FILE_PATH
        
    return opts

def get_ytdl_options(format_str=None):
    opts = {
        'format': format_str if format_str else 'best',
        'outtmpl': f'{Config.DOWNLOAD_DIR}/%(title)s.%(ext)s',
        'geo_bypass': True,
        'nocheckcertificate': True,
        'quiet': True,
        'no_warnings': True,
        'source_address': '0.0.0.0',
        'external_downloader': 'aria2c',
        'external_downloader_args': [
            '-x', '16', '-s', '16', '-k', '1M',
            '--min-split-size=1M', '--max-connection-per-server=16'
        ],
    }
    
    if Config.USE_PROXY and Config.PROXIES:
        proxy = random.choice(Config.PROXIES)
        opts['proxy'] = proxy
        opts['external_downloader_args'].extend(['--all-proxy', proxy])
        
    if Config.USE_COOKIES and os.path.exists(Config.COOKIES_FILE_PATH):
        opts['cookiefile'] = Config.COOKIES_FILE_PATH

    if Config.MAX_FILE_SIZE:
        opts['max_filesize'] = Config.MAX_FILE_SIZE * 1024 * 1024

    return opts
