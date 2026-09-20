import time, psutil
from pyrogram import Client, filters
from xyrondownloader import boot_time
from xyrondownloader.plugins.forcesub import check_subscription


def get_readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]
    while count < 4:
        count += 1
        remainder, result = (
            divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        )
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)
    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        ping_time += time_list.pop() + ", "
    time_list.reverse()
    return ping_time + ":".join(time_list)


@Client.on_message(filters.command(["ping", "alive"]))
async def universal_ping(client, message):
    if not await check_subscription(client, message):
        return

    start_time = time.time()
    reply = await message.reply_text(
        "⏳ __Checking...__", reply_to_message_id=message.id
    )
    latency = round((time.time() - start_time) * 1000, 2)
    current_uptime_sec = int(time.time() - boot_time)

    cpu_usage = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory()

    text = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"      ⚡ **System Status** ⚡\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🏓 __Latency:__  `{latency} ms`\n"
        f"⏱ __Uptime:__  `{get_readable_time(current_uptime_sec)}`\n"
        f"🖥 __CPU:__  `{cpu_usage}%`\n"
        f"💾 __RAM:__  `{ram.percent}%`\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✨ **@MysticDownloaderBot** • __Online__ ✅"
    )

    await reply.edit_text(text)