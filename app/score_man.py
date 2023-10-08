from telethon import types
from datetime import datetime, timedelta
from app.data import load_config
from app.telegram import send_scores_to_group, get_reply
from app.db import search_score, search_user, change_score, update_checkin, update_limit, create_code, init_renew_value, update_score
from app.regcode import generate_code
from app.emby_api import User_Policy
from app.telethon_api import reply
from random import randint, choices

group_id = load_config()['GROUP_ID']
admin_ids = load_config()['ADMIN_IDS']

user_msg_count = {}
user_id_old = None

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
            print(user_msg_count)

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
        n = score // 100
        result_score = (score - n * 100) / (n + 1)
        sigma_sum = sum(100 / i for i in range(1, n + 1))
        result_score += sigma_sum

        ratio = result_score / total_score
        user_ratios[user_id] = ratio

    return user_ratios, total_score

# 结算积分
async def handle_settle(client_user, event):
    tgid = event.sender_id
    if tgid in admin_ids:
        user_ratios, total_score = await calculate_scores()
        user_score = await update_score(user_ratios, total_score)
        await send_scores_to_group(client_user, group_id, user_score)
        user_msg_count.clear()                  # 清空字典
    else:
        await reply(event, '您非管理员, 无权执行此命令')

# 修改积分
async def handle_change_score(event):
    tgid = event.sender_id
    text = event.message.text
    _, *score = text.split(' ')
    reply_tgid = await get_reply(event)
    if reply_tgid is not None and tgid in admin_ids:
        await change_score(reply_tgid, int(score[0]))
        result_score = await search_score(reply_tgid)
        await reply(event, f'已更改, 当前用户积分为 {result_score[1]}')
    else:
        await reply(event, f'你非管理员 或 请回复一条消息')

async def handle_checkin(client, event):
    tgid = event.sender_id
    current_time = datetime.now().date()
    code_time = current_time + timedelta(days=90)
    result = await search_score(tgid)
    # diff_time = current_time - result[3]
    if result is None or result[3] is None or (current_time - result[3]) >= timedelta(days=1):
        score_value = randint(-2,5)
        if result is None or (result[2] % 7 != 0):
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
                    if user_result[4] is True:                  # 解封Emby
                        BlockMedia = ("Japan")
                        await User_Policy(user_result[1], BlockMedia)
                    message = '增加续期时间 1 天'
                else:
                    renew_value_1 = int(renew_value / 30)
                    await change_score(tgid, renew_value_1)
                    message = f'尚无账户, 已等比转为积分, 获得 {renew_value_1}'
            elif roulette == 'renew_7':
                if user_result is not None:
                    await update_limit(tgid, days=7)
                    if user_result[4] is True:                  # 解封Emby
                        BlockMedia = ("Japan")
                        await User_Policy(user_result[1], BlockMedia)
                    message = '增加续期时间 7 天'
                else:
                    renew_value_7 = int(renew_value / 30 * 7)
                    await change_score(tgid, renew_value_7)
                    message = f'尚无账户, 已等比转为积分, 获得 {renew_value_7}'
            elif roulette == 'renew_code':
                code, public_key, sha256_hash = await generate_code(admin_ids[0], 0)
                await create_code(code, public_key, sha256_hash, 0, code_time)
                message = '获得续期码(1月), 已私聊发送'
                await client.send_message(tgid, f'续期码(1月):\n`{code}`\n有效期至 {code_time}')
            elif roulette == 'signup_code':
                code, public_key, sha256_hash = await generate_code(admin_ids[0], 1)
                await create_code(code, public_key, sha256_hash, 1, code_time)
                message = '获得注册码, 已私聊发送'
                await client.send_message(tgid, f'注册码:\n`{code}`\n有效期至 {code_time}')
        await update_checkin(tgid)
    else:
        message = '今日已签到, 禁止重复签到'

    # 删除消息
    await reply(event, message)
