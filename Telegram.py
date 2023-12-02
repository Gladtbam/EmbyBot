from LoadConfig import init_config
from telethon import TelegramClient, events, Button
from telethon.tl.types import PeerUser, PeerChat, PeerChannel
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch
from telethon.tl.functions.users import GetFullUserRequest
import asyncio
import logging

config = init_config()

client = TelegramClient('session', config.telegram.ApiId, config.telegram.ApiHash).start(bot_token=config.telegram.Token) # type: ignore

@client.on(events.NewMessage(pattern=fr'^/start({config.telegram.BotName})?$'))
async def start(event):
    try:
        message = await event.respond(f'欢迎使用 {config.telegram.BotName} 机器人！')
        await help(event)
    except Exception as e:
        logging.error(e)
    finally:
        await asyncio.sleep(10)
        await event.delete()
        await message.delete()
        raise events.StopPropagation

@client.on(events.NewMessage(pattern=fr'^/help({config.telegram.BotName})?$'))
async def help(event):
    try:
        messages = f'''
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
            message = await event.respond(messages)
        else:
            message = await event.reply(messages)
    except Exception as e:
        logging.error(e)
    finally:
        await asyncio.sleep(10)
        await event.delete()
        await message.delete()
        raise events.StopPropagation

# @client.on(events.NewMessage(pattern=fr'^/checkin({config.telegram.BotName})?$'))