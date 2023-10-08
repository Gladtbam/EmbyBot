from telethon import Button
from asyncio import sleep
from app.db import search_user, change_score, search_score, create_score_user, delete_user, delete_score_user
from app.emby_api import UserPlaylist
from app.data import load_config
from app.telethon_api import reply, respond

admin_ids = load_config()['ADMIN_IDS']
chat_id = load_config()['GROUP_ID']

bot_name = load_config()['Telegram']['BOT_NAME']
emby_url = load_config()['Emby']['URL']

signup_method = {"time": 0, "remain_num": 0.0}      # 注册方法
signup_message = None

async def start_init(client):
    async for user in client.iter_participants(chat_id):
        if user.bot is False:
            result = await search_score(user.id)
            if result is None:
                await create_score_user(user.id)

async def handle_start(event):
    await event.respond(f'欢迎使用 {bot_name} 机器人！')
    await handle_help(event)

async def handle_help(event):
    message = f'''
/help - [私聊]帮助
/checkin - 签到
/signup - 注册, 仅开放注册时使用
/request - 求片, 具体使用查看WiKi
/code - [私聊]使用注册码注册, 或者使用续期码续期。例: /code 123
/del - [管理员]删除 Emby 账户, 需回复一个用户
/me - [私聊]查看 Emby 账户 和 个人 信息(包含其它工具)
/info - [管理员]查看用户信息
/settle - [管理员]手动结算积分
/change - [管理员]手动修改积分, 正数加负数减
    '''
    if event.is_private:
        await respond(event, message, parse_mode='Markdown')
    else:
        await reply(event, f'请私聊 {bot_name}')

# 查看信息 (私人)
async def handle_me(event):
    tgid = event.sender_id
    user_result = await search_user(tgid)
    score_result = await search_score(tgid)
    keyboard = [
        [
            Button.inline("生成“码”", b"create_code"),
            Button.inline("NSFW开关", b"nsfw"),
            Button.inline("续期", b"renew")
        ],
        [
            # Button.inline("忘记密码", b"reset_pw"),
            Button.inline("线路查询", b"weblink"),
            Button.inline("查询续期积分", b"get_renew")
        ]
    ]
    if user_result is not None:
        played_ratio = await UserPlaylist(user_result[1], user_result[3].strftime("%Y-%m-%d"))
        played_ratio = "{:.3f}%".format(played_ratio * 100)
        message = f'''
**Telegram ID**: `{user_result[0]}`
**Emby ID**: `{user_result[1]}`
**用户名**: `{user_result[2]}`
**有效期**: `{user_result[3]}`
**观看度**: `{played_ratio}`
**Ban**: `{user_result[4]}`
'''
    else:
        message = f'**尚无 Emby 账户**\n'
    if score_result is None:
        await change_score(tgid, 0)
        message += f'''
**积分**: 0
**签到天数**: 0
'''
    else:
        message += f'''
**积分**: `{score_result[1]}`
**签到天数**: `{score_result[2]}`
'''

    if event.is_private:
        if user_result is not None:
            await respond(event, message, parse_mode='Markdown', buttons=keyboard)
        else:
            await respond(event, message, parse_mode='Markdown')
    else:
        await reply(event, '仅私聊')

# 查看信息 (管理员)
async def handle_info(event):
    tgid = event.sender_id
    reply_tgid = await get_reply(event)
    user_result = await search_user(reply_tgid)
    score_result = await search_score(reply_tgid)
    if user_result is not None:
        played_ratio = await UserPlaylist(user_result[1], user_result[3].strftime("%Y-%m-%d"))
        played_ratio = "{:.3f}%".format(played_ratio * 100)
        message = f'''
**Telegram ID**: `{user_result[0]}`
**Emby ID**: `{user_result[1]}`
**用户名**: `{user_result[2]}`
**有效期**: `{user_result[3]}`
**观看度**: `{played_ratio}`
**Ban**: `{user_result[4]}`
'''
    else:
        message = f'**尚无 Emby 账户**\n'
    if score_result is None:
        await change_score(tgid, 0)
        message += f'''
**积分**: 0
**签到天数**: 0
'''
    else:
        message += f'''
**积分**: `{score_result[1]}`
**签到天数**: `{score_result[2]}`
'''

    if tgid in admin_ids:
        await reply(event, message, parse_mode='Markdown')
    else:
        await reply(event, '您非管理员, 无权执行此命令')


# 获取回复信息的TG ID
async def get_reply(event):
    reply_message = await event.get_reply_message()
    reply_tgid = None
    if reply_message:
        reply_tgid = reply_message.sender_id
    else:
        await reply(event, '请回复一条消息')
    return reply_tgid

# 发送积分更新消息
async def send_scores_to_group(client_user, group_id, user_scores):
    message = "活跃积分获取情况：\n\n"
    for user_id, score_value in user_scores.items():
        if score_value != 1:
            user = await client_user.get_entity(user_id)
            username = user.first_name + ' ' + user.last_name if user.last_name else user.first_name
            message += f"[{username}](tg://user?id={user_id}) 获得: {score_value} 积分\n"
        else:
            message += "\t无活跃积分大于 1 的成员"

    await client_user.send_message(group_id, message, parse_mode='Markdown')

# 获取 Emby URL
async def handle_weblink(event):
    await respond(event, f'Emby 地址:\n`{emby_url}`')

# 删除消息
async def delete_bot_message(event):
    if "/" in event.message.text:
        await sleep(10)
        await event.message.delete()

# 用户入群/退群
async def handle_add_chat(client, event):
    if event.user_added or event.user_joined:
        await create_score_user(event.user_id)
    if event.user_left or (event.user_kicked and event.action_message is not None):
        print(event)
        await delete_score_user(event.user_id)
        if await search_user(event.user_id) is not None:
            await delete_user(event.user_id)

    if event.user_kicked and event.action_message is not None:
        user_info = await client.get_entity(event.user_id)
        username = user_info.first_name + ' ' + user_info.last_name if user_info.last_name else user_info.first_name
        message = f"[{username}](tg://user?id={event.user_id}) 被管理员踢出"
        messages = await client.send_message(chat_id, message, parse_mode='Markdown')
        await sleep(10)
        await messages.delete()