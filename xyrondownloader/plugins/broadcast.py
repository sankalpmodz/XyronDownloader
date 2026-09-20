import asyncio
from pyrogram import Client, filters
from config import Config
from xyrondownloader.core.database import get_all_users, get_all_chats

@Client.on_message(filters.command("broadcast") & filters.user(Config.OWNER_ID))
async def broadcast(client, message):
    if not message.reply_to_message: 
        return await message.reply_text(
            "⚠️ **Reply to a message to broadcast it.**\n\n"
            "🛠 **Supported Flags:**\n"
            "`-user` : Include only users\n"
            "`-nochat` : Exclude groups\n"
            "`-copy` : Remove forwarded tag", 
            quote=True
        )
    
    args = message.text.split()[1:]
    flags = [arg.lower() for arg in args if arg.startswith("-")]

    send_to_users = True
    send_to_chats = True
    use_copy = False
    
    if "-copy" in flags:
        use_copy = True
        
    if "-nochat" in flags:
        send_to_chats = False
        
    if "-user" in flags and "-nochat" not in flags:
        send_to_chats = False

    msg = await message.reply_text("📢 **Broadcasting... Please wait.**", quote=True)
    
    targets = set()
    
    if send_to_users:
        async for user in await get_all_users():
            targets.add(user["_id"])
            
    if send_to_chats:
        try:
            async for chat in await get_all_chats():
                targets.add(chat["_id"])
        except Exception:
            pass
            
    success_count = 0
    fail_count = 0
    
    for target_id in targets:
        try:
            if use_copy:
                await message.reply_to_message.copy(chat_id=target_id)
            else:
                await message.reply_to_message.forward(chat_id=target_id)
            success_count += 1
            await asyncio.sleep(0.1)
        except Exception:
            fail_count += 1
            
    await msg.edit_text(
        f"✅ **Broadcast Complete!**\n\n"
        f"🎯 **Successfully Sent:** `{success_count}`\n"
        f"❌ **Failed/Blocked:** `{fail_count}`\n"
        f"⚙️ **Flags Used:** `{', '.join(flags) if flags else 'None'}`"
    )
