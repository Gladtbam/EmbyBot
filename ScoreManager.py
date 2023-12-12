from Telegram import client
from LoadConfig import init_config
from telethon import events, types
import DataBase
import EmbyAPI
from GenCode import generate_code
from datetime import datetime, timedelta
from random import randint, choices, choice
import logging
import asyncio
import re

config = init_config()
user_msg_count = {}
user_id_old = None
oldsum = 0

@client.on(events.NewMessage(pattern=fr'^/checkin({config.telegram.BotName})?$'))
async def checkin(event):
    try:
        current_time = datetime.now().date()
        query = await DataBase.GetUser(event.sender_id)
        if query is None or (current_time - query.LastCheckin.date()) >= timedelta(days=1): # type: ignore
            score = randint(-2, 5)
            if query is None or query.Checkin % 7 != 0:
                    _bool = await DataBase.ChangeCheckin(event.sender_id, score)
                    if _bool:
                        await event.reply(f'签到成功, 获得 {score} 分')
                    else:
                        await event.reply(f'签到失败, 请联系管理员')
            else:
                emby = await DataBase.GetEmby(event.sender_id)
                renew_value = await DataBase.GetRenewValue()
                options = ['fullcode', 'halfcode', 'weekcode', 'daycode', 'double']
                probability = [0.01, 0.02, 0.12, 0.15, 0.7]
                roulette = choices(options, probability)[0]
                if roulette == 'fullcode':
                    s = choice(['renew', 'signup'])
                    code = await generate_code(s)
                    if code is not None:
                        await DataBase.ChangeCheckin(event.sender_id)
                        await client.send_message(event.sender_id, f"您的 {'续期码' if s == 'renew' else '注册码'} 码为:\n`{code}`")
                elif roulette == 'halfcode':
                    if emby is not None:
                        _bool = await DataBase.UpdateLimitDate(event.sender_id, days=15)
                        if emby.Ban is True:
                            await EmbyAPI.User_Policy(emby.EmbyId, BlockMeida=("Japan"))
                        if _bool:
                            await DataBase.ChangeCheckin(event.sender_id)
                            await event.reply(f'签到成功, 续期 15 天')
                    else:
                        value = int(renew_value / 30 * 15)
                        _bool = await DataBase.ChangeCheckin(event.sender_id, value)
                        if _bool:
                            await event.reply(f'无Emby账户, 等比转换积分, 获得 {value} 分')
                elif roulette == 'weekcode':
                    if emby is not None:
                        _bool = await DataBase.UpdateLimitDate(event.sender_id, days=7)
                        if emby.Ban is True:
                            await EmbyAPI.User_Policy(emby.EmbyId, BlockMeida=("Japan"))
                        if _bool:
                            await DataBase.ChangeCheckin(event.sender_id)
                            await event.reply(f'签到成功, 续期 7 天')
                    else:
                        value = int(renew_value / 30 * 7)
                        _bool = await DataBase.ChangeCheckin(event.sender_id, value)
                        if _bool:
                            await event.reply(f'无Emby账户, 等比转换积分, 获得 {value} 分')
                elif roulette == 'daycode':
                    if emby is not None:
                        _bool = await DataBase.UpdateLimitDate(event.sender_id, days=1)
                        if emby.Ban is True:
                            await EmbyAPI.User_Policy(emby.EmbyId, BlockMeida=("Japan"))
                        if _bool:
                            await DataBase.ChangeCheckin(event.sender_id)
                            await event.reply(f'签到成功, 续期 1 天')
                    else:
                        value = int(renew_value / 30)
                        _bool = await DataBase.ChangeCheckin(event.sender_id, value)
                        if _bool:
                            await event.reply(f'无Emby账户, 等比转换积分, 获得 {value} 分')
                elif roulette == 'double':
                    value = int(score) * 2
                    _bool = await DataBase.ChangeCheckin(event.sender_id, value)
                    if _bool:
                        await event.reply(f'签到成功, 积分翻倍, 获得 {value} 分')
                    else:
                        await event.reply(f'签到失败, 请联系管理员')
        else:
            await event.reply(f'签到失败, 今日已签到, 禁止重复签到')
    except Exception as e:
        logging.error(e)
                
    finally:
        await asyncio.sleep(10)
        await event.delete()
        # raise events.StopPropagation
                
