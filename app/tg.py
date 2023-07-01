from datetime import datetime, timedelta
from telethon import events, Button, functions
from telethon.tl.types import ChatBannedRights
from telethon.utils import get_display_name, get_peer_id
from asyncio import sleep
from app.db import create_user, search_user, delete_user, search_code, delete_code, update_limit, change_score, search_score, update_score, init_renew_value
from app.emby import New_User, User_Policy, Password, User_delete
from app.data import load_config
from app.regcode import verify_code
from app.tgscore import user_msg_count, calculate_scores, handle_checkin
import re

admin_ids = load_config()['ADMIN_IDS']
group_id = load_config()['GROUP_ID']
# renew_value = load_config()['Renew_Value']
renew_value = -(int(init_renew_value()))
bot_name = load_config()['BOT_NAME']

signup_method = {"time": 0, "remain_num": 0.0}      # 注册方法

# 注册命令处理逻辑
def register_commands(client, client_user):
    @client.on(events.NewMessage)
    async def handle_commands(event):           #传递event
        text = event.message.text

        tgid = event.sender_id
        # 检查消息是否为命令
        if re.match(fr'^/start({bot_name})?$', text):
            await handle_start(event)

        elif re.match(fr'^/help({bot_name})?$', text):
            if event.is_private:                        # 私聊
                await handle_help(event)
            else:
                await event.reply('仅私聊')

        elif re.match(fr'^/signup({bot_name})?$', text):
            command, *args = text.split(' ')
            await handle_signup_method(event, tgid, args)

        elif re.match(fr'^/code({bot_name})?$', text):
            command, *args = text.split(' ')
            if len(args) > 0:
                if event.is_private or tgid in admin_ids:
                    await handle_code(event, tgid, args[0])
                else:
                    await event.reply('仅私聊')
            else:
                await event.reply('请回复一个“码”')

        elif re.match(fr'^/del({bot_name})?$', text):
            if tgid in admin_ids:               # 判断是否在管理员列表中
                await handle_delete(event)
            else:
                await event.reply('您非管理员, 无权执行此命令')

        elif re.match(fr'^/me({bot_name})?$', text):
            if event.is_private or tgid in admin_ids:
                await handle_me(event, tgid)
            else:
                await event.reply('仅私聊')

        elif re.match(fr'^/info({bot_name})?$', text):
            if tgid in admin_ids:
                await handle_info(event, tgid)
            else:
                await event.reply('您非管理员, 无权执行此命令')

        elif re.match(fr'^/settle({bot_name})?$', text):
            if tgid in admin_ids:
                await handle_settle(client_user)
            else:
                await event.reply('您非管理员, 无权执行此命令')

        elif re.match(fr'^/change({bot_name})?$', text):
            command, *args = text.split(' ')
            if len(args) > 0:
                if tgid in admin_ids:
                    await handle_change_score(event, args[0])
                else:
                    await event.reply('您非管理员, 无权执行此命令')
            else:
                await event.reply('请回复一个值, 正整数为加, 负整数为减')

        elif re.match(fr'^/checkin({bot_name})?$', text):
            await handle_checkin(event, client, tgid)

        elif re.match(fr'^/getrenew({bot_name})?$', text):
            if event.is_private or tgid in admin_ids:
                await event.respond(f'今日续期积分: {abs(renew_value)}')
            else:
                await event.reply('仅私聊')

        elif re.match(r'^/.*@WuMingv2Bot\b', text):
            if tgid not in admin_ids:
                await handle_forbid_wuming(event, client_user, tgid)

async def get_reply(event):
    reply_message = await event.get_reply_message()
    reply_tgid = None
    if reply_message:
        reply_tgid = reply_message.sender_id
    else:
        await event.reply('请回复一条消息')
    return reply_tgid

async def handle_start(event):
    await event.respond('欢迎使用机器人！')
    await handle_help(event)

async def handle_help(event):
    message = f'''
/help - [私聊]帮助
/checkin - 签到
/signup - 注册, 仅开放注册时使用。
/code - [私聊]使用注册码注册, 或者使用续期码续期。例: /code 123
/del - [管理员]删除 Emby 账户, 需回复一个用户
/me - [私聊]查看 Emby 账户 和 个人 信息(包含其它工具)
/info - [管理员]查看用户信息
/settle - [管理员]手动结算积分
/change - [管理员]手动修改积分, 正数加负数减
/getrenew - [私聊]获取今日续期所需积分
    '''
    await event.respond(message, parse_mode='Markdown')

