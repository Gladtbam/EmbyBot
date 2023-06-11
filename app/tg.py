from datetime import datetime, timedelta
from telethon import events, Button
from asyncio import sleep
from app.db import create_user, search_user, delete_user, search_code, delete_code
from app.emby import New_User, User_Policy, Password, User_delete
from app.db import load_config
from app.regcode import verify_code

admin_ids = load_config()['ADMIN_IDS']

# 注册命令处理逻辑
def register_commands(client):
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
            command, *args = text.split(' ')            # 解构参数
            if len(args) > 0:
                await handle_signup_code(event, tgid, args[0])
            else:
                await event.respond('未开放注册！！！\n如果有注册码, 请使用注册码注册')

        elif text.startswith('/code'):
            if event.is_private or tgid in admin_ids:
                await handle_code(event)
            else:
                await event.respond('仅私聊')

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

        elif text.startswith('/renew'):
            command, *args = text.split(' ')
            if len(args) > 0:
                await handle_renew(event, tgid, args[0])
            else:
                await event.respond('请输入续期码')

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

async def handle_help(event):
    await event.respond('这是帮助信息。')

async def handle_signup_code(event, tgid, code):
    result = await search_code(code)
    if result is not None:
        verify_result = await verify_code(code, result[1], result[2]) 
        func_bit = int(result[3][0].strip())
        tgid_code = int(result[3][1:].strip())
        if verify_result:
            if func_bit == 1:
                if tgid_code == tgid or tgid_code in admin_ids:
                    await handle_signup(event, tgid)
                    await delete_code(code)
                else:
                    await event.respond('ID校验失败, 不属于你的注册码')
            else:
                await event.respond('校验失败, 非注册码')
        else:
            await event.respond('校验失败, 该注册码失效, 可能已被使用或篡改\n请检查您的注册码')
    else:
        await event.respond('校验失败, 该注册码失效, 可能已被使用或篡改\n请检查您的注册码')

async def handle_signup(event, tgid):
    user = await event.client.get_entity(tgid)  # 获取tg用户信息
    tgname = user.username                      # 获取tg用户ID

    result = await search_user(tgid)       # 搜索数据库是否存在用户

    if tgname:
        if result is not None:
            message = '用户已存在'
        else:
            embyid = await New_User(tgname)
            await create_user(tgid, embyid, tgname)
            await User_Policy(embyid)
            passwd = await Password(embyid)

            message = f'创建成功！！！\nEMBY ID: {embyid}\n用户名: {tgname}\n初始密码: {passwd}\n请及时修改密码'
    else:
        message = '未设置Telegram用户名, 请设置后重试'
    
    await event.respond(message)

async def handle_code(event):
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

    if result:
        await delete_user(reply_tgid)
        await User_delete(result[1])
        await event.respond(f'用户: {result[1]} 已删除')
    else:
        await event.respond('用户不存在')

async def handle_me(event, tgid):
    user_result = await search_user(tgid)
    renew_button = Button.inline("续期", b"renew")
    keyboard = [
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

async def handle_renew(event, tgid, code):
    result = await search_code(code)
    if result is not None:
        verify_result = await verify_code(code, result[1], result[2]) 
        func_bit = int(result[3][0].strip())
        tgid_code = int(result[3][1:].strip())
        if verify_result:
            if func_bit == 0:
                if tgid_code == tgid or tgid_code in admin_ids:
                    await event.respond('激活码续期: 未完成')
                    await delete_code(code)
                else:
                    await event.respond('ID校验失败, 不属于你的注册码')
            else:
                await event.respond('校验失败, 非续期码')
        else:
            await event.respond('校验失败, 该续期码失效, 可能已被使用或篡改\n请检查您的续期码')
    else:
        await event.respond('校验失败, 该续期码失效, 可能已被使用或篡改\n请检查您的续期码')
