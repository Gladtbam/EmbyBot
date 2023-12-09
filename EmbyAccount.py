from Telegram import client
from LoadConfig import init_config
from telethon import events, types
from datetime import datetime, timedelta
import DataBase
import EmbyAPI
import GenCode
import re
import asyncio
import logging

config = init_config()

signup_info = {"time": 0, "remain_num": 0.0}      # 注册方法
signup_message = None

@client.on(events.NewMessage(pattern=fr'^/signup(?:{config.telegram.BotName})?(\s.*)?$'))
async def signup_method(event):
    global signup_message
    _, *args = event.message.text.split(' ')
    current_time = datetime.now().timestamp()
    user = await DataBase.GetUser(event.sender_id)
    signup_value = await DataBase.GetRenewValue() * config.other.Ratio
    try:
        if event.sender_id in config.other.AdminId:
            if len(args) > 0:
                if re.match(r'^\d+$', args[0]):
                    signup_info["remain_num"] = args[0]
                    signup_message = await client.send_message(config.telegram.ChatID, f'开启注册, 剩余 {signup_info["remain_num"]} 个名额')
                elif re.match(r'^(\d+[hms])+$', args[0]):
                    last_time = re.match(r'(\d+h)?(\d+m)?(\d+s)?', args[0])
                    if last_time is not None:
                        hours = int(last_time.group(1)[:-1]) if last_time.group(1) else 0
                        minutes = int(last_time.group(2)[:-1]) if last_time.group(2) else 0
                        seconds = int(last_time.group(3)[:-1]) if last_time.group(3) else 0
                        signup_info["time"] = current_time + (timedelta(hours=hours) + timedelta(minutes=minutes) + timedelta(seconds=seconds)).total_seconds()
                    dt_object = datetime.fromtimestamp(float(signup_info["time"]))
                    signup_message = await client.send_message(config.telegram.ChatID, f'开启注册, 时间截至 {dt_object.strftime("%Y-%m-%d %H:%M:%S")}')
                await client.pin_message(config.telegram.ChatID, signup_message, notify=True)
            else:
                await signup(event, event.sender_id)
        else:
            if signup_info['remain_num'] > 0:
                await signup(event, event.sender_id)
                signup_info['remain_num'] -= 1
                await client.edit_message(config.telegram.ChatID, signup_message, f"开启注册, 剩余注册人数: {signup_info['remain_num']}")
            elif signup_info['time'] > current_time:
                await signup(event, event.sender_id)
            elif user is not None and user.Score >= signup_value:
                await signup(event, event.sender_id)
                await DataBase.ChangeScore(event.sender_id, -signup_value)
            else:
                await event.reply(f'注册失败, 积分不足, 当前积分: {user.Score if user is not None else 0}, 注册所需积分: {signup_value}')
    except Exception as e:
        logging.error(e)
    finally:
        await asyncio.sleep(10)
        await event.delete()
        # # await event.message.delete()
        if (signup_info['remain_num'] == 0 or signup_info['time'] < current_time) and signup_message is not None:
            await signup_message.delete()
        # raise events.StopPropagation
    
async def signup(event, TelegramId):
    try:
        user = await event.client.get_entity(TelegramId)
        TelegramName = user.username
        BlockMedia = ("Japan")
        
        if TelegramName is None:
            await event.reply(f'注册失败, 请先设置 Telegram 用户名')
            return False
        else:
            emby = await DataBase.GetEmby(TelegramId)
            if emby is None:
                EmbyId = await EmbyAPI.NewUser(TelegramName)
                if EmbyId is not None:
                    await EmbyAPI.User_Policy(EmbyId, BlockMeida=BlockMedia)
                    Pw = await EmbyAPI.Password(EmbyId)
                    _bool = await DataBase.CreateEmby(TelegramId, EmbyId, TelegramName)
                    if _bool:
                        await event.reply(f'注册成功, \nEMBY ID: `{EmbyId}`\n用户名: `{TelegramName}`\n初始密码: `{Pw}`\n\n请及时修改密码')
                        return True
                    else:
                        await event.reply(f'注册失败, ⚠️数据库错误，请联系管理员')
                        return False
                else:
                    await event.reply(f'注册失败, 无法创建账户，请联系管理员')
                    return False
            else:
                await event.reply(f'用户已存在')
                return False
    except Exception as e:
        logging.error(e)
        return False
    finally:
        await asyncio.sleep(10)
        await event.delete()
        # raise events.StopPropagation
    
@client.on(events.NewMessage(pattern=fr'^/code({config.telegram.BotName})?\s+(.*)$'))
async def codeCheck(event):
    _, *args = event.message.text.split(' ')
    try:
        if len(args) > 0:
            if event.is_private or event.sender_id in config.other.AdminId:
                await code(event, args[0])
            else:
                await event.reply(f'请私聊 {config.telegram.BotName} 机器人')
        else:
            await event.reply(f'请回复 “码”')
    except Exception as e:
        logging.error(e)
    finally:
        await asyncio.sleep(10)
        await event.delete()
        # await event.message.delete()
        # raise events.StopPropagation
    
