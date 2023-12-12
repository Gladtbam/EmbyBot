from LoadConfig import init_config
from telethon import TelegramClient, events, Button
from telethon.tl.types import PeerUser, PeerChat, PeerChannel
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch
from telethon.tl.functions.users import GetFullUserRequest
import DataBase
import EmbyAPI
import asyncio
import logging

config = init_config()

client = TelegramClient('session', config.telegram.ApiId, config.telegram.ApiHash).start(bot_token=config.telegram.Token) # type: ignore

@client.on(events.NewMessage(pattern=fr'^/start({config.telegram.BotName})?$'))
async def start(event):
    message = None
    try:
        message = await event.respond(f'欢迎使用 {config.telegram.BotName} 机器人！')
        await help(event)
    except Exception as e:
        logging.error(e)
    finally:
        await asyncio.sleep(10)
        await event.delete()
        await message.delete() if message is not None else None
        raise events.StopPropagation

@client.on(events.NewMessage(pattern=fr'^/help({config.telegram.BotName})?$'))
async def help(event):
    message = None
    try:
        messages = f'''
/help - [私聊]帮助
/checkin - 签到
/signup - 注册, 仅开放注册时使用
/me - [私聊]查看 Emby 账户 和 个人 信息(包含其它工具)
/code - [私聊]使用注册码注册, 或者使用续期码续期。例: /code 123
/del - [管理员]删除 Emby 账户, 需回复一个用户
/warn - [管理员]警告用户, 需回复一个用户
/info - [管理员]查看用户信息
/settle - [管理员]手动结算积分
/change - [管理员]手动修改积分, 正数加负数减
    '''
        if event.is_private:
            message = await event.respond(messages)
        else:
            message = await event.reply(f'请私聊 {config.telegram.BotName} 机器人使用')
    except Exception as e:
        logging.error(e)
    finally:
        await asyncio.sleep(10)
        await event.delete()
        await message.delete() if message is not None else None
        raise events.StopPropagation

@client.on(events.NewMessage(pattern=fr'^/me({config.telegram.BotName})?$'))
async def me(event, TelegramId = None):
    messages = None
    keyboard = [
        [
            Button.inline('生成 “码”', data='code_create'),
            Button.inline('NSFW开关', data='nfsw'),
            Button.inline('忘记密码', data='forget_password')
        ],
        [
            Button.inline('续期', data='renew'),
            Button.inline('线路查询', data='line'),
            Button.inline('查询续期积分', data='query_renew')
        ],
        [
            Button.inline('求片', data='request'),
            Button.inline('上传字幕', data='subtitle'),
        ]
    ]
    if TelegramId is None:
        TelegramId = event.sender_id
    try:
        emby = await DataBase.GetEmby(TelegramId)
        user = await DataBase.GetUser(TelegramId)
        if user is not None:
            message = f'''
**Telegram ID**: `{user.TelegramId}`
**积分**: `{user.Score}`
**签到天数**: `{user.Checkin}`
**警告次数**: `{user.Warning}`
'''
        else:
            message = f'''
**Telegram ID**: `{TelegramId}`
**尚未建立积分账户**
'''
            
        if emby is not None:
            played_ratio = await EmbyAPI.UserPlaylist(emby.EmbyId, emby.LimitDate.strftime("%Y-%m-%d"))
            if played_ratio is not None:
                played_ratio = "{:.4f}%".format(played_ratio * 100)
            message += f'''
**Emby ID**: `{emby.EmbyId}`
**用户名**: `{emby.EmbyName}`
**观看度**: `{played_ratio}`
**Ban**: `{emby.Ban}`
'''
            if emby.Ban is True:
                message += f'**删除期**: `{emby.deleteDate}`'
            else:
                message += f'**有效期**: `{emby.LimitDate}`'
        
        if event.is_private:
            if emby is not None:
                await event.respond(message, parse_mode='Markdown', buttons=keyboard)
            else:
                await event.respond(message, parse_mode='Markdown')
        elif event.sender_id in config.other.AdminId and TelegramId != event.sender_id:
            messages = await event.reply(message, parse_mode='Markdown')
        else:
            messages = await event.reply(f'请私聊 {config.telegram.BotName} 机器人')
    except Exception as e:
        logging.error(e)
    finally:
        await asyncio.sleep(10)
        await event.delete()
        await messages.delete() if messages is not None else None
        raise events.StopPropagation
            
@client.on(events.NewMessage(pattern=fr'^/info({config.telegram.BotName})?$'))
async def info(event):
    message = None
    try:
        if event.sender_id in config.other.AdminId:
            if event.is_reply:
                reply = await event.get_reply_message()
                await me(event, reply.sender_id)
            else:
                message = await event.reply(f'请回复一个用户')
        else:
            message = await event.reply(f'仅管理员可用')
            await DataBase.ChangeWarning(event.sender_id)
    except Exception as e:
        logging.error(e)
    finally:
        await asyncio.sleep(10)
        await event.delete()
        await message.delete() if message is not None else None
        # raise events.StopPropagation
    
@client.on(events.CallbackQuery(data='line'))
async def line(event):
    message = None
    try:
        url = config.emby.Host.split(':')
        if len(url) == 2:
            if url[0] == 'https':
                url = config.emby.Host + ':443'
            else:
                url = config.emby.Host + ':80'
        else:
            url = config.emby.Host
        message = await event.respond(f'Emby 地址: `{url}`')
    except Exception as e:
        logging.error(e)
    finally:
        await asyncio.sleep(10)
        await event.delete()
        await message.delete() if message is not None else None
        raise events.StopPropagation
    
@client.on(events.ChatAction)
async def chat_action(event):
    message = None
    try:
        if event.user_joined or event.user_added:
            message = await client.send_message(event.chat_id, f'欢迎 [{event.user.first_name}](tg://user?id={event.user.id}) 加入本群\n 请查看[Wiki]({config.other.Wiki})了解本群规则和Bot使用方法)')
            await DataBase.CreateUsers(event.user.id)
        if event.user_left or event.user_kicked:
            message = await client.send_message(event.chat_id, f'[{event.user.first_name}](tg://user?id={event.user.id}) 离开了本群')
            await DataBase.DeleteUser(event.user.id)
            emby = await DataBase.GetEmby(event.user.id)
            if emby is not None:
                await DataBase.DeleteEmby(event.user.id)
                await EmbyAPI.DeleteEmbyUser(emby.EmbyId)
        if event.user_added and event.action_message.action.user_id == client.get_me().id:
            await client.send_message(event.chat_id, f'感谢使用 {config.telegram.BotName} 机器人, 请私聊机器人使用')
            async for user in client.iter_participants(config.telegram.ChatID):
                if user.bot is False:
                    qurey = await DataBase.GetUser(user.id)
                    if qurey is None:
                        await DataBase.CreateUsers(user.id)
    except Exception as e:
        logging.error(e)
    finally:
        await asyncio.sleep(10)
        await event.delete()
        await message.delete() if message is not None else None
        # raise events.StopPropagation