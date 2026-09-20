import asyncio
from config import Config

async def run_gallery_dl(url, chat_id, msg_id):
    unique_id = f"{chat_id}_{msg_id}"
    cmd = ["gallery-dl", "--destination", Config.DOWNLOAD_DIR, "--filename", f"dl_{unique_id}_{{num}}.{{extension}}", "--no-mtime", url]
    process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await process.communicate()
    if process.returncode != 0: return False, stderr.decode()
    return True, unique_id