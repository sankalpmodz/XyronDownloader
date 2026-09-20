import os, random
from config import Config

def get_extract_options():
    opts = {'noplaylist': True, 'geo_bypass': True, 'nocheckcertificate': True, 'quiet': True, 'no_warnings': True, 'extract_flat': False, 'source_address': '0.0.0.0'}
    if Config.USE_COOKIES and os.path.exists(Config.COOKIES_FILE_PATH): opts['cookiefile'] = Config.COOKIES_FILE_PATH
    return opts

def get_download_options():
    opts = {
        'outtmpl': f'{Config.DOWNLOAD_DIR}/%(title)s.%(ext)s',
        'geo_bypass': True, 'nocheckcertificate': True, 'quiet': True, 'no_warnings': True, 'noplaylist': True,
        'source_address': '0.0.0.0',
        'external_downloader': 'aria2c',
        'external_downloader_args': ['-x', '16', '-s', '16', '-k', '1M', '--min-split-size=1M', '--max-connection-per-server=16']
    }
    if Config.USE_PROXY and Config.PROXIES:
        proxy = random.choice(Config.PROXIES)
        opts['proxy'] = proxy
        opts['external_downloader_args'].extend(['--all-proxy', proxy])
    if Config.USE_COOKIES and os.path.exists(Config.COOKIES_FILE_PATH): opts['cookiefile'] = Config.COOKIES_FILE_PATH
    if Config.MAX_FILE_SIZE: opts['max_filesize'] = Config.MAX_FILE_SIZE * 1024 * 1024
    return opts