async def handle_signup_method(event, tgid, args):
    current_time = datetime.now().timestamp()
    if tgid in admin_ids:
        if len(args) > 0:
            if re.match(r'^\d+$', args[0]):         # 注册人数
                signup_method['remain_num'] = args[0]
            elif re.match(r'^(\d+[hms])+$', args[0]):
                total_seconds = await parse_combined_duration(args[0])
                signup_method['time'] = current_time + total_seconds
        else:
            await handle_signup(event, tgid)
    else:
        if signup_method['remain_num'] != 0:
            await handle_signup(event, tgid)
            signup_method['remain_num'] = int(signup_method['remain_num']) - 1
        elif float(signup_method['time']) > current_time:
            await handle_signup(event, tgid)
        else:
            await event.reply('未开放注册！！！\n如果有注册码, 请通过 `/code` 使用注册码注册')

async def handle_code(event, tgid, code):
    result = await search_code(code)
    if result is not None:
        verify_result = await verify_code(code, result[1], result[2]) 
        func_bit = int(result[3][0].strip())
        tgid_code = int(result[3][1:].strip())
        if verify_result:
            if func_bit == 1:           # 注册
                if tgid_code == tgid or tgid_code in admin_ids:
                    await handle_signup(event, tgid)
                    await delete_code(code)
                else:
                    await event.respond('ID校验失败, 不属于你的注册码')
            elif func_bit == 0:         # 续期
                result_user = await search_user(tgid)
                current_time = datetime.now()
                if result_user is not None:                                  # 没必要if，报个jr错
                    limitdate = result_user[3]
                    remain_day = limitdate - current_time
                    if remain_day.days <= 7:                            # 当剩余时间小于7天
                        if tgid_code in admin_ids:
                            await update_limit(tgid)
                            await delete_code(code)
                            if result_user[4] is True:                  # 解封Emby
                                BlockMedia = ("Japan")
                                await User_Policy(result_user[1], BlockMedia)
                            await event.respond('续期成功')
                        else:
                            score_result = await search_score(tgid_code)
                            if int(score_result[1]) >= 100:
                                await update_limit(tgid)
                                await change_score(tgid_code, renew_value)
                                await delete_code(code)
                                if result_user[4] is True:
                                    BlockMedia = ("Japan")
                                    await User_Policy(result_user[1], BlockMedia)
                                await event.respond('续期成功')
                            else:
                                await event.respond('积分不足')
                    else:
                        await event.respond(f'离到期还有 {remain_day.days} 天\n目前小于 7 天才允许续期')
                else:
                    await event.respond('用户不存在, 请注册')
        else:
            await event.respond('校验失败, 该“码”已失效, 可能已被使用或篡改\n请检查您的“码”')
    else:
        await event.respond('校验失败, 该“码”已失效, 可能已被使用或篡改\n请检查您的“码”')

async def handle_signup(event, tgid):
    user = await event.client.get_entity(tgid)  # 获取tg用户信息
    tgname = user.username                      # 获取tg用户ID

    result = await search_user(tgid)       # 搜索数据库是否存在用户

    if tgname:
        if result is not None:
            message = '用户已存在'
        else:
            if tgid in admin_ids:
                BlockMedia = ()
            else:
                BlockMedia = ("Japan")
            embyid = await New_User(tgname)
            await create_user(tgid, embyid, tgname)
            await User_Policy(embyid, BlockMedia)
            passwd = await Password(embyid)

            message = f'创建成功！！！\nEMBY ID: {embyid}\n用户名: {tgname}\n初始密码: {passwd}\n请及时修改密码'
    else:
        message = '未设置Telegram用户名, 请设置后重试'
    
    await event.respond(message)

async def handle_delete(event):
    reply_tgid = await get_reply(event)
    result = await search_user(reply_tgid)

    if result and reply_tgid is not None:
        await delete_user(reply_tgid)
        await User_delete(result[1])
        await event.reply(f'用户: {result[1]} 已删除')
    else:
        await event.reply('用户不存在')