@client.on(events.NewMessage(chats=config.telegram.ChatID))
async def new_message(event):
    global user_id_old
    global oldsum
    if isinstance(event.message, types.Message) and isinstance(event.message.from_id, types.PeerUser):
        user_id = event.message.from_id.user_id
        if not event.message.text.startswith('/') and ['冒泡', '冒个泡', '好', '签到', '观看度'] not in event.message.text:
            if (user_id_old != user_id) and (user_id not in config.other.AdminId):
                user_id_old = user_id
                oldsum = 0
                if user_id in user_msg_count:
                    user_msg_count[user_id] += 1
                else:
                    user_msg_count[user_id] = 1
            else:
                oldsum += 1
            if oldsum >= 5:
                user = await event.client.get_entity(user_id)
                username = user.first_name + ' ' + user.last_name if user.last_name else user.first_name
                _bool = await DataBase.ChangeWarning(user_id)
                if _bool:
                    await event.reply(f"用户 [{username}](tg://user?id={user_id}) 发送消息过于频繁, 警告一次")
                else:
                    await client.send_message(config.telegram.ChatID, f"用户 [{username}](tg://user?id={user_id}) 发送消息过于频繁, 警告失败, 管理员手动处理")
                    
async def calculate_ratio():
    TotalScore = 0
    UserRatio = {}
    for user_id, score in user_msg_count.items():
        TotalScore += score
        
    for user_id, score in user_msg_count.items():
        n = score // 100
        result_score = (score - n * 100) / (n + 1)
        sigma_sum = sum(100 / i for i in range(1, n + 1))
        result_score += sigma_sum
        ratio = result_score / TotalScore
        UserRatio[user_id] = ratio
        
    return UserRatio, TotalScore

@client.on(events.NewMessage(pattern=fr'^/change({config.telegram.BotName})?\s+(.*)$'))
async def change(evnet):
    message = None
    try:
        if evnet.sender_id in config.other.AdminId:
            _, *args = evnet.message.text.split(' ')
            if len(args) > 0:
                reply = await evnet.get_reply_message()
                _bool = await DataBase.ChangeCheckin(reply.sender_id, int(args[0]))
                if _bool:
                    user = await DataBase.GetUser(reply.sender_id)
                    message = await evnet.reply(f'修改成功, 当前用户积分为 {user.Score}')
                else:
                    message = await evnet.reply(f'修改失败')
            else:
                message = await evnet.reply(f'参数错误, 请检查参数')
        else:
            message = await evnet.reply(f'权限不足')
            await DataBase.ChangeWarning(evnet.sender_id)
    except Exception as e:
        logging.error(e)
    finally:
        await asyncio.sleep(10)
        await evnet.delete()
        await message.delete() if message is not None else None
        raise events.StopPropagation
    
@client.on(events.NewMessage(pattern=fr'^/settle({config.telegram.BotName})?$'))
async def settle(event):
    try:
        if event.sender_id in config.other.AdminId:
            UserRatio, TotalScore = await calculate_ratio()
            userScore = await DataBase.SettleScore(UserRatio, TotalScore)
            if userScore is not None:
                message = await client.send_message(config.telegram.ChatID, f'积分结算完成, 共结算 {TotalScore} 分\n\t结算后用户积分如下:\n', parse_mode='Markdown')
                for userId, userValue in userScore.items():
                    user = await client.get_entity(userId)
                    username = user.first_name + ' ' + user.last_name if user.last_name else None
                    # message += f"[{username}](tg://user?id={userId}) 获得 {userValue} 分\n"
                    message = await client.edit_message(message, message.text + f"[{username}](tg://user?id={userId}) 获得 {userValue} 分\n", parse_mode='Markdown')
                # await client.send_message(config.telegram.ChatID, message, parse_mode='Markdown')
                user_msg_count.clear()
            else:
                await event.reply(f'结算失败, 无可结算积分')
        else:
            await event.reply(f'非管理员, 权限不足')
            await DataBase.ChangeWarning(event.sender_id)
    except Exception as e:
        logging.error(e)
    finally:
        await asyncio.sleep(10)
        await event.delete()
        # raise events.StopPropagation
        
@client.on(events.NewMessage(pattern=fr'^/warn({config.telegram.BotName})?$'))
async def change(evnet):
    message = None
    try:
        if evnet.sender_id in config.other.AdminId:
            reply = await evnet.get_reply_message()
            _bool = await DataBase.ChangeWarning(reply.sender_id)
            if _bool:
                user = await client.get_entity(reply.sender_id)
                username = user.first_name + ' ' + user.last_name if user.last_name else user.first_name
                message = await evnet.reply(f'[{username}](tg://user?id={reply.sender_id}) 被警告')
            else:
                message = await evnet.reply(f'警告失败')
        else:
            message = await evnet.reply(f'权限不足')
            await DataBase.ChangeWarning(evnet.sender_id)
    except Exception as e:
        logging.error(e)
    finally:
        await asyncio.sleep(10)
        await evnet.delete()
        await message.delete() if message is not None else None
        raise events.StopPropagation