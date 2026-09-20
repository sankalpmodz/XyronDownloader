# 🍪 Cookies Directory

This directory is designated for storing authentication cookies in **Netscape HTTP Cookie format** to bypass rate limits, bot detection, and geo/age restrictions on YouTube and Instagram.

---

## 📁 Expected Files

| Filename | Platform | Usage |
| :--- | :--- | :--- |
| `cookies.txt` | **YouTube** | Used by `yt-dlp` for YouTube audio/video analysis and downloads |
| `insta.txt` | **Instagram** | Used by `gallery-dl` and `yt-dlp` for Instagram posts, reels, and stories |

---

## 🛠 How to Generate Cookie Files

1. Install a Netscape-compatible cookie exporter extension in your browser:
   - **Chrome / Brave / Edge:** [Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
   - **Firefox:** [Cookie Quick Manager](https://addons.mozilla.org/en-US/firefox/addon/cookie-quick-manager/)
2. Log into your account (e.g. YouTube or Instagram) in your browser.
3. Click the extension icon and export the cookies in **Netscape format**.
4. Save the file in this directory as:
   - `xyrondownloader/cookies/cookies.txt` (for YouTube)
   - `xyrondownloader/cookies/insta.txt` (for Instagram)
5. Ensure `USE_COOKIES=True` in your `.env` configuration.

---

> 🔒 **Security Notice:** Actual `.txt` cookie files contain sensitive session tokens. The project's `.gitignore` automatically prevents `*.txt` files in this directory from being tracked or committed to Git.