# 查看 Emby 信息
async def handle_me(event, tgid):
    user_result = await search_user(tgid)
    score_result = await search_score(tgid)
    keyboard = [
        [
            Button.inline("生成“码”", b"create_code"),
            Button.inline("NSFW开关", b"nsfw"),
            Button.inline("续期", b"renew")
        ],
        [
            Button.inline("忘记密码", b"reset_pw"),
            Button.inline("线路查询", b"weblink")
        ]
    ]
    if user_result is not None:
        message = f'''
**Telegram ID**: `{user_result[0]}`
**Emby ID**: `{user_result[1]}`
**用户名**: `{user_result[2]}`
**有效期**: `{user_result[3]}`
**Ban**: `{user_result[4]}`
'''
    else:
        message = f'**尚无 Emby 账户**\n'
    if score_result is None:
        await change_score(tgid, 0)
        message += f'**积分**: 0'
    else:
        message += f"**积分**: `{score_result[1]}`"

    if user_result is not None:
        await event.respond(message, parse_mode='Markdown', buttons=keyboard)
    else:
        await event.respond(message, parse_mode='Markdown')

# 查看积分信息
async def handle_info(event, tgid):
    reply_tgid = await get_reply(event)
    user_result = await search_user(reply_tgid)
    score_result = await search_score(reply_tgid)
    if user_result is not None:
        message = f'''
**Telegram ID**: `{user_result[0]}`
**Emby ID**: `{user_result[1]}`
**用户名**: `{user_result[2]}`
**有效期**: `{user_result[3]}`
**Ban**: `{user_result[4]}`
'''
    else:
        message = f'**尚无 Emby 账户**\n'
    if score_result is None:
        await change_score(tgid, 0)
        message += f'**积分**: 0'
    else:
        message += f"**积分**: `{score_result[1]}`"
    await event.reply(message, parse_mode='Markdown')

# 发送积分更新消息
async def send_scores_to_group(client_user, group_id, user_scores):
    message = "昨日积分获取情况：\n\n"
    for user_id, score_value in user_scores.items():
        user = await client_user.get_entity(user_id)
        username = user.first_name + ' ' + user.last_name if user.last_name else user.first_name
        message += f"[{username}](tg://user?id={user_id}) 获得: {score_value} 积分\n"
    
    await client_user.send_message(group_id, message, parse_mode='Markdown')

# 计算总时间
async def parse_duration(duration_str):
    total_seconds = 0
    pattern = r'(\d+)([hms])'
    matches = re.findall(pattern, duration_str)
    for value, unit in matches:
        value = int(value)
        if unit == 'h':
            total_seconds += value * 3600
        elif unit == 'm':
            total_seconds += value * 60
        elif unit == 's':
            total_seconds += value
    return total_seconds

async def parse_combined_duration(duration_str):
    total_seconds = 0
    pattern = r'(\d+h)?(\d+m)?(\d+s)?'
    match = re.match(pattern, duration_str)
    if match:
        hours = match.group(1)
        minutes = match.group(2)
        seconds = match.group(3)

        if hours:
            hours = int(hours[:-1])  # 去除末尾的 'h' 并转换为整数
            total_seconds += hours * 3600

        if minutes:
            minutes = int(minutes[:-1])  # 去除末尾的 'm' 并转换为整数
            total_seconds += minutes * 60

        if seconds:
            seconds = int(seconds[:-1])  # 去除末尾的 's' 并转换为整数
            total_seconds += seconds

    return total_seconds

async def handle_change_score(event, score):
    reply_tgid = await get_reply(event)
    if reply_tgid is not None:
        await change_score(reply_tgid, int(score))
        result_score = await search_score(reply_tgid)
        await event.reply(f'已更改, 当前用户积分为 {result_score[1]}')
    else:
        await event.reply(f'请回复一条消息')

async def handle_settle(client_user):
    user_ratios, total_score = await calculate_scores()
    user_score = await update_score(user_ratios, total_score)
    await send_scores_to_group(client_user, group_id, user_score)
    user_msg_count.clear()                  # 清空字典
# 全体禁言
async def mute_group(client, group_id):
    await client.edit_permissions(group_id, '*', ChatBannedRights(until_date=None, send_messages=False))

# 全体解禁
async def unmute_group(client, group_id):
    await client.edit_permissions(group_id, '*', ChatBannedRights(until_date=None, send_messages=True))

async def handle_forbid_wuming(event, client_user, tgid):
    message_id = event.message.id
    message = f"/warn"
    await client_user(functions.messages.SendMessageRequest(peer=get_peer_id(group_id),message=message,reply_to_msg_id=message_id))
