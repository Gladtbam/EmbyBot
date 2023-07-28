from telethon import events, Button
from asyncio import sleep
from datetime import datetime
from app.regcode import generate_code
from app.emby import User_Policy, Get_UserInfo, Password, UserPlaylist
from app.db import create_code, search_user, update_limit, change_score, search_score, init_renew_value
from app.data import load_config
from app.arr.search import handle_add_search

admin_ids = load_config()['ADMIN_IDS']
# renew_value = load_config()['Renew_Value']
emby_url = load_config()['Emby']['URL']

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
        # elif data == 'reset_pw':
        #     await handle_resetpw(event, tgid)
        elif data == 'weblink':
            await event.respond(f'Emby 地址:\n`{emby_url}`')
        elif data == 'get_renew':
            await event.respond(f'今日续期积分: {int(init_renew_value())}')
        elif data in ['movie_zh', 'movie_euus', 'movie_jak', 'movie_other', 'movie_anime', 'tv_zh', 'tv_euus', 'tv_jak', 'tv_other', 'tv_anime']:
            await handle_add_search(client, event, data)

async def handle_create_code(event):
    keyboard = [
        Button.inline("注册码", b"activation_code"),
        Button.inline("续期码", b"renew_code")
    ]
    message = await event.respond('1. 非特殊情况, 非管理员只能使用续期码\n2. 续期码创建在使用之后才扣除积分\n3. 由于与生成用户(非管理员)绑定, 因此不要随便公布你的续期码', buttons=keyboard)
    await sleep(10)
    await message.delete()

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
    message = await event.respond(f'点击确认, 减除 {int(init_renew_value())} 积分(折扣前)续期', buttons=keyboard)
    await sleep(10)
    await message.delete()

async def handle_renew_right(event, tgid):
    result = await search_user(tgid)
    current_time = datetime.now()
    if result is not None:
        limitdate = result[3]
        remain_day = limitdate - current_time
        if remain_day.days <= 7:
            score_result = await search_score(tgid)
            played_ratio = await UserPlaylist(result[1], result[3].strftime("%Y-%m-%d"))
            if played_ratio >= 1:
                renew_value = 0
            else:
                renew_value = -(int(int(init_renew_value()) * ( 1 - (0.5 * played_ratio))))
            if int(score_result[1]) >= abs(renew_value):
                await update_limit(tgid)
                await change_score(tgid, renew_value)
                if result[4] is True:                  # 解封Emby
                    BlockMedia = ("Japan")
                    await User_Policy(result[1], BlockMedia)
                await event.respond('续期成功')
            else:
                await event.respond(f'积分不足, 当前所需积分 {abs(renew_value)}(折扣后)')
        else:
            await event.respond(f'离到期还有 {remain_day.days} 天\n目前小于 7 天才允许续期')

async def handle_resetpw(event, tgid):
    result = await search_user(tgid)
    Pw = await Password(result[1])
    await event.respond(f"密码已重置\n当前密码为: `{Pw}`\n请及时修改密码")

async def handle_nsfw(event, tgid):
    result = await search_user(tgid)
    if result is not None:
        user_info = await Get_UserInfo(result[1])
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
