from telethon import events, types
from datetime import datetime, timedelta
from asyncio import sleep
from app.data import load_config
from app.db import search_score, search_user, change_score, update_checkin, update_limit, create_code, init_renew_value
from app.regcode import generate_code
from random import random, randint, choices

group_id = load_config()['GROUP_ID']
admin_ids = load_config()['ADMIN_IDS']
# file_path = 'user_msg_count.json'

user_msg_count = {}
user_id_old = None

def score_commands(client):
    @client.on(events.NewMessage(chats=group_id))
    async def handle_new_message(event):                        # 统计用户消息
        global user_id_old
        if isinstance(event.message, types.Message) and isinstance(event.message.from_id, types.PeerUser):
            user_id = event.message.from_id.user_id
            message = event.message

            if message.media is not None:
                if message.photo is not None:
                    msg_type = 'photo'
                elif message.video is not None:
                    msg_type = 'video'
                elif message.document is not None:
                    msg_type = 'document'
                else:
                    msg_type = 'media'
            else:
                msg_type = 'text'
            
            if user_id not in admin_ids and (user_id != user_id_old):
                if not event.message.text.startswith('/'):
                    if user_id in user_msg_count:
                        if msg_type in user_msg_count[user_id]:
                            user_msg_count[user_id][msg_type] += 1
                        else:
                            user_msg_count[user_id][msg_type] = 1
                    else:
                        user_msg_count[user_id] = {msg_type: 1}

                    user_id_old = user_id
                # print(user_msg_count)
            # await save_user_msg_count(file_path, user_msg_count)

# 计算比例
async def calculate_scores():
    scores = {}
    total_score = 0

    for user_id, messages in user_msg_count.items():
        score = 0
        for msg_type, count in messages.items():
            if msg_type in ['photo', 'video']:            # 图片和视频消息 2分
                score += count * 2
            elif msg_type == 'text':                        # 文本消息 1分
                score += count * 1
            elif msg_type == 'voice':                       # 视频消息 3分
                score += count * 3
            elif msg_type == 'document':                    # 文件(贴纸)消息 3分
                score += count * 1
        scores[user_id] = score
        total_score += score

    user_ratios = {}
    for user_id, score in scores.items():
        # b = (a - n*100)/(n+1) + Σ(100/i)
        n = score // 100
        result_score = (score - n * 100) / (n + 1)
        sigma_sum = sum(100 / i for i in range(1, n + 1))
        result_score += sigma_sum

        ratio = result_score / total_score
        user_ratios[user_id] = ratio

    return user_ratios, total_score

async def handle_checkin(event, client, tgid):
    current_time = datetime.now()
    result = await search_score(tgid)
    # diff_time = current_time - result[3]
    if result is None or result[3] is None or (current_time - result[3]) >= timedelta(days=1):
        score_value = randint(-2,5)
        if result is None or result[2] < 7:
            await change_score(tgid, score_value)
            message = f'签到成功, 获得 {score_value} 分'
        else:
            user_result = await search_user(tgid)
            renew_value = int(init_renew_value())
            options = ['signup_code', 'renew_code','renew_7', 'renew_1', 'x2']
            probabilities = [0.03, 0.05, 0.1, 0.2, 0.62]
            roulette = choices(options, weights=probabilities, k=1)[0]
            if roulette == 'x2':
                score_value = abs(score_value) * 2
                await change_score(tgid, score_value)
                await update_checkin(tgid)
                message = f'积分翻倍,获得 {score_value} 分'
            elif roulette == 'renew_1':
                if user_result is not None:
                    await update_limit(tgid, days=1)
                    message = '增加续期时间 1 天'
                else:
                    renew_value_1 = int(renew_value / 30)
                    await change_score(tgid, renew_value_1)
                    message = f'尚无账户, 已等比转为积分, 获得 {renew_value_1}'
            elif roulette == 'renew_7':
                if user_result is not None:
                    await update_limit(tgid, days=7)
                    message = '增加续期时间 7 天'
                else:
                    renew_value_7 = int(renew_value / 30 * 7)
                    await change_score(tgid, renew_value_7)
                    message = f'尚无账户, 已等比转为积分, 获得 {renew_value_7}'
            elif roulette == 'renew_code':
                code, public_key, sha256_hash, data = await generate_code(admin_ids[0], 0)
                await create_code(code, public_key, sha256_hash, data)
                message = '获得续期码(1月), 已私聊发送'
                await client.send_message(tgid, f'续期码(1月):\n{code}')
            elif roulette == 'signup_code':
                code, public_key, sha256_hash, data = await generate_code(admin_ids[0], 1)
                await create_code(code, public_key, sha256_hash, data)
                message = '获得注册码, 已私聊发送'
                await client.send_message(tgid, f'注册码:\n{code}')
        await update_checkin(tgid)
    else:
        message = f'已签到, 上次签到时间: {result[3]}'

    # 删除消息
    reply_message = await event.reply(message)
    message_ids = [reply_message.id, reply_message.reply_to_msg_id]
    print(message_ids)
    await sleep(10)
    await client.delete_messages(event.chat_id, message_ids)