async def code(event, code):
    try:
        plaintext = await GenCode.decrypt_code(code)
        if plaintext is not None:
            if plaintext == 'signup':
                await signup(event, event.sender_id)
                await DataBase.DeleteCode(code)
            elif plaintext == 'renew':
                emby = await DataBase.GetEmby(event.sender_id)
                if emby is not None:
                    remain_day = emby.LimitDate.date() - datetime.now().date()
                    if remain_day.days <= 7:
                        await DataBase.UpdateLimitDate(event.sender_id)
                        await DataBase.DeleteCode(code)
                        if emby.Ban is True:
                            await EmbyAPI.User_Policy(emby.EmbyId, BlockMeida=("Japan"))
                        await event.reply(f'续期成功')
                    else:
                        await event.reply(f'离到期还有 {remain_day.days} 天\n目前小于 7 天才允许续期')
                else:
                    await event.reply(f'用户不存在, 请注册')
            else:
                await event.reply(f'不存在对应的：{plaintext}, 码无效, 请联系管理员')
        else:
            await event.reply(f'码无效')
    except Exception as e:
        logging.error(e)
    finally:
        await asyncio.sleep(10)
        await event.delete()
        # await event.message.delete()
        # raise events.StopPropagation
    
@client.on(events.NewMessage(pattern=fr'^/del({config.telegram.BotName})?$'))
async def delete(event):
    try:
        if event.sender_id in config.other.AdminId:
            if event.reply_to_msg_id is not None:
                message = await event.get_reply_message()
                if isinstance(message, types.Message) and isinstance(message.from_id, types.PeerUser):
                    user_id = message.from_id.user_id
                    emby = await DataBase.GetEmby(user_id)
                    if emby is not None:
                        _bool_db = await DataBase.DeleteEmby(user_id)
                        _bool_emby = await EmbyAPI.DeleteEmbyUser(emby.EmbyId)
                        if _bool_db and _bool_emby:
                            await event.reply(f'用户 {emby.EmbyId} 删除成功')
                        else:
                            await event.reply(f'用户 {emby.EmbyId} 删除失败, 原因: db: {_bool_db}, emby: {_bool_emby}')
                    else:
                        await event.reply(f'用户不存在')
                else:
                    await event.reply(f'请回复一个用户')
            else:
                await event.reply(f'请回复一个用户')
        else:
            await event.reply(f'非管理员, 权限不足')
    except Exception as e:
        logging.error(e)
    finally:
        await asyncio.sleep(10)
        await event.delete()
        # await event.message.delete()
        # raise events.StopPropagation
    
@client.on(events.CallbackQuery(data='renew'))
async def renew(event):
    try:
        emby = await DataBase.GetEmby(event.sender_id)
        if emby is not None:
            remain_day = emby.LimitDate.date() - datetime.now().date()
            if remain_day.days <= 7:
                user = await DataBase.GetUser(event.sender_id)
                played_ratio = await EmbyAPI.UserPlaylist(emby.EmbyId, emby.LimitDate.strftime("%Y-%m-%d"))
                if played_ratio is not None:
                    if played_ratio >= 1:
                        renew_value = 0
                    else:
                        renew_value = int(await DataBase.GetRenewValue()) * (1 - (0.5 * played_ratio))
                    if user is not None and user.Score >= renew_value:
                        await DataBase.UpdateLimitDate(event.sender_id)
                        await DataBase.ChangeScore(event.sender_id, -renew_value)
                        if emby.Ban is True:
                            await EmbyAPI.User_Policy(emby.EmbyId, BlockMeida=("Japan"))
                        await event.respond(f'续期成功, 扣除积分: {renew_value}')
                    else:
                        await event.respond(f'续期失败, 积分不足, 当前积分: {user.Score if user is not None else 0}, 续期所需积分: {renew_value}')
                else:
                    await event.respond(f'续期失败, 未查询到观看度, 请稍后重试')
            else:
                await event.respond(f'离到期还有 {remain_day.days} 天\n目前小于 7 天才允许续期')
        else:
            await event.respond(f'用户不存在, 请注册')
    except Exception as e:
        logging.error(e)
    finally:
        await asyncio.sleep(10)
        await event.delete()
        # await event.message.delete()
        # raise events.StopPropagation
    
@client.on(events.CallbackQuery(data='nfsw'))
async def nfsw(event):
    try:
        emby = await DataBase.GetEmby(event.sender_id)
        if emby is not None:
            emby_info = await EmbyAPI.GetUserInfo(emby.EmbyId)
            if len(emby_info['Policy']['BlockedMediaFolders']) > 0:
                await EmbyAPI.User_Policy(emby.EmbyId, BlockMeida=())
                await event.respond(f'NSFW On')
            else:
                await EmbyAPI.User_Policy(emby.EmbyId, BlockMeida=("Japan"))
                await event.respond(f'NSFW Off')
        else:
            await event.respond(f'用户不存在, 请注册')
    except Exception as e:
        logging.error(e)
    finally:
        await asyncio.sleep(10)
        await event.delete()
        # await event.message.delete()
        # raise events.StopPropagation
    
@client.on(events.CallbackQuery(data='forget_password'))
async def forget_password(event):
    try:
        emby = await DataBase.GetEmby(event.sender_id)
        if emby is not None:
            Pw = await EmbyAPI.Password(emby.EmbyId, ResetPassword=True)
            await event.respond(f'密码已重置:\n `{Pw}`\n请及时修改密码')
        else:
            await event.respond(f'用户不存在, 请注册')
    except Exception as e:
        logging.error(e)
    finally:
        await asyncio.sleep(60)
        await event.delete()
        # raise events.StopPropagation
    
@client.on(events.CallbackQuery(data='query_renew'))
async def query_renew(event):
    try:
        value = await DataBase.GetRenewValue()
        await event.respond(f'当前续期积分: {value}')
    except Exception as e:
        logging.error(e)
    finally:
        await asyncio.sleep(10)
        await event.delete()
        # await event.message.delete()
        # raise events.StopPropagation