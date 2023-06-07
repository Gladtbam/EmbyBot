from telethon import events
from app.db import create_user, search_user, delete_user
from app.emby import New_User, User_Policy, Password, User_delete
from app.db import load_config

admin_ids = load_config()['ADMIN_IDS']

# 处理命令的装饰器
def command_handler(command):
    def decorator(func):
        async def wrapper(event):
            await func(event)

        return wrapper
    return decorator

# 注册命令处理逻辑
def register_commands(client):
    @client.on(events.NewMessage)
    async def handle_commands(event):
        text = event.message.text

        tgid = event.sender_id
        # 检查消息是否为命令
        if text.startswith('/start'):
            await handle_start(event)
        elif text.startswith('/help'):
            await handle_help(event)
        elif text.startswith('/signup'):
            await handle_signup(event,tgid)
        elif text.startswith('/del'):
            if tgid in admin_ids:               # 判断是否在管理员列表中
                await handle_delete(event, tgid)
            else:
                await event.respond('您非管理员, 无权执行此命令')

async def handle_start(event):
    await event.respond('欢迎使用机器人！')

async def handle_help(event):
    if event.is_private is not True:
        await event.respond('仅私聊')
    else:
        await event.respond('这是帮助信息。')

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

async def handle_delete(event):
    reply_message = await event.get_reply_message()
    reply_tgid = reply_message.sender_id

    result = await search_user(reply_tgid)
    await delete_user(reply_tgid)

    await User_delete(result[1])

    await event.respond(f'用户: {result[1]} 已删除')

