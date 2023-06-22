from telethon import events, Button
from asyncio import TimeoutError, wait_for, sleep
from datetime import datetime, timedelta
from app.regcode import generate_code, verify_code
from app.emby import User_Policy, Get_UserInfo
from app.tg import handle_create_code
from app.db import create_code, search_code, delete_code, search_user, update_limit, change_score
from app.data import load_config

admin_ids = load_config()['ADMIN_IDS']

def register_callback(client, client_user):
    @client.on(events.CallbackQuery)
    async def handle_callback(event):
        tgid = event.sender_id
        data = event.data.decode()

        if data == 'activation_code':
            await handle_activation_code(event, tgid)
        elif data == 'renew_code':
            await handle_renew_code(event, tgid)
        elif data == 'create_code':
            await handle_create_code(event)
        elif data == 'renew':
            await handle_renew(event)
        elif data == 'renew_right':
            await handle_renew_right(event, tgid)
        elif data == 'nsfw':
            await handle_nsfw(event, tgid)

async def handle_activation_code(event,tgid):
    if tgid in admin_ids:
        await event.answer('正在生成注册码！')
        func_bit = 1
        code, public_key, sha256_hash, data = await generate_code(tgid, func_bit)
        await create_code(code, public_key, sha256_hash, data)
        await event.respond(f"生成的注册码为:(点击复制) \n`{code}`")
    else:
        await event.answer('您非管理员')

async def handle_renew_code(event, tgid):
    await event.answer('正在生成续期码！')
    func_bit = 0
    code, public_key, sha256_hash, data = await generate_code(tgid, func_bit)
    await create_code(code, public_key, sha256_hash, data)
    await event.respond(f"你生成的续期码为:(点击复制) \n`{code}`")

async def handle_renew(event):
    right_button = Button.inline("确定", b"renew_right")
    keyboard = [
        [right_button]
    ]
    message = await event.respond('点击确认, 减除 100 积分续期', buttons=keyboard)
    await sleep(10)
    await message.delete()

async def handle_renew_right(event, tgid):
    result = await search_user(tgid)
    current_time = datetime.now()
    if result is not None:
        limitdate = result[3]
        remain_day = limitdate - current_time
        if remain_day.days <= 7:
            await update_limit(tgid)
            await change_score(tgid, -100)
            if result[4] is True:                  # 解封Emby
                BlockMedia = ("Japan")
                await User_Policy(result[1], BlockMedia)
        else:
            await event.respond(f'离到期还有 {remain_day.days} 天\n目前小于 7 天才允许续期')

async def handle_nsfw(event, tgid):
    result = await search_user(tgid)
    if result is not None:
        user_info = await Get_UserInfo(result[1])
        print(user_info["Policy"]["BlockedMediaFolders"])
        if len(user_info["Policy"]["BlockedMediaFolders"]) > 0:
            BlockMedia = ()
            await User_Policy(result[1], BlockMedia)
            await event.respond('NSFW On')
        else:
            BlockMedia = ("Japan")
            await User_Policy(result[1], BlockMedia)
            await event.respond('NSFW OFF')

async def wait_user_input(event):
    try:
        async for user_input in event.client.iter_messages(event.chat_id, from_user=event.sender_id):
            return user_input.message.strip()
    except StopAsyncIteration:
        return None
