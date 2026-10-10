# ⚡ Xyron Downloader Bot (TypeTube Edition) ⚡

**Next-Generation Multi-Platform Downloader with Cookie-Free YouTube Integration**

This edition of Xyron Downloader uses **TypeTube** for YouTube, completely eliminating the need for YouTube cookies with a 99.99% hit rate and sub-second resolution.

---

## 🌟 Key Features in This Edition

- ⚡ **Cookie-Free YouTube Resolution:** Powered by [TypeTube API](https://typetube.xysushi.in) (`pip install typetube`). Direct high-speed signed playback streams without any `cookies.txt` requirement.
- 🚀 **Multi-Worker Range Chunk Downloads:** Uses parallel HTTP range requests (`Range: bytes=start-end`) to bypass YouTube CDN throttling and saturate high-speed VPS connections.
- 🎬 **Instant Lossless Muxing:** Muxes 1080p/720p H.264 video streams with AAC audio streams via `ffmpeg -c:v copy -c:a copy` in under 2 seconds.
- 🔍 **InnerTube Inline Search:** Inline search (`@YourBot <query>`) continues using high-speed YouTube **InnerTube** API for instantaneous results up to 50 items.
- 📸 **Instagram with yt-dlp & gallery-dl:** Instagram reels, posts, multi-item carousels, and stories are powered by yt-dlp and gallery-dl.
- 🎵 **TikTok & Pinterest Support:** Full support for TikTok no-watermark downloads and Pinterest media.

---

## 📁 Project Structure

```
typetube/
├── config.py                 # Configuration loader with TypeTube settings
├── sample.env                # Environment template
├── requirements.txt          # Dependencies (including typetube & yt-dlp)
├── start                     # Shell launcher
├── LICENSE                   # License
├── README.md                 # Documentation
└── xyrondownloader/
    ├── __init__.py           # Package setup & logging
    ├── __main__.py           # Bot entry point & scheduler
    ├── cookies/              # Cookie storage (insta.txt for Instagram)
    ├── helpers/              # Helper utilities
    │   ├── youtube.py        # Range downloader & FFmpeg muxer helpers
    │   ├── insta.py          # Instagram yt-dlp / gallery-dl options
    │   ├── tiktok.py         # TikTok options
    │   ├── pinterest.py      # Pinterest helpers
    │   ├── thumbnail.py      # Thumbnail fetcher
    │   └── utils.py          # Sanitizer for Telegram markdown
    ├── core/                 # Core download logic
    │   ├── youtube.py        # TypeTube YouTube resolution & downloader
    │   ├── search.py         # InnerTube search engine for inline mode
    │   ├── insta.py          # Instagram handler (yt-dlp + gallery-dl)
    │   ├── tiktok.py         # TikTok handler
    │   ├── pinterest.py      # Pinterest handler
    │   └── database.py       # MongoDB database driver
    └── plugins/              # Pyrogram command & callback handlers
        ├── router.py         # Message router & callback dispatcher
        ├── inline.py         # Inline search handler (InnerTube)
        ├── start.py          # /start command
        ├── forcesub.py       # Dual force subscribe middleware
        ├── broadcast.py      # Admin broadcast tool
        ├── ban_unban.py      # Ban/Unban management
        ├── banned.py         # Banned users list
        ├── stats.py          # User statistics
        └── ping.py           # Ping & system status
```

---

## 🚀 Setup & Installation (VPS)

### 1. Install Dependencies
```bash
cd typetube
pip install -r requirements.txt
pip install typetube
```

### 2. Configure `.env`
```bash
cp sample.env .env
nano .env
```
Fill in your `API_ID`, `API_HASH`, `BOT_TOKEN`, `OWNER_ID`, and `MONGO_DB_URI`.
No YouTube cookies are needed!

### 3. Run the Bot
```bash
python3 -m xyrondownloader
```
