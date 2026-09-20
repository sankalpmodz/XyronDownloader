<div align="center">

# ⚡ Xyron Downloader Bot ⚡

**A Next-Generation, Ultra-Fast Multi-Platform Media Downloader Telegram Bot**

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Pyrogram-v2.0-blue?style=for-the-badge&logo=telegram&logoColor=white)](https://docs.pyrogram.org/)
[![Downloader](https://img.shields.io/badge/yt--dlp-Latest-red?style=for-the-badge&logo=youtube&logoColor=white)](https://github.com/yt-dlp/yt-dlp)
[![Database](https://img.shields.io/badge/MongoDB-Motor-47A248?style=for-the-badge&logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![License](https://img.shields.io/badge/License-Source--Available%20%2F%20Restricted-critical?style=for-the-badge)](./LICENSE)
[![Author](https://img.shields.io/badge/Author-SankalpModz-blueviolet?style=for-the-badge&logo=github)](https://github.com/sankalpmodz)

<p align="center">
  Download high-resolution videos, audio, reels, photos, albums, and stories from <b>YouTube, Instagram, TikTok, and Pinterest</b> with lightning-fast speeds, aria2c multi-threaded acceleration, Telegram inline search mode, smart daily limits, and full MongoDB persistence.
</p>

---

[Key Features](#-key-features) •
[Supported Platforms](#-supported-platforms) •
[Bot Architecture](#-architecture--tech-stack) •
[Prerequisites](#-prerequisites) •
[Installation Guide](#-installation--setup-guide) •
[Configuration Guide](#-configuration-reference-env) •
[Cookies Setup](#-cookies-setup-guide) •
[Production Deployment](#-247-production-deployment-systemd) •
[Admin Commands](#-admin--utility-commands) •
[License & Legal Notice](#-license--copyright-protection)

---

</div>

## 🌟 Key Features

- ⚡ **Multi-Platform Powerhouse:** Seamlessly downloads content from **YouTube**, **Instagram**, **TikTok**, and **Pinterest**.
- 🚀 **Hardware & Aria2c Accelerated:** Multi-connection chunked downloads (`aria2c` with 16 connections per file) maximize network bandwidth.
- 🔍 **Instant Inline Search Mode:** 
  - Search YouTube directly from any Telegram chat using `@YourBotUsername <query>`.
  - Built with the high-speed **Innertube** API (zero latency, up to 50 search results).
  - Smart context detection: sends direct downloadable links in PM and elegant interactive preview cards in groups/channels.
- 🎛️ **Dynamic Resolution & Audio Selection:** Interactive inline buttons allow users to choose from available qualities (1080p, 720p, 480p, 360p, or Best Audio M4A).
- 🎵 **Adaptive Audio Bitrate Display:** Automatically detects and displays actual audio bitrate on completion (e.g., `Best Audio (256kbps M4A)`).
- 📸 **Instagram Multi-Media Carousel (Album) Support:** Groups multiple Instagram carousel photos/videos into a single Telegram media album to prevent chat spam.
- 🖼️ **Auto-Conversion for WebP:** Automatically converts Instagram `.webp` formats to `.jpg` on the fly to avoid Telegram `PHOTO_EXT_INVALID` errors.
- 🛡️ **Smart Anti-Abuse & Bandwidth Protections:**
  - **Live Video Blocker:** Rejects live streams in advance to protect server bandwidth.
  - **Max Duration Filter (`MAX_DURATION`):** Automatically prevents downloading videos exceeding the configured duration limit (in minutes).
  - **Max File Size Filter (`MAX_FILE_SIZE`):** Estimates total video + audio size before download and verifies exact size before upload (default 2000 MB for Telegram MTProto limit).
  - **Download Concurrency Control:** Python `asyncio.Semaphore` prevents server memory exhaustion during traffic spikes.
  - **Daily Download Quota (`DAILY_DOWNLOAD_LIMIT`):** Per-user daily quotas reset automatically every 24 hours (with Owner bypass).
- 🔒 **Dual Force Subscription System:** Protect your community growth by requiring users to join both an official Channel and an official Group before utilizing the bot.
- 📊 **Administrative Suite:** Complete broadcast engine with progress tracking, live user count statistics, ping latency monitor, user banning/unbanning, and dedicated log group telemetry.
- 🌐 **IPv6 Fallback & IPv4 Binding:** Built-in `'0.0.0.0'` address binding fixes VPS `[Errno 101] Network is unreachable` errors.

---

## 📱 Supported Platforms

| Platform | Supported Content | Features |
| :--- | :--- | :--- |
| **YouTube** | Videos, Shorts, Music | Quality selector (360p - 1080p+), Best Audio M4A with bitrate indicator, Live stream blocker |
| **Instagram** | Reels, Posts, Carousels, Stories | Album grouping (sends multiple photos in 1 album), WebP converter, Audio extraction |
| **TikTok** | HD Videos, Sounds | No-watermark video download, Audio extraction, Duration checks |
| **Pinterest** | Pins, Videos, Images, GIFs | Direct media resolution extraction, fast download |

---

## 🏗 Architecture & Tech Stack

```
XyronDownloader/
├── config.py                 # Central configuration loader
├── sample.env                # Template for environment variables
├── requirements.txt          # Python project dependencies
├── start                     # Shell launcher script
├── LICENSE                   # SankalpModz Restricted License
├── README.md                 # Project documentation
└── xyrondownloader/
    ├── __init__.py           # Package initializer & client setup
    ├── __main__.py           # Bot startup entry point
    ├── cookies/              # Cookie storage for YouTube & Instagram
    │   ├── .gitkeep
    │   ├── cookies.txt       # Netscape formatted cookies for YouTube
    │   └── insta.txt         # Cookies for Instagram
    ├── core/                 # Platform download & database logic
    │   ├── database.py       # MongoDB async driver (Motor)
    │   ├── youtube.py        # YouTube extraction, quality parsing & upload
    │   ├── insta.py          # Instagram posts, reels, albums & WebP conversion
    │   ├── tiktok.py         # TikTok video & audio extraction
    │   ├── pinterest.py      # Pinterest media handler
    │   └── search.py         # Ultra-fast Innertube search engine
    ├── helpers/              # Helper utilities & option builders
    │   ├── youtube.py        # yt-dlp option presets & ID extractors
    │   ├── insta.py          # Instagram request headers & options
    │   ├── tiktok.py         # TikTok downloader options
    │   ├── pinterest.py      # Pinterest scraping helpers
    │   ├── thumbnail.py      # Thumbnail fetcher
    │   └── utils.py          # Sanitizer for Telegram Markdown/HTML parsers
    └── plugins/              # Pyrogram message & callback handlers
        ├── start.py          # /start command & deep-link routing
        ├── router.py         # URL router & message dispatcher
        ├── inline.py         # Telegram Inline search mode handler
        ├── forcesub.py       # Channel & Group force subscribe middleware
        ├── broadcast.py      # Admin broadcast engine
        ├── ban_unban.py      # User ban & unban commands
        ├── banned.py         # Banned user interceptor
        ├── stats.py          # /stats command
        └── ping.py           # /ping & uptime command
```

---

## 📋 Prerequisites

Before installing the bot, ensure your system meets the following requirements:

- **Operating System:** Linux (Ubuntu 20.04/22.04/24.04 LTS or Debian 11/12 recommended) / Windows 10/11
- **Python:** Version `3.10` or higher
- **FFmpeg:** Required for merging video and audio streams
- **aria2c:** Required for high-speed multi-connection downloads
- **Git:** For cloning and updating the repository
- **MongoDB Database:** A free cluster from [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)

---

## 🚀 Installation & Setup Guide

### 1. Update Server & Install System Dependencies

On Ubuntu / Debian:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git ffmpeg aria2
```

On CentOS / RHEL / Fedora:
```bash
sudo dnf install -y python3 python3-pip git ffmpeg aria2
```

### 2. Clone the Repository

```bash
git clone https://github.com/sankalpmodz/XyronDownloader.git
cd XyronDownloader
```

### 3. Create & Activate Virtual Environment

It is strongly recommended to run the bot inside an isolated Python virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

*(On Windows PowerShell: `venv\Scripts\Activate.ps1`)*

### 4. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Create your production `.env` file from the provided template:
```bash
cp sample.env .env
nano .env
```
Fill in all required credentials as detailed in the [Configuration Reference](#-configuration-reference-env) section below. Press `Ctrl + O` then `Enter` to save, and `Ctrl + X` to exit `nano`.

### 6. Start the Bot

Run the bot directly in your terminal:
```bash
python3 -m xyrondownloader
```
If configured correctly, you will see the startup banner and confirmation that the bot is listening for updates.

---

## ⚙️ Configuration Reference (`.env`)

| Variable | Required | Default | Description |
| :--- | :---: | :---: | :--- |
| `API_ID` | **Yes** | — | Telegram API ID obtained from [my.telegram.org](https://my.telegram.org) |
| `API_HASH` | **Yes** | — | Telegram API Hash obtained from [my.telegram.org](https://my.telegram.org) |
| `BOT_TOKEN` | **Yes** | — | Telegram Bot Token obtained from [@BotFather](https://t.me/BotFather) |
| `OWNER_ID` | **Yes** | — | Telegram User ID of the primary administrator/owner |
| `MONGO_DB_URI` | **Yes** | — | MongoDB connection string (e.g., `mongodb+srv://user:pass@cluster.mongodb.net/`) |
| `ENABLE_LOGGER` | No | `True` | Set to `True` to send activity logs to the log group |
| `LOG_GROUP_ID` | Conditional | `0` | Telegram Chat ID of the log group/channel (e.g., `-1001234567890`) |
| `DAILY_DOWNLOAD_LIMIT` | No | `15` | Maximum downloads per user per 24 hours (`0` for unlimited) |
| `MAX_DURATION` | No | `60` | Maximum video duration allowed in minutes (`0` for unlimited) |
| `MAX_FILE_SIZE` | No | `2000` | Maximum allowed file size in MB (`2000` for standard Telegram 2GB limit) |
| `FORCE_SUB_CHANNEL_ID`| No | `0` | Channel ID for Force Subscribe (`0` to disable) |
| `FORCE_SUB_CHANNEL_LINK`| No | — | Public/Private invite link for the Force Subscribe Channel |
| `FORCE_SUB_GROUP_ID` | No | `0` | Group ID for Force Subscribe (`0` to disable) |
| `FORCE_SUB_GROUP_LINK` | No | — | Public/Private invite link for the Force Subscribe Group |
| `USE_PROXY` | No | `False` | Set to `True` to route yt-dlp traffic through proxies |
| `PROXIES` | No | — | Comma-separated proxies (`http://ip:port,http://user:pass@ip:port`) |
| `USE_COOKIES` | No | `False` | Set to `True` to pass cookie files to yt-dlp |
| `COOKIES_FILE_PATH` | No | `xyrondownloader/cookies/cookies.txt` | Path to YouTube Netscape cookies file |
| `INSTA_COOKIES_FILE` | No | `xyrondownloader/cookies/insta.txt` | Path to Instagram cookies file |
| `DOWNLOAD_DIR` | No | `downloads` | Local temporary directory for downloading files |

---

## 🍪 Cookies Setup Guide

Both YouTube and Instagram aggressively block requests coming from cloud hosting providers (AWS, Hetzner, DigitalOcean, Contabo, etc.). Configuring cookies ensures 100% extraction success.

### YouTube Cookies:
1. Install a browser extension such as **Get cookies.txt LOCALLY** (Chrome/Firefox).
2. Log into a spare Google/YouTube account in your browser.
3. Open YouTube, open the extension, and export cookies in **Netscape format**.
4. Save or copy the content to `xyrondownloader/cookies/cookies.txt` on your server.
5. In `.env`, ensure `USE_COOKIES=True`.

### Instagram Cookies:
1. Log into your Instagram account in your browser.
2. Export the cookies in Netscape format using the extension.
3. Save the content to `xyrondownloader/cookies/insta.txt`.

> ⚠️ **Security Warning:** Never commit your active `cookies.txt` or `insta.txt` to GitHub or any public repository! The `.gitignore` in this project is pre-configured to keep cookie files private.

---

## 🔄 24/7 Production Deployment (Systemd)

To keep the bot running automatically in the background, restart upon server reboots, and restart on any unexpected failure, create a Linux `systemd` service:

1. Create a service file:
```bash
sudo nano /etc/systemd/system/xyronbot.service
```

2. Paste the following configuration (replace `/root/XyronDownloader` and `root` with your actual username and project directory):
```ini
[Unit]
Description=Xyron Downloader Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/XyronDownloader
ExecStart=/root/XyronDownloader/venv/bin/python3 -m xyrondownloader
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

3. Reload systemd, enable the service, and start the bot:
```bash
sudo systemctl daemon-reload
sudo systemctl enable xyronbot
sudo systemctl start xyronbot
```

4. Check bot status and real-time logs:
```bash
sudo systemctl status xyronbot
sudo journalctl -u xyronbot -f
```

---

## 🛠 Admin & Utility Commands

| Command | Permission | Description |
| :--- | :---: | :--- |
| `/start` | Everyone | Welcome message, user registration, and deep-link downloader |
| `/ping` | Everyone | Displays server latency, response time, and bot uptime |
| `/stats` | Admin / Owner | Displays total registered bot users and system resource usage (RAM, CPU) |
| `/broadcast` | Owner Only | Reply to any message/media to broadcast it to all registered bot users |
| `/ban <user_id>` | Owner Only | Bans a specified user from using the bot |
| `/unban <user_id>` | Owner Only | Unbans a previously banned user |

---

## ⚖️ License & Copyright Protection

**Copyright (c) 2026 SankalpModz ([@sankalpmodz](https://github.com/sankalpmodz)). All Rights Reserved.**

This repository is distributed under the **SankalpModz Source-Available & Restricted License (v1.0)**.

### Permitted:
- ✅ Private, non-commercial self-hosting for personal use.
- ✅ Inspecting, learning, and contributing via pull requests to the upstream repository.

### Strictly Prohibited:
- ❌ **No Unauthorized Redistribution or Re-uploading:** You are **NOT** permitted to re-upload, mirror, clone, or publish copies or derivative versions of this codebase on GitHub, GitLab, Telegram, or any public platform.
- ❌ **No Rebranding or Plagiarism:** You are **NOT** permitted to strip or modify author credits, remove `@sankalpmodz` attributions, or claim authorship/ownership of this project.
- ❌ **No Commercial Exploitation or Resale:** You are **NOT** permitted to sell this code, charge users for hosted bot access, or incorporate it into commercial products.

### DMCA & Legal Enforcement:
> [!CAUTION]
> Any unauthorized re-distribution, repository duplication, or removal of author credits will be met with an immediate **DMCA Takedown Notice** filed directly with GitHub Legal (`github.com/contact/dmca`) and upstream service providers, along with all legal remedies available under international copyright law.

For permissions or queries, contact the author via [GitHub Profile](https://github.com/sankalpmodz).

---

<div align="center">
  <b>Developed with ❤️ by <a href="https://github.com/sankalpmodz">SankalpModz</a></b>
</div>