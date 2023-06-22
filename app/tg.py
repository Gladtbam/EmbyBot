from datetime import datetime, timedelta
from telethon import events, Button, functions
from telethon.tl.types import ChatBannedRights
from telethon.utils import get_display_name, get_peer_id
from asyncio import sleep
from app.db import create_user, search_user, delete_user, search_code, delete_code, update_limit, change_score, search_score, update_score, yn_score
from app.emby import New_User, User_Policy, Password, User_delete
from app.data import load_config
from app.regcode import verify_code
from app.tgscore import user_msg_count, calculate_scores
import re

admin_ids = load_config()['ADMIN_IDS']
group_id = load_config()['GROUP_ID']

signup_method = {"time": 0, "remain_num": 0.0}      # 注册方法

# 注册命令处理逻辑
def register_commands(client, client_user):
    @client.on(events.NewMessage)
    async def handle_commands(event):           #传递event
        text = event.message.text

        tgid = event.sender_id
        # 检查消息是否为命令
        if text.startswith('/start'):
            await handle_start(event)

        elif text.startswith('/help'):
            if event.is_private:                        # 私聊
                await handle_help(event)
            else:
                await event.respond('仅私聊')

        elif text.startswith('/signup'):
            command, *args = text.split(' ')
            await handle_signup_method(event, tgid, args)

        elif text.startswith('/code'):
            command, *args = text.split(' ')
            if len(args) > 0:
                if event.is_private or tgid in admin_ids:
                    await handle_code(event, tgid, args[0])
                else:
                    await event.respond('仅私聊')
            else:
                await event.respond('请回复一个“码”')

        elif text.startswith('/del'):
            if tgid in admin_ids:               # 判断是否在管理员列表中
                await handle_delete(event)
            else:
                await event.respond('您非管理员, 无权执行此命令')

        elif text.startswith('/me'):
            if event.is_private or tgid in admin_ids:
                await handle_me(event, tgid)
            else:
                await event.respond('仅私聊')

        elif text.startswith('/info'):
            if event.is_private or tgid in admin_ids:
                await handle_info(event, tgid)
            else:
                await event.respond('仅私聊')

        elif text.startswith('/settle'):
            if tgid in admin_ids:
                await handle_settle(client_user)
            else:
                await event.respond('您非管理员, 无权执行此命令')

        elif text.startswith('/change'):
            command, *args = text.split(' ')
            if len(args) > 0:
                if tgid in admin_ids:
                    await handle_change_score(event, args[0])
                else:
                    await event.respond('您非管理员, 无权执行此命令')
            else:
                await event.respond('请回复一个值, 整数为+, 负数为-')

        elif text.startswith('/ex'):
            await handle_exchange(event, client_user, tgid)

async def get_reply(event):
    reply_message = await event.get_reply_message()
    reply_tgid = None
    if reply_message:
        reply_tgid = reply_message.sender_id
    else:
        await event.respond('请回复一条消息')
    return reply_tgid

async def handle_start(event):
    await event.respond('欢迎使用机器人！')
    await handle_help(event)

async def handle_help(event):
    message = f'''
/help - 帮助
/signup - 注册, 仅开放注册时使用。
/code - 使用注册码注册, 或者使用续期码续期。例: /code 123
/del - 删除 Emby 账户, 仅管理员使用, 需回复一个用户
/me - 查看 Emby 账户信息(包含其它工具), 仅私聊
/info - 查看个人信息, 积分等
/settle - 手动结算积分, 仅管理员使用
/change - 手动修改积分, 仅管理员, 正数加负数减
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
            await event.respond('未开放注册！！！\n如果有注册码, 请通过 `/code` 使用注册码注册')

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
                        else:
                            await update_limit(tgid)
                            await change_score(tgid_code, -100)
                            await delete_code(code)
                            if result_user[4] is True:
                                BlockMedia = ("Japan")
                                await User_Policy(result_user[1], BlockMedia)
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

async def handle_create_code(event):
    activation_button = Button.inline("注册码", b"activation_code")
    renew_button = Button.inline("续期码", b"renew_code")
    keyboard = [
        [activation_button],
        [renew_button]
    ]
    message = await event.respond('1. 非特殊情况, 非管理员只能使用续期码\n2. 续期码创建在使用之后才扣除积分\n3. 由于与生成用户(非管理员)绑定, 因此不要随便公布你的续期码', buttons=keyboard)
    await sleep(10)
    await message.delete()

async def handle_delete(event):
    reply_tgid = await get_reply(event)
    result = await search_user(reply_tgid)

    if result and reply_tgid is not None:
        await delete_user(reply_tgid)
        await User_delete(result[1])
        await event.respond(f'用户: {result[1]} 已删除')
    else:
        await event.respond('用户不存在')

# 查看 Emby 信息
async def handle_me(event, tgid):
    user_result = await search_user(tgid)
    code_button = Button.inline("生成“码”", b"create_code")
    nsfw_button = Button.inline("NSFW开关", b"nsfw")
    renew_button = Button.inline("续期", b"renew")
    keyboard = [
        [code_button],
        [nsfw_button],
        [renew_button]
    ]
    if user_result is not None:
        message = f'''
**Telegram ID**: `{user_result[0]}`
**Emby ID**: `{user_result[1]}`
**用户名**: `{user_result[2]}`
**有效期**: `{user_result[3]}`
**Ban**: `{user_result[4]}`
'''
        await event.respond(message, parse_mode='Markdown', buttons=keyboard)
    else:
        await event.respond('您尚未有账户')

# 查看积分信息
async def handle_info(event, tgid):
    score_result = await search_score(tgid)
    if score_result is None:
        await change_score(tgid, 0)
        message = f"**积分**: 0"
        await event.respond(message, parse_mode='Markdown')
    else:
        message = f"**积分**: `{score_result[1]}`"
        await event.respond(message, parse_mode='Markdown')

# 发送积分更新消息
async def send_scores_to_group(client_user, group_id, user_scores):
    message = "昨日积分获取情况：\n\n"
    for user_id, score_value in user_scores.items():
        user = await client_user.get_entity(user_id)
        username = get_display_name(user)
        message += f"@{username} 获得: {score_value} 积分\n"
    
    await client_user.send_message(group_id, message)

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
        await event.respond(f'已更改, 当前用户积分为 {result_score[1]}')
    else:
        await event.respond(f'请回复一条消息')

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

async def handle_exchange(event, client_user, tgid):
    reply_message = await event.get_reply_message()
    message_id = reply_message.id
    forward_id = reply_message.fwd_from.from_id.user_id
    forward_message = reply_message.message
    if forward_id == 5400993444:
        org_score = re.search(r"群积分：(\d+)", forward_message)
        score = int(org_score.group(1))
        back_score = int(score / 10)
        message = f"/minus {score}"

        score_result = await search_score(tgid)
        if score_result is not None:
            if score_result[2] is not True:
                await client_user(functions.messages.SendMessageRequest(peer=get_peer_id(group_id),message=message,reply_to_msg_id=message_id))
                await change_score(tgid, back_score)
                await yn_score(tgid)
            else:
                await event.respond('已兑换, 不可重复兑换')
        else:
            await change_score(tgid, 0)
            await event.respond('请重试')