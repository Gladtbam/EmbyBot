from datetime import datetime, timedelta
from telethon import Button
from asyncio import sleep
from app.db import create_code
from app.db import create_user, search_user, delete_user, search_code, delete_code, update_limit, change_score, search_score, init_renew_value
from app.emby_api import New_User, User_Policy, Password, User_delete, UserPlaylist, Get_UserInfo
from app.telegram import get_reply
from app.data import load_config, parse_combined_duration
from app.regcode import verify_code, generate_code
import re

admin_ids = load_config()['ADMIN_IDS']
chat_id = load_config()['GROUP_ID']
bot_name = load_config()['Telegram']['BOT_NAME']

signup_method = {"time": 0, "remain_num": 0.0}      # 注册方法
signup_message = None

# 注册条件
async def handle_signup_method(client, event):
    global signup_message

    tgid = event.sender_id
    text = event.message.text
    _, *args = text.split(' ')
    print(args)
    current_time = datetime.now().timestamp()
    tg_score = await search_score(tgid)
    signup_value = int(init_renew_value()) * load_config()['SIGNUP']
    if tgid in admin_ids:
        if len(args) > 0:
            if re.match(r'^\d+$', args[0]):         # 注册人数
                signup_method['remain_num'] = args[0]
                signup_message = await client.send_message(chat_id, f"开启注册, 剩余注册人数: {signup_method['remain_num']}")
            elif re.match(r'^(\d+[hms])+$', args[0]):
                total_seconds = await parse_combined_duration(args[0])
                signup_method['time'] = current_time + total_seconds
                dt_object = datetime.fromtimestamp(float(signup_method['time']))
                signup_message = await client.send_message(chat_id, f"开启注册, 时间截至{dt_object}")
            await client.pin_message(chat_id, signup_message, notify=False)
        else:
            await handle_signup(client, event, tgid)
    else:
        if signup_method['remain_num'] != 0:
            await handle_signup(client, event, tgid)
            signup_method['remain_num'] = int(signup_method['remain_num']) - 1
            await client.edit_message(chat_id, signup_message, f"开启注册, 剩余注册人数: {signup_method['remain_num']}")
        elif float(signup_method['time']) > current_time:
            await handle_signup(client, event, tgid)
        elif tg_score is not None and tg_score[1] >= signup_value:
            await handle_signup(client, event, tgid)
            await change_score(tgid, -(signup_value))
        else:
            await event.reply('积分不足或未开放注册！！！\n如果有注册码, 请通过 `/code` 使用注册码注册')

# 注册
async def handle_signup(client, event, tgid):
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

            message = f'创建成功！！！\nEMBY ID: `{embyid}`\n用户名: `{tgname}`\n初始密码: `{passwd}`\n\n请及时修改密码'
    else:
        message = '未设置Telegram用户名, 请设置后重试'

    await client.send_message(tgid, message)

# 使用 “码”
async def handle_code_check(client, event):
    tgid = event.sender_id
    text = event.message.text
    _, *code = text.split(' ')
    if len(code) > 0:
        if event.is_private or tgid in admin_ids:
            await handle_code(client, event, tgid, code[0])
        else:
            message = await event.reply('仅私聊')
            await sleep(30)
            await message.delete()
    else:
        message = await event.reply('请回复一个“码”')
        await sleep(30)
        await message.delete()

async def handle_code(client, event, tgid, code):

    result = await search_code(code)
    if result is not None:
        verify_result = await verify_code(code, result[1], result[2])
        func_bit = int(result[3])
        if verify_result:
            if func_bit == 1:           # 注册
                await handle_signup(client, event, tgid)
                await delete_code(code)
                message = await event.respond('注册完成, 本次注册已使用注册码')
            elif func_bit == 0:         # 续期
                result_user = await search_user(tgid)
                current_time = datetime.now().date()
                if result_user is not None:                                  # 没必要if，报个jr错
                    limitdate = result_user[3]
                    remain_day = limitdate - current_time
                    if remain_day.days <= 7:                            # 当剩余时间小于7天
                        await update_limit(tgid)
                        await delete_code(code)
                        if result_user[4] is True:                  # 解封Emby
                            BlockMedia = ("Japan")
                            await User_Policy(result_user[1], BlockMedia)
                        message = await event.respond('续期成功')
                    else:
                        message = await event.respond(f'离到期还有 {remain_day.days} 天\n目前小于 7 天才允许续期')
                else:
                    message = await event.respond('用户不存在, 请注册')
        else:
            message = await event.respond('校验失败, 该“码”已失效, \n请检查您的“码”')
    else:
        message = await event.respond('该“码”不存在, 请输入正确的“码”')
    
    await sleep(30)
    await message.delete() # type: ignore

# 删除 Emby 用户
async def handle_delete(event):
    if event.sender_id in admin_ids:   
        reply_tgid = await get_reply(event)
        result = await search_user(reply_tgid)

        if result and reply_tgid is not None:
            await delete_user(reply_tgid)
            await User_delete(result[1])
            message = await event.reply(f'用户: {result[1]} 已删除')
        else:
            message = await event.reply('用户不存在')
    else:
        message = await event.reply('您非管理员, 无权执行此命令')

    await sleep(30)
    await message.delete()

async def handle_create_code(event):
    keyboard = [
        Button.inline("注册码", b"activation_code"),
        Button.inline("续期码", b"renew_code")
    ]
    message = await event.respond(f'点击生成注册码或续期码\n使用前请先查看 WiKi, 否则造成的损失自付', buttons=keyboard)
    await sleep(10)
    await message.delete()

async def handle_create_code_right(event):
    tgid = event.sender_id
    print(event.data.decode())

    if event.data == b'renew_code':
        func_bit = 0
    elif event.data == b'activation_code':
        func_bit = 1
    else:
        func_bit = 9
        event.reply('无法创建正确的码')
    result = await search_score(tgid)
    value = int(init_renew_value())

    if func_bit == 0:
        await event.answer('正在生成续期码！')
    elif func_bit == 1:
        await event.answer('正在生成注册码！')

    code, public_key, sha256_hash = await generate_code(tgid, func_bit)

    if tgid in admin_ids:
        code_time = datetime.now().date() + timedelta(days=90)
    else:
        code_time = datetime.now().date() + timedelta(days=30)
        if result is not None and result[1] > value:
            await change_score(tgid, -(value))
        else:
            await event.respond("积分不足, 无法生成")
            
    if tgid in admin_ids or (result is not None and result[1] > value):
        await create_code(code, public_key, sha256_hash, func_bit, code_time)
        if func_bit == 0:
            await event.respond(f"你生成的续期码为:(点击复制) \n`{code}`\n有效期至 {code_time}")
        elif func_bit == 1:
            await event.respond(f"你生成的注册码为:(点击复制) \n`{code}`\n有效期至 {code_time}")

# 续期
async def handle_renew(event):
    tgid = event.sender_id
    result = await search_user(tgid)
    current_time = datetime.now().date()
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

# 密码重置
async def handle_resetpw(event):
    tgid = event.sender_id
    result = await search_user(tgid)
    Pw = await Password(result[1])
    await event.respond(f"密码已重置\n当前密码为: `{Pw}`\n请及时修改密码")

# NSFW 开关
async def handle_nsfw(event):
    tgid = event.sender_id
